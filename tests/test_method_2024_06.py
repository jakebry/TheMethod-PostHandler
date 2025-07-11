from src.methods.method_2024_06 import scrape_posts_from_html

def test_scrape_posts_from_html():
    html = """
    <html><body>
    <!-- TODO: Add realistic sample HTML for Threads post -->
    </body></html>
    """
    posts = scrape_posts_from_html(html)
    assert isinstance(posts, list)
