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
import hashlib
import requests
from collections import OrderedDict
import openpyxl
from openpyxl.drawing.image import Image as XLImage
import random
from supabase.client import create_client, Client
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('threads_scraper.log'),
        logging.StreamHandler()
    ]
)

class ThreadsScraper:
    def __init__(self):
        self.base_url = "https://www.threads.net"
        load_dotenv()
        
        # Load environment variables
        self.username = os.getenv('THREADS_USERNAME')
        self.password = os.getenv('THREADS_PASSWORD')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not all([self.username, self.password, self.supabase_url, self.supabase_key]):
            raise ValueError("Missing required environment variables. Please check your .env file.")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        self.driver = self._setup_driver()
        self._seen_posts = set()

    def _setup_driver(self):
        """Set up and configure the Chrome WebDriver."""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')  # Run in headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logging.error(f"Error setting up Chrome driver: {str(e)}")
            raise

    def _save_to_supabase(self, posts: List[Dict[str, Any]], username: str) -> None:
        """Save posts to Supabase database."""
        try:
            # Create a batch of posts to insert
            posts_to_insert = []
            for post in posts:
                # Prepare post data for Supabase
                post_data = {
                    'author': username,
                    'content': post['content'],
                    'posted_at': post['timestamp'],
                    'image_urls': post['images'] if post.get('images') else []
                }
                posts_to_insert.append(post_data)
            
            # Insert posts in batches of 100
            batch_size = 100
            for i in range(0, len(posts_to_insert), batch_size):
                batch = posts_to_insert[i:i + batch_size]
                result = self.supabase.table('posts').insert(batch).execute()
                logging.info(f"Inserted batch of {len(batch)} posts to Supabase")
            
            logging.info(f"Successfully saved {len(posts)} posts to Supabase")
            
        except Exception as e:
            logging.error(f"Error saving to Supabase: {str(e)}")
            raise

    def _download_images(self, post, username):
        if not post.get('images'):
            logging.info(f"No images to download for post: {post.get('content', '')[:100]}...")
            return []
        
        image_paths = []
        try:
            os.makedirs('images', exist_ok=True)
            logging.info("Created/verified images directory")
        except Exception as e:
            logging.error(f"Failed to create images directory: {e}")
            return []
            
        logging.info(f"Attempting to download {len(post['images'])} images for post")
        for idx, url in enumerate(post['images']):
            try:
                logging.info(f"Processing image {idx+1}/{len(post['images'])}")
                logging.info(f"Image URL: {url}")
                
                # Use a hash of the URL and timestamp for uniqueness
                hash_str = hashlib.md5((url + post['timestamp'] + post['content']).encode('utf-8')).hexdigest()[:8]
                # Get file extension from URL, default to jpg
                ext = url.split('.')[-1].split('?')[0]
                if len(ext) > 5 or '/' in ext or not ext.isalnum():
                    ext = 'jpg'
                filename = f"images/{username}_{hash_str}_{idx}.{ext}"
                
                logging.info(f"Downloading image to: {filename}")
                response = requests.get(url, timeout=10)
                logging.info(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    logging.info(f"Successfully saved image to {filename}")
                    image_paths.append(filename)
                else:
                    logging.error(f"Failed to download image {url}: HTTP {response.status_code}")
            except Exception as e:
                logging.error(f"Error downloading image {url}: {e}")
                continue
        
        return image_paths

    def get_all_posts(self, username: str, max_scrolls: int = 50) -> Optional[List[Dict[str, Any]]]:
        self.driver.get(f"https://www.threads.net/@{username}")
        time.sleep(8)  # Initial wait for page load
        
        all_posts = []
        seen = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        no_new_content_count = 0
        SCROLL_PAUSE_TIME = 2
        MAX_NO_NEW_CONTENT = 3
        
        while scrolls < max_scrolls and no_new_content_count < MAX_NO_NEW_CONTENT:
            try:
                # Scroll with a smoother approach
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_amount = current_height - last_height
                
                if scroll_amount > 0:
                    for i in range(3):
                        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount/3});")
                        time.sleep(SCROLL_PAUSE_TIME/3)
                else:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(SCROLL_PAUSE_TIME)
                
                # Wait for any lazy-loaded images
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                except TimeoutException:
                    pass
                
                # Get the page content after scrolling
                html = self.driver.page_source
                
                # Parse posts from the current page state
                posts = self._parse_post_from_html(html)
                
                if posts:
                    new_posts_found = False
                    for post in posts:
                        key = (post['content'], post['timestamp'])
                        if key not in seen:
                            seen.add(key)
                            all_posts.append(post)
                            new_posts_found = True
                    
                    if not new_posts_found:
                        no_new_content_count += 1
                    else:
                        no_new_content_count = 0
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_content_count += 1
                
                if no_new_content_count >= MAX_NO_NEW_CONTENT:
                    logging.info(f"No new content found after {MAX_NO_NEW_CONTENT} attempts. Stopping scroll.")
                    break
                
                last_height = new_height
                scrolls += 1
                
                time.sleep(SCROLL_PAUSE_TIME + random.uniform(0.5, 1.5))
                
            except Exception as e:
                logging.error(f"Error during scrolling: {e}")
                traceback.print_exc()
                time.sleep(SCROLL_PAUSE_TIME * 2)
                continue
        
        if all_posts:
            # Download images for each post
            for post in all_posts:
                post['images'] = self._download_images(post, username)
            
            # Save to Supabase
            self._save_to_supabase(all_posts, username)
            
        return all_posts if all_posts else None

    def close(self):
        """Close the browser and clean up resources."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error closing driver: {str(e)}")

def main():
    try:
        scraper = ThreadsScraper()
        username = 'j.p_morgan_trading'
        posts = scraper.get_all_posts(username)
        
        if posts:
            logging.info(f"Successfully scraped {len(posts)} posts from @{username}")
        else:
            logging.warning(f"No posts found for @{username}")
            
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        traceback.print_exc()
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 