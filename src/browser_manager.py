import os
import json
import logging
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict, Any
from src.performance_monitor import get_performance_monitor, monitor_operation

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Optimized browser manager with session persistence and anti-detection measures.
    """
    
    def __init__(self):
        # Use local cache directory for development, Docker cache for production
        if os.path.exists("/app/.cache"):
            self.cache_dir = Path("/app/.cache")
        else:
            # Local development - use current directory
            self.cache_dir = Path(".cache")
        
        self.profiles_dir = self.cache_dir / "browser_profiles"
        self.sessions_dir = self.cache_dir / "sessions"
        
        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Performance monitor
        self.performance_monitor = get_performance_monitor()
        
    def get_optimized_browser_args(self) -> list:
        """Get optimized browser arguments for faster startup and anti-detection."""
        return [
            # Performance optimizations
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-domain-reliability",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--disable-translate",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            
            # Memory optimizations
            "--memory-pressure-off",
            "--max_old_space_size=4096",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--mute-audio",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            
            # Anti-detection measures
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-ipc-flooding-protection",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-features=TranslateUI",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-domain-reliability",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--disable-translate",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            
            # User agent spoofing
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Additional flags for Threads compatibility
            "--disable-features=site-per-process",
            "--disable-site-isolation-trials",
            "--disable-features=VizDisplayCompositor",
            "--disable-features=TranslateUI",
            "--disable-features=BlinkGenPropertyTrees",
            "--disable-features=BlinkScheduler",
            "--disable-features=BlinkSchedulerDfs",
            "--disable-features=BlinkSchedulerHighPriority",
            "--disable-features=BlinkSchedulerLowPriority",
            "--disable-features=BlinkSchedulerNormalPriority",
            "--disable-features=BlinkSchedulerUrgentPriority",
        ]
    
    def get_profile_path(self, profile_name: str) -> Path:
        """Get the path for a specific browser profile."""
        return self.profiles_dir / profile_name
    
    def get_session_path(self, session_name: str) -> Path:
        """Get the path for a specific session file."""
        return self.sessions_dir / f"{session_name}.json"
    
    def save_session(self, session_name: str, cookies: list, storage_state: dict):
        """Save browser session data for later restoration."""
        session_data = {
            "cookies": cookies,
            "storage_state": storage_state,
            "timestamp": str(Path().stat().st_mtime)
        }
        
        session_path = self.get_session_path(session_name)
        with open(session_path, 'w') as f:
            json.dump(session_data, f)
        
        logger.info(f"Saved session: {session_name}")
    
    def load_session(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Load browser session data if it exists."""
        session_path = self.get_session_path(session_name)
        
        if session_path.exists():
            try:
                with open(session_path, 'r') as f:
                    session_data = json.load(f)
                logger.info(f"Loaded session: {session_name}")
                return session_data
            except Exception as e:
                logger.warning(f"Failed to load session {session_name}: {e}")
        
        return None
    
    def create_context(self, profile_name: str = "default", session_name: str = None) -> BrowserContext:
        """Create a browser context with optimized settings and optional session restoration."""
        
        profile_path = self.get_profile_path(profile_name)
        profile_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing session if available
        session_data = None
        if session_name:
            session_data = self.load_session(session_name)
        
        context_options = {
            "ignore_https_errors": True,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/Los_Angeles",
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        }
        
        # Restore session data if available
        if session_data and session_data.get("storage_state"):
            context_options["storage_state"] = session_data["storage_state"]
        
        self.context = self.browser.new_context(**context_options)
        
        # Set cookies after context creation if available
        if session_data and session_data.get("cookies"):
            self.context.add_cookies(session_data["cookies"])
        
        # Set additional properties to avoid detection
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        return self.context
    
    @monitor_operation("browser_launch")
    def launch_browser(self) -> Browser:
        """Launch browser with optimized settings."""
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=self.get_optimized_browser_args()
        )
        
        logger.info("Browser launched with optimized settings")
        return self.browser
    
    def create_page(self, profile_name: str = "default", session_name: str = None) -> Page:
        """Create a page with optimized context and session management."""
        if not self.browser:
            self.launch_browser()
        
        context = self.create_context(profile_name, session_name)
        page = context.new_page()
        
        # Set additional page properties
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        return page
    
    def save_current_session(self, session_name: str):
        """Save the current browser session."""
        if self.context:
            try:
                cookies = self.context.cookies()
                storage_state = self.context.storage_state()
                self.save_session(session_name, cookies, storage_state)
            except Exception as e:
                logger.error(f"Failed to save session: {e}")
    
    def close(self):
        """Close browser and cleanup resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        # Log performance summary
        self.performance_monitor.log_performance_summary()
        
        logger.info("Browser manager closed")

# Global browser manager instance
_browser_manager = None

def get_browser_manager() -> BrowserManager:
    """Get the global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager

def cleanup_browser_manager():
    """Cleanup the global browser manager."""
    global _browser_manager
    if _browser_manager:
        _browser_manager.close()
        _browser_manager = None 