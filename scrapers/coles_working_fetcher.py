#!/usr/bin/env python3
"""
Working Coles fetcher based on the approach from abhinav-pandey29/coles-scraper.
Uses undetected-chromedriver and selenium-wire to bypass bot detection.
"""

import logging
import random
import time
from typing import Callable, Dict, List, Optional

import requests
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
from seleniumwire import webdriver

logger = logging.getLogger(__name__)


class ColesWorkingFetcher:
    """
    Class to manage requests to Coles website using the working approach.
    Based on abhinav-pandey29/coles-scraper.
    """

    DEFAULT_HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }
    DEFAULT_REFRESH_URLS = [
        "https://www.coles.com.au/browse/fruit-vegetables",
        "https://www.coles.com.au/browse/frozen",
        "https://www.coles.com.au/browse/dairy-eggs-fridge",
        "https://www.coles.com.au/browse/household",
        "https://www.coles.com.au/browse/drinks/soft-drinks",
    ]

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        headers: Optional[Dict] = None,
        refresh_urls: List[str] = None,
        sleep_func=time.sleep,
    ):
        """
        Initialize the fetcher with session management.
        """
        self.session = session or requests.Session()
        self.session.headers = (
            headers.copy() if headers else self.DEFAULT_HEADERS.copy()
        )
        self.refresh_urls = refresh_urls or self.DEFAULT_REFRESH_URLS
        self.refresh_url = random.choice(self.refresh_urls)
        self.sleep_func = sleep_func

        if not self.session.headers.get("cookie"):
            self.refresh_cookie()

    def get(self, url: str) -> requests.Response:
        """
        Performs a GET request. On error (network or bot detection), refreshes the cookie and retries.
        """
        try:
            response = self._get(url)
        except (requests.RequestException, ValueError) as e:
            logger.error("Error retrieving page with URL '%s': %s", url, e)
            self.refresh_cookie()
            response = self._get(url)

        return response

    def _get(self, url: str) -> requests.Response:
        """
        Internal GET request method that raises a ValueError if bot detection content is found.
        """
        response = self.session.get(url=url)
        response.raise_for_status()

        if ("Incapsula" in str(response.content)) or (
            "Pardon Our Interruption" in str(response.content)
        ):
            logger.warning("Request blocked by bot detection measures.")
            raise ValueError("Bot detected!")

        return response

    def refresh_cookie(self):
        """
        Refreshes current request session's cookie using undetected-chromedriver.

        This method opens a browser, and performs two consecutive visits to a predefined
        Coles webpage. 1. The first visit triggers the initial creation of the cookie.
        2. The second visit allows interception of a valid cookie from network requests.

        The intercepted cookie is then stored in the session's headers. This ensures
        that subsequent HTTP requests are properly authenticated.
        """
        logger.info("Refreshing cookie using refresh_url: %s", self.refresh_url)
        driver = self._init_seleniumwire_webdriver()
        driver.request_interceptor = self.intercept_cookie

        try:
            # First call to prompt cookie creation,
            # Second call to intercept cookie and update headers
            for _ in range(2):
                try:
                    driver.get(self.refresh_url)
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#coles-targeting-header-container")
                        )
                    )
                    self.sleep_func(5)
                except Exception as e:
                    logger.warning(f"Error while refreshing cookie: {e}")
                    break
        finally:
            driver.quit()

    def _init_seleniumwire_webdriver(self):
        """Initialize selenium-wire webdriver with undetected-chromedriver."""
        options = uc.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Use selenium-wire with undetected-chromedriver
        return webdriver.Chrome(options=options)

    def intercept_cookie(self, request):
        """Intercept cookie from network requests."""
        if request.url.startswith(self.refresh_url):
            cookie_value = request.headers.get("cookie")
            if cookie_value:
                logger.info("Intercepted cookie: %s", cookie_value)
                self.session.headers["cookie"] = cookie_value