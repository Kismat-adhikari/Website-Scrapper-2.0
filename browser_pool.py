"""
Browser Pool - Phase 4 Implementation
Reuses browser instances for better performance on JS-heavy sites
"""

import asyncio
import logging
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BrowserPool:
    """Pool of reusable browser instances"""
    
    def __init__(self, pool_size: int = 3, browser_type: str = 'chromium'):
        """
        Initialize browser pool
        
        Args:
            pool_size: Number of browsers to keep in pool
            browser_type: 'chromium', 'firefox', or 'webkit'
        """
        self.pool_size = pool_size
        self.browser_type = browser_type
        self.browsers: List[Browser] = []
        self.available_browsers: List[Browser] = []
        self.playwright = None
        self.initialized = False
        self.last_used = {}
        self.max_idle_time = timedelta(minutes=5)
    
    async def initialize(self):
        """Initialize the browser pool"""
        if self.initialized:
            return
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browsers based on type
            if self.browser_type == 'chromium':
                browser_launcher = self.playwright.chromium
            elif self.browser_type == 'firefox':
                browser_launcher = self.playwright.firefox
            else:
                browser_launcher = self.playwright.webkit
            
            # Launch pool_size browsers
            for i in range(self.pool_size):
                browser = await browser_launcher.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                self.browsers.append(browser)
                self.available_browsers.append(browser)
                self.last_used[id(browser)] = datetime.now()
                logger.info(f"Launched browser {i+1}/{self.pool_size}")
            
            self.initialized = True
            logger.info(f"Browser pool initialized with {self.pool_size} browsers")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser pool: {e}")
            raise
    
    async def acquire(self) -> Optional[Browser]:
        """
        Acquire a browser from the pool
        
        Returns:
            Browser instance or None if pool is exhausted
        """
        if not self.initialized:
            await self.initialize()
        
        # Wait for available browser (with timeout)
        max_wait = 30  # seconds
        waited = 0
        
        while not self.available_browsers and waited < max_wait:
            await asyncio.sleep(0.5)
            waited += 0.5
        
        if not self.available_browsers:
            logger.warning("No browsers available in pool")
            return None
        
        browser = self.available_browsers.pop(0)
        self.last_used[id(browser)] = datetime.now()
        logger.debug(f"Acquired browser from pool ({len(self.available_browsers)} remaining)")
        
        return browser
    
    async def release(self, browser: Browser):
        """
        Release a browser back to the pool
        
        Args:
            browser: Browser instance to release
        """
        if browser in self.browsers and browser not in self.available_browsers:
            # Close all contexts to clean up
            try:
                contexts = browser.contexts
                for context in contexts:
                    await context.close()
            except Exception as e:
                logger.warning(f"Error closing contexts: {e}")
            
            self.available_browsers.append(browser)
            self.last_used[id(browser)] = datetime.now()
            logger.debug(f"Released browser to pool ({len(self.available_browsers)} available)")
    
    async def cleanup_idle_browsers(self):
        """Close and restart browsers that have been idle too long"""
        now = datetime.now()
        
        for browser in self.available_browsers[:]:
            browser_id = id(browser)
            if browser_id in self.last_used:
                idle_time = now - self.last_used[browser_id]
                
                if idle_time > self.max_idle_time:
                    logger.info(f"Restarting idle browser (idle for {idle_time.seconds}s)")
                    
                    # Remove from pool
                    self.available_browsers.remove(browser)
                    self.browsers.remove(browser)
                    
                    # Close old browser
                    try:
                        await browser.close()
                    except:
                        pass
                    
                    # Launch new browser
                    try:
                        if self.browser_type == 'chromium':
                            browser_launcher = self.playwright.chromium
                        elif self.browser_type == 'firefox':
                            browser_launcher = self.playwright.firefox
                        else:
                            browser_launcher = self.playwright.webkit
                        
                        new_browser = await browser_launcher.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-setuid-sandbox']
                        )
                        
                        self.browsers.append(new_browser)
                        self.available_browsers.append(new_browser)
                        self.last_used[id(new_browser)] = now
                        
                    except Exception as e:
                        logger.error(f"Failed to restart browser: {e}")
    
    async def close_all(self):
        """Close all browsers in the pool"""
        logger.info("Closing all browsers in pool")
        
        for browser in self.browsers:
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        self.browsers.clear()
        self.available_browsers.clear()
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
        
        self.initialized = False
        logger.info("Browser pool closed")
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            'total_browsers': len(self.browsers),
            'available_browsers': len(self.available_browsers),
            'in_use': len(self.browsers) - len(self.available_browsers),
            'initialized': self.initialized
        }


# Global browser pool instance
_browser_pool: Optional[BrowserPool] = None


async def get_browser_pool(pool_size: int = 3) -> BrowserPool:
    """Get or create the global browser pool"""
    global _browser_pool
    
    if _browser_pool is None:
        _browser_pool = BrowserPool(pool_size=pool_size)
        await _browser_pool.initialize()
    
    return _browser_pool


async def close_browser_pool():
    """Close the global browser pool"""
    global _browser_pool
    
    if _browser_pool:
        await _browser_pool.close_all()
        _browser_pool = None
