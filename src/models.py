from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PayCode:
    id: int
    name: str


@dataclass
class Shift:
    employee_name: str
    date: date
    time_range: str  # 'nnnn-nnnn'

    def __str__(self) -> str:
        return f"{self.date} shift {self.time_range}"


@dataclass
class PayCodeEntry:
    employee_name: str
    date: date
    paycode: PayCode
    hours: float

    def __str__(self) -> str:
        return f"{self.date} {self.paycode.name} ({self.hours}h)"


RosterEntry = Shift | PayCodeEntry
