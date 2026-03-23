## pyright: reportUnusedVariable=false
# pyright: reportUnknownMemberType=false
## pyright: reportUnusedImport=false
## pyright: reportUnusedFunction=false


from config import Config
from excel_manager import ExcelWorkbook
from kronos_driver import RosterSelenium
from models import PayCodeShift, Shift

from dotenv import load_dotenv
from selenium.webdriver.remote.webdriver import WebDriver
from datetime import date, datetime
from typing import Dict
import re
import time
import os



USE_PROXY = False; # ssh -N -D 8080 kayon@refract.online
USE_MANUEL_SETTINGS = True;
# START_DATE = date(2025, 10, 6);
# END_DATE = date(2025, 11, 2);
START_DATE = date(2026, 3, 23);
END_DATE = date(2026, 4, 19);
DAY_OFFSET = 0;
HIGHLIGHT_THEME = 8;
TIMECODE_REGEX = re.compile(r"^\d{4}-\d{4}$") # nnnn-nnnn, n = digit



def get_xlsx_path() -> str:
    cwd = os.getcwd()
    for file in os.listdir(cwd):
        if file.endswith(".xlsx"):
            return os.path.join(cwd, file)
    return ""



# TODO: move to kronos_driver.py
def setup_kronos(kronos_driver: RosterSelenium, user: str, password: str):
    kronos_driver.setup_driver(USE_PROXY, 8080)
    kronos_driver.login(user, password)
    kronos_driver.select_schedule_hyperfind()

    time.sleep(9)

    kronos_driver.select_date(START_DATE, END_DATE)

    time.sleep(6)



def parse_shift(employee_name: str, date_str: str, cell_content: str, config: Config) -> Shift | PayCodeShift | None:
    if cell_content in config.VALUE_DICT:
        shift_string = config.VALUE_DICT[cell_content]
        return Shift(employee_name, date_str, shift_string)

    if TIMECODE_REGEX.match(cell_content):
        return Shift(employee_name, date_str, cell_content)

    paycode_split = cell_content.split("/", 1)
    code = paycode_split[0].strip()

    if code in config.PAYCODES:
        if len(paycode_split) == 1 or not paycode_split[1].strip():
            return None

        try:
            hours = float(paycode_split[1])
        except ValueError:
            raise Exception(f"Invalid hours value '{paycode_split[1]}' for paycode '{code}'")

        paycode = config.PAYCODES[code]

        return PayCodeShift(employee_name, date_str, paycode, hours)
    
    return None



def is_valid_fill(fill: Dict[str, str]) -> bool:
    THEME = 3

    if fill["rgb"] == "93CDDD":
        return True;

    source = fill.get("source")

    is_correct_theme = (
        source is not None
        and source.startswith("theme(")
        and int(source[6:].split(",")[0]) == THEME
    )
    return is_correct_theme



def get_invalid_employees(driver: WebDriver, shift_entries: Dict[str, list[Shift | PayCodeShift]]) -> list[str]:
    employees = driver.execute_script("return window.getEmployees();")
    name_to_id = {e['1']: e['Id'] for e in employees}

    invalid_list: list[str] = [];

    for employee_name, _ in shift_entries.items():
        employee_id = name_to_id.get(employee_name)
        if not employee_id:
            invalid_list.append(employee_name)

    return invalid_list;



# TODO: only sleep if the shifts
def upload_shifts(driver: WebDriver, shift_entries: Dict[str, list[Shift | PayCodeShift]]):
    employees = driver.execute_script("return window.getEmployees();")
    name_to_id = {e['1']: e['Id'] for e in employees}

    for employee_name, shifts in shift_entries.items():
        
        employee_id = name_to_id.get(employee_name)
        if not employee_id:
            continue

        for shift in shifts:

            if isinstance(shift, Shift):
                
                driver.execute_script(
                    "addShift(arguments[0], arguments[1], arguments[2]);",
                    employee_id, shift.date, shift.shift_string
                )
                time.sleep(0.15)
                print(f"Added shift {shift.shift_string} for {employee_name}:{employee_id} on {shift.date}")
                continue;
            
            paycode_obj: Dict[str, str | int]= {'id': shift.paycode.id, 'name': shift.paycode.name}
            driver.execute_script(
                "addPayCode(arguments[0], arguments[1], arguments[2], arguments[3]);",
                employee_id, shift.date, paycode_obj, shift.hours
            )
            time.sleep(0.3)
            print(f"Added paycode {shift.paycode.name} ({shift.hours}h) for {employee_name} on {shift.date}")
            
        time.sleep(0.8)

        



def parse_date(date: str) -> str: 
    date_dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")    
    return date_dt.strftime("%Y-%m-%d")



def proccess_excel(config: Config, workbook: ExcelWorkbook) -> tuple[dict[str, list[Shift | PayCodeShift]], set[str], int]:
    first_employee_row: int = int(config.ICU_DEFAULTS["first_employee_row"])
    name_col: int = int(config.ICU_DEFAULTS["kronos_name_col"])
    first_day_col = int(config.ICU_DEFAULTS['first_day_col'])
    last_day_col = int(config.ICU_DEFAULTS['last_day_col']);
    date_row = int(config.ICU_DEFAULTS['date_row'])
    start_day_col = first_day_col + DAY_OFFSET
    if start_day_col > 22: start_day_col += 1; # account for buffer
    shift_entries: Dict[str, list[Shift | PayCodeShift]] = {};
    unknown_symbols: set[str] = set();
    employee_count: int = 0;

    for row in range(first_employee_row, 300):
        employee_name = workbook.get_cell(row, name_col)
        # theme = workbook.get_highlight_theme(row, name_col)
        fill = workbook.normalize_fill_rgb(workbook.sheet.cell(row=row, column=name_col))

        print(f"Processing row {row}: '{employee_name}' with fill {fill}")
        if  not employee_name or not is_valid_fill(fill):
            continue;
        # if not employee_name or theme != HIGHLIGHT_THEME:
        #     continue;
        employee_count += 1;

        shift_list: list[Shift | PayCodeShift] = [];

        for col in range(start_day_col, last_day_col + 1):
            if col == config.ICU_DEFAULTS['buffer_col']:
                continue;
            
            cell_content = workbook.get_cell(row, col)

            if not cell_content: 
                continue;
            
            cell_content = cell_content.strip();

            if cell_content in config.SKIP_VALUES:
                continue;
    
            date_str = parse_date(workbook.get_cell(date_row, col));

            shift = parse_shift(employee_name, date_str, cell_content, config)

            if shift:
                shift_list.append(shift);
            else:
                print(f"Skipping unknown cell content: {cell_content} at row {row}, col {col}")
                unknown_symbols.add(cell_content);


        if shift_list:
            shift_entries[employee_name] = shift_list;
    
    # sort
    shift_entries = {k: v for k, v in sorted(shift_entries.items(), key=lambda item: item[0])}
    return shift_entries, unknown_symbols, employee_count





def inject_js(kronos_driver: RosterSelenium):
    
    js_folder = "./src/js"
    js_files = ["utils.js", "add-shift.js", "add-paycode.js"]

    for js_file in js_files:
        with open(os.path.join(js_folder, js_file), 'r', encoding='utf-8') as f:        
            js_code = f.read()
            kronos_driver.driver.execute_script("""
                    var script = document.createElement('script');
                    script.type = 'text/javascript';
                    script.text = arguments[0];
                    document.documentElement.appendChild(script);
                """, 
                js_code
            )



def main():

    kronos_driver =  RosterSelenium()
    config = Config()

    load_dotenv(override=True)
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")

    if user == None or password == None:
        raise Exception("KRONOS_USERNAME or KRONOS_PASSWORD enviroment vars not set")

    sheet_name: str = str(config.ICU_DEFAULTS["sheet_name"])

    _ = input("Press ENTER to start kronos...")

    setup_kronos(kronos_driver, user, password);

    kronos_driver.set_kronos_frame();

    inject_js(kronos_driver)
    
    _ = input("Press ENTER to ingest excel...")

    workbook: ExcelWorkbook = ExcelWorkbook(get_xlsx_path(), sheet_name)
    shift_entries, unknown_symbols, employee_count = proccess_excel(config, workbook)

    print("Roster ingestion complete")
    print(f"Proccessed {len(shift_entries)} shifts from {employee_count} employees");
    print("Unknown Symbols:")
    print(unknown_symbols)

    print("Invalid Employees:")
    for employee in get_invalid_employees(kronos_driver.driver, shift_entries):
        print(employee)

    _ = input("Press ENTER to upload shifts...")

    upload_shifts(kronos_driver.driver, shift_entries)

    _ = input("Press ENTER to finish...")





if __name__ == "__main__":
    main()
