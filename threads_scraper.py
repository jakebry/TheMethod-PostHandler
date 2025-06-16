from typing import List, Dict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
from selenium import webdriver

class ThreadsScraper:
    def __init__(self):
        self.username = os.getenv('THREADS_USERNAME')
        if not self.username:
            self.username = input('Enter your Threads username: ')
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=options)

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def get_all_posts(self, username: str, max_posts: int = None) -> List[Dict]:
        """Get all posts from a user's profile."""
        try:
            # Navigate to the user's profile
            self.driver.get(f"https://www.threads.net/@{username}")
            print(f"Navigated to profile: {username}")
            
            # Wait for the page to be fully loaded
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for the main content to be visible
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Wait a bit more for dynamic content to load
            time.sleep(5)
            
            posts = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 50  # Increased max attempts
            
            while True:
                # Try to get posts using JavaScript
                try:
                    # Execute JavaScript to get all post containers
                    post_containers = self.driver.execute_script("""
                        return Array.from(document.querySelectorAll('article')).map(article => {
                            return {
                                html: article.outerHTML,
                                text: article.textContent,
                                images: Array.from(article.querySelectorAll('img')).map(img => img.src)
                            };
                        });
                    """)
                    
                    if post_containers:
                        print(f"Found {len(post_containers)} posts via JavaScript")
                        for container in post_containers:
                            try:
                                post_data = self._parse_post(container['html'])
                                if post_data:
                                    posts.append(post_data)
                                    print(f"Successfully parsed post {len(posts)}")
                            except Exception as e:
                                print(f"Error parsing post: {str(e)}")
                                continue
                    
                except Exception as e:
                    print(f"Error getting posts via JavaScript: {str(e)}")
                
                # Check if we've reached the maximum number of posts
                if max_posts and len(posts) >= max_posts:
                    print(f"Reached maximum number of posts ({max_posts})")
                    break
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:  # Try 3 times before giving up
                        print("Reached end of page or no more content loading")
                        break
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                # Check if we've exceeded max scroll attempts
                if scroll_attempts >= max_scroll_attempts:
                    print(f"Reached maximum scroll attempts ({max_scroll_attempts})")
                    break
            
            print(f"Total posts collected: {len(posts)}")
            return posts
            
        except Exception as e:
            print(f"Error getting posts: {str(e)}")
            return []

if __name__ == "__main__":
    # Initialize the scraper
    scraper = ThreadsScraper()
    
    try:
        print(f"Starting to scrape posts from @{scraper.username}")
        
        # Get all posts (limit to 10 for testing)
        posts = scraper.get_all_posts(scraper.username, max_posts=10)
        
        # Print results
        print(f"\nFound {len(posts)} posts")
        for i, post in enumerate(posts, 1):
            print(f"\nPost {i}:")
            print(f"Text: {post.get('text', 'No text')}")
            print(f"Images: {len(post.get('images', []))} images found")
            if post.get('images'):
                print("Image URLs:")
                for img in post['images']:
                    print(f"- {img}")
        
        # Pause for manual inspection
        input("\nBrowser is open for inspection. Press Enter to close and exit...")
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        # Clean up
        scraper.close() 