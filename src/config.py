from dataclasses import dataclass
from datetime import date

from models import PayCode


# --- Run settings ---

USE_PROXY = False  # ssh -N -D 8080 kayon@refract.online
PROXY_PORT = 8080
START_DATE = date(2026, 11, 2)
END_DATE = date(2026, 11, 29)
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
    last_day_col: int  # first_day_col + 28
    spacer_col: int  # empty column between the two fortnights


ICU_LAYOUT = SheetLayout(
    sheet_name="ICU-HDU",
    kronos_name_col=37,
    exclude_marker_col=38,
    date_row=2,
    first_employee_row=3,
    first_day_col=8,
    last_day_col=36,
    spacer_col=22,
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

    # Ignore the following, not entered by ICU
    # "LSL":    PayCode(id = 229, name = "LVE-Long Service Leave"), # has 'shortName: "LSL"' in the payload, not sure if needed?
    # "ML":     PayCode(id = 252, name = "LVE-Maternity Paid"), # has 'shortName: "MAT"'
    # "MLUP":   PayCode(id = 251, name = "LVE-Maternity Unpaid"), # has 'shortName: "MAU"'
}


# TODO: Globbing
IGNORED_CELL_VALUES = [
    "O",
    "E/NRM",
    "L/NRM",
    "NRM/L",
    "N/NRM",
    "NRM",
    "NA",
    "UNI",

    "WK3", # glob (WK1, WK2 etc)
    "WK11",
    "WK13",
    "WK15",
    "WK17",

    "LSL",

    "ML" # glob (ML/11.5, ML/7.5)
    "MLUP" # glob
    "M/L"
    "ML/11.5"
    "RPH"
]
