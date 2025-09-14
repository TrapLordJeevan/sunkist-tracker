#!/usr/bin/env python3
"""
Working Coles scraper based on the approach from abhinav-pandey29/coles-scraper.
Uses session management and cookie handling to bypass bot detection.
"""

import asyncio
import requests
import time
import random
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class ColesWorkingScraper(BaseScraper):
    """Working Coles scraper using session management and cookie handling."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.coles.com.au"
        self.session = requests.Session()
        
        # Set up realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Initialize session with cookies
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting the main page to get cookies."""
        try:
            print("   🍪 Initializing session with cookies...")
            response = self.session.get(self.base_url, timeout=15)
            
            if response.status_code == 200:
                print("   ✅ Session initialized successfully")
                # Add a small delay to simulate human behavior
                time.sleep(random.uniform(1, 3))
            else:
                print(f"   ⚠️  Session initialization returned status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error initializing session: {e}")
    
    async def search_target_products(self) -> Dict:
        """Search for target products using the working approach."""
        try:
            print("🔍 Searching for target products on Coles using working approach...")
            
            all_products = []
            search_terms = ['sunkist zero sugar', 'fanta zero sugar', 'pepsi max mango']
            
            for search_term in search_terms:
                print(f"\n🔎 Searching for: {search_term}")
                
                # Try multiple approaches for each search term
                products = await self._search_with_multiple_approaches(search_term)
                
                for product in products:
                    if self.is_target_product(product['name']):
                        all_products.append(product)
                        print(f"   ✅ Found: {product['name']} - ${product['price']:.2f} (${product['price_per_litre']:.2f}/L)")
                    else:
                        print(f"   ⚠️  Not target product: {product['name']}")
                
                # Add delay between searches
                await asyncio.sleep(random.uniform(2, 4))
            
            if all_products:
                print(f"\n✅ Successfully found {len(all_products)} target products from Coles")
                return {
                    'retailer': 'coles',
                    'products': all_products,
                    'total_found': len(all_products)
                }
            else:
                print("\n⚠️ Could not find any target products from Coles")
                return {
                    'retailer': 'coles',
                    'products': [],
                    'total_found': 0,
                    'error': 'No target products found - may be due to bot protection or products not available'
                }
            
        except Exception as e:
            print(f"Error scraping Coles: {e}")
            return {
                'retailer': 'coles',
                'products': [],
                'error': str(e)
            }
    
    async def _search_with_multiple_approaches(self, search_term: str) -> List[Dict]:
        """Try multiple approaches to search for products."""
        products = []
        
        # Approach 1: Direct search
        search_products = await self._search_direct(search_term)
        products.extend(search_products)
        
        # Approach 2: Category browsing
        category_products = await self._search_category()
        products.extend(category_products)
        
        # Remove duplicates
        seen_names = set()
        unique_products = []
        for product in products:
            if product['name'] not in seen_names:
                seen_names.add(product['name'])
                unique_products.append(product)
        
        return unique_products
    
    async def _search_direct(self, search_term: str) -> List[Dict]:
        """Try direct search approach."""
        try:
            print(f"   🔍 Trying direct search for: {search_term}")
            
            # Build search URL
            search_url = f"{self.base_url}/search?q={search_term.replace(' ', '%20')}"
            
            # Add random delay
            await asyncio.sleep(random.uniform(1, 2))
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                if "incapsula" not in response.text.lower():
                    print(f"   ✅ Direct search successful")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    return self._parse_products(soup)
                else:
                    print(f"   ❌ Direct search blocked by Incapsula")
            else:
                print(f"   ❌ Direct search failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Direct search error: {e}")
        
        return []
    
    async def _search_category(self) -> List[Dict]:
        """Try category browsing approach."""
        try:
            print(f"   📂 Trying category browsing...")
            
            # Try the soft drinks category
            category_url = f"{self.base_url}/browse/drinks/soft-drinks"
            
            # Add random delay
            await asyncio.sleep(random.uniform(1, 2))
            
            response = self.session.get(category_url, timeout=15)
            
            if response.status_code == 200:
                if "incapsula" not in response.text.lower():
                    print(f"   ✅ Category browsing successful")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    return self._parse_products(soup)
                else:
                    print(f"   ❌ Category browsing blocked by Incapsula")
            else:
                print(f"   ❌ Category browsing failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Category browsing error: {e}")
        
        return []
    
    def _parse_products(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse products from HTML."""
        products = []
        
        # Look for product containers - try multiple selectors
        product_selectors = [
            '[data-testid="product-tile"]',
            '.product-tile',
            '.product-item',
            '[data-testid="product"]',
            '.product-card',
            '.product'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                print(f"   📦 Found {len(elements)} products with selector: {selector}")
                break
        
        if not product_elements:
            print(f"   ⚠️  No product containers found")
            return products
        
        for element in product_elements[:20]:  # Limit to first 20 results
            try:
                product = self._extract_product_info(element)
                if product and product['name']:
                    products.append(product)
            except Exception as e:
                print(f"   ❌ Error parsing product: {e}")
                continue
        
        return products
    
    def _extract_product_info(self, element) -> Dict:
        """Extract product information from a product element."""
        product = {
            'name': '',
            'price': 0.0,
            'size': '',
            'price_per_litre': 0.0,
            'in_stock': True,
            'url': '',
            'image_url': ''
        }
        
        # Extract product name
        name_selectors = [
            'h3 a', 'h2 a', '.product-name a', 
            '[data-testid="product-name"]', 'a[data-testid="product-name"]',
            '.product-title', '.product-name', 'h3', 'h2'
        ]
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                product['name'] = name_elem.get_text(strip=True)
                # Get URL if it's a link
                if name_elem.name == 'a' and name_elem.get('href'):
                    href = name_elem.get('href')
                    if href.startswith('/'):
                        product['url'] = self.base_url + href
                    else:
                        product['url'] = href
                break
        
        # Extract price
        price_selectors = [
            '.price', '.product-price', '[data-testid="price"]',
            '.price-value', '.current-price', '.price-now'
        ]
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                product['price'] = self.extract_price(price_text)
                break
        
        # Extract size from name or separate size element
        size_selectors = [
            '.product-size', '.size', '[data-testid="size"]'
        ]
        for selector in size_selectors:
            size_elem = element.select_one(selector)
            if size_elem:
                product['size'] = self.extract_size(size_elem.get_text(strip=True))
                break
        
        # If no separate size element, try to extract from name
        if not product['size'] and product['name']:
            product['size'] = self.extract_size(product['name'])
        
        # Check stock status
        stock_indicators = element.select('.out-of-stock, .unavailable, [data-testid="out-of-stock"]')
        if stock_indicators:
            product['in_stock'] = False
        
        # Calculate price per litre
        if product['price'] > 0 and product['size']:
            product['price_per_litre'] = self.calculate_price_per_litre(product['price'], product['size'])
        
        # Extract image URL
        img_elem = element.select_one('img')
        if img_elem:
            product['image_url'] = img_elem.get('src', '') or img_elem.get('data-src', '')
        
        return product