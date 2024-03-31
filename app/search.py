import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException, StaleElementReferenceException, NoSuchElementException
from utils.url import UrlParser  
from infra.logging_config import log_info, log_warning, log_error

class NYSearch:
    def __init__(self, driver, query, subject):
        self.driver = driver
        self.query = query
        self.subject = subject
        self.quantity = 0
        self.url = UrlParser(self.query)

    # Opens the search page
    def open_search(self):
        try:
            self.driver.get(self.url.construct_url())
            log_info(f"Search page opened for URL: {self.url.construct_url()}")
        except Exception as e:
            log_error(f"Failed to open search page: {e}")

    # Retrieves the quantity of news items found
    def news_quantity(self):
        try:
            element_text = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='site-content']/div/div[1]/div[1]/p"))
            ).text
            matches = re.findall(r'\d+', element_text)
            quantity = matches[0] if matches else "0"
            log_info(f"Number of news items found: {quantity}")
            return quantity
        except TimeoutException:
            log_error("Timeout occurred while trying to find the number of news articles.")
        except NoSuchElementException:
            log_error("The news quantity element was not found on the page.")
        except Exception as e:
            log_error(f"An unexpected error occurred while retrieving news quantity: {e}")
        return "0"

    # Selects the subject from the search filters
    def select_subject(self):
        time.sleep(2)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='fides-banner-button-primary']"))
            ).click()

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='search-multiselect-button']"))
            ).click()

            options_labels = self.driver.find_elements(By.XPATH, "//ul[@data-testid='multi-select-dropdown-list']/li//span[@class='css-16eo56s']")
            
            for option_label in options_labels:
                option_text = option_label.text.strip()
                match = re.match(r"([a-zA-Z]+)", option_text)
                if match:
                    clean_option_text = match.group(1)
                    if clean_option_text.lower() == self.subject.lower():
                        option_input = option_label.find_element(By.XPATH, "./ancestor::li//input[@type='checkbox']")
                        option_input.click()
                        log_info(f"Subject '{self.subject}' selected.")
                        break
        except TimeoutException:
            log_warning("Timeout occurred while trying to select the subject.")

    # Clicks the 'Show More' button to load more news items
    def click_show_more(self):
        while True:
            try:
                show_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='search-show-more-button']"))
                )
                show_more_button.click()
            except TimeoutException:
                log_info("All news items loaded.")
                break
            except StaleElementReferenceException:
                continue

    # Performs the search and handles the sequence of actions
    def search(self):
        try:
            log_info(f"Initiating search with query '{self.query}' and subject '{self.subject}'.")
            self.open_search()
            self.select_subject()
            self.news_quantity()
            self.click_show_more()
        except Exception as e:
            log_error(f"An unexpected error occurred during the search: {e}")
        