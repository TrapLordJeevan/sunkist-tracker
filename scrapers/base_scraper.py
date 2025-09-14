"""
Base scraper class with common functionality for all retailers.
"""

import asyncio
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from product_schema import ProductSchema

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all retailer scrapers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
    
    def setup_driver(self):
        """Set up Chrome WebDriver with anti-detection measures."""
        if self.driver is None:
            chrome_options = Options()
            # Remove headless mode for better anti-detection
            # chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Anti-detection measures
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-automation')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set realistic user agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def extract_price(self, price_text: str) -> float:
        """Extract numeric price from text."""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
        return 0.0
    
    def extract_size(self, size_text: str) -> str:
        """Extract size information from text, preserving multipack information."""
        if not size_text:
            return "Unknown"
        
        # For multipacks, we want to preserve the full size information
        # Look for multipack patterns first
        multipack_patterns = [
            r'(\d+\s*x\s*\d+(?:\.\d+)?\s*(?:ml|l))',  # "12 x 1.25L" or "20 x 375 mL"
            r'(\d+(?:\.\d+)?\s*(?:ml|l).*?pack\s*of\s*\d+\))',  # "375 ml (Pack of 24)"
        ]
        
        for pattern in multipack_patterns:
            match = re.search(pattern, size_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Look for single size patterns
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*L',  # Litres
            r'(\d+(?:\.\d+)?)\s*ml',  # Millilitres
            r'(\d+(?:\.\d+)?)\s*kg',  # Kilograms
            r'(\d+(?:\.\d+)?)\s*g',   # Grams
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, size_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return size_text.strip()
    
    def convert_to_litres(self, size_text: str) -> float:
        """Convert size to litres for price comparison, handling multipacks."""
        if not size_text:
            return 0.0
        
        size_lower = size_text.lower()
        
        # Handle multipacks like "375 ml (Pack of 24)" or "12 x 1.25L"
        # Look for patterns like "X x Yml" or "Yml (Pack of X)"
        
        # Pattern 1: "12 x 1.25L" or "20 x 375 mL"
        pack_match = re.search(r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l)', size_lower)
        if pack_match:
            count = float(pack_match.group(1))
            volume = float(pack_match.group(2))
            unit = pack_match.group(3)
            
            if unit == 'ml':
                total_ml = count * volume
                return total_ml / 1000  # Convert to litres
            else:  # 'l'
                return count * volume
        
        # Pattern 2: "375 ml (Pack of 24)" or "1.25L (Pack of 12)"
        pack_of_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|l).*?pack\s*of\s*(\d+)', size_lower)
        if pack_of_match:
            volume = float(pack_of_match.group(1))
            unit = pack_of_match.group(2)
            count = float(pack_of_match.group(3))
            
            if unit == 'ml':
                total_ml = count * volume
                return total_ml / 1000  # Convert to litres
            else:  # 'l'
                return count * volume
        
        # Pattern 3: Single item like "375ml" or "1.25L"
        single_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|l)', size_lower)
        if single_match:
            volume = float(single_match.group(1))
            unit = single_match.group(2)
            
            if unit == 'ml':
                return volume / 1000  # Convert to litres
            else:  # 'l'
                return volume
        
        # Fallback: try to extract any number and assume ml
        number_match = re.search(r'(\d+(?:\.\d+)?)', size_text)
        if number_match:
            return float(number_match.group(1)) / 1000
        
        return 0.0
    
    def calculate_price_per_litre(self, price: float, size_text: str) -> float:
        """Calculate price per litre."""
        litres = self.convert_to_litres(size_text)
        if litres > 0:
            return price / litres
        return 0.0
    
    def is_target_product(self, product_name: str) -> bool:
        """Check if product is one of our target products (Sunkist Zero Sugar, Fanta Zero Sugar, or Pepsi Max Mango)."""
        if not product_name:
            return False
            
        name_lower = product_name.lower()
        
        # Exclude mixes, concentrates, syrups, and drink makers
        exclude_terms = [
            'mix', 'concentrate', 'syrup', 'drink maker', 'soda maker',
            'powder', 'crystal', 'tablet', 'capsule', 'drops',
            'flavoring', 'flavouring', 'essence', 'extract'
        ]
        
        if any(term in name_lower for term in exclude_terms):
            return False
        
        # Check for Sunkist Zero Sugar (explicit brand name)
        if 'sunkist' in name_lower:
            zero_sugar_indicators = [
                'zero sugar', 'zero-sugar', 'zero sugar', 'sugar free',
                'diet', 'zero', 'no sugar'
            ]
            has_zero_sugar = any(indicator in name_lower for indicator in zero_sugar_indicators)
            if has_zero_sugar:
                return True
        
        # Check for Fanta Zero Sugar (explicit brand name)
        if 'fanta' in name_lower:
            zero_sugar_indicators = [
                'zero sugar', 'zero-sugar', 'zero sugar', 'sugar free',
                'diet', 'zero', 'no sugar'
            ]
            has_zero_sugar = any(indicator in name_lower for indicator in zero_sugar_indicators)
            if has_zero_sugar:
                return True
        
        # Check for Pepsi Max Mango (explicit brand name)
        if 'pepsi max' in name_lower and 'mango' in name_lower:
            return True
        
        # For Amazon, also accept products that match our search terms even without explicit brand names
        # This is more flexible for Amazon where brand names might not be prominent
        zero_sugar_indicators = ['zero sugar', 'zero-sugar', 'sugar free', 'diet', 'zero', 'no sugar']
        has_zero_sugar = any(indicator in name_lower for indicator in zero_sugar_indicators)
        
        if has_zero_sugar:
            # Check for orange flavor (likely Sunkist or Fanta)
            if 'orange' in name_lower:
                return True
            
            # Check for mango flavor (likely Pepsi Max Mango)
            if 'mango' in name_lower:
                return True
        
        # If we get here, it's not one of our target products
        return False
    
    def _has_size_info(self, product_name: str) -> bool:
        """Check if product name contains size information (ml, L, etc.)."""
        size_patterns = [
            r'\d+\s*ml', r'\d+\s*l\b', r'\d+\s*litre', r'\d+\s*liter',
            r'\d+\s*oz', r'\d+\s*fl\s*oz'
        ]
        
        for pattern in size_patterns:
            if re.search(pattern, product_name.lower()):
                return True
        return False
    
    def is_can_preferred(self, product: dict) -> bool:
        """Check if product is a can (preferred over bottles)."""
        name_lower = product.get('name', '').lower()
        size_lower = product.get('size', '').lower()
        
        can_indicators = ['can', 'tin', '355ml', '375ml', '330ml']
        bottle_indicators = ['bottle', '2l', '1.25l', '1l', '600ml']
        
        has_can = any(indicator in name_lower or indicator in size_lower for indicator in can_indicators)
        has_bottle = any(indicator in name_lower or indicator in size_lower for indicator in bottle_indicators)
        
        return has_can and not has_bottle
    
    def meets_price_preference(self, product: dict, max_price_per_litre: float = 2.50) -> bool:
        """Check if product meets price preference (under $2.50/L for cans)."""
        price_per_litre = product.get('price_per_litre', 0)
        is_can = self.is_can_preferred(product)
        
        # For cans, allow up to $2.50/L
        # For bottles, use standard filtering
        if is_can:
            return price_per_litre <= max_price_per_litre
        else:
            # For bottles, be more strict (e.g., $2.00/L)
            return price_per_litre <= 2.00
    
    @abstractmethod
    async def search_target_products(self) -> Dict:
        """Search for target products (Sunkist Zero Sugar, Fanta Zero Sugar, Pepsi Max Mango)."""
        pass
    
    def validate_and_normalize_products(self, raw_products: List[Dict], store: str) -> List[Dict]:
        """Validate and normalize a list of raw products to standard schema."""
        validated_products = []
        
        for raw_product in raw_products:
            try:
                normalized = ProductSchema.normalize_product(raw_product, store)
                if normalized:
                    validated_products.append(normalized)
                else:
                    logger.warning(f"Failed to normalize product: {raw_product.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error processing product: {e}")
                continue
        
        logger.info(f"Validated {len(validated_products)}/{len(raw_products)} products for {store}")
        return validated_products
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close_driver()