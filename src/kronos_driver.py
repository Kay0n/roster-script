import time
import os
from datetime import date

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as condition
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.proxy import Proxy, ProxyType
from excel_manager import ExcelWorkbook


class RosterSelenium():

	def setup_driver(self, use_proxy=False, proxy_port=8080):
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


	def wait_and_click(self, selector: tuple):
		clickable_element = self.wait.until(condition.element_to_be_clickable(selector))
		clickable_element.click()
	

	def js_click(self, selector: tuple):
		element = self.driver.find_element(selector[0], selector[1])
		self.driver.execute_script("arguments[0].click();", element)

	
	def login(self, user, password):
		self.driver.get("https://kronos.calvarycare.org.au/")
		self.driver.set_window_size(1920, 1048)
		self.driver.find_element(By.ID, "userNameInput").click()
		self.driver.find_element(By.ID, "userNameInput").send_keys(user)
		self.driver.find_element(By.ID, "passwordInput").send_keys(password)
		self.driver.find_element(By.ID, "submitButton").click()
		
	
	def select_schedule_hyperfind(self):
		self.driver.find_element(By.XPATH, "//li[5]/div/div/span[2]").click()
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


	def get_all_employee_names(self):
		"""
		Gets all employee names by scrolling in small increments
		"""
		try:
				scrollable_container = WebDriverWait(self.driver, 10).until(
					condition.presence_of_element_located((By.ID, "tableview-1022"))
				)
				print("PASSED FIND SCROLLABLE")
				all_names = set()
				scroll_position = 0
				scroll_increment = 600  
				prev_set_size = 0
				no_new_names_count = 0
				scroll_delay_seconds = 0.2
				
				while True:
					elements = self.driver.find_elements('xpath', "//*[starts-with(@id, 'employeeId_')]")
					current_names = {element.text.strip() for element in elements if element.text.strip()}
					
					all_names.update(current_names)
					
					if prev_set_size == len(all_names):
							no_new_names_count += 1
							if no_new_names_count >= 6:  # no new names found in 6 attempts, at bottom.
								break
					else:
						no_new_names_count = 0
						prev_set_size = len(all_names)
					
					scroll_position += scroll_increment
					
					self.driver.execute_script("""
							let element = arguments[0];
							element.scrollTop = arguments[1];
					""", scrollable_container, scroll_position)
					time.sleep(scroll_delay_seconds)  
					
					current_scroll_amount = self.driver.execute_script("return arguments[0].scrollTop;", scrollable_container)
					total_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", scrollable_container)
					visible_height = self.driver.execute_script("return arguments[0].clientHeight;", scrollable_container)
					
					if current_scroll_amount >= (total_scroll_height - visible_height) and no_new_names_count > 0:
						break
				
				# remove "\nSigned off period" from each name if applicable
				cleaned_names = [name.replace('\nSigned off period', '') for name in all_names]

				return sorted(list(cleaned_names))  
		
		except Exception as e:
			print(f"Error while scrolling...")
			raise e
				

	





	def generate_moves(self, workbook, kronos_list, highlight_color=8):
		"""
		Compare two lists of names and track relative movements needed to match order.
		
		Args:
				workbook: Excel workbook object with get_cell and get_cell_highlight methods
				kronos_list: List of names in sorted reference order
				highlight_color: Color code to filter by (default: "#92CDDC")
				
		Returns:
				List of movements (integers) and "skip" strings, sorted alphabetically by name
		"""
		def get_highlighted_names(workbook, highlight_theme, name_col=37) -> list[(str, int)]:
				"""Extract names from workbook where cell highlight matches specified color."""
				names_with_rows = []
				row = 1
				
				# Continue until end color
				while True:
					name = workbook.get_cell(row, name_col)
					cell_color_theme = workbook.get_highlight_theme(row, name_col)
					print(cell_color_theme)
					if cell_color_theme == highlight_theme:
						names_with_rows.append((name, row))

					if name == "END": # TODO: better solution 
						break

					if row >= 140:
						break

					row += 1
						
				return names_with_rows
		
		def calculate_movements(names_with_rows: list[(str, int)], kronos_list) -> list[(int,int|str)]:
			"""Calculate relative movements between valid names in the Kronos list."""
			movements = []
			prev_kronos_index = -1
			
			for name, row in names_with_rows:
				if name in kronos_list:
					current_kronos_index = kronos_list.index(name)
					
					# First valid name found
					if prev_kronos_index == -1: 
						movements.append((row,0)) # TODO: wont work if first name in excel isn't first name in kronos
					else:
						# Calculate relative movement from previous position
						movement = current_kronos_index - prev_kronos_index - 1
						movements.append((row,movement))
					
					prev_kronos_index = current_kronos_index
				else:
					movements.append((row,"skip"))
			
			return movements
		
		# Get highlighted names with their row numbers
		highlighted_names = get_highlighted_names(workbook, highlight_color)

		sorted_names = sorted(highlighted_names, key=lambda x: x[0])
		
		# Calculate movements for each valid name
		movements = calculate_movements(sorted_names, kronos_list)
		return movements
















	










