#!/usr/bin/env python3
"""
Simple Coles fetcher using undetected-chromedriver.
"""

import logging
import random
import time
from typing import Dict, List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ColesSimpleFetcher:
    """
    Simple Coles fetcher using undetected-chromedriver.
    """

    DEFAULT_HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }

    def __init__(self):
        """Initialize the fetcher."""
        self.session = requests.Session()
        self.session.headers = self.DEFAULT_HEADERS.copy()
        self.driver = None

    def get(self, url: str) -> requests.Response:
        """
        Performs a GET request using undetected-chromedriver.
        """
        try:
            # Use undetected-chromedriver to get the page
            if not self.driver:
                self._init_driver()
            
            print(f"   🌐 Loading: {url}")
            
            # Add longer random delay to simulate human behavior
            import random
            delay = random.uniform(10, 20)  # 10-20 seconds
            print(f"   ⏳ Waiting {delay:.1f} seconds before loading page...")
            time.sleep(delay)
            
            self.driver.get(url)
            
            # Wait for page to load and handle Incapsula challenge
            time.sleep(8)
            
            # Check if we got the Incapsula challenge
            page_source_lower = self.driver.page_source.lower()
            if "pardon our interruption" in page_source_lower:
                print(f"   ⚠️  Incapsula challenge detected, waiting for it to resolve...")
                # Wait longer for the challenge to resolve
                time.sleep(15)
                
                # Check again
                page_source_lower = self.driver.page_source.lower()
                if "pardon our interruption" in page_source_lower:
                    print(f"   ❌ Incapsula challenge not resolved, refreshing driver...")
                    self._refresh_driver()
                    time.sleep(5)
                    self.driver.get(url)
                    time.sleep(10)
                else:
                    print(f"   ✅ Incapsula challenge resolved")
            else:
                print(f"   ✅ Page loaded successfully")
            
            # Get the page source
            html = self.driver.page_source
            
            # Create a mock response object
            class MockResponse:
                def __init__(self, html_content):
                    self.text = html_content
                    self.content = html_content.encode('utf-8')
                    self.status_code = 200
                    self.headers = {}
            
            return MockResponse(html)
            
        except Exception as e:
            logger.error("Error retrieving page with URL '%s': %s", url, e)
            raise

    def _init_driver(self):
        """Initialize Chrome driver with anti-detection measures."""
        try:
            print("   🔧 Initializing Chrome driver with anti-detection...")
            options = Options()
            
            # Anti-detection arguments
            options.add_argument("--log-level=3")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Additional anti-detection measures
            options.add_argument("--disable-automation")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-default-apps")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set a realistic user agent
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
            
            # Use webdriver-manager to auto-download the correct ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("   ✅ Anti-detection driver initialized")
            
        except Exception as e:
            logger.error("Error initializing driver: %s", e)
            raise

    def _refresh_driver(self):
        """Refresh the driver to avoid detection."""
        try:
            print("   🔄 Refreshing driver to avoid detection...")
            if self.driver:
                self.driver.quit()
            self.driver = None
            self._init_driver()
        except Exception as e:
            logger.error("Error refreshing driver: %s", e)

    def close(self):
        """Close the driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()