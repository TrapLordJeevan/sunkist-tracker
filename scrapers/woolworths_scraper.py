"""
Woolworths scraper for Sunkist Zero Sugar products.
Uses the working individual product API approach.
"""

import asyncio
import requests
from typing import List, Dict
from .base_scraper import BaseScraper


class WoolworthsScraper(BaseScraper):
    """Scraper for Woolworths online store using individual product API."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.woolworths.com.au"
        self.search_url = "https://www.woolworths.com.au/apis/ui/Search/products"
        self.product_url = "https://www.woolworths.com.au/apis/ui/Product"
        
        # Set up session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://www.woolworths.com.au',
            'Referer': 'https://www.woolworths.com.au/',
        })
    
    async def search_target_products(self) -> Dict:
        """Search for target products (Sunkist Zero Sugar, Fanta Zero Sugar, Pepsi Max Mango) on Woolworths."""
        try:
            # Get fresh session cookies
            await self._get_session_cookies()
            
            # Search terms for all target products
            search_terms = [
                "sunkist zero sugar",
                "fanta zero sugar", 
                "pepsi max mango"
            ]
            
            all_results = []
            
            # Search for each target product
            for search_term in search_terms:
                print(f"   🔍 Searching Woolworths for: {search_term}")
                
                # Search for products to get stock codes
                products = await self._search_products(search_term)
                
                if not products:
                    print(f"   ⚠️  No products found for: {search_term}")
                    continue
                
                # Get individual product details for each target product
                for product in products:
                    product_name = product.get('DisplayName', '').lower()
                    
                    # Check if this product matches our target products
                    if self.is_target_product(product_name):
                        stockcode = product.get('Stockcode')
                        if stockcode:
                            # Get individual product data (this has the prices!)
                            individual_data = await self._get_individual_product(stockcode)
                            
                            # Extract product info using both search and individual data
                            product_info = self._extract_product_info(product, individual_data)
                            
                            if product_info:
                                all_results.append(product_info)
                                print(f"   ✅ Found: {product_info['name']} - ${product_info['price']:.2f} (${product_info['price_per_litre']:.2f}/L)")
                            
                            # Small delay to avoid rate limiting
                            await asyncio.sleep(0.5)
                
                # Delay between different search terms
                await asyncio.sleep(1)
            
            results = all_results
            
            return {
                'retailer': 'woolworths',
                'products': results,
                'total_found': len(results)
            }
            
        except Exception as e:
            print(f"Error scraping Woolworths: {e}")
            return {
                'retailer': 'woolworths',
                'products': [],
                'total_found': 0,
                'error': str(e)
            }
    
    async def _get_session_cookies(self):
        """Get fresh session cookies."""
        try:
            response = self.session.get('https://www.woolworths.com.au/', timeout=10)
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            print(f"Error getting session: {e}")
            return False
    
    async def _search_products(self, search_term="sunkist zero sugar"):
        """Search for products to get stock codes."""
        url = "https://www.woolworths.com.au/apis/ui/Search/products"
        
        payload = {
            "Filters": [],
            "IsSpecial": False,
            "Location": f"/shop/search/products?searchTerm={search_term.replace(' ', '%20')}",
            "PageNumber": 1,
            "PageSize": 36,
            "SearchTerm": search_term,
            "SortType": "TraderRelevance",
            "IsHideUnavailableProducts": False
        }
        
        api_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.woolworths.com.au',
            'Referer': f'https://www.woolworths.com.au/shop/search/products?searchTerm={search_term.replace(" ", "%20")}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        try:
            response = self.session.post(url, json=payload, headers=api_headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('Products', [])
                
                # The products are nested - extract the actual product data
                actual_products = []
                for product in products:
                    if 'Products' in product:
                        # This is a bundle with nested products
                        actual_products.extend(product['Products'])
                    else:
                        # This is a direct product
                        actual_products.append(product)
                
                return actual_products
            else:
                print(f"API request failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    async def _get_individual_product(self, stockcode):
        """Get individual product details using the product API - this is where prices are!"""
        if not stockcode:
            return None
        
        url = f"https://www.woolworths.com.au/apis/ui/Product/{stockcode}"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error getting product {stockcode}: {e}")
            return None
    
    def _extract_product_info(self, product, individual_data=None):
        """Extract product information from both search and individual product data."""
        try:
            name = product.get('DisplayName', '')
            stockcode = product.get('Stockcode', '')
            
            # Use individual product data if available (this has the prices!)
            if individual_data:
                price = individual_data.get('Price', 0)
                instore_price = individual_data.get('InstorePrice', 0)
                cup_price = individual_data.get('CupPrice', 0)
                cup_string = individual_data.get('CupString', '')
                package_size = individual_data.get('PackageSize', '')
                is_in_stock = individual_data.get('IsInStock', True)
                is_on_special = individual_data.get('IsOnSpecial', False)
                was_price = individual_data.get('WasPrice', 0)
            else:
                # Fallback to search result data
                price = product.get('Price', 0)
                instore_price = product.get('InstorePrice', 0)
                cup_price = product.get('CupPrice', 0)
                cup_string = product.get('CupString', '')
                package_size = product.get('PackageSize', '')
                is_in_stock = product.get('IsInStock', True)
                is_on_special = product.get('IsOnSpecial', False)
                was_price = product.get('WasPrice', 0)
            
            # Calculate price per litre
            price_per_litre = 0.0
            if cup_price > 0:
                price_per_litre = cup_price
            elif price > 0 and package_size:
                price_per_litre = self._calculate_price_per_litre(price, package_size)
            
            return {
                'name': name,
                'price': price,
                'price_display': f"${price:.2f}" if price > 0 else "Price not available",
                'instore_price': instore_price,
                'price_per_litre': price_per_litre,
                'price_per_litre_display': f"${price_per_litre:.2f}/L" if price_per_litre > 0 else "N/A",
                'cup_string': cup_string,
                'size': package_size,
                'url': f"https://www.woolworths.com.au/shop/productdetails/{stockcode}",
                'retailer': 'Woolworths',
                'in_stock': is_in_stock,
                'is_on_special': is_on_special,
                'was_price': was_price,
                'stockcode': stockcode
            }
            
        except Exception as e:
            print(f"Error extracting product info: {e}")
            return None
    
    def _calculate_price_per_litre(self, price, size):
        """Calculate price per litre from size string."""
        if not size or price <= 0:
            return 0.0
        
        import re
        
        # Convert size to litres
        if 'L' in size:
            litres = float(re.search(r'(\d+(?:\.\d+)?)', size).group(1))
        elif 'mL' in size:
            ml_match = re.search(r'(\d+(?:\.\d+)?)', size)
            if ml_match:
                ml = float(ml_match.group(1))
                litres = ml / 1000
            else:
                return 0.0
        else:
            return 0.0
        
        if litres > 0:
            return price / litres
        
        return 0.0