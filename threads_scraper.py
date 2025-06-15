import json
import time
import logging
import traceback
import re
from typing import Dict, Optional, Any, List
import os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException
)
from datetime import datetime
from bs4 import BeautifulSoup

class DebugFilter(logging.Filter):
    """Filter to only show important debug messages."""
    def filter(self, record):
        # Only show debug messages that are important for troubleshooting
        if record.levelno != logging.DEBUG:
            return True
        
        # Filter out noisy debug messages
        skip_patterns = [
            "Current page source",
            "Found div elements",
            "Div ",
            "Selector ",
            "Element found:",
            "Chrome options configured"
        ]
        
        return not any(pattern in record.getMessage() for pattern in skip_patterns)

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO by default
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('threads_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add debug filter
debug_filter = DebugFilter()
logger.addFilter(debug_filter)

# Create a separate debug logger for detailed debugging
debug_logger = logging.getLogger('threads_scraper.debug')
debug_logger.setLevel(logging.DEBUG)
debug_handler = logging.FileHandler('threads_scraper.debug.log')
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
debug_logger.addHandler(debug_handler)

class ThreadsScraper:
    def __init__(self):
        self.base_url = "https://www.threads.net"
        load_dotenv()
        self.username = os.getenv('THREADS_USERNAME')
        self.password = os.getenv('THREADS_PASSWORD')
        self.driver = self._setup_driver()
        self._login()

    def _log_debug(self, message: str):
        """Log debug messages to the debug file only."""
        debug_logger.debug(message)

    def _log_error(self, message: str, error: Optional[Exception] = None):
        """Log error messages with optional exception details."""
        if error:
            logger.error(f"{message}: {str(error)}")
            debug_logger.error(f"{message}: {str(error)}\n{traceback.format_exc()}")
        else:
            logger.error(message)
            debug_logger.error(message)

    def _login(self):
        """Handle login to Threads."""
        try:
            logger.info("Attempting to log in to Threads...")
            self._log_debug(f"Using username: {self.username}")
            
            # First try to access Threads directly
            self.driver.get("https://www.threads.net/login")
            time.sleep(5)
            self._log_debug(f"Initial URL: {self.driver.current_url}")
            
            # Check if we need to log in through Instagram
            if "instagram.com" in self.driver.current_url:
                logger.info("Redirected to Instagram login")
                
                # Wait for username field and enter credentials
                username_field = self._wait_for_element(By.NAME, "username")
                if username_field:
                    username_field.clear()
                    username_field.send_keys(self.username)
                    self._log_debug("Username entered")
                else:
                    self._log_error("Username field not found")
                    return False
                
                # Wait for password field and enter credentials
                password_field = self._wait_for_element(By.NAME, "password")
                if password_field:
                    password_field.clear()
                    password_field.send_keys(self.password)
                    self._log_debug("Password entered")
                else:
                    self._log_error("Password field not found")
                    return False
                
                # Find and click login button
                login_button = self._wait_for_element(By.XPATH, "//button[@type='submit']")
                if login_button:
                    self._log_debug("Login button found, attempting to click")
                    login_button.click()
                    logger.info("Login button clicked")
                else:
                    self._log_error("Login button not found")
                    return False
                
                # Wait for login to complete
                time.sleep(10)
                self._log_debug(f"Post-login URL: {self.driver.current_url}")
                
                # Check if login was successful
                if "login" in self.driver.current_url.lower():
                    self._log_error("Login failed - still on login page")
                    screenshot_path = f"login_error_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Login error screenshot saved to {screenshot_path}")
                    return False
                
                logger.info("Login successful")
                return True
            else:
                logger.info("Already logged in or on Threads page")
                return True
                
        except Exception as e:
            self._log_error("Login failed", e)
            screenshot_path = f"login_exception_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Login exception screenshot saved to {screenshot_path}")
            return False

    def _setup_driver(self):
        """Set up and return a configured Chrome WebDriver with detailed error handling."""
        try:
            logger.info("Setting up Chrome WebDriver...")
            options = uc.ChromeOptions()
            # Remove headless mode for login
            # options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Add additional options for debugging
            options.add_argument("--enable-logging")
            options.add_argument("--v=1")
            
            logger.debug("Chrome options configured")
            driver = uc.Chrome(options=options)
            logger.info("Chrome WebDriver setup successful")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _wait_for_element(self, by: By, value: str, timeout: int = 20) -> Optional[Any]:
        """Wait for an element with detailed error handling."""
        try:
            self._log_debug(f"Waiting for element: {by}={value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self._log_error(f"Timeout waiting for element: {by}={value}")
            return None
        except Exception as e:
            self._log_error(f"Error waiting for element {by}={value}", e)
            return None

    def _parse_post_from_html(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Parse a post from HTML content using BeautifulSoup.
        
        Args:
            html_content: The HTML content to parse
            
        Returns:
            A dictionary containing the parsed post data or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all div elements with text content
            divs = soup.find_all('div')
            
            # Filter divs by text length (100-1000 chars)
            candidate_divs = [div for div in divs if 100 <= len(div.get_text(strip=True)) <= 1000]
            
            for div in candidate_divs:
                text = div.get_text(strip=True)
                
                # Try to match the post pattern
                post_match = re.match(r'^(.*?)\s+(\d{1,2}h)\s+More', text)
                if post_match:
                    username = post_match.group(1)
                    timestamp = post_match.group(2)
                    
                    # Extract the main content by removing header and interaction buttons
                    content = text.split('More')[1].strip()
                    content = re.sub(r'Like\s+\d+|Comment\s+\d+|Repost|Share', '', content).strip()
                    
                    # Extract engagement stats
                    likes_match = re.search(r'Like\s+(\d+)', text)
                    comments_match = re.search(r'Comment\s+(\d+)', text)
                    
                    post_data = {
                        'author': username,
                        'timestamp': timestamp,
                        'content': content,
                        'likes': int(likes_match.group(1)) if likes_match else 0,
                        'comments': int(comments_match.group(1)) if comments_match else 0
                    }
                    
                    return post_data
            
            return None
            
        except Exception as e:
            self._log_error("Error parsing post from HTML", e)
            return None

    def get_most_recent_post(self, username):
        """Get the most recent post from a user's profile."""
        try:
            self._log_debug(f"Navigating to profile: {username}")
            self.driver.get(f"https://www.threads.net/@{username}")
            
            # Wait for JS to render posts
            time.sleep(8)
            self._log_debug(f"Current URL: {self.driver.current_url}")
            self._log_debug(f"Page title: {self.driver.title}")

            # Save the full rendered HTML for inspection
            rendered_html = self.driver.page_source
            rendered_html_path = f"rendered_html_{username}.html"
            with open(rendered_html_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            self._log_debug(f"Full rendered HTML saved to {rendered_html_path}")

            # Parse the post using BeautifulSoup
            post_data = self._parse_post_from_html(rendered_html)
            if post_data:
                return post_data
            
            # Fallback to Selenium if BeautifulSoup parsing fails
            post_selector = "div[tabindex='0'][role='button']"
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, post_selector)) > 0
                )
            except Exception as e:
                self._log_debug(f"No post containers found with selector {post_selector}: {e}")
                self.driver.save_screenshot(f"no_post_selector_{username}.png")
                return None
            
            posts = self.driver.find_elements(By.CSS_SELECTOR, post_selector)
            self._log_debug(f"Found {len(posts)} post containers.")
            if not posts:
                self._log_debug("No posts found after wait.")
                return None
            
            # Try to extract the text from the first post
            for el in posts:
                try:
                    if el.is_displayed():
                        post_text = el.text.strip()
                        if post_text:
                            # Try parsing the post text directly
                            post_data = self._parse_post_from_html(f"<div>{post_text}</div>")
                            if post_data:
                                return post_data
                except Exception as e:
                    self._log_debug(f"Error reading post element: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self._log_error("Error in get_most_recent_post", e)
            return None

def main():
    try:
        logger.info("Starting Threads scraper")
        scraper = ThreadsScraper()
        
        username = input("Enter Threads username (without @): ").strip()
        logger.info(f"Processing username: {username}")
        
        print(f"Fetching the most recent post for @{username}...")
        post = scraper.get_most_recent_post(username)
        
        if post:
            print("\nMost Recent Post:")
            print(f"Author: @{post['author']}")
            print(f"Posted: {post['timestamp']}")
            print(f"Content: {post['content']}")
            print(f"Likes: {post['likes']}")
            print(f"Comments: {post['comments']}")
            
            output_file = f"{username}_most_recent_post.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(post, f, indent=2, ensure_ascii=False)
            logger.info(f"Post data saved to {output_file}")
            print(f"\nMost recent post saved to {output_file}")
        else:
            logger.warning("No post found or error occurred")
            print("No post found or error occurred. Check threads_scraper.log for details.")
            
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"An error occurred: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check threads_scraper.log for detailed error information")
        print("2. Make sure Google Chrome is installed and up to date")
        print("3. Try running the script again")
        print("4. If the error persists, check the log file for specific error messages")

if __name__ == "__main__":
    main() 