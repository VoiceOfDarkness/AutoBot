from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class UserState:
    balance: float
    claimed_last_at: Optional[str]
    shield: int
    shield_active: bool
    shield_immunity_at: Optional[str]
    daily_next_at: Optional[str]
    fuel_last_at: Optional[str]
    shield_ended_at: Optional[str]

    @classmethod
    def from_response(cls, data: dict) -> "UserState":
        return cls(
            balance=float(data["balance"]),
            claimed_last_at=data.get("claimed_last"),
            shield_active=data.get("shield_active"),
            shield_immunity_at=data.get("shield_immunity_at"),
            shield=int(data["shield"]),
            daily_next_at=data.get("daily_next_at"),
            fuel_last_at=data.get("fuel_last_at"),
            shield_ended_at=data.get("shield_ended_at"),
        )

    def should_claim_daily(self, current_time: datetime) -> bool:
        if not self.daily_next_at:
            return False
        next_claim_time = datetime.fromisoformat(self.daily_next_at)
        return current_time >= next_claim_time

    def should_claim(self, current_time: datetime) -> bool:
        if not self.claimed_last_at:
            return False
        next_claim_time = datetime.fromisoformat(self.claimed_last_at) + timedelta(
            hours=1, minutes=30
        )
        return current_time > next_claim_time

    def should_get_fuel(self, current_time: datetime) -> bool:
        if not self.fuel_last_at:
            return False
        next_fuel_time = datetime.fromisoformat(self.fuel_last_at) + timedelta(hours=2)
        return current_time > next_fuel_time and self.balance > 10

    def should_get_shield(self, current_time: datetime) -> bool:
        if not self.shield_ended_at:
            return False
        return not self.shield_active and self.balance > 15

    def should_get_shield_immunity(self, current_time: datetime) -> bool:
        if not self.shield_immunity_at:
            return False
        shield_immunity_time = datetime.fromisoformat(
            self.shield_immunity_at
        ) + timedelta(hours=1, minutes=30)
        return current_time > shield_immunity_time and self.balance > 8

    # def _should_get_roulette(self, current_time: datetime) -> bool:
    #     return self.balance > 0
