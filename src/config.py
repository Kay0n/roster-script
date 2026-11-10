import re
from dataclasses import dataclass

from models import PayCode


# --- Run settings (defaults for the command line options in main.py) ---

USE_PROXY = False  # ssh -N -D 8080 kayon@refract.online
PROXY_PORT = 8080
START_DAY_OFFSET = 0

KRONOS_URL = "https://kronos.calvarycare.org.au/"
HYPERFIND_NAME = "CAH-C9430-ICU"


# --- Sheet layout ---

@dataclass(frozen=True)
class SheetLayout:
    sheet_name: str
    kronos_name_col: int
    exclude_marker_col: int
    date_row: int
    first_employee_row: int
    first_day_col: int
    last_day_col: int  # first_day_col + 28 (28 days + name_repeat_col)
    name_repeat_col: int  # names column repeated between the two fortnights, not a day
    name_repeat_header: str  # name col heading in date row

    @property
    def day_cols(self) -> list[int]:
        """One column per roster day, in order, without name_repeat_col."""
        return [c for c in range(self.first_day_col, self.last_day_col + 1) if c != self.name_repeat_col]


ICU_LAYOUT = SheetLayout(
    sheet_name="ICU-HDU",
    kronos_name_col=37,
    exclude_marker_col=38,
    date_row=2,
    first_employee_row=3,
    first_day_col=8,
    last_day_col=36,
    name_repeat_col=22,
    name_repeat_header="NAME",
)


# --- Cell values ---

SHIFT_TIMES: dict[str, str] = {
    "AM":        "0645-1900",
    "PM":        "1845-0700",
    "E":         "0645-1500",
    "L":         "1430-2230",
    "N":         "2215-0700",

    "ADMIN+4":   "0645-1900",
    "ADMIN":     "0645-1445",
    "7.5":       "0645-1445",
    "7.6":       "0645-1535",

    "SKILLS":    "1000-1400",
    "skills":    "1000-1400",

    "CALS":      "0645-1445",
    "ALS":       "0645-1445",
    "ALS/7.5":   "0645-1445",
    "PALS":      "0645-1445",
    "ACM":       "0645-1445",
    "SD/7.5":    "0645-1445",
    "SD/11.5":   "0645-1845",
    "UPSKILL":   "0645-1445",
    "Study 7.5": "0645-1445",
    "STUDY":     "0645-1445",
    "Orient":    "0645-1445",
    "ECMO/SD":   "0645-1445",
}


PAYCODES: dict[str, PayCode] = {
    "AL":     PayCode(id=226, name="LVE-Annual"),
    "SL":     PayCode(id=915, name="LVE-Personal No Certificate"),
    "LWOP":   PayCode(id=269, name="LVE-Unpaid"),
    # To check:
    # "PHNW", "RPH", "STUDY", "SD", "ORIENT",

    # ignore, not entered by ICU
    # "LSL":    PayCode(id = 229, name = "LVE-Long Service Leave"), # has 'shortName: "LSL"' in the payload, not sure if needed?
    # "ML":     PayCode(id = 252, name = "LVE-Maternity Paid"), # has 'shortName: "MAT"'
    # "MLUP":   PayCode(id = 251, name = "LVE-Maternity Unpaid"), # has 'shortName: "MAU"'
}


# Used when paycode is overdrawn
FALLBACK_PAYCODE = PAYCODES["LWOP"]


IGNORED_CELL_VALUES = {
    "O",
    "E/NRM",
    "L/NRM",
    "NRM/L",
    "N/NRM",
    "NRM",
    "NA",
    "UNI",
    "LSL",
    "M/L",
    "RPH",
}

IGNORED_CELL_PATTERNS = [
    re.compile(r"^WK\d+$"),          # WK1, WK11, ...
    re.compile(r"^ML(UP)?(/.*)?$"),  # ML, MLUP, ML/11.5, ML/7.5, ...
]
