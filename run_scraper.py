from threads_scraper_updated import ThreadsScraper
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_scraper.py <username>")
        print("Example: python run_scraper.py j.p_morgan_trading")
        sys.exit(1)
        
    username = sys.argv[1]
    print(f"Starting scraper for user: {username}")
    
    try:
        scraper = ThreadsScraper()
        posts = scraper.get_all_posts(username)
        
        if posts:
            print(f"\nSuccessfully scraped {len(posts)} posts from {username}")
            # Save posts to text file
            with open(f"{username}_posts.txt", "w", encoding="utf-8") as f:
                for post in posts:
                    f.write(f"Author: {post['author']}\n")
                    f.write(f"Timestamp: {post['timestamp']}\n")
                    f.write(f"Content: {post['content']}\n")
                    f.write(f"Likes: {post['likes']} | Comments: {post['comments']}\n")
                    if post['images']:
                        f.write(f"Images: {', '.join(post['images'])}\n")
                    f.write("-" * 40 + "\n")
            print(f"Posts saved to {username}_posts.txt")
        else:
            print(f"No posts found for {username}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 