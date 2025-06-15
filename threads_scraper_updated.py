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

class ThreadsScraper:
    def __init__(self):
        self.base_url = "https://www.threads.net"
        load_dotenv()
        self.username = os.getenv('THREADS_USERNAME')
        self.password = os.getenv('THREADS_PASSWORD')
        self.driver = self._setup_driver()
        self._login()

    def _login(self):
        self.driver.get("https://www.threads.net/login")
        time.sleep(5)
        if "instagram.com" in self.driver.current_url:
            username_field = self._wait_for_element(By.NAME, "username")
            if username_field:
                username_field.clear()
                username_field.send_keys(self.username)
            password_field = self._wait_for_element(By.NAME, "password")
            if password_field:
                password_field.clear()
                password_field.send_keys(self.password)
            login_button = self._wait_for_element(By.XPATH, "//button[@type='submit']")
            if login_button:
                login_button.click()
                time.sleep(10)

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
            divs = soup.find_all('div')
            candidate_divs = [div for div in divs if 40 <= len(div.get_text(strip=True)) <= 2000]
            print(f"[DEBUG] Found {len(candidate_divs)} candidate divs.")
            for i, div in enumerate(candidate_divs[:10]):  # Print first 10 for brevity
                print(f"[DEBUG] Candidate div {i+1}: {div.get_text(separator=' ', strip=True)[:300]}")
            posts = []
            for div in candidate_divs:
                text = div.get_text(separator=' ', strip=True)
                post_match = re.search(r'(@?\w+)\s+(\d+[hdm])', text)
                if not post_match:
                    continue
                username = post_match.group(1).strip()
                timestamp = post_match.group(2).strip()
                content_parts = text.split(timestamp, 1)
                if len(content_parts) < 2:
                    continue
                content = content_parts[1].strip()
                content = re.sub(r'\s*(Like|Comment|Repost|Share)\s+\d+.*$', '', content).strip()
                likes = re.search(r'Like\s*(\d+)', text)
                comments = re.search(r'Comment\s*(\d+)', text)
                images = []
                skipped_images = []
                print(f"\n[IMAGE DEBUG] Processing images for post by {username}")
                all_images = div.find_all('img')
                print(f"[IMAGE DEBUG] Found {len(all_images)} total images in post")
                for idx, img in enumerate(all_images):
                    url = img.get('src') or img.get('data-src')
                    if not url:
                        skipped_images.append((url, "No src or data-src attribute"))
                        print(f"[IMAGE DEBUG] Skipping image with no src or data-src attribute.")
                        continue
                    url_base = self._strip_url_query(url)
                    profile_url_base = self._strip_url_query(profile_image_url) if profile_image_url else None
                    global_profile_url_base = self._strip_url_query(global_profile_image_url) if global_profile_image_url else None
                    # Only skip the first <img> if it matches the profile image base URL
                    if idx == 0 and profile_url_base and url_base == profile_url_base:
                        skipped_images.append((url, "First image in post div matches profile image base URL"))
                        print(f"[IMAGE DEBUG] Skipping first image in post div (matches profile image base): {url}")
                        continue
                    # Skip if it's an exact match with profile image (base URL)
                    if profile_url_base and url_base == profile_url_base:
                        skipped_images.append((url, "profile_image_url base match"))
                        print(f"[IMAGE DEBUG] Skipping profile image (profile_image_url base match): {url}")
                        continue
                    if global_profile_url_base and url_base == global_profile_url_base:
                        skipped_images.append((url, "global_profile_image_url base match"))
                        print(f"[IMAGE DEBUG] Skipping profile image (global_profile_image_url base match): {url}")
                        continue
                    # Loosen pattern-based filtering: only skip if also matches profile image or is most common
                    # (already handled above)
                    # Skip if the image appears in the header area of the post
                    parent_div = img.find_parent('div')
                    grandparent_div = parent_div.find_parent('div') if parent_div else None
                    header_classes = ['header', 'profile', 'user']
                    def has_header_class(div):
                        if not div:
                            return False
                        class_str = ' '.join(div.get('class', [])) if div.has_attr('class') else ''
                        id_str = div.get('id', '') if div.has_attr('id') else ''
                        combined = (class_str + ' ' + id_str).lower()
                        return any(hc in combined for hc in header_classes)
                    if has_header_class(parent_div) or has_header_class(grandparent_div):
                        skipped_images.append((url, "Image in header/profile/user area"))
                        print(f"[IMAGE DEBUG] Skipping image in header/profile/user area: {url}")
                        continue
                    print(f"[IMAGE DEBUG] Adding post image: {url}")
                    images.append(url)
                if not images:
                    print(f"[IMAGE DEBUG] No images found for post: '{content[:80]}...' (timestamp: {timestamp})")
                    print(f"[IMAGE DEBUG] Skipped {len(skipped_images)} images for this post:")
                    for skip_url, reason in skipped_images:
                        print(f"    [SKIPPED] {skip_url} | Reason: {reason}")
                print(f"[POST DEBUG] Timestamp: {timestamp}, Content: {content[:60]}...")
                print(f"[POST DEBUG] Found {len(images)} images for this post")
                for img_url in images:
                    print(f"[POST DEBUG]   Image URL: {img_url}")
                post_data = {
                    "author": username,
                    "timestamp": timestamp,
                    "content": content,
                    "likes": int(likes.group(1)) if likes else 0,
                    "comments": int(comments.group(1)) if comments else 0,
                    "images": images if images else None
                }
                posts.append(post_data)
            print(f"[DEBUG] Parsed {len(posts)} posts from HTML.")
            return posts if posts else None
        except Exception as e:
            print(f"[DEBUG] Exception in _parse_post_from_html: {e}")
            traceback.print_exc()
            return None

    def get_all_posts(self, username: str, max_scrolls: int = 20) -> Optional[List[Dict[str, Any]]]:
        profile_image_url = self.get_profile_image_url(username)
        self.driver.get(f"https://www.threads.net/@{username}")
        time.sleep(8)
        all_posts = []
        seen = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        # Track all image URLs to find the most common (likely profile image)
        image_url_counter = {}
        while scrolls < max_scrolls:
            html = self.driver.page_source
            # First, collect all image URLs in this HTML
            soup = BeautifulSoup(html, 'html.parser')
            for img in soup.find_all('img'):
                url = img.get('src') or img.get('data-src')
                if url:
                    url_base = self._strip_url_query(url)
                    image_url_counter[url_base] = image_url_counter.get(url_base, 0) + 1
            # Find the most common image URL (likely profile image)
            global_profile_image_url = max(image_url_counter, key=image_url_counter.get) if image_url_counter else None
            posts = self._parse_post_from_html(html, profile_image_url, global_profile_image_url)
            if posts:
                for post in posts:
                    key = (post['content'], post['timestamp'])
                    if key not in seen:
                        seen.add(key)
                        all_posts.append(post)
            
            # Scroll with a smoother approach
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_amount = current_height - last_height
            if scroll_amount > 0:
                # Scroll in smaller increments
                for i in range(3):
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount/3});")
                    time.sleep(1)
            else:
                # If no new content, try a full scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait longer for content to load
            time.sleep(5)
            
            # Try to wait for any lazy-loaded images
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                pass
                
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try one more scroll to be sure
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
            last_height = new_height
            scrolls += 1
        return all_posts if all_posts else None

    def _download_images(self, post, username):
        if not post.get('images'):
            return []
        image_paths = []
        os.makedirs('images', exist_ok=True)
        print(f"[DEBUG] Attempting to download {len(post['images'])} images for post")
        for idx, url in enumerate(post['images']):
            try:
                # Use a hash of the URL and timestamp for uniqueness
                hash_str = hashlib.md5((url + post['timestamp'] + post['content']).encode('utf-8')).hexdigest()[:8]
                # Get file extension from URL, default to jpg
                ext = url.split('.')[-1].split('?')[0]
                if len(ext) > 5 or '/' in ext or not ext.isalnum():
                    ext = 'jpg'
                filename = f"images/{username}_{hash_str}_{idx}.{ext}"
                print(f"[DEBUG] Downloading image {idx+1}/{len(post['images'])}: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"[DEBUG] Successfully saved image to {filename}")
                    image_paths.append(filename)
                else:
                    print(f"[DEBUG] Failed to download image {url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"[DEBUG] Failed to download image {url}: {e}")
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
