"""
Retry utilities with exponential backoff and randomized headers.
"""

import time
import random
import logging
from typing import Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_random_headers() -> Dict[str, str]:
    """Get randomized headers to avoid detection."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """Decorator for retrying functions with exponential backoff."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to avoid thundering herd
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """Add random delay between requests."""
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"Random delay: {delay:.2f} seconds")
    time.sleep(delay)

class RequestSession:
    """Enhanced requests session with retry logic and randomized headers."""
    
    def __init__(self, max_retries: int = 3):
        import requests
        self.session = requests.Session()
        self.max_retries = max_retries
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET request with retry logic."""
        return self._request_with_retry('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST request with retry logic."""
        return self._request_with_retry('POST', url, **kwargs)
    
    @retry_with_backoff(max_retries=3)
    def _request_with_retry(self, method: str, url: str, **kwargs):
        """Make request with retry logic."""
        # Add random headers
        headers = kwargs.get('headers', {})
        headers.update(get_random_headers())
        kwargs['headers'] = headers
        
        # Add timeout if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        logger.debug(f"Making {method} request to {url}")
        
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        
        # Add random delay after successful request
        random_delay()
        
        return response