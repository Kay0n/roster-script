from dataclasses import dataclass


@dataclass(frozen=True)
class PayCode:
    id: int
    name: str


@dataclass
class Shift:
    employee_name: str
    date: str  # 'YYYY-MM-DD'
    time_range: str  # 'nnnn-nnnn'


@dataclass
class PayCodeEntry:
    employee_name: str
    date: str  # 'YYYY-MM-DD'
    paycode: PayCode
    hours: float


RosterEntry = Shift | PayCodeEntry
