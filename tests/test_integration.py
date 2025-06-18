import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import tempfile
import shutil

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from threads_scraper_supabase import ThreadsScraper


class TestThreadsScraperIntegration:
    """Integration tests for ThreadsScraper with Supabase"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_table.insert.return_value = mock_insert
        mock_client.table.return_value = mock_table
        return mock_client, mock_table, mock_insert
    
    @pytest.fixture
    def sample_html_with_posts(self):
        """Sample HTML with Threads posts data"""
        sample_data = {
            "props": {
                "pageProps": {
                    "feed": {
                        "threads": [
                            {
                                "thread_items": [
                                    {
                                        "post": {
                                            "caption": {"text": "Test post content 1"},
                                            "taken_at": 1710000000,
                                            "image_versions2": {
                                                "candidates": [
                                                    {"url": "https://example.com/img1.jpg"}
                                                ]
                                            }
                                        }
                                    },
                                    {
                                        "post": {
                                            "caption": {"text": "Test post content 2"},
                                            "taken_at": 1710000001,
                                            "image_versions2": {
                                                "candidates": []
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
        
        return f'''
        <html>
            <body>
                <script type="application/json">{json.dumps(sample_data)}</script>
                <div class="post">Some other content</div>
            </body>
        </html>
        '''
    
    @pytest.fixture
    def scraper_with_mocks(self, mock_supabase):
        """Create a ThreadsScraper instance with mocked dependencies"""
        mock_client, mock_table, mock_insert = mock_supabase
        
        # Set up environment variables
        os.environ['THREADS_USERNAME'] = 'test_user'
        os.environ['THREADS_PASSWORD'] = 'test_pass'
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test_key'
        
        with patch.object(ThreadsScraper, '_setup_driver') as mock_driver:
            with patch('threads_scraper_supabase.create_client', return_value=mock_client):
                scraper = ThreadsScraper()
                scraper.driver = mock_driver
                return scraper, mock_client, mock_table, mock_insert
    
    def test_a_can_find_data_to_parse(self, scraper_with_mocks, sample_html_with_posts):
        """Test A: Can the scraper find the correct data to parse?"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Mock the driver to return our sample HTML
        scraper.driver.page_source = sample_html_with_posts
        
        # Test that the scraper can find and extract posts from HTML
        posts = scraper._parse_post_from_html(sample_html_with_posts)
        
        # Verify that posts were found
        assert posts is not None
        assert len(posts) > 0
        assert isinstance(posts, list)
        
        # Verify the structure of found posts
        for post in posts:
            assert 'content' in post
            assert 'timestamp' in post
            assert 'images' in post
            assert isinstance(post['content'], str)
            assert len(post['content']) > 0
    
    def test_b_data_successfully_parsed(self, scraper_with_mocks, sample_html_with_posts):
        """Test B: Was the data successfully parsed?"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Parse the sample HTML
        posts = scraper._parse_post_from_html(sample_html_with_posts)
        
        # Verify parsing results
        assert len(posts) == 2  # We expect 2 posts from our sample data
        
        # Check first post
        first_post = posts[0]
        assert first_post['content'] == "Test post content 1"
        # Use the actual converted timestamp instead of hardcoded value
        expected_timestamp_1 = datetime.fromtimestamp(1710000000, timezone.utc).isoformat().replace('+00:00', 'Z')
        assert first_post['timestamp'] == expected_timestamp_1
        assert first_post['images'] == ["https://example.com/img1.jpg"]
        
        # Check second post
        second_post = posts[1]
        assert second_post['content'] == "Test post content 2"
        # Use the actual converted timestamp instead of hardcoded value
        expected_timestamp_2 = datetime.fromtimestamp(1710000001, timezone.utc).isoformat().replace('+00:00', 'Z')
        assert second_post['timestamp'] == expected_timestamp_2
        assert second_post['images'] == []  # No images in second post
    
    def test_c_posts_updated_to_supabase(self, scraper_with_mocks, sample_html_with_posts):
        """Test C: Were the posts updated to Supabase?"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Parse posts first
        posts = scraper._parse_post_from_html(sample_html_with_posts)
        
        # Save to Supabase
        scraper._save_to_supabase(posts, 'test_username')
        
        # Verify Supabase was called correctly
        mock_client.table.assert_called_once_with('posts')
        mock_table.insert.assert_called_once()
        
        # Check the data that was sent to Supabase
        args, kwargs = mock_table.insert.call_args
        inserted_posts = args[0]
        
        # Verify the structure of data sent to Supabase
        assert len(inserted_posts) == 2
        
        # Check first post data structure
        first_inserted = inserted_posts[0]
        assert first_inserted['author'] == 'test_username'
        assert first_inserted['content'] == "Test post content 1"
        # Use the actual converted timestamp instead of hardcoded value
        expected_timestamp_1 = datetime.fromtimestamp(1710000000, timezone.utc).isoformat().replace('+00:00', 'Z')
        assert first_inserted['posted_at'] == expected_timestamp_1
        assert first_inserted['image_urls'] == ["https://example.com/img1.jpg"]
        
        # Check second post data structure
        second_inserted = inserted_posts[1]
        assert second_inserted['author'] == 'test_username'
        assert second_inserted['content'] == "Test post content 2"
        # Use the actual converted timestamp instead of hardcoded value
        expected_timestamp_2 = datetime.fromtimestamp(1710000001, timezone.utc).isoformat().replace('+00:00', 'Z')
        assert second_inserted['posted_at'] == expected_timestamp_2
        assert second_inserted['image_urls'] == []
        
        # Verify execute was called
        mock_insert.execute.assert_called_once()
    
    def test_full_pipeline_integration(self, scraper_with_mocks, sample_html_with_posts):
        """Test the complete pipeline: find data → parse → save to Supabase"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Mock the driver methods
        scraper.driver.get.return_value = None
        scraper.driver.page_source = sample_html_with_posts
        scraper.driver.execute_script.return_value = 1000  # Mock scroll height
        
        # Mock the _download_images method to avoid actual downloads
        with patch.object(scraper, '_download_images', return_value=[]):
            # Run the full pipeline
            result = scraper.get_all_posts('test_username', max_scrolls=1)
        
        # Verify the pipeline worked end-to-end
        assert result is not None
        assert len(result) == 2
        
        # Verify Supabase was called
        mock_client.table.assert_called_with('posts')
        mock_table.insert.assert_called()
        mock_insert.execute.assert_called()
    
    def test_error_handling_invalid_html(self, scraper_with_mocks):
        """Test error handling when HTML doesn't contain expected data"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Test with invalid HTML
        invalid_html = "<html><body><div>No posts here</div></body></html>"
        
        posts = scraper._parse_post_from_html(invalid_html)
        
        # Should return empty list, not crash
        assert posts == []
    
    def test_error_handling_malformed_json(self, scraper_with_mocks):
        """Test error handling when JSON in HTML is malformed"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Test with malformed JSON
        malformed_html = '''
        <html>
            <body>
                <script type="application/json">{"invalid": "json"</script>
            </body>
        </html>
        '''
        
        posts = scraper._parse_post_from_html(malformed_html)
        
        # Should handle gracefully and return empty list
        assert posts == []
    
    def test_supabase_connection_error_handling(self, scraper_with_mocks, sample_html_with_posts):
        """Test error handling when Supabase connection fails"""
        scraper, mock_client, mock_table, mock_insert = scraper_with_mocks
        
        # Make Supabase throw an exception
        mock_table.insert.side_effect = Exception("Supabase connection failed")
        
        posts = scraper._parse_post_from_html(sample_html_with_posts)
        
        # Should raise an exception when trying to save
        with pytest.raises(Exception, match="Supabase connection failed"):
            scraper._save_to_supabase(posts, 'test_username')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 