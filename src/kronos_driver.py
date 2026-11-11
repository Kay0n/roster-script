"""Everything that touches the Kronos web app: browser setup, navigation and the injected JS."""

# pyright: reportUnknownMemberType=false

import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchFrameException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as condition
from selenium.webdriver.support.wait import WebDriverWait

import config
from models import PayCode, PayCodeEntry, RosterEntry, Shift


JS_FILE = Path(__file__).parent / "js" / "kronos.js"
GRID_ID = "krnScheduleGrid_schedule_by_employee"
TIMEOUT = 30  # seconds per page step

# Unverified whether adding a shift sends a request; try 0
SHIFT_ADD_DELAY = 0.6

# True while the #loaderdiv spinner shows in any frame
LOADER_VISIBLE_SCRIPT = """
function allDocuments(win) {
    let docs;
    try { docs = [win.document]; } catch (e) { return []; }  // cross-origin frame
    for (let i = 0; i < win.frames.length; i++) docs.push(...allDocuments(win.frames[i]));
    return docs;
}
let root = window;
try { window.top.document; root = window.top; } catch (e) {}

return allDocuments(root).some(doc => {
    const loader = doc.getElementById('loaderdiv');
    if (!loader) return false;
    const style = doc.defaultView.getComputedStyle(loader);
    return style.display !== 'none' && style.visibility !== 'hidden' && loader.getClientRects().length > 0;
});
"""
LOADER_APPEAR_TIMEOUT = 5.0  # max wait for a load to start
LOADER_SETTLE_TIME = 1.0  # spinner must stay gone this long, loads can run back to back

# True once the grid and its stores have loaded
SCHEDULE_READY_SCRIPT = f"""
if (typeof Ext === 'undefined') return false;
const grid = Ext.getCmp('{GRID_ID}');
if (!grid) return false;
const resources = grid.getResourceStore();
const events = grid.getEventStore ? grid.getEventStore() : grid.getStore();
return !resources.isLoading() && !events.isLoading() && resources.getCount() > 0;
"""

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
        self.wait = WebDriverWait(self.driver, TIMEOUT)

    def quit(self):
        self.driver.quit()

    # --- High level ---

    def open_schedule(self, user: str, password: str, start_date: date, end_date: date):
        """Log in, open the ICU schedule for the date range and inject the helper JS."""
        self.login(user, password)
        self.select_hyperfind()
        self.select_date_range(start_date, end_date)
        self.switch_to_schedule_frame()
        self.inject_js()

    def get_employee_ids(self) -> dict[str, int]:
        """Kronos employee name -> employee id, for everyone in the loaded schedule."""
        self._reinject_js()
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
                        time.sleep(SHIFT_ADD_DELAY)
                    elif self.add_paycode(employee_id, entry):
                        report.fell_back.append(entry)
                    report.added.append(entry)
                    print(f"Added {entry} for {employee_name}:{employee_id}")
                except KronosError as e:
                    report.failed.append((entry, str(e)))
                    print(f"FAILED {entry} for {employee_name}:{employee_id}: {e}")

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

        self._find((By.ID, "userNameInput"), "login page").send_keys(user)
        self._find((By.ID, "passwordInput"), "login page").send_keys(password)
        submit_button = self._find((By.ID, "submitButton"), "login page")
        submit_button.click()
        # Scripts run mid-redirect can crash marionette
        self.wait.until(condition.staleness_of(submit_button), "login page to submit")
        self.wait.until(
            lambda d: d.execute_script("return document.readyState === 'complete';"),
            "home page to load after login",
        )
        self._wait_for_loader("home page to load after login")

    def select_hyperfind(self):
        self._wait_and_click((By.XPATH, "//li[6]/div/div/span[2]"), "schedule menu item after login")
        self._switch_to_frame_index(1)
        # Clicking hyperfind mid-load leaves Kronos stuck on its spinner
        self._wait_for_loader("first schedule load")
        self._js_click((By.ID, "hyperfindIcon"), "hyperfind button")
        self._js_click((By.XPATH, "//section[2]/header/a/span"), "hyperfind list")
        link = self._js_click((By.LINK_TEXT, config.HYPERFIND_NAME), f"hyperfind {config.HYPERFIND_NAME!r}")
        self.wait.until(condition.invisibility_of_element(link), "hyperfind list to close")
        self._wait_for_loader("schedule to load the hyperfind")

    def select_date_range(self, start_date: date, end_date: date):
        self._js_click((By.XPATH, "//div[2]/button/i"), "date range button")
        self._find((By.XPATH, "//span/div/input"), "start date input").send_keys(start_date.strftime("%d%m%Y"))
        self._find((By.XPATH, "//span[2]/div/div/div/span/div/input"), "end date input").send_keys(end_date.strftime("%d%m%Y"))
        apply_button = self._wait_and_click((By.XPATH, "//button[2]/span"), "date range apply button")
        self.wait.until(condition.invisibility_of_element(apply_button), "date range dialog to close")
        self._wait_for_loader("schedule to load the date range")

    def switch_to_schedule_frame(self, ext_timeout: int = 10):
        """Switch into the schedule grid's iframe once the grid has loaded"""
        self.driver.switch_to.default_content()

        iframes = self.wait.until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "iframe.krn-widget-iframe"),
            "a .krn-widget-iframe to appear",
        )

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "schedule" not in src.lower():
                continue

            self.driver.switch_to.frame(iframe)

            try:
                WebDriverWait(self.driver, ext_timeout).until(
                    lambda d: d.execute_script("return typeof window.Ext !== 'undefined';")
                )
            except TimeoutException:
                print("ExtJS not found in this iframe")
                self.driver.switch_to.default_content()
                continue

            self._wait_for_schedule_loaded("schedule grid to load")
            return

        raise KronosError("No schedule iframe with an ExtJS grid found")

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

    def _reinject_js(self):
        """Re-inject the JS if Kronos reloaded the frame"""
        try:
            if self.driver.execute_script("return typeof window.rosterTool !== 'undefined';"):
                return
        except WebDriverException:
            pass  # frame gone
        print("Schedule frame was reloaded, injecting JS again")
        self.switch_to_schedule_frame()
        self.inject_js()

    def _wait_for_loader(self, step: str):
        """Wait for the spinner to appear, if it will, then stay gone"""
        last_error: WebDriverException | None = None

        def loader_visible() -> bool:
            nonlocal last_error
            try:
                return bool(self.driver.execute_script(LOADER_VISIBLE_SCRIPT))
            except WebDriverException as e:
                last_error = e  # likely mid-navigation, so treat as loading
                return True

        appear_deadline = time.monotonic() + LOADER_APPEAR_TIMEOUT
        while not loader_visible() and time.monotonic() < appear_deadline:
            time.sleep(0.25)

        deadline = time.monotonic() + TIMEOUT
        gone_since: float | None = None
        while True:
            now = time.monotonic()
            if loader_visible():
                gone_since = None
            elif gone_since is None:
                gone_since = now
            elif now - gone_since >= LOADER_SETTLE_TIME:
                return
            if now > deadline:
                detail = f"last error: {last_error.msg}" if last_error else "loading spinner still showing"
                raise TimeoutException(f"{step} ({detail} after {TIMEOUT}s)")
            time.sleep(0.25)

    def _wait_for_schedule_loaded(self, step: str):
        self.wait.until(lambda d: d.execute_script(SCHEDULE_READY_SCRIPT), step)

    def _switch_to_frame_index(self, index: int):
        def switched(d: WebDriver) -> bool:
            try:
                d.switch_to.frame(index)
                return True
            except NoSuchFrameException:
                return False

        self.wait.until(switched, f"frame {index} to appear")

    def _find(self, selector: tuple[str, str], step: str) -> WebElement:
        return self.wait.until(condition.presence_of_element_located(selector), step)

    def _wait_and_click(self, selector: tuple[str, str], step: str) -> WebElement:
        element = self.wait.until(condition.element_to_be_clickable(selector), step)
        element.click()
        return element

    def _js_click(self, selector: tuple[str, str], step: str) -> WebElement:
        element = self._find(selector, step)
        self.driver.execute_script("arguments[0].click();", element)
        return element
