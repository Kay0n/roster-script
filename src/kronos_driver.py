## pyright: reportUnusedVariable=false
# pyright: reportUnknownMemberType=false
## pyright: reportUnusedImport=false
## pyright: reportUnusedFunction=false


import time
from datetime import date

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as condition
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement



class RosterSelenium():

	driver: WebDriver
	wait: WebDriverWait[WebDriver]

	def setup_driver(self, use_proxy: bool=False, proxy_port: int=8080):
		options = Options()
		firefox_profile = webdriver.FirefoxProfile()
		options.page_load_strategy = 'normal'  # Changed from default to handle dynamic content better
		options.set_preference("browser.tabs.remote.autostart", False)
		options.set_preference("browser.tabs.remote.autostart.2", False)
		if use_proxy:
			firefox_profile.set_preference("network.proxy.type", 1)  # 1 means manual proxy configuration
			firefox_profile.set_preference("network.proxy.socks", "localhost")  
			firefox_profile.set_preference("network.proxy.socks_port", proxy_port)  
			firefox_profile.set_preference("network.proxy.socks_version", 5)
			options.profile = firefox_profile
		self.driver = webdriver.Firefox(options=options)
		self.wait = WebDriverWait(self.driver, 12)
		self.driver.implicitly_wait(12)
		self.vars = {}
	

	def teardown_driver(self):
		self.driver.quit()


	def wait_and_click(self, selector: tuple[str, str]):
		clickable_element = self.wait.until(condition.element_to_be_clickable(selector))
		clickable_element.click()
	

	def js_click(self, selector: tuple[str, str]):
		element: WebElement = self.driver.find_element(selector[0], selector[1])
		self.driver.execute_script("arguments[0].click();", element)


	def set_kronos_frame(self, timeout: int = 20):

		self.driver.switch_to.default_content()

		iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe.krn-widget-iframe")
		if not iframes:
			print("No .krn-widget-iframe elements found")
			return False

		for _, iframe in enumerate(iframes):
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
					lambda d: d.execute_script(
						"return !!Ext.getCmp('krnScheduleGrid_schedule_by_employee');"
					)
				)
				return True
			except Exception:
				print("Grid not found in this iframe")
				self.driver.switch_to.default_content()

		print("No matching schedule iframe found")
		return False
	
	
	def login(self, user: str, password: str):
		self.driver.get("https://kronos.calvarycare.org.au/")
		self.driver.set_window_size(1920, 1048)
 
		self.driver.find_element(By.ID, "userNameInput").click()
		self.driver.find_element(By.ID, "userNameInput").send_keys(user)
		self.driver.find_element(By.ID, "passwordInput").send_keys(password)
		self.driver.find_element(By.ID, "submitButton").click()

		
	def select_schedule_hyperfind(self):
		self.driver.find_element(By.XPATH, "//li[6]/div/div/span[2]").click()
		self.driver.switch_to.frame(1)
		time.sleep(6) # stops page hang
		self.js_click((By.ID, "hyperfindIcon"))
		self.js_click((By.XPATH, "//section[2]/header/a/span"))
		self.js_click((By.LINK_TEXT, "CAH-C9430-ICU"))


	def convert_date(self, date_obj: date) -> str:
		return date_obj.strftime("%d%m%Y")
	

	def select_date(self, date1: date, date2: date):
		self.js_click((By.XPATH, "//div[2]/button/i"))
		self.driver.find_element(By.XPATH, "//span/div/input").send_keys(self.convert_date(date1))
		self.driver.find_element(By.XPATH, "//span[2]/div/div/div/span/div/input").send_keys(self.convert_date(date2))
		self.wait_and_click((By.XPATH, "//button[2]/span"))


















	
