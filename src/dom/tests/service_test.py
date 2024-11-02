import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tokencost import count_string_tokens

from src.dom.service import DomService
from src.driver.service import DriverService


def test_process_html_file():
	driver = DriverService(headless=False).get_driver()

	driver.get('https://www.kayak.ch')
	# driver.get('https://example.com/')

	# driver.implicitly_wait(5)

	# Wait for accept cookies button to appear
	accept_cookies_button = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located(
			(By.XPATH, '/html/body/div[4]/div/div[2]/div/div/div[3]/div/div[1]/button[1]/div/div')
		)
	)
	accept_cookies_button.click()

	# Wait for banner to disappear
	time.sleep(1)

	# Process the HTML file
	dom_service = DomService(driver)
	result = dom_service.get_current_state()

	# Add assertions based on expected content of page.html
	print(f'Processed DOM content: {result.output_string}')
	# print(f'Selector map: {result.selector_map}')

	print('Tokens:', count_string_tokens(result.output_string, 'gpt-4o'))