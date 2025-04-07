# config.py
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
            "7.5": "0645-1500",
            "7.6": "0645-1535",
            "SKILLS": "1000-1400",
            "skills": "1000-1400",
            "CALS": "0645-1500",
            "ALS": "0645-1500",
            "ALS/7.5": "0645-1500", 
            "PALS": "0645-1500",
            # manual time match
            "1830-2230": "1830-2230",
            "1030-1900": "1030-1900",
            "1430-1900": "1430-1900",
            "1100-1900": "1100-1900",
            "0730-1500": "0730-1500",
            "0730-1501": "0730-1501",
            "0730-1502": "0730-1502",
            "1045-1900":"1045-1900",
            "0800-1600":"0800-1600",


        }

        self.SPECIAL_VALUES = [ 
            # These contain symbols that require paycodes 
            # and need to be entered manually. They are not exact matches. 
            "AL/", "A/L", "M/L", "ML", "MLUP", "UPML",
            "PHNW", "RPH", "STUDY", "LSL", "SD", "SL", "ORIENT",
        ]


        self.ICU_DEFAULTS = {
            'name_col': 5,
            'kronos_name_col': 37,
            'first_employee_row': 3,
            'first_day_col': 8,
            'last_day_col': 36,  # first_day_col + 28
            'day_offset': 0,
            'excel_file_path': "",
            "sheet_name": "ICU-HDU",
        }