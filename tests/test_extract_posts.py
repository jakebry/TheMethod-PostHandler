import unittest
from bs4 import BeautifulSoup
from threads_scraper_final import extract_posts

class ExtractPostsTest(unittest.TestCase):
    def test_extract_from_require_structure(self):
        with open('script_26.json', 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(f'<script type="application/json">{content}</script>', 'html.parser')
        posts = extract_posts(soup)
        self.assertGreater(len(posts), 0)
        self.assertIn('content', posts[0])
        self.assertIn('timestamp', posts[0])

if __name__ == '__main__':
    unittest.main()
