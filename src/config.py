# config.py

from typing import Dict
from models import PayCode


class Config:
    def __init__(self):
        self.VALUE_DICT = {
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
            "ACM" :      "0645-1445",
            "SD/7.5":    "0645-1445",
            "SD/11.5":   "0645-1845",
            "UPSKILL":   "0645-1445",
            "Study 7.5": "0645-1445",

        }


        self.PAYCODES: Dict[str, PayCode] = {
            "AL":     PayCode(id=226, name="LVE-Annual"),
            "SL":     PayCode(id=915, name="LVE-Personal No Certificate"),
            # "SL/x"
            # "ORIENT"
            # Ignore the following, not entered by ICU
            # "LSL":    PayCode(id = 229, name = "LVE-Long Service Leave"), # has 'shortName: "LSL"' in the payload, not sure if needed?
            # "ML":     PayCode(id = 252, name = "LVE-Maternity Paid"), # has 'shortName: "MAT"'
            # "MLUP":   PayCode(id = 251, name = "LVE-Maternity Unpaid"), # has 'shortName: "MAU"'
        }

        # TODO: Globbing
        self.SKIP_VALUES = [
            "O",
            "E/NRM",
            "L/NRM",
            "NRM/L",
            "N/NRM",
            "NA", 
            "UNI",

            "WK3", # glob (WK1, WK2 etc)
            "WK11"
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


        # TODO: Convert to paycode objects. Work out parsing AL/, A/L etc 
        # self.SPECIAL_VALUES = [ 
        #     "AL/", "A/L", "M/L", "ML", "MLUP", "UPML",
        #     "PHNW", "RPH", "STUDY", "LSL", "SD", "SL", "ORIENT",
        # ]


        self.ICU_DEFAULTS: Dict[str, str | int] = {
            'kronos_name_col': 37,
            'x_check_col': 38,
            'date_row': 2,
            'first_employee_row': 3,
            'first_day_col': 8,
            'last_day_col': 36,  # first_day_col + 28
            'buffer_col': 22,
            "sheet_name": "ICU-HDU",
        }