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

class ThreadsScraper:
    def __init__(self):
        self.base_url = "https://www.threads.net"
        load_dotenv()
        self.username = os.getenv('THREADS_USERNAME')
        self.password = os.getenv('THREADS_PASSWORD')
        if not self.username or not self.password:
            raise ValueError("THREADS_USERNAME and THREADS_PASSWORD must be set in .env file")
        self.driver = self._setup_driver()
        self._seen_posts = set()  # Initialize the set for tracking seen posts
        self._login()

    def close(self):
        """Close the browser and clean up resources."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing driver: {str(e)}")

    def _login(self):
        """Login to Threads using Instagram credentials."""
        try:
            print("Attempting to login...")
            self.driver.get("https://www.threads.net/login")
            time.sleep(5)  # Wait for initial page load
            
            # Save the login page HTML for debugging
            with open('login_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("Saved login page HTML to login_page.html")
            
            # Check if we're redirected to Instagram login
            if "instagram.com" in self.driver.current_url:
                print("Redirected to Instagram login page")
                
                # Wait for and fill username
                username_field = self._wait_for_element(By.NAME, "username")
                if not username_field:
                    print("Could not find username field. Current page source:")
                    print(self.driver.page_source[:1000])  # Print first 1000 chars
                    raise Exception("Could not find username field")
                username_field.clear()
                username_field.send_keys(self.username)
                print("Entered username")
                
                # Wait for and fill password
                password_field = self._wait_for_element(By.NAME, "password")
                if not password_field:
                    print("Could not find password field. Current page source:")
                    print(self.driver.page_source[:1000])  # Print first 1000 chars
                    raise Exception("Could not find password field")
                password_field.clear()
                password_field.send_keys(self.password)
                print("Entered password")
                
                # Click login button
                login_button = self._wait_for_element(By.XPATH, "//button[@type='submit']")
                if not login_button:
                    print("Could not find login button. Current page source:")
                    print(self.driver.page_source[:1000])  # Print first 1000 chars
                    raise Exception("Could not find login button")
                login_button.click()
                print("Clicked login button")
                
                # Wait for login to complete
                time.sleep(10)
                
                # Save the post-login page HTML for debugging
                with open('post_login.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Saved post-login page HTML to post_login.html")
                
                # Check if login was successful
                if "instagram.com" in self.driver.current_url:
                    raise Exception("Login failed - still on Instagram page")
                print("Login successful")
            else:
                print("Already logged in or on unexpected page")
                print("Current URL:", self.driver.current_url)
                print("Current page source preview:")
                print(self.driver.page_source[:1000])  # Print first 1000 chars
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            raise

    def _setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        return uc.Chrome(options=options)

    def _wait_for_element(self, by: By, value: str, timeout: int = 20) -> Optional[Any]:
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception:
            return None

    def get_profile_image_url(self, username: str) -> str:
        self.driver.get(f"https://www.threads.net/@{username}")
        time.sleep(5)
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        # Try to find the first <img> tag in the profile header area
        # This may need to be adjusted if Threads changes their layout
        img_tag = soup.find('img')
        if img_tag and img_tag.has_attr('src'):
            return img_tag['src']
        return None

    def _strip_url_query(self, url):
        if not url:
            return url
        return url.split('?', 1)[0]

    def _parse_post_from_html(self, html_content: str, profile_image_url: str = None, global_profile_image_url: str = None) -> Optional[List[Dict[str, Any]]]:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Save the HTML we're trying to parse for debugging
            with open('parse_attempt.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("Saved HTML being parsed to parse_attempt.html")
            
            # Try different selectors for post containers
            post_containers = soup.select("div[role='article']")
            if not post_containers:
                print("No posts found with role='article', trying alternative selectors...")
                post_containers = soup.select("article")
                if not post_containers:
                    post_containers = soup.select("div[data-testid='post']")
                    if not post_containers:
                        post_containers = soup.select("div[class*='post']")
            
            print(f"[DEBUG] Found {len(post_containers)} post containers.")
            if len(post_containers) == 0:
                print("HTML structure preview:")
                print(html_content[:2000])  # Print first 2000 chars
            
            posts = []
            for idx, container in enumerate(post_containers):
                try:
                    # Skip containers that are too small (likely UI elements)
                    if len(container.get_text(strip=True)) < 10:
                        continue
                        
                    # Extract text content
                    text = container.get_text(separator=' ', strip=True)
                    print(f"\n[DEBUG] Processing container {idx + 1}:")
                    print(f"[DEBUG] Raw text: {text[:200]}...")  # Print first 200 chars
                    
                    # Look for username using role='link' and aria-label
                    username_elem = container.select_one('a[role="link"][aria-label*="profile"]')
                    if not username_elem:
                        print(f"[DEBUG] No username element found in container {idx + 1}")
                        continue
                    
                    username = username_elem.get_text(strip=True)
                    if not username or username.isdigit():  # Skip if username is just a number
                        print(f"[DEBUG] Invalid username in container {idx + 1}: {username}")
                        continue
                    
                    # Find timestamp using aria-label
                    timestamp_elem = container.select_one('time[aria-label]')
                    if not timestamp_elem:
                        print(f"[DEBUG] No timestamp element found in container {idx + 1}")
                        continue
                    
                    timestamp = timestamp_elem.get('aria-label', '').strip()
                    if not timestamp:
                        print(f"[DEBUG] Empty timestamp in container {idx + 1}")
                        continue
                    
                    print(f"[DEBUG] Found username: {username}, timestamp: {timestamp}")
                    
                    # Find content using role='text'
                    content_elem = container.select_one('div[role="text"]')
                    if not content_elem:
                        print(f"[DEBUG] No content element found in container {idx + 1}")
                        continue
                    
                    content = content_elem.get_text(strip=True)
                    if not content:
                        print(f"[DEBUG] Empty content in container {idx + 1}")
                        continue
                    
                    print(f"[DEBUG] Extracted content: {content[:100]}...")
                    
                    # Find likes and comments using aria-label
                    likes = 0
                    comments = 0
                    
                    # Look for likes button with aria-label
                    likes_elem = container.select_one('button[aria-label*="like"]')
                    if likes_elem:
                        likes_text = likes_elem.get('aria-label', '')
                        likes_match = re.search(r'(\d+)', likes_text)
                        if likes_match:
                            likes = int(likes_match.group(1))
                    
                    # Look for comments button with aria-label
                    comments_elem = container.select_one('button[aria-label*="comment"]')
                    if comments_elem:
                        comments_text = comments_elem.get('aria-label', '')
                        comments_match = re.search(r'(\d+)', comments_text)
                        if comments_match:
                            comments = int(comments_match.group(1))
                    
                    print(f"[DEBUG] Found likes: {likes}, comments: {comments}")
                    
                    # Process images within this post container
                    images = []
                    skipped_images = []
                    print(f"\n[IMAGE DEBUG] Processing images for post by {username}")
                    
                    # Find all images within this post container
                    post_images = container.find_all('img')
                    print(f"[IMAGE DEBUG] Found {len(post_images)} total images in post")
                    
                    for img_idx, img in enumerate(post_images):
                        try:
                            url = img.get('src') or img.get('data-src')
                            if not url:
                                print(f"[IMAGE DEBUG] Skipping image {img_idx + 1}: No URL found")
                                continue
                            
                            # Skip profile images
                            if url == profile_image_url or url == global_profile_image_url:
                                skipped_images.append((url, "Profile image"))
                                print(f"[IMAGE DEBUG] Skipping image {img_idx + 1}: Profile image")
                                continue
                            
                            # Get image dimensions
                            width = img.get('width')
                            height = img.get('height')
                            
                            # Skip small images (likely icons)
                            if width and height and int(width) < 100 and int(height) < 100:
                                skipped_images.append((url, "Small image (likely icon)"))
                                print(f"[IMAGE DEBUG] Skipping image {img_idx + 1}: Small image ({width}x{height})")
                                continue
                            
                            # Skip images in header/profile areas using role attributes
                            parent_div = img.find_parent('div')
                            if parent_div and parent_div.get('role') in ['banner', 'complementary']:
                                skipped_images.append((url, "Image in header/profile area"))
                                print(f"[IMAGE DEBUG] Skipping image {img_idx + 1}: Header/profile image")
                                continue
                            
                            # Check if the image URL is from a CDN (likely a post image)
                            if 'cdn' in url.lower() or 'instagram' in url.lower():
                                print(f"[IMAGE DEBUG] Adding post image {img_idx + 1}: CDN image")
                                images.append(url)
                            else:
                                # For non-CDN images, check if they're large enough to be post images
                                if width and height and (int(width) > 200 or int(height) > 200):
                                    print(f"[IMAGE DEBUG] Adding post image {img_idx + 1}: Large non-CDN image ({width}x{height})")
                                    images.append(url)
                                else:
                                    skipped_images.append((url, "Small non-CDN image"))
                                    print(f"[IMAGE DEBUG] Skipping image {img_idx + 1}: Small non-CDN image ({width}x{height})")
                        
                        except Exception as img_error:
                            print(f"[ERROR] Failed to process image {img_idx + 1}: {str(img_error)}")
                            continue
                    
                    # Create post object
                    post = {
                        'author': username,
                        'timestamp': timestamp,
                        'content': content,
                        'likes': likes,
                        'comments': comments,
                        'images': images
                    }
                    
                    # Generate a unique hash for this post
                    post_hash = hashlib.md5(f"{username}{timestamp}{content}".encode()).hexdigest()
                    
                    # Only add if we haven't seen this post before
                    if post_hash not in self._seen_posts:
                        self._seen_posts.add(post_hash)
                        posts.append(post)
                        print(f"[DEBUG] Added new post from {username}")
                    else:
                        print(f"[DEBUG] Skipping duplicate post from {username}")
                
                except Exception as post_error:
                    print(f"[ERROR] Failed to process post container {idx + 1}: {str(post_error)}")
                    print(f"[ERROR] Traceback: {traceback.format_exc()}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"[ERROR] Failed to parse HTML content: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return None

    def wait_for_images_to_load(self, timeout=10):
        """Wait until all images in the viewport have a non-empty src attribute."""
        import time
        from selenium.webdriver.common.by import By
        end_time = time.time() + timeout
        while time.time() < end_time:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            if all(img.get_attribute("src") for img in images):
                return True
            time.sleep(0.5)
        print("[DEBUG] Timeout waiting for images to load.")
        return False

    def get_all_posts(self, username: str, max_scrolls: int = 50) -> Optional[List[Dict[str, Any]]]:
        profile_image_url = self.get_profile_image_url(username)
        self.driver.get(f"https://www.threads.net/@{username}")
        time.sleep(8)  # Initial wait for page load
        
        # Save the full HTML for debugging
        with open('full_page.html', 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        all_posts = []
        seen = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        no_new_content_count = 0
        SCROLL_PAUSE_TIME = 2  # Base pause time between scrolls
        MAX_NO_NEW_CONTENT = 3  # Number of times to try before giving up
        
        # Track all image URLs to find the most common (likely profile image)
        image_url_counter = {}
        
        while scrolls < max_scrolls and no_new_content_count < MAX_NO_NEW_CONTENT:
            try:
                # Scroll with a smoother approach
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_amount = current_height - last_height
                
                if scroll_amount > 0:
                    # Scroll in smaller increments for smoother loading
                    for i in range(3):
                        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount/3});")
                        time.sleep(SCROLL_PAUSE_TIME/3)
                else:
                    # If no new content, try a full scroll
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
                
                # Update image URL counter
                soup = BeautifulSoup(html, 'html.parser')
                for img in soup.find_all('img'):
                    url = img.get('src') or img.get('data-src')
                    if url:
                        url_base = self._strip_url_query(url)
                        image_url_counter[url_base] = image_url_counter.get(url_base, 0) + 1
                
                # Find the most common image URL (likely profile image)
                global_profile_image_url = max(image_url_counter, key=image_url_counter.get) if image_url_counter else None
                
                # Parse posts from the current page state
                posts = self._parse_post_from_html(html, profile_image_url, global_profile_image_url)
                
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
                        no_new_content_count = 0  # Reset counter if we found new posts
                
                # Check if we've reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_content_count += 1
                
                if no_new_content_count >= MAX_NO_NEW_CONTENT:
                    print(f"[DEBUG] No new content found after {MAX_NO_NEW_CONTENT} attempts. Stopping scroll.")
                    break
                
                last_height = new_height
                scrolls += 1
                
                # Add a small random delay to avoid detection
                time.sleep(SCROLL_PAUSE_TIME + random.uniform(0.5, 1.5))
                
                # Wait for images to load after each scroll
                self.wait_for_images_to_load(timeout=10)
                
            except Exception as e:
                print(f"[DEBUG] Error during scrolling: {e}")
                traceback.print_exc()
                # Try to continue scrolling if possible
                time.sleep(SCROLL_PAUSE_TIME * 2)
                continue
        
        print(f"[DEBUG] Completed scrolling after {scrolls} iterations. Found {len(all_posts)} unique posts.")
        return all_posts if all_posts else None

    def _download_images(self, post, username):
        if not post.get('images'):
            print(f"[DEBUG] No images to download for post: {post.get('content', '')[:100]}...")
            return []
        
        image_paths = []
        try:
            os.makedirs('images', exist_ok=True)
            print(f"[DEBUG] Created/verified images directory")
        except Exception as e:
            print(f"[DEBUG] Failed to create images directory: {e}")
            return []
            
        print(f"[DEBUG] Attempting to download {len(post['images'])} images for post")
        for idx, url in enumerate(post['images']):
            try:
                print(f"[DEBUG] Processing image {idx+1}/{len(post['images'])}")
                print(f"[DEBUG] Image URL: {url}")
                
                # Use a hash of the URL and timestamp for uniqueness
                hash_str = hashlib.md5((url + post['timestamp'] + post['content']).encode('utf-8')).hexdigest()[:8]
                # Get file extension from URL, default to jpg
                ext = url.split('.')[-1].split('?')[0]
                if len(ext) > 5 or '/' in ext or not ext.isalnum():
                    ext = 'jpg'
                filename = f"images/{username}_{hash_str}_{idx}.{ext}"
                
                print(f"[DEBUG] Downloading image to: {filename}")
                response = requests.get(url, timeout=10)
                print(f"[DEBUG] Response status code: {response.status_code}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"[DEBUG] Successfully saved image to {filename}")
                    image_paths.append(filename)
                else:
                    print(f"[DEBUG] Failed to download image {url}: HTTP {response.status_code}")
                    print(f"[DEBUG] Response content: {response.text[:200]}...")
            except requests.exceptions.RequestException as e:
                print(f"[DEBUG] Network error downloading image {url}: {e}")
            except IOError as e:
                print(f"[DEBUG] File system error saving image {url}: {e}")
            except Exception as e:
                print(f"[DEBUG] Unexpected error downloading image {url}: {e}")
                print(f"[DEBUG] Error type: {type(e)}")
                print(f"[DEBUG] Error details: {str(e)}")
        
        print(f"[DEBUG] Successfully downloaded {len(image_paths)}/{len(post['images'])} images")
        return image_paths

    def _load_existing_posts(self, filename):
        posts = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                post = {}
                for line in f:
                    if line.strip() == '-' * 40:
                        if post:
                            posts.append(post)
                        post = {}
                    elif line.startswith('Author: '):
                        post['author'] = line[len('Author: '):].strip()
                    elif line.startswith('Timestamp: '):
                        post['timestamp'] = line[len('Timestamp: '):].strip()
                    elif line.startswith('Content: '):
                        post['content'] = line[len('Content: '):].strip()
                    elif line.startswith('Likes: '):
                        likes_comments = line[len('Likes: '):].strip().split('|')
                        post['likes'] = int(likes_comments[0].replace('Likes:', '').strip())
                        post['comments'] = int(likes_comments[1].replace('Comments:', '').strip()) if len(likes_comments) > 1 else 0
                    elif line.startswith('Images: '):
                        post['images'] = [img.strip() for img in line[len('Images: '):].split(',') if img.strip()]
                if post:
                    posts.append(post)
        return posts

    def _delete_all_images(self):
        images_dir = 'images'
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                file_path = os.path.join(images_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"[DEBUG] Failed to delete {file_path}: {e}")

def main():
    scraper = ThreadsScraper()
    username = 'j.p_morgan_trading'
    filename = f"{username}_posts.txt"
    excel_filename = f"{username}_posts.xlsx"
    existing_posts = scraper._load_existing_posts(filename)
    # Delete all images before parsing
    scraper._delete_all_images()
    posts = scraper.get_all_posts(username)
    # Use a set of (content, timestamp) for deduplication
    existing_keys = set((p['content'], p['timestamp']) for p in existing_posts)
    # Map for quick lookup of images for existing posts
    existing_images_map = { (p['content'], p['timestamp']): p.get('images') for p in existing_posts }
    new_posts = []
    if posts:
        for post in posts:
            key = (post['content'], post['timestamp'])
            if key not in existing_keys:
                # Download images and update post with local paths
                post['images'] = scraper._download_images(post, username)
                new_posts.append(post)
            else:
                # If post already exists, keep its images (do not re-download)
                post['images'] = existing_images_map.get(key)
                new_posts.append(post)
        # Prepend new posts to the file
        all_posts = new_posts + [p for p in existing_posts if (p['content'], p['timestamp']) not in set((p['content'], p['timestamp']) for p in new_posts)]
        # Deduplicate all_posts by (content, timestamp)
        unique_posts = OrderedDict()
        for post in all_posts:
            key = (post['content'], post['timestamp'])
            if key not in unique_posts:
                unique_posts[key] = post
        # Save to Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Posts"
        # Find max number of images in any post
        max_images = max(len(post.get('images', [])) if post.get('images') else 0 for post in unique_posts.values())
        # Header
        headers = ["Author", "Timestamp", "Content", "Likes", "Comments"] + [f"Image {i+1}" for i in range(max_images)]
        ws.append(headers)
        for post in unique_posts.values():
            row = [post['author'], post['timestamp'], post['content'], post['likes'], post['comments']]
            images = post.get('images', []) or []
            # Add image paths for now, will embed below
            for i in range(max_images):
                row.append(images[i] if i < len(images) else "")
            ws.append(row)
        # Embed images
        for idx, post in enumerate(unique_posts.values(), start=2):  # start=2 to skip header
            images = post.get('images', []) or []
            for img_idx, img_path in enumerate(images):
                if os.path.exists(img_path):
                    try:
                        img = XLImage(img_path)
                        # Resize image for cell (optional, e.g., 100x100)
                        img.width = 100
                        img.height = 100
                        col_letter = openpyxl.utils.get_column_letter(6 + img_idx)  # 6th col is Image 1
                        ws.add_image(img, f"{col_letter}{idx}")
                    except Exception as e:
                        print(f"[EXCEL DEBUG] Failed to embed image {img_path}: {e}")
        wb.save(excel_filename)
        print(f"{len(new_posts)} new posts added. {len(unique_posts)} total posts saved to {excel_filename}")
    else:
        print("No posts found.")

if __name__ == "__main__":
    main()
