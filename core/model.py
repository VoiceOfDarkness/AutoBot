from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum


class FuelLevel(Enum):
    LEVEL_1 = (1, 30)
    LEVEL_2 = (2, 60)
    LEVEL_3 = (3, 90)
    LEVEL_4 = (4, 120)
    LEVEL_5 = (5, 150)

    def __init__(self, level: int, delay: int):
        self.level = level
        self.delay = delay

    @classmethod
    def from_level(cls, level: int) -> "FuelLevel":
        for fuel_level in cls:
            if fuel_level.level == level:
                return fuel_level
        return max(cls, key=lambda x: x.level)


@dataclass
class TaskState:
    completed_task: bool
    last_completed_at: Optional[str]

    @classmethod
    def from_response(cls, data: List[dict]) -> "TaskState":
        if not data:
            return cls(
                completed_task=False,
                last_completed_at=None,
            )
        return cls(
            completed_task=True,
            last_completed_at=data[0]["locale_time"],
        )

    def is_ready(self, current_time: datetime) -> bool:
        if self.completed_task:
            return False
        if self.last_completed_at:
            task_completed_at = datetime.fromisoformat(
                self.last_completed_at
            ) + timedelta(hours=1)
            return current_time > task_completed_at
        return True


@dataclass
class UserState:
    balance: float
    level_fuel: int
    claimed_last_at: Optional[str]
    shield: int
    shield_active: bool
    shield_immunity_at: Optional[str]
    daily_next_at: Optional[str]
    fuel_last_at: Optional[str]
    shield_ended_at: Optional[str]
    spin_after_at: Optional[str]
    task: TaskState

    @classmethod
    def from_response(cls, data: dict, task_data: List) -> "UserState":
        return cls(
            balance=float(data["balance"]),
            level_fuel=int(data["level_fuel"]),
            claimed_last_at=data.get("claimed_last"),
            shield_active=data.get("shield_active"),
            shield_immunity_at=data.get("shield_immunity_at"),
            shield=int(data["shield"]),
            daily_next_at=data.get("daily_next_at"),
            fuel_last_at=data.get("fuel_last_at"),
            shield_ended_at=data.get("shield_free_after_at"),
            spin_after_at=data.get("spin_after_at"),
            task=TaskState.from_response(task_data),
        )

    def _get_fuel_delay(self) -> int:
        fuel_level = FuelLevel.from_level(self.level_fuel)
        return fuel_level.delay

    def should_get_fuel(self, current_time: datetime) -> bool:
        if not self.fuel_last_at:
            return True

        delay_minutes = self._get_fuel_delay()
        next_fuel_time = datetime.fromisoformat(self.fuel_last_at) + timedelta(
            minutes=delay_minutes
        )

        return current_time > next_fuel_time

    def should_claim_daily(self, current_time: datetime) -> bool:
        if not self.daily_next_at:
            return True
        next_claim_time = datetime.fromisoformat(self.daily_next_at) + timedelta(
            hours=1
        )
        return current_time >= next_claim_time

    def should_claim(self, current_time: datetime) -> bool:
        if not self.claimed_last_at:
            return True
        next_claim_time = datetime.fromisoformat(self.claimed_last_at) + timedelta(
            hours=1, minutes=15
        )
        return current_time > next_claim_time

    def should_get_shield(self, current_time: datetime) -> bool:
        if not self.shield_ended_at:
            return True
        return not self.shield_active and self.balance > 15

    def should_get_shield_immunity(self, current_time: datetime) -> bool:
        if not self.shield_immunity_at:
            return True
        shield_immunity_time = datetime.fromisoformat(
            self.shield_immunity_at
        ) + timedelta(hours=1, minutes=30)
        return current_time > shield_immunity_time and self.balance > 8

    def should_get_onclick_task(self, current_time: datetime) -> bool:
        return self.task.is_ready(current_time)

    def should_get_roulette(self, current_time: datetime) -> bool:
        if not self.spin_after_at:
            return True
        spin_after_time = datetime.fromisoformat(self.spin_after_at) + timedelta(
            hours=1
        )
        return current_time > spin_after_time
