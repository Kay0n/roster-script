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
            "CALS": "0645-1500",
            "ALS": "0645-1500",     
            "ALS/7.5": "0645-1500", 
            "PALS": "0645-1500",
            "1830-2230": "1830-2230",
            "1430-1900": "1430-1900",
        }

        self.SPECIAL_VALUES = [
            "AL/", "A/L", "M/L", "ML", "MLUP", "UPML",
            "PHNW", "RPH", "STUDY", "LSL", "SD", "SL", "ORIENT",
        ]

        self.DEFAULTS = {
            'name_column': 6,
            'first_employee_row': 3,
            'first_day_column': 8,
            'last_day_column': 36,  # first_day_column + 28
            'day_offset': 0,
            'excel_file_path': "C:/Users/tobyo/Documents/ms-key-service-x64/roster-script/17th June - 14 July 2024.xlsx",
            'sheet_name': "KRONOS"
        }