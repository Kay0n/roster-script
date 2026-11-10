"""Everything that touches the Kronos web app: browser setup, navigation and the injected JS."""

# pyright: reportUnknownMemberType=false

import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as condition
from selenium.webdriver.support.wait import WebDriverWait

import config
from models import PayCode, PayCodeEntry, RosterEntry, Shift


JS_FILE = Path(__file__).parent / "js" / "kronos.js"
GRID_ID = "krnScheduleGrid_schedule_by_employee"

# rosterTool.addPayCode returns a Promise; pass its outcome back to Selenium's async callback
ADD_PAYCODE_SCRIPT = """
const done = arguments[arguments.length - 1];
rosterTool.addPayCode(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4])
    .then(result => done({ok: true, fellBack: result.fellBack}))
    .catch(error => done({ok: false, error: rosterTool.describeError(error)}));
"""


class KronosError(Exception):
    pass


@dataclass
class AddReport:
    added: list[RosterEntry] = field(default_factory=list)
    fell_back: list[PayCodeEntry] = field(default_factory=list)  # also in added
    failed: list[tuple[RosterEntry, str]] = field(default_factory=list)
    unknown_employees: list[str] = field(default_factory=list)

    def print_summary(self):
        print(f"Added {len(self.added)} entries, {len(self.failed)} failed")

        if self.fell_back:
            print(f"Overdrawn, added as {config.FALLBACK_PAYCODE.name} instead:")
            for entry in self.fell_back:
                print(f"    {entry.employee_name}: {entry}")

        if self.failed:
            print("Failed:")
            for entry, error in self.failed:
                print(f"    {entry.employee_name}: {entry}: {error}")

        if self.unknown_employees:
            print("Skipped, not found in Kronos:")
            for name in self.unknown_employees:
                print(f"    {name}")


def _paycode_arg(paycode: PayCode) -> dict[str, str | int]:
    return {"id": paycode.id, "name": paycode.name}


def _create_firefox(use_proxy: bool, proxy_port: int) -> webdriver.Firefox:
    options = Options()
    options.page_load_strategy = "normal"
    options.set_preference("browser.tabs.remote.autostart", False)
    options.set_preference("browser.tabs.remote.autostart.2", False)

    firefox_profile = webdriver.FirefoxProfile()
    if use_proxy:
        firefox_profile.set_preference("network.proxy.type", 1)  # 1 = manual proxy configuration
        firefox_profile.set_preference("network.proxy.socks", "localhost")
        firefox_profile.set_preference("network.proxy.socks_port", proxy_port)
        firefox_profile.set_preference("network.proxy.socks_version", 5)
    options.profile = firefox_profile

    # Use geckodriver from PATH so Selenium Manager doesn't download a non-Nix Firefox
    geckodriver_path = shutil.which("geckodriver")
    if not geckodriver_path:
        raise FileNotFoundError("geckodriver not found in PATH")
    firefox_path = shutil.which("firefox")
    if not firefox_path:
        raise FileNotFoundError("firefox not found in PATH")
    options.binary_location = firefox_path

    # devenv's python sets LD_LIBRARY_PATH to its pinned libstdc++, which breaks the system Firefox
    env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
    service = Service(executable_path=geckodriver_path, env=env)
    return webdriver.Firefox(service=service, options=options)


class KronosDriver:

    def __init__(self, use_proxy: bool = False, proxy_port: int = 8080):
        self.driver = _create_firefox(use_proxy, proxy_port)
        self.wait = WebDriverWait(self.driver, 12)
        self.driver.implicitly_wait(12)

    def quit(self):
        self.driver.quit()

    # --- High level ---

    def open_schedule(self, user: str, password: str, start_date: date, end_date: date):
        """Log in, open the ICU schedule for the date range and inject the helper JS."""
        self.login(user, password)
        self.select_hyperfind()
        time.sleep(9)
        self.select_date_range(start_date, end_date)
        time.sleep(6)
        self.switch_to_schedule_frame()
        self.inject_js()

    def get_employee_ids(self) -> dict[str, int]:
        """Kronos employee name -> employee id, for everyone in the loaded schedule."""
        employees = self.driver.execute_script("return rosterTool.getEmployees();")
        return {e["1"]: e["Id"] for e in employees}

    def add_entries_to_schedule(self, entries: dict[str, list[RosterEntry]]) -> AddReport:
        """Add every entry to the schedule grid, skipping employees Kronos doesn't know. Doesn't save."""
        employee_ids = self.get_employee_ids()
        report = AddReport()

        for employee_name, employee_entries in entries.items():
            employee_id = employee_ids.get(employee_name)
            if not employee_id:
                report.unknown_employees.append(employee_name)
                continue

            for entry in employee_entries:
                try:
                    if isinstance(entry, Shift):
                        self.add_shift(employee_id, entry)
                    elif self.add_paycode(employee_id, entry):
                        report.fell_back.append(entry)
                    report.added.append(entry)
                    print(f"Added {entry} for {employee_name}:{employee_id}")
                except KronosError as e:
                    report.failed.append((entry, str(e)))
                    print(f"FAILED {entry} for {employee_name}:{employee_id}: {e}")
                time.sleep(0.6)

            time.sleep(1.0)

        return report

    def add_shift(self, employee_id: int, shift: Shift):
        try:
            self.driver.execute_script(
                "rosterTool.addShift(arguments[0], arguments[1], arguments[2]);",
                employee_id, shift.date.isoformat(), shift.time_range,
            )
        except WebDriverException as e:
            raise KronosError(e.msg) from e

    def add_paycode(self, employee_id: int, entry: PayCodeEntry) -> bool:
        """Returns True if Kronos rejected the paycode as overdrawn and the fallback paycode was used."""
        try:
            result = self.driver.execute_async_script(
                ADD_PAYCODE_SCRIPT,
                employee_id, entry.date.isoformat(), _paycode_arg(entry.paycode), entry.hours,
                _paycode_arg(config.FALLBACK_PAYCODE),
            )
        except WebDriverException as e:
            raise KronosError(e.msg) from e

        if not result["ok"]:
            raise KronosError(result["error"])
        return result["fellBack"]

    # --- Navigation steps ---

    def login(self, user: str, password: str):
        self.driver.get(config.KRONOS_URL)
        self.driver.set_window_size(1920, 1048)

        self.driver.find_element(By.ID, "userNameInput").click()
        self.driver.find_element(By.ID, "userNameInput").send_keys(user)
        self.driver.find_element(By.ID, "passwordInput").send_keys(password)
        self.driver.find_element(By.ID, "submitButton").click()

    def select_hyperfind(self):
        self.driver.find_element(By.XPATH, "//li[6]/div/div/span[2]").click()
        self.driver.switch_to.frame(1)
        time.sleep(6)  # stops page hang
        self._js_click((By.ID, "hyperfindIcon"))
        self._js_click((By.XPATH, "//section[2]/header/a/span"))
        self._js_click((By.LINK_TEXT, config.HYPERFIND_NAME))

    def select_date_range(self, start_date: date, end_date: date):
        self._js_click((By.XPATH, "//div[2]/button/i"))
        self.driver.find_element(By.XPATH, "//span/div/input").send_keys(start_date.strftime("%d%m%Y"))
        self.driver.find_element(By.XPATH, "//span[2]/div/div/div/span/div/input").send_keys(end_date.strftime("%d%m%Y"))
        self._wait_and_click((By.XPATH, "//button[2]/span"))

    def switch_to_schedule_frame(self, timeout: int = 20) -> bool:
        """Switch into the iframe that holds the ExtJS schedule grid."""
        self.driver.switch_to.default_content()

        iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe.krn-widget-iframe")
        if not iframes:
            print("No .krn-widget-iframe elements found")
            return False

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "schedule" not in src.lower():
                continue

            self.driver.switch_to.frame(iframe)

            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script("return typeof window.Ext !== 'undefined';")
                )
            except Exception:
                print("ExtJS not found in this iframe")
                self.driver.switch_to.default_content()
                continue

            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script(f"return !!Ext.getCmp('{GRID_ID}');")
                )
                return True
            except Exception:
                print("Grid not found in this iframe")
                self.driver.switch_to.default_content()

        print("No matching schedule iframe found")
        return False

    def inject_js(self):
        self.driver.execute_script(
            """
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.text = arguments[0];
            document.documentElement.appendChild(script);
            """,
            JS_FILE.read_text(encoding="utf-8"),
        )

    # --- Helpers ---

    def _wait_and_click(self, selector: tuple[str, str]):
        self.wait.until(condition.element_to_be_clickable(selector)).click()

    def _js_click(self, selector: tuple[str, str]):
        element: WebElement = self.driver.find_element(*selector)
        self.driver.execute_script("arguments[0].click();", element)
