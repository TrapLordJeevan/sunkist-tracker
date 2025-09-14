"""
Amazon scraper for Sunkist Zero Sugar products.
"""

import asyncio
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class AmazonScraper(BaseScraper):
    """Scraper for Amazon Australia."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.amazon.com.au"
        self.search_url = "https://www.amazon.com.au/s"
    
    async def search_target_products(self) -> Dict:
        """Search for target products (Sunkist Zero Sugar, Fanta Zero Sugar, Pepsi Max Mango) on Amazon."""
        try:
            self.setup_driver()
            
            all_products = []
            # Search terms to find our target products
            search_terms = [
                'sunkist zero sugar orange',
                'fanta zero sugar orange', 
                'pepsi max mango',
                'sunkist zero sugar',
                'fanta zero sugar',
                'pepsi max mango soda'
            ]
            
            for search_term in search_terms:
                print(f"   🔎 Searching Amazon for: {search_term}")
                
                # Search for products on Amazon
                search_url = f"{self.search_url}?k={search_term.replace(' ', '+')}"
                self.driver.get(search_url)
                
                # Wait for page to load
                await asyncio.sleep(5)
                
                # Handle potential captcha or login prompts
                try:
                    # Check if we need to handle any popups
                    if "captcha" in self.driver.page_source.lower():
                        print(f"   ⚠️ Amazon captcha detected for: {search_term}")
                        continue
                except:
                    pass
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                products = self._parse_products(soup)
                
                # Filter for target products
                target_products_found = 0
                for product in products:
                    if self.is_target_product(product['name']):
                        all_products.append(product)
                        target_products_found += 1
                        print(f"   ✅ Found: {product['name']} - ${product['price']:.2f} (${product['price_per_litre']:.2f}/L)")
                    # Don't print non-target products to reduce noise
                
                if target_products_found == 0:
                    print(f"   ⚠️  No target products found for '{search_term}'")
                
                # Longer delay between searches to avoid detection
                await asyncio.sleep(10)
            
            return {
                'retailer': 'amazon',
                'products': all_products,
                'total_found': len(all_products)
            }
            
        except Exception as e:
            print(f"Error scraping Amazon: {e}")
            return {
                'retailer': 'amazon',
                'products': [],
                'error': str(e)
            }
        finally:
            self.close_driver()
    
    def _parse_products(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse product information from Amazon search results."""
        products = []
        
        # Amazon uses various selectors for product containers
        product_selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '.s-search-result'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                break
        
        for element in product_elements[:15]:  # Check more results to find target products
            try:
                product = self._extract_product_info(element)
                if product and product['name']:  # Just check if we got a valid product
                    products.append(product)
            except Exception as e:
                print(f"Error parsing Amazon product: {e}")
                continue
        
        return products
    
    def _extract_brand_name(self, element) -> str:
        """Extract brand name from various parts of the product element."""
        # Look for brand in different selectors
        brand_selectors = [
            '.a-size-base-plus',  # Brand often in this class
            '.a-size-base',       # Alternative brand location
            '.a-color-base',      # Brand color
            '[data-cy="title-recipe-brand"]',  # Brand-specific selector
            '.s-color-base',      # Another brand location
        ]
        
        for selector in brand_selectors:
            brand_elem = element.select_one(selector)
            if brand_elem:
                brand_text = brand_elem.get_text(strip=True)
                # Check if this looks like a brand name
                if brand_text and len(brand_text) < 50:  # Brands are usually short
                    brand_lower = brand_text.lower()
                    # Check if it's one of our target brands
                    if any(target_brand in brand_lower for target_brand in 
                          ['sunkist', 'fanta', 'pepsi', 'coca-cola', 'coke']):
                        return brand_text
        
        # Also check the product name itself for brand names
        name_elem = element.select_one('h2 a span, h2 a, .a-link-normal span')
        if name_elem:
            name_text = name_elem.get_text(strip=True).lower()
            if 'sunkist' in name_text:
                return 'Sunkist'
            elif 'fanta' in name_text:
                return 'Fanta'
            elif 'pepsi' in name_text:
                return 'Pepsi'
        
        return ""
    
    def _extract_product_info(self, element) -> Dict:
        """Extract product information from a product element."""
        product = {
            'name': '',
            'price': 0.0,
            'size': '',
            'price_per_litre': 0.0,
            'in_stock': True,
            'url': '',
            'image_url': '',
            'delivery_info': ''
        }
        
        # Extract product name with filtering
        name_selectors = [
            'h2 a span', 'h2 a', '.s-size-mini a span',
            '[data-cy="title-recipe-title"]', '.s-color-base', '.a-link-normal span'
        ]
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                # Filter out irrelevant results
                if (name and len(name) > 10 and 
                    not any(irrelevant in name.lower() for irrelevant in 
                           ['let us know', 'sponsored', 'advertisement', 'click here', 'see more'])):
                    product['name'] = name
                    break
        
        # Try to extract brand name from other parts of the product listing
        brand = self._extract_brand_name(element)
        if brand and brand not in product['name'].lower():
            # Add brand to the product name if it's not already there
            product['name'] = f"{brand} {product['name']}"
        
        # Extract product URL
        link_elem = element.select_one('h2 a, .s-size-mini a')
        if link_elem:
            href = link_elem.get('href', '')
            if href:
                product['url'] = self.base_url + href if href.startswith('/') else href
        
        # Extract price
        price_selectors = [
            '.a-price-whole', '.a-price .a-offscreen',
            '.a-price-range', '.a-price-symbol + .a-price-whole'
        ]
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                product['price'] = self.extract_price(price_text)
                break
        
        # If no price found, try alternative selectors
        if product['price'] == 0.0:
            price_alt_selectors = [
                '.a-price-range .a-price-whole',
                '.a-price .a-price-whole'
            ]
            for selector in price_alt_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    product['price'] = self.extract_price(price_text)
                    break
        
        # Extract size from name or separate size element
        size_selectors = [
            '.a-size-base', '.a-text-bold'
        ]
        for selector in size_selectors:
            size_elem = element.select_one(selector)
            if size_elem:
                size_text = size_elem.get_text(strip=True)
                if any(unit in size_text.lower() for unit in ['ml', 'l', 'litre', 'liter']):
                    product['size'] = self.extract_size(size_text)
                    break
        
        # If no separate size element, try to extract from name
        if not product['size'] and product['name']:
            product['size'] = self.extract_size(product['name'])
        
        # Check stock status
        stock_indicators = element.select('.a-color-price, .a-color-base')
        out_of_stock_indicators = element.select('.a-color-secondary, .a-text-strike')
        
        if out_of_stock_indicators:
            product['in_stock'] = False
        
        # Check for delivery information
        delivery_elem = element.select_one('.a-color-base, .a-size-small')
        if delivery_elem:
            delivery_text = delivery_elem.get_text(strip=True)
            if any(keyword in delivery_text.lower() for keyword in ['prime', 'delivery', 'shipping']):
                product['delivery_info'] = delivery_text
        
        # Calculate price per litre
        if product['price'] > 0 and product['size']:
            product['price_per_litre'] = self.calculate_price_per_litre(product['price'], product['size'])
        
        # Extract image URL
        img_elem = element.select_one('img')
        if img_elem:
            product['image_url'] = img_elem.get('src', '') or img_elem.get('data-src', '')
        
        return product
    
    def is_sunkist_zero_sugar(self, product_name: str) -> bool:
        """Enhanced check for Sunkist Zero Sugar products on Amazon."""
        if not product_name:
            return False
        
        name_lower = product_name.lower()
        
        # Must contain sunkist
        if 'sunkist' not in name_lower:
            return False
        
        # Must be zero sugar variant
        zero_sugar_indicators = [
            'zero sugar', 'zero-sugar', 'zero sugar', 'sugar free',
            'diet', 'zero', 'no sugar'
        ]
        
        has_zero_sugar = any(indicator in name_lower for indicator in zero_sugar_indicators)
        
        # Exclude regular sugar versions
        regular_sugar_indicators = [
            'original', 'regular', 'classic'
        ]
        
        has_regular_sugar = any(indicator in name_lower for indicator in regular_sugar_indicators)
        
        return has_zero_sugar and not has_regular_sugar