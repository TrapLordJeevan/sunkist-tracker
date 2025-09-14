"""
Coles scraper for target products using working approach.
"""

import asyncio
import json
import re
import time
import random
from typing import List, Dict
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from .coles_simple_fetcher import ColesSimpleFetcher


class ColesScraper(BaseScraper):
    """Scraper for Coles online store."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.coles.com.au"
        self.search_url = "https://www.coles.com.au/search"
        
        # Initialize the simple fetcher
        print("   🔧 Initializing Coles simple fetcher...")
        self.fetcher = ColesSimpleFetcher()
        print("   ✅ Coles simple fetcher initialized")
        
        # Search terms for our target products
        self.search_terms = [
            'sunkist zero sugar',
            'fanta zero sugar', 
            'pepsi max mango'
        ]
    
    async def search_target_products(self) -> Dict:
        """Search for target products (Sunkist Zero Sugar, Fanta Zero Sugar, Pepsi Max Mango) on Coles."""
        try:
            print("🔍 Searching for target products on Coles using working approach...")
            
            all_products = []
            
            # Search for each product type
            for search_term in self.search_terms:
                print(f"\n🔎 Searching for: {search_term}")
                
                # Try multiple approaches for each search term
                products = await self._search_with_multiple_approaches(search_term)
                
                for product in products:
                    if self.is_target_product(product['name']):
                        all_products.append(product)
                        print(f"   ✅ Found: {product['name']} - ${product['price']:.2f} (${product['price_per_litre']:.2f}/L)")
                    else:
                        print(f"   ⚠️  Not target product: {product['name']}")
                
                # Add much longer delay between searches to avoid detection
                delay = random.uniform(30, 60)  # 30-60 seconds between searches
                print(f"   ⏳ Waiting {delay:.1f} seconds to avoid detection...")
                await asyncio.sleep(delay)
            
            if all_products:
                print(f"\n✅ Successfully found {len(all_products)} target products from Coles")
                return {
                    'retailer': 'coles',
                    'products': all_products,
                    'total_found': len(all_products)
                }
            else:
                print("\n⚠️ Could not find any target products from Coles")
                print("💡 This might be due to bot protection or products not being available")
                print("💡 Manual alternatives:")
                print("   - Visit coles.com.au directly in your browser")
                print("   - Search for 'sunkist zero sugar', 'fanta zero sugar', or 'pepsi max mango'")
                print("   - Check prices manually")
                
                return {
                    'retailer': 'coles',
                    'products': [],
                    'total_found': 0,
                    'error': 'Could not find product data - may be due to bot protection or products not available',
                    'manual_url': 'https://www.coles.com.au/search?q=sunkist%20zero%20sugar%20OR%20fanta%20zero%20sugar%20OR%20pepsi%20max%20mango'
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
        
        # Try direct search first for specific products
        print(f"   🔍 Trying direct search for: {search_term}")
        direct_products = await self._search_direct(search_term)
        products.extend(direct_products)
        
        # If no products found, try category browsing as fallback
        if not products:
            print(f"   📂 No direct results, trying category browsing...")
            category_products = await self._search_category_with_pagination()
            # Filter category products to only include our target products
            filtered_products = []
            for product in category_products:
                if self.is_target_product(product.get('name', '')):
                    filtered_products.append(product)
            products.extend(filtered_products)
        
        return products
    
    async def _search_direct(self, search_term: str) -> List[Dict]:
        """Try direct search approach using the working fetcher."""
        try:
            print(f"   🔍 Trying direct search for: {search_term}")
            
            # Build search URL
            search_url = f"{self.search_url}?q={search_term.replace(' ', '%20')}"
            
            # Add random delay
            await asyncio.sleep(random.uniform(1, 2))
            
            # Use the working fetcher
            response = self.fetcher.get(search_url)
            
            if response.status_code == 200:
                print(f"   ✅ Direct search successful")
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._parse_products(soup)
            else:
                print(f"   ❌ Direct search failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Direct search error: {e}")
        
        return []
    
    async def _search_category_with_pagination(self) -> List[Dict]:
        """Try category browsing with pagination to get all products."""
        try:
            print(f"   📂 Trying category browsing with pagination...")
            
            all_products = []
            page = 1
            max_pages = 1  # Just get the first page to avoid detection
            
            while page <= max_pages:
                print(f"   📄 Loading page {page}...")
                
                # Build category URL with page parameter
                if page == 1:
                    category_url = f"{self.base_url}/browse/drinks/soft-drinks"
                else:
                    category_url = f"{self.base_url}/browse/drinks/soft-drinks?page={page}"
                
                # Add random delay
                await asyncio.sleep(random.uniform(2, 4))
                
                # Use the working fetcher
                response = self.fetcher.get(category_url)
                
                if response.status_code == 200:
                    print(f"   ✅ Page {page} loaded successfully")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_products = self._parse_products(soup)
                    
                    if page_products:
                        all_products.extend(page_products)
                        print(f"   📦 Found {len(page_products)} products on page {page}")
                        page += 1
                    else:
                        print(f"   ⚠️  No products found on page {page}, stopping pagination")
                        break
                else:
                    print(f"   ❌ Page {page} failed with status {response.status_code}")
                    break
            
            print(f"   📊 Total products found across {page-1} pages: {len(all_products)}")
            return all_products
                
        except Exception as e:
            print(f"   ❌ Category browsing error: {e}")
            return []
    
    async def _search_direct_fresh(self, search_term: str) -> List[Dict]:
        """Try direct search with a fresh driver instance."""
        try:
            print(f"   🔍 Trying direct search with fresh driver for: {search_term}")
            
            # Create a fresh fetcher instance to avoid detection
            from .coles_simple_fetcher import ColesSimpleFetcher
            fresh_fetcher = ColesSimpleFetcher()
            
            try:
                # Build search URL
                search_url = f"{self.search_url}?q={search_term.replace(' ', '%20')}"
                
                # Add random delay
                await asyncio.sleep(random.uniform(3, 6))
                
                # Use the fresh fetcher
                response = fresh_fetcher.get(search_url)
                
                if response.status_code == 200:
                    print(f"   ✅ Fresh direct search successful")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    return self._parse_products(soup)
                else:
                    print(f"   ❌ Fresh direct search failed with status {response.status_code}")
                    return []
                    
            finally:
                # Always close the fresh fetcher
                fresh_fetcher.close()
                
        except Exception as e:
            print(f"   ❌ Fresh direct search error: {e}")
            return []
    
    async def _search_category(self) -> List[Dict]:
        """Try category browsing approach using the working fetcher."""
        try:
            print(f"   📂 Trying category browsing...")
            
            # Try the soft drinks category
            category_url = f"{self.base_url}/browse/drinks/soft-drinks"
            
            # Add random delay
            await asyncio.sleep(random.uniform(1, 2))
            
            # Use the working fetcher
            response = self.fetcher.get(category_url)
            
            if response.status_code == 200:
                print(f"   ✅ Category browsing successful")
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._parse_products(soup)
            else:
                print(f"   ❌ Category browsing failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Category browsing error: {e}")
        
        return []
    
    async def _search_products(self, search_term: str) -> List[Dict]:
        """Search for products on Coles using the search term."""
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept-language': 'en-AU,en;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'connection': 'keep-alive',
                'upgrade-insecure-requests': '1',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'cache-control': 'max-age=0'
            }
            
            # Build search URL
            search_url = f"{self.search_url}?q={search_term.replace(' ', '%20')}"
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            if "incapsula" in response.text.lower():
                print(f"   ❌ Bot protection detected for search: {search_term}")
                return []
            
            # Parse search results
            soup = BeautifulSoup(response.content, 'html.parser')
            products = self._parse_products(soup)
            
            return products
            
        except Exception as e:
            print(f"Error searching for {search_term}: {e}")
            return []
    
    async def _extract_product_from_url(self, url: str) -> Dict:
        """Extract product data from a Coles product URL using __NEXT_DATA__ and JSON-LD."""
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept-language': 'en-AU,en;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'connection': 'keep-alive',
                'upgrade-insecure-requests': '1',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'cache-control': 'max-age=0'
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            if "incapsula" in response.text.lower():
                print(f"   ❌ Bot protection detected for {url}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # First, try to extract from __NEXT_DATA__ (more reliable for Coles)
            next_data_scripts = soup.find_all('script', id='__NEXT_DATA__')
            
            for script in next_data_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Navigate to product data
                    product = data.get('props', {}).get('pageProps', {}).get('product', {})
                    if product:
                        name = product.get('name', '')
                        brand = product.get('brand', '')
                        size = product.get('size', '')
                        price = float(product.get('pricing', {}).get('now', 0))
                        price_per_litre = float(product.get('pricing', {}).get('unit', {}).get('price', 0))
                        availability = product.get('availability', True)
                        
                        return {
                            'name': name,
                            'price': price,
                            'size': size,
                            'price_per_litre': price_per_litre,
                            'in_stock': availability,
                            'url': url,
                            'image_url': '',
                            'brand': brand,
                            'description': ''
                        }
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error parsing __NEXT_DATA__: {e}")
                    continue
            
            # Fallback to JSON-LD if __NEXT_DATA__ not found
            jsonld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string)
                    
                    if data.get('@type') == 'Product':
                        # Extract product information
                        name = data.get('name', '')
                        brand = data.get('brand', {}).get('name', '')
                        description = data.get('description', '')
                        
                        # Extract pricing
                        price = 0.0
                        currency = 'AUD'
                        availability = 'InStock'
                        
                        offers = data.get('offers', [])
                        if offers:
                            offer = offers[0] if isinstance(offers, list) else offers
                            price = float(offer.get('price', 0))
                            currency = offer.get('priceCurrency', 'AUD')
                            availability = offer.get('availability', 'InStock')
                        
                        # Extract size from name or additional properties
                        size = self.extract_size(name)
                        
                        # Look for additional properties for more details
                        additional_property = data.get('additionalProperty', [])
                        for prop in additional_property:
                            if prop.get('name') == 'Size' and prop.get('value'):
                                size = prop['value']
                                break
                        
                        # Calculate price per litre
                        price_per_litre = 0.0
                        if price > 0 and size:
                            price_per_litre = self.calculate_price_per_litre(price, size)
                        
                        return {
                            'name': name,
                            'price': price,
                            'size': size,
                            'price_per_litre': price_per_litre,
                            'in_stock': availability == 'https://schema.org/InStock',
                            'url': url,
                            'image_url': '',
                            'brand': brand,
                            'description': description
                        }
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error parsing JSON-LD: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error extracting product from {url}: {e}")
            return None
    
    def _parse_products(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse product information from Coles search results."""
        products = []
        
        # Look for product containers - Coles uses various selectors
        product_selectors = [
            '[data-testid="product-tile"]',
            'div[data-testid="product-tile"]',
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
                break
        
        for element in product_elements[:10]:  # Limit to first 10 results
            try:
                product = self._extract_product_info(element)
                if product and product['name']:
                    products.append(product)
                    print(f"   📦 Parsed: {product['name']} - ${product['price']:.2f}")
            except Exception as e:
                print(f"Error parsing Coles product: {e}")
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
            '[data-testid="product-name"]', 'a[data-testid="product-name"]'
        ]
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                product['name'] = name_elem.get_text(strip=True)
                product['url'] = self.base_url + name_elem.get('href', '') if name_elem.get('href') else ''
                break
        
        # Extract price
        price_selectors = [
            '.price', '.product-price', '[data-testid="price"]',
            '.price-value', '.current-price'
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