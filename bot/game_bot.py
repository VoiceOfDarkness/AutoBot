import time
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from datetime import datetime, timedelta
from typing import List, Tuple, Callable
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
        self.status_message = "Ожидание..."
        self.user_data = {}

    def run(self):
        self.running = True
        console.print(Panel("[title]🎮 GameBot запускается[/title]", expand=False))

        with Live(self._generate_status_table(), refresh_per_second=1) as live:
            while self.running:
                try:
                    self._process_cycle()
                    self.status_message = "Ожидание следующего цикла..."
                    live.update(self._generate_status_table())
                    time.sleep(300)
                except Exception as e:
                    self._handle_error(e)
                    live.update(self._generate_status_table())

    def _generate_status_table(self) -> Table:
        table = Table(show_header=False, box=None, padding=(0, 1))

        if self.user_data:
            table.add_row(
                "[info]💰 Баланс:[/info]",
                f"[value]{self.user_data.get('balance', 0):.2f}[/value]",
            )
            table.add_row(
                "[info]🛡️ Щит:[/info]",
                f"[value]{self.user_data.get('shield', 0)} ({'Активен' if self.user_data.get('shield_active') else 'Неактивен'})[/value]",
            )

            times = {
                "⏰ Последний клейм": self.user_data.get("claimed_last"),
                "🔄 Следующий дейли": self.user_data.get("daily_next_at"),
                "⛽ Последняя заправка": self.user_data.get("fuel_last_at"),
                "🛡 Иммунитет щита до": self.user_data.get("shield_immunity_at"),
                "🛡 Щит активен до": self.user_data.get("shield_ended_at"),
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
        table.add_row(f"[info]Статус:[/info] {self.status_message}")

        return Panel(table, expand=False)

    def _process_cycle(self):
        try:
            user_data = self.client.get_user()
            if not user_data or "user" not in user_data:
                raise ValueError("Некорректный ответ от API")

            self.user_data = user_data["user"]
            state = UserState.from_response(user_data["user"])
            current_time = datetime.now()

            self._process_actions(state, current_time)

        except Exception as e:
            self.status_message = f"[error]Ошибка: {str(e)}[/error]"
            raise

    def _process_actions(self, state: UserState, current_time: datetime):
        actions: List[Tuple[Callable, Callable, str]] = [
            (state.should_claim_daily, self._daily, "ежедневную награду"),
            (state.should_claim, self._claim, "баланс"),
            (state.should_get_fuel, self._get_fuel, "топливо"),
            (state.should_get_shield, self._get_shield, "щит"),
            (
                state.should_get_shield_immunity,
                self._get_shield_immunity,
                "иммунитет щита",
            ),
        ]

        for should_execute, execute, action_name in actions:
            try:
                if should_execute(current_time):
                    self.status_message = f"Получаем {action_name}..."
                    execute()
                    console.print(
                        f"[success]✓ Успешно получили {action_name}[/success]"
                    )
                    time.sleep(5)
            except Exception as e:
                console.print(
                    f"[error]✗ Ошибка при получении {action_name}: {e}[/error]"
                )

    def _handle_error(self, error: Exception):
        for delay in self.retry_delays:
            self.status_message = f"[error]Ошибка: {str(error)}. Повторная попытка через {delay} секунд...[/error]"
            time.sleep(delay)
            try:
                return
            except Exception as e:
                self.status_message = (
                    f"[error]Ошибка при повторной попытке: {str(e)}[/error]"
                )

        self.status_message = "[error]Достигнуто максимальное количество попыток. Бот останавливается.[/error]"
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
