import time
from datetime import datetime, timedelta
from time import sleep
from typing import Callable, List, Tuple
from collections import deque

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from core.model import UserState

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "title": "blue bold",
        "value": "bright_white",
        "log": "dim white",
        "timestamp": "bright_black",
    }
)

console = Console(theme=custom_theme)


class GameBot:
    def __init__(self, api_client):
        self.client = api_client
        self.running = False
        self.retry_delays = [5, 10, 30, 60]
        self.status_message = "Waiting..."
        self.user_data = {}
        self.logs = deque(maxlen=10)  # last 10 logs
        self._add_log("System initialized", "info")

    def _add_log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append((timestamp, message, level))

    def _generate_status_table(self) -> Table:
        main_table = Table(show_header=False, box=None, padding=(0, 2))

        if self.user_data:
            main_table.add_row(
                "[info]💰 Balance:[/info]",
                f"[value]{self.user_data.get('balance', 0):.2f}[/value]",
            )
            shield_status = (
                "Active" if self.user_data.get("shield_active") else "Not Active"
            )
            main_table.add_row(
                "[info]🛡️ Shield:[/info]",
                f"[value]{self.user_data.get('shield', 0)} ({shield_status})[/value]",
            )

        times = {
            "⏰ Last Claim": self.user_data.get("claimed_last"),
            "🔄 Next Daily": self.user_data.get("daily_next_at"),
            "⛽ Last refueling": self.user_data.get("fuel_last_at"),
            "🛡 Shield immunity up to": self.user_data.get("shield_immunity_at"),
            "🛡 Shield is active until": self.user_data.get("shield_free_after_at"),
            "🎰 Spin after": self.user_data.get("spin_after_at"),
        }

        for label, time_str in times.items():
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str.replace("Z", "")) + timedelta(
                        hours=1
                    )
                    formatted_time = dt.strftime("%H:%M:%S %d.%m.%Y")
                    time_left = (dt - datetime.now()).total_seconds()
                    if time_left > 0:
                        hours = int(time_left // 3600)
                        minutes = int((time_left % 3600) // 60)
                        seconds = int(time_left % 60)
                        time_left_str = (
                            f" ({hours:02d}:{minutes:02d}:{seconds:02d} left)"
                        )
                    else:
                        time_left_str = " (Ready!)"
                    main_table.add_row(
                        f"[info]{label}:[/info]",
                        f"[value]{formatted_time}{time_left_str}[/value]",
                    )
                except:
                    main_table.add_row(
                        f"[info]{label}:[/info]", "[value]No data[/value]"
                    )

        main_table.add_row("")
        main_table.add_row(f"[info]Status:[/info] {self.status_message}")

        if self.logs:
            main_table.add_row("")
            main_table.add_row("[info]Recent Activity:[/info]")
            for timestamp, message, level in reversed(self.logs):
                main_table.add_row(
                    f"[timestamp]{timestamp}[/timestamp]",
                    f"[{level}]{message}[/{level}]",
                )

        return Panel(main_table, title="[title]🎮 GameBot Status[/title]", expand=False)

    def run(self):
        try:
            user_data = self.client.get_user()
            if not user_data or "user" not in user_data:
                self._add_log("Failed to initialize user data", "error")
                return

            self.user_data = user_data["user"]

            if self.user_data["tech_work"]:
                self._add_log("Tech work is active. Bot is disabled", "error")
                console.print(
                    Panel("Tech work is active. Bot is disabled", style="error")
                )
                return

            self.running = True
            self._add_log("GameBot is starting", "success")

        except Exception as e:
            self._add_log(f"Initialization error: {str(e)}", "error")
            return

        with Live(self._generate_status_table(), refresh_per_second=1) as live:
            while self.running:
                try:
                    self._process_cycle()
                    self.status_message = "Waiting for next cycle..."
                    live.update(self._generate_status_table())
                    time.sleep(300)
                except Exception as e:
                    self._handle_error(e)
                    live.update(self._generate_status_table())

    def _process_cycle(self):
        try:
            task_data = self.client.get_tasks()
            state = UserState.from_response(self.user_data, task_data["listCompleted"])
            current_time = datetime.now()
            self._process_actions(state, current_time)

        except Exception as e:
            self.status_message = f"[error]Error: {str(e)}[/error]"
            self._add_log(f"Error in process cycle: {str(e)}", "error")
            raise

    def _process_actions(self, state: UserState, current_time: datetime):
        actions: List[Tuple[Callable, Callable, str]] = [
            (state.should_claim_daily, self._daily, "daily reward"),
            (state.should_claim, self._claim, "balance"),
            (state.should_get_fuel, self._get_fuel, "fuel"),
            (state.should_get_shield, self._get_shield, "shield"),
            (
                state.should_get_shield_immunity,
                self._get_shield_immunity,
                "shield immunity",
            ),
            (state.should_get_onclick_task, self._get_task_adv, "task"),
            (state.should_get_roulette, self._get_roulette, "roulette"),
        ]

        for should_execute, execute, action_name in actions:
            try:
                if should_execute(current_time):
                    self.status_message = f"Getting {action_name}..."
                    self._add_log(f"Attempting to get {action_name}", "info")
                    execute()
                    self.status_message = f"Completed successfully: {action_name}."
                    self._add_log(f"Successfully obtained {action_name}", "success")
                    sleep(30)
            except Exception as e:
                error_message = f"Error while executing {action_name}: {e}"
                self._add_log(error_message, "error")
                console.print(f"[error]✗ {error_message}[/error]")

    def _handle_error(self, error: Exception):
        for delay in self.retry_delays:
            error_message = f"Error: {str(error)}. Retrying in {delay} seconds..."
            self.status_message = f"[error]{error_message}[/error]"
            self._add_log(error_message, "warning")
            time.sleep(delay)
            try:
                return
            except Exception as e:
                self._add_log(f"Retry failed: {str(e)}", "error")

        final_message = "Maximum number of attempts reached. Bot stops."
        self.status_message = f"[error]{final_message}[/error]"
        self._add_log(final_message, "error")
        console.print(Panel(self.status_message, style="error"))
        self.running = False

    def _claim(self):
        response = self.client.claim()
        self.user_data = response["user"]
        self._add_log("Claimed balance successfully", "success")

    def _daily(self):
        response = self.client.get_daily()
        self.user_data = response["user"]
        self._add_log("Collected daily reward", "success")

    def _get_fuel(self):
        response = self.client.get_fuel()
        self.user_data = response["user"]
        self._add_log("Refueled successfully", "success")

    def _get_shield(self):
        response = self.client.get_shield()
        self.user_data = response["user"]
        self._add_log("Shield obtained", "success")

    def _get_shield_immunity(self):
        response = self.client.get_shield_immunity()
        self.user_data = response["user"]
        self._add_log("Shield immunity obtained", "success")

    def _get_task_adv(self):
        response = self.client.get_onclick_task()
        self.user_data = response["user"]
        self._add_log("Started task advertisement", "info")
        sleep(10)
        self._add_log("Completed task advertisement", "success")

    def _get_roulette(self):
        response = self.client.get_roulette()
        self.user_data = response["user"]
        self._add_log("Spin completed", "success")
