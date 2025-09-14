"""
Results formatting utilities for displaying search results.
"""

from typing import List, Dict, Any
from datetime import datetime


class ResultsFormatter:
    """Handles formatting of search results for display."""
    
    def create_summary(self, products: List[Dict], best_deal: Dict) -> Dict:
        """Create a summary of the search results."""
        summary = {
            'total_products_found': len(products),
            'in_stock_products': len([p for p in products if p.get('in_stock', False)]),
            'retailers_checked': len(set(p.get('retailer', '') for p in products)),
            'best_deal_summary': None,
            'price_range': None,
            'search_timestamp': datetime.now().isoformat()
        }
        
        if best_deal:
            summary['best_deal_summary'] = {
                'retailer': best_deal.get('retailer', ''),
                'price': best_deal.get('price', 0),
                'price_per_litre': best_deal.get('price_per_litre', 0),
                'size': best_deal.get('size', ''),
                'in_stock': best_deal.get('in_stock', False)
            }
        
        # Calculate price range
        valid_prices = [p.get('price_per_litre', 0) for p in products if p.get('price_per_litre', 0) > 0]
        if valid_prices:
            summary['price_range'] = {
                'min': min(valid_prices),
                'max': max(valid_prices),
                'average': sum(valid_prices) / len(valid_prices)
            }
        
        return summary
    
    def format_product_display(self, product: Dict) -> str:
        """Format a single product for display."""
        lines = []
        
        # Product name
        name = product.get('name', 'Unknown Product')
        lines.append(f"📦 {name}")
        
        # Price and size
        price = product.get('price', 0)
        size = product.get('size', 'Unknown')
        price_per_litre = product.get('price_per_litre', 0)
        
        lines.append(f"💰 ${price:.2f} ({size}) - ${price_per_litre:.2f}/L")
        
        # Stock status
        in_stock = product.get('in_stock', False)
        stock_emoji = "✅" if in_stock else "❌"
        lines.append(f"{stock_emoji} Stock: {'Available' if in_stock else 'Out of Stock'}")
        
        # Delivery info (for Amazon)
        delivery_info = product.get('delivery_info', '')
        if delivery_info:
            lines.append(f"🚚 Delivery: {delivery_info}")
        
        # URL
        url = product.get('url', '')
        if url:
            lines.append(f"🔗 {url}")
        
        return "\n".join(lines)
    
    def format_retailer_summary(self, retailer: str, products: List[Dict]) -> str:
        """Format summary for a specific retailer."""
        if not products:
            return f"❌ {retailer.title()}: No products found"
        
        in_stock_count = len([p for p in products if p.get('in_stock', False)])
        cheapest = min(products, key=lambda x: x.get('price_per_litre', float('inf')))
        
        lines = [
            f"🏪 {retailer.title()}: {len(products)} products found",
            f"✅ {in_stock_count} in stock",
            f"💰 Cheapest: ${cheapest.get('price_per_litre', 0):.2f}/L"
        ]
        
        return "\n".join(lines)
    
    def format_comparison_table(self, products: List[Dict]) -> str:
        """Format products in a comparison table."""
        if not products:
            return "No products to compare"
        
        # Sort by price per litre
        sorted_products = sorted(products, key=lambda x: x.get('price_per_litre', float('inf')))
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"{'Retailer':<12} {'Product':<30} {'Price':<8} {'Size':<10} {'$/L':<8} {'Stock':<6}")
        lines.append("=" * 80)
        
        for product in sorted_products:
            retailer = product.get('retailer', 'Unknown')[:11]
            name = product.get('name', 'Unknown')[:29]
            price = f"${product.get('price', 0):.2f}"
            size = product.get('size', 'Unknown')[:9]
            price_per_litre = f"${product.get('price_per_litre', 0):.2f}"
            stock = "✅" if product.get('in_stock', False) else "❌"
            
            lines.append(f"{retailer:<12} {name:<30} {price:<8} {size:<10} {price_per_litre:<8} {stock:<6}")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def format_error_message(self, retailer: str, error: str) -> str:
        """Format error message for a retailer."""
        return f"❌ {retailer.title()}: {error}"
    
    def format_search_stats(self, results: Dict) -> str:
        """Format search statistics."""
        stats = []
        
        total_products = 0
        successful_retailers = 0
        
        for retailer, data in results.get('retailers', {}).items():
            if 'error' in data:
                stats.append(f"❌ {retailer.title()}: Failed")
            else:
                product_count = len(data.get('products', []))
                total_products += product_count
                successful_retailers += 1
                stats.append(f"✅ {retailer.title()}: {product_count} products")
        
        summary = [
            f"🔍 Search completed at {results.get('timestamp', 'Unknown time')}",
            f"📊 {successful_retailers}/3 retailers successful",
            f"📦 {total_products} total products found"
        ]
        
        return "\n".join(summary + stats)