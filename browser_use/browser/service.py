"""
Selenium browser on steroids.
"""

import base64
import logging
import os
import tempfile
import time
from typing import Literal

from Screenshot import Screenshot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from browser_use.browser.views import BrowserState, TabInfo
from browser_use.dom.service import DomService
from browser_use.dom.views import SelectorMap
from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)

# Constants
MINIMUM_WAIT_TIME = 0.5
MAXIMUM_WAIT_TIME = 5
HEADLESS_MODE = '--headless=new'
WINDOW_SIZE = '--window-size=1280,1024'
START_MAXIMIZED = '--start-maximized'
DISABLE_EXTENSIONS = '--disable-extensions'
DISABLE_BLINK_FEATURES = '--disable-blink-features=AutomationControlled'
EXCLUDE_SWITCHES = ['enable-automation']
USE_AUTOMATION_EXTENSION = False
NO_SANDBOX = '--no-sandbox'
DISABLE_DEV_SHM_USAGE = '--disable-dev-shm-usage'
DISABLE_GPU = '--disable-gpu'
REMOTE_DEBUGGING_PORT = '--remote-debugging-port=9222'
DISABLE_SETUID_SANDBOX = '--disable-setuid-sandbox'
SINGLE_PROCESS = '--single-process'
DISABLE_BACKGROUND_TIMER_THROTTLING = '--disable-background-timer-throttling'
DISABLE_POPUP_BLOCKING = '--disable-popup-blocking'
DISABLE_INFOBARS = '--disable-infobars'
DISABLE_BACKGROUNDING_OCCLUDED_WINDOWS = '--disable-backgrounding-occluded-windows'
DISABLE_RENDERER_BACKGROUNDING = '--disable-renderer-backgrounding'


class Browser:
    def __init__(self, headless: bool = False, keep_open: bool = False):
        self.headless = headless
        self.keep_open = keep_open
        self._tab_cache: dict[str, TabInfo] = {}
        self._current_handle = None
        self._ob = Screenshot.Screenshot()

        # Initialize driver during construction
        self.driver: webdriver.Chrome | None = self._setup_webdriver()
        self._cached_state = self._update_state()

    def _setup_webdriver(self) -> webdriver.Chrome:
        """Sets up and returns a Selenium WebDriver instance with anti-detection measures."""
        try:
            # if webdriver is not starting, try to kill it or rm -rf ~/.wdm
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument(HEADLESS_MODE)  # Updated headless argument

            # Essential automation and performance settings
            chrome_options.add_argument(DISABLE_BLINK_FEATURES)
            chrome_options.add_experimental_option('excludeSwitches', EXCLUDE_SWITCHES)
            chrome_options.add_experimental_option('useAutomationExtension', USE_AUTOMATION_EXTENSION)
            
            # Container environment settings
            chrome_options.add_argument(NO_SANDBOX)
            chrome_options.add_argument(DISABLE_DEV_SHM_USAGE)
            chrome_options.add_argument(DISABLE_GPU)
            chrome_options.add_argument(REMOTE_DEBUGGING_PORT)
            chrome_options.add_argument(DISABLE_SETUID_SANDBOX)
            chrome_options.add_argument(SINGLE_PROCESS)
            
            # Window settings
            chrome_options.add_argument(WINDOW_SIZE)
            chrome_options.add_argument(START_MAXIMIZED)
            chrome_options.add_argument(DISABLE_EXTENSIONS)

            # Background process optimization
            chrome_options.add_argument(DISABLE_BACKGROUND_TIMER_THROTTLING)
            chrome_options.add_argument(DISABLE_POPUP_BLOCKING)

            # Additional stealth settings
            chrome_options.add_argument(DISABLE_INFOBARS)
            chrome_options.add_argument(DISABLE_BACKGROUNDING_OCCLUDED_WINDOWS)
            chrome_options.add_argument(DISABLE_RENDERER_BACKGROUNDING)

            # Force headless mode for container environment
            chrome_options.add_argument(HEADLESS_MODE)

            # Initialize the Chrome driver with better error handling
            service = ChromeService(ChromeDriverManager().install())
            logger.info("Attempting to start Chrome with service path: %s", service.path)
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver started successfully")

            # Execute stealth scripts
            driver.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {
                    'source': """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    window.chrome = {
                        runtime: {}
                    };
                    
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: Promise.resolve.bind(Promise)
                        })
                    });
                """
                },
            )

            return driver

        except Exception as e:
            logger.error(f'Failed to initialize Chrome driver: {str(e)}', exc_info=True)
            # Clean up any existing driver
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except Exception:
                    pass
            raise

    def _get_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            self.driver = self._setup_webdriver()
        return self.driver

    def wait_for_page_load(self):
        """
        Ensures page is fully loaded before continuing.
        Waits for either document.readyState to be complete or minimum WAIT_TIME, whichever is longer.
        """
        driver = self._get_driver()

        # Start timing
        start_time = time.time()

        # Wait for page load
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception:
            pass

        # Calculate remaining time to meet minimum WAIT_TIME
        elapsed = time.time() - start_time
        remaining = max(MINIMUM_WAIT_TIME - elapsed, 0)

        logger.debug(
            f'--Page loaded in {elapsed:.2f} seconds, waiting for additional {remaining:.2f} seconds'
        )

        # Sleep remaining time if needed
        if remaining > 0:
            time.sleep(remaining)

    def _update_state(self, use_vision: bool = False) -> BrowserState:
        """
        Update and return state.
        """
        driver = self._get_driver()
        dom_service = DomService(driver)
        content = dom_service.get_clickable_elements()

        screenshot_b64 = None
        if use_vision:
            screenshot_b64 = self.take_screenshot(selector_map=content.selector_map)

        self.current_state = BrowserState(
            items=content.items,
            selector_map=content.selector_map,
            url=driver.current_url,
            title=driver.title,
            current_tab_handle=self._current_handle or driver.current_window_handle,
            tabs=self.get_tabs_info(),
            screenshot=screenshot_b64,
        )

        return self.current_state

    def close(self, force: bool = False):
        if not self.keep_open or force:
            if self.driver:
                driver = self._get_driver()
                driver.quit()
                self.driver = None
        else:
            input('Press Enter to close Browser...')
            self.keep_open = False
            self.close()

    def __del__(self):
        """
        Close the browser driver when instance is destroyed.
        """
        if hasattr(self, 'driver') and self.driver is not None:
            self.close()

    # region - Browser Actions

    def take_screenshot(self, selector_map: SelectorMap | None, full_page: bool = False) -> str:
        """
        Returns a base64 encoded screenshot of the current page.
        """
        driver = self._get_driver()

        if selector_map:
            self.highlight_selector_map_elements(selector_map)

        if full_page:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            screenshot = self._ob.full_screenshot(
                driver,
                save_path=temp_dir,
                image_name='temp.png',
                is_load_at_runtime=True,
                load_wait_time=1,
            )

            # Read file as base64
            with open(os.path.join(temp_dir, 'temp.png'), 'rb') as img:
                screenshot = base64.b64encode(img.read()).decode('utf-8')

            # Cleanup temp directory
            os.remove(os.path.join(temp_dir, 'temp.png'))
            os.rmdir(temp_dir)
        else:
            screenshot = driver.get_screenshot_as_base64()

        if selector_map:
            self.remove_highlights()

        return screenshot

    def highlight_selector_map_elements(self, selector_map: SelectorMap):
        driver = self._get_driver()
        # First remove any existing highlights/labels
        self.remove_highlights()

        script = """
        const highlights = {
        """

        # Build the highlights object with all xpaths and indices
        for index, xpath in selector_map.items():
            script += f'"{index}": "{xpath}",\n'

        script += """
        };
        
        for (const [index, xpath] of Object.entries(highlights)) {
            const el = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (!el) continue;  // Skip if element not found
            el.style.outline = "2px solid red";
            el.setAttribute('browser-user-highlight-id', 'selenium-highlight');
            
            const label = document.createElement("div");
            label.className = 'selenium-highlight-label';
            label.style.position = "fixed";
            label.style.background = "red";
            label.style.color = "white";
            label.style.padding = "2px 6px";
            label.style.borderRadius = "10px";
            label.style.fontSize = "12px";
            label.style.zIndex = "9999999";
            label.textContent = index;
            const rect = el.getBoundingClientRect();
            label.style.top = (rect.top - 20) + "px";
            label.style.left = rect.left + "px";
            document.body.appendChild(label);
        }
        """

        driver.execute_script(script)

    def remove_highlights(self):
        """
        Removes all highlight outlines and labels created by highlight_selector_map_elements
        """
        driver = self._get_driver()
        driver.execute_script(
            """
            // Remove all highlight outlines
            const highlightedElements = document.querySelectorAll('[browser-user-highlight-id="selenium-highlight"]');
            highlightedElements.forEach(el => {
                el.style.outline = '';
                el.removeAttribute('selenium-browser-use-highlight');
            });
            

            // Remove all labels
            const labels = document.querySelectorAll('.selenium-highlight-label');
            labels.forEach(label => label.remove());
            """
        )

    # endregion

    # region - User Actions
    def _webdriver_wait(self):
        driver = self._get_driver()
        return WebDriverWait(driver, 10)

    def _input_text_by_xpath(self, xpath: str, text: str):
        driver = self._get_driver()

        try:
            # Wait for element to be both present and interactable
            element = self._webdriver_wait().until(EC.element_to_be_clickable((By.XPATH, xpath)))

            # Scroll element into view using ActionChains for smoother scrolling
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()

            # Try to clear using JavaScript first
            driver.execute_script("arguments[0].value = '';", element)

            # Then send keys
            element.send_keys(text)

            self.wait_for_page_load()

        except Exception as e:
            raise Exception(
                f'Failed to input text into element with xpath: {xpath}. Error: {str(e)}'
            )

    def _click_element_by_xpath(self, xpath: str):
        """
        Optimized method to click an element using xpath.
        """
        driver = self._get_driver()
        wait = self._webdriver_wait()

        try:
            # First try the direct approach with a shorter timeout
            try:
                element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath)),
                    message=f'Element not clickable: {xpath}',
                )
                element.click()
                self.wait_for_page_load()
                return
            except Exception:
                pass

            # If that fails, try a simplified approach
            try:
                # Try with ID if present in xpath
                if 'id=' in xpath:
                    id_value = xpath.split('id=')[-1].split(']')[0]
                    element = driver.find_element(By.ID, id_value)
                    if element.is_displayed() and element.is_enabled():
                        driver.execute_script('arguments[0].click();', element)
                        self.wait_for_page_load()
                        return
            except Exception:
                pass

            # Last resort: force click with JavaScript
            try:
                element = driver.find_element(By.XPATH, xpath)
                driver.execute_script(
                    """
                    arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
                    arguments[0].click();
                """,
                    element,
                )
                self.wait_for_page_load()
                return
            except Exception as e:
                raise Exception(f'Failed to click element: {str(e)}')

        except Exception as e:
            raise Exception(f'Failed to click element with xpath: {xpath}. Error: {str(e)}')

    def handle_new_tab(self) -> None:
        """Handle newly opened tab and switch to it"""
        driver = self._get_driver()
        handles = driver.window_handles
        new_handle = handles[-1]  # Get most recently opened handle

        # Switch to new tab
        driver.switch_to.window(new_handle)
        self._current_handle = new_handle

        # Wait for page load
        self.wait_for_page_load()

        # Create and cache tab info
        tab_info = TabInfo(handle=new_handle, url=driver.current_url, title=driver.title)
        self._tab_cache[new_handle] = tab_info

    def get_tabs_info(self) -> list[TabInfo]:
        """Get information about all tabs"""
        driver = self._get_driver()
        current_handle = driver.current_window_handle
        self._current_handle = current_handle

        tabs_info = []
        for handle in driver.window_handles:
            # Use cached info if available, otherwise get new info
            if handle in self._tab_cache:
                tab_info = self._tab_cache[handle]
            else:
                # Only switch if we need to get info
                if handle != current_handle:
                    driver.switch_to.window(handle)
                tab_info = TabInfo(handle=handle, url=driver.current_url, title=driver.title)
                self._tab_cache[handle] = tab_info

            tabs_info.append(tab_info)

        # Switch back to current tab if we moved
        if driver.current_window_handle != current_handle:
            driver.switch_to.window(current_handle)

        return tabs_info

    # endregion

    @time_execution_sync('--get_state')
    def get_state(self, use_vision: bool = False) -> BrowserState:
        """
        Get the current state of the browser including page content and tab information.
        """
        self._cached_state = self._update_state(use_vision=use_vision)
        return self._cached_state

    @property
    def selector_map(self) -> SelectorMap:
        return self._cached_state.selector_map

    def xpath(self, index: int) -> str:
        return self.selector_map[index]

    def get_element(self, index: int) -> WebElement:
        driver = self._get_driver()
        return driver.find_element(By.XPATH, self.xpath(index))

    def wait_for_element(self, css_selector: str, timeout: int = 10) -> WebElement:
        """Wait for an element to appear and return it."""
        wait = WebDriverWait(self._get_driver(), timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
