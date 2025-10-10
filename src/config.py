# config.py

from typing import Dict
from models import PayCode


class Config:
    def __init__(self):
        self.VALUE_DICT = {
            "AM": "0645-1900",
            "PM": "1845-0700",
            "E": "0645-1500",
            "L": "1430-2230",
            "N": "2215-0700",
            "ADMIN+4": "0645-1900",
            "ADMIN": "0645-1500",
            "7.5": "0645-1445",
            "7.6": "0645-1535",
            "SKILLS": "1000-1400",
            "skills": "1000-1400",
            "CALS": "0645-1500",
            "ALS": "0645-1500",
            "ALS/7.5": "0645-1500", 
            "PALS": "0645-1500",
        }


        self.PAYCODES: Dict[str, PayCode] = {
            "AL": PayCode(id = 226, name = "LVE-Annual"),
        }


        self.SKIP_VALUES = [
            "O",
            "E/NRM",
            "L/NRM",
            "N/NRM",
        ]


        # TODO: Convert to paycode objects. Work out parsing AL/, A/L etc 
        # self.SPECIAL_VALUES = [ 
        #     "AL/", "A/L", "M/L", "ML", "MLUP", "UPML",
        #     "PHNW", "RPH", "STUDY", "LSL", "SD", "SL", "ORIENT",
        # ]


        self.ICU_DEFAULTS: Dict[str, str | int] = {
            'kronos_name_col': 37,
            'date_row': 2,
            'first_employee_row': 3,
            'first_day_col': 8,
            'last_day_col': 36,  # first_day_col + 28
            'buffer_col': 22,
            "sheet_name": "ICU-HDU",
        }