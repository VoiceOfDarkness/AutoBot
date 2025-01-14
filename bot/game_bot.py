import time
from datetime import datetime
from time import sleep
from typing import Callable, List, Tuple

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
        self.task_data = {}

    def run(self):
        self.running = True
        console.print(Panel("[title]🎮 GameBot is starting[/title]", expand=False))

        with Live(self._generate_status_table(), refresh_per_second=1) as live:
            while self.running:
                try:
                    self._process_cycle()
                    self.status_message = "Waiting for next call..."
                    live.update(self._generate_status_table())
                    time.sleep(300)
                except Exception as e:
                    self._handle_error(e)
                    live.update(self._generate_status_table())

    def _generate_status_table(self) -> Table:
        table = Table(show_header=False, box=None, padding=(0, 1))

        if self.user_data:
            table.add_row(
                "[info]💰 Balance:[/info]",
                f"[value]{self.user_data.get('balance', 0):.2f}[/value]",
            )
            table.add_row(
                "[info]🛡️ Shield:[/info]",
                f"[value]{self.user_data.get('shield', 0)} ({'Active' if self.user_data.get('shield_active') else 'Not Active'})[/value]",
            )

            times = {
                "⏰ Last Claim": self.user_data.get("claimed_last"),
                "🔄 Next Daily": self.user_data.get("daily_next_at"),
                "⛽ Last refueling": self.user_data.get("fuel_last_at"),
                "🛡 Shield immunity up to": self.user_data.get("shield_immunity_at"),
                "🛡 Shield is active until": self.user_data.get("shield_ended_at"),
                "🎰 Spin after": self.user_data.get("spin_after_at"),
            }

            for label, time_str in times.items():
                if time_str:
                    try:
                        dt = datetime.fromisoformat(time_str.replace("Z", ""))
                        formatted_time = dt.strftime("%H:%M:%S %d.%m.%Y")
                        table.add_row(
                            f"[info]{label}:[/info]", f"[value]{formatted_time}[/value]"
                        )
                    except:
                        table.add_row(
                            f"[info]{label}:[/info]", "[value]Нет данных[/value]"
                        )

        table.add_row("")
        table.add_row("")
        table.add_row(f"[info]Status:[/info] {self.status_message}")

        return Panel(table, expand=False)

    def _process_cycle(self):
        try:
            user_data = self.client.get_user()
            task_data = self.client.get_tasks()
            if not user_data or "user" not in user_data:
                raise ValueError("Incorrect response from API")

            self.user_data = user_data["user"]
            self.task_data = task_data["listCompleted"][0]

            state = UserState.from_response(
                user_data["user"], task_data["listCompleted"][0]
            )
            current_time = datetime.now()

            self._process_actions(state, current_time)

        except Exception as e:
            self.status_message = f"[error]Error: {str(e)}[/error]"
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
                    execute()
                    self.status_message = f"Completed successfully: {action_name}."
                    console.print(f"[success]✓ {self.status_message}[/success]")
                    time.sleep(5)
            except Exception as e:
                console.print(
                    f"[error]✗ Error while executing {action_name}: {e}[/error]"
                )

    def _handle_error(self, error: Exception):
        for delay in self.retry_delays:
            self.status_message = (
                f"[error]Error: {str(error)}. Try after {delay} seconds...[/error]"
            )
            time.sleep(delay)
            try:
                return
            except Exception as e:
                self.status_message = f"[error]Error while retrying: {str(e)}[/error]"

        self.status_message = (
            "[error]Maximum number of attempts reached. Bot stops.[/error]"
        )
        console.print(Panel(self.status_message, style="error"))
        self.running = False

    def _claim(self):
        response = self.client.claim()
        self.user_data = response["user"]

    def _daily(self):
        self.client.get_daily()

    def _get_fuel(self):
        self.client.get_fuel()

    def _get_shield(self):
        self.client.get_shield()

    def _get_shield_immunity(self):
        self.client.get_shield_immunity()

    def _get_task_adv(self):
        self.client.get_onclick_task()
        sleep(10)

    def _get_roulette(self):
        self.client.get_roulette()
