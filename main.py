#!/usr/bin/env python3
"""
Sunkist Zero Sugar Price Tracker MVP
Finds the cheapest way to purchase Sunkist Zero Sugar by checking:
- Coles
- Woolworths  
- Amazon

Compares prices per litre and checks availability.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import PriceDatabase
from logger_config import setup_logging

logger = logging.getLogger(__name__)

from scrapers.coles_scraper import ColesScraper
from scrapers.woolworths_scraper import WoolworthsScraper
from scrapers.amazon_scraper import AmazonScraper
from utils.price_calculator import PriceCalculator
from utils.results_formatter import ResultsFormatter


class SunkistTracker:
    def __init__(self):
        self.coles_scraper = ColesScraper()
        self.woolworths_scraper = WoolworthsScraper()
        
        # Use Amazon web scraper
        self.amazon_scraper = AmazonScraper()
        
        self.price_calculator = PriceCalculator()
        self.formatter = ResultsFormatter()
        self.database = PriceDatabase()
    
    async def find_cheapest_sunkist(self) -> Dict:
        """Main method to find the cheapest target products across all retailers."""
        print("Searching for target products across retailers...")
        print("=" * 80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'retailers': {},
            'best_deal': None,
            'summary': {}
        }
        
        # Run scrapers concurrently for better performance
        try:
            coles_task = asyncio.create_task(self.coles_scraper.search_target_products())
            woolies_task = asyncio.create_task(self.woolworths_scraper.search_target_products())
            amazon_task = asyncio.create_task(self.amazon_scraper.search_target_products())
            
            coles_results, woolies_results, amazon_results = await asyncio.gather(
                coles_task, woolies_task, amazon_task, return_exceptions=True
            )
            
            # Process results
            if not isinstance(coles_results, Exception):
                results['retailers']['coles'] = coles_results
                print(f"✅ Coles: Found {len(coles_results.get('products', []))} products")
            else:
                print(f"❌ Coles: Error - {coles_results}")
                results['retailers']['coles'] = {'error': str(coles_results)}
            
            if not isinstance(woolies_results, Exception):
                results['retailers']['woolworths'] = woolies_results
                print(f"✅ Woolworths: Found {len(woolies_results.get('products', []))} products")
            else:
                print(f"❌ Woolworths: Error - {woolies_results}")
                results['retailers']['woolworths'] = {'error': str(woolies_results)}
            
            if not isinstance(amazon_results, Exception):
                results['retailers']['amazon'] = amazon_results
                print(f"✅ Amazon: Found {len(amazon_results.get('products', []))} products")
            else:
                print(f"❌ Amazon: Error - {amazon_results}")
                results['retailers']['amazon'] = {'error': str(amazon_results)}
                
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return {'error': str(e)}
        
        # Calculate best deals
        all_products = []
        for retailer, data in results['retailers'].items():
            if 'products' in data:
                for product in data['products']:
                    product['retailer'] = retailer
                    all_products.append(product)
        
        if all_products:
            best_deal = self.price_calculator.find_best_deal(all_products)
            results['best_deal'] = best_deal
            results['summary'] = self.formatter.create_summary(all_products, best_deal)
        
        return results
    
    def display_results(self, results: Dict):
        """Display the search results in a user-friendly format."""
        if 'error' in results:
            print(f"\n❌ Error: {results['error']}")
            return
        
        print("\n" + "=" * 60)
        print("🏆 BEST DEAL FOUND")
        print("=" * 60)
        
        if results['best_deal']:
            best = results['best_deal']
            packaging = "🥫 Can" if self._is_can(best) else "🍾 Bottle"
            print(f"🏪 Retailer: {best['retailer'].title()}")
            print(f"📦 Product: {best['name']}")
            print(f"💰 Price: ${best['price']:.2f}")
            print(f"📏 Size: {best['size']} {packaging}")
            print(f"💧 Price per litre: ${best['price_per_litre']:.2f}")
            print(f"✅ In Stock: {'Yes' if best.get('in_stock', False) else 'No'}")
            if best.get('delivery_info'):
                print(f"🚚 Delivery: {best['delivery_info']}")
        else:
            print("❌ No suitable products found")
        
        print("\n" + "=" * 60)
        print("📊 ALL RESULTS SUMMARY")
        print("=" * 60)
        
        # Collect all products from all retailers
        all_products = []
        for retailer, data in results['retailers'].items():
            if 'error' in data:
                print(f"\n{retailer.title()}: ❌ {data['error']}")
                continue
                
            products = data.get('products', [])
            print(f"\n{retailer.title()}: {len(products)} products found")
            
            # Add retailer info to each product and filter out $0.00/L products
            for product in products:
                product['retailer'] = retailer.title()
                
                # Filter out products with $0.00/L (pricing errors)
                if product.get('price_per_litre', 0) > 0:
                    all_products.append(product)
                else:
                    print(f"   ⚠️  Filtered out {product.get('name', 'Unknown')} - $0.00/L (pricing error)")
        
        # Sort all products by price per litre (cheapest first)
        all_products.sort(key=lambda x: x.get('price_per_litre', float('inf')))
        
        # Display all products sorted by price per litre
        print(f"\nALL PRODUCTS SORTED BY PRICE PER LITRE:")
        print("-" * 60)
        for i, product in enumerate(all_products, 1):
            status = "In Stock" if product.get('in_stock', False) else "Out of Stock"
            packaging = "Can" if self._is_can(product) else "Bottle"
            retailer = product.get('retailer', 'Unknown')
            print(f"{i:2d}. [{status}] [{packaging}] [{retailer}] {product['name']} - ${product['price']:.2f} ({product['size']}) - ${product['price_per_litre']:.2f}/L")
        
        # Display filtered results by brand and packaging type
        self._display_filtered_results(all_products)
    
    def _display_filtered_results(self, all_products: List[Dict]):
        """Display filtered results by brand and packaging type."""
        print(f"\nFILTERED RESULTS BY BRAND & PACKAGING:")
        print("=" * 60)
        
        # Group products by brand and packaging type
        brands = ['Sunkist', 'Fanta', 'Pepsi']
        packaging_types = {
            'Individual Bottles': ['1.25l', '1l', '600ml', '500ml'],
            '24 Pack Cans': ['24', 'x24', 'pack of 24'],
            '12 Pack Bottles': ['12 x 1.25l', '12 x 1l', '12 x 600ml'],
            '30 Pack Cans': ['30', 'x30', 'pack of 30']
        }
        
        for brand in brands:
            print(f"\n{brand.upper()}:")
            print("-" * 40)
            
            # Filter products for this brand
            brand_products = [p for p in all_products if brand.lower() in p.get('name', '').lower()]
            
            if not brand_products:
                print(f"   No {brand} products found")
                continue
            
            for packaging_name, size_indicators in packaging_types.items():
                # Find products matching this packaging type
                matching_products = []
                for product in brand_products:
                    name_lower = product.get('name', '').lower()
                    size_lower = product.get('size', '').lower()
                    
                    if any(indicator in name_lower or indicator in size_lower for indicator in size_indicators):
                        matching_products.append(product)
                
                if matching_products:
                    # Sort by price per litre and get the best deal
                    matching_products.sort(key=lambda x: x.get('price_per_litre', float('inf')))
                    best = matching_products[0]
                    
                    status = "In Stock" if best.get('in_stock', False) else "Out of Stock"
                    packaging_type = "Can" if self._is_can(best) else "Bottle"
                    retailer = best.get('retailer', 'Unknown')
                    
                    print(f"   [{status}] [{packaging_type}] {packaging_name}: {best['name']}")
                    print(f"      [{retailer}] ${best['price']:.2f} ({best['size']}) - ${best['price_per_litre']:.2f}/L")
                else:
                    print(f"   {packaging_name}: Not available")
    
    def _is_can(self, product: Dict) -> bool:
        """Check if product is a single can (not a pack)."""
        name_lower = product.get('name', '').lower()
        size_lower = product.get('size', '').lower()
        
        # Check if it's a pack/multi-pack (these should be treated differently)
        pack_indicators = ['pack of', 'pack of', 'multi', 'bulk', 'case of', 'x24', 'x12', 'x6']
        is_pack = any(indicator in name_lower for indicator in pack_indicators)
        
        if is_pack:
            return False  # Packs are not considered single cans
        
        can_indicators = ['can', 'tin', '355ml', '375ml', '330ml']
        bottle_indicators = ['bottle', '2l', '1.25l', '1l', '600ml']
        
        has_can = any(indicator in name_lower or indicator in size_lower for indicator in can_indicators)
        has_bottle = any(indicator in name_lower or indicator in size_lower for indicator in bottle_indicators)
        
        return has_can and not has_bottle


async def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    
    logger.info("Sunkist Price Tracker")
    logger.info("Finding the cheapest deals across Coles, Woolworths, and Amazon...")
    logger.info("Location: Your local area")
    logger.info("Preference: Cans over bottles (up to $2.50/L for cans)")
    logger.info("Excluding: Syrups, concentrates, and non-soda products")
    
    tracker = SunkistTracker()
    
    try:
        results = await tracker.find_cheapest_sunkist()
        tracker.display_results(results)
        
        # Save results to database
        all_products = []
        for retailer_data in results.get('retailers', {}).values():
            if 'products' in retailer_data:
                all_products.extend(retailer_data['products'])
        
        if all_products:
            saved_count = tracker.database.save_prices(all_products)
            logger.info(f"Saved {saved_count} prices to database")
        
        # Save results to file
        with open('latest_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to latest_results.json")
        
    except KeyboardInterrupt:
        logger.info("Search cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())