"""
Price calculation utilities for comparing products across retailers.
"""

from typing import List, Dict, Optional


class PriceCalculator:
    """Handles price calculations and comparisons."""
    
    def find_best_deal(self, products: List[Dict]) -> Optional[Dict]:
        """Find the best deal among all products, prioritizing cans."""
        if not products:
            return None
        
        # Filter products that are in stock and have valid pricing
        valid_products = [
            p for p in products 
            if (p.get('in_stock', False) and 
                p.get('price', 0) > 0 and 
                p.get('price_per_litre', 0) > 0)
        ]
        
        if not valid_products:
            return None
        
        # Separate cans and bottles
        cans = [p for p in valid_products if self._is_can(p)]
        bottles = [p for p in valid_products if not self._is_can(p)]
        
        # Prioritize cans with $2.50/L threshold
        preferred_cans = [p for p in cans if p.get('price_per_litre', 0) <= 2.50]
        
        if preferred_cans:
            # Return cheapest can under $2.50/L
            return min(preferred_cans, key=lambda x: x['price_per_litre'])
        else:
            # If no cans under $2.50/L, check bottles first
            preferred_bottles = [p for p in bottles if p.get('price_per_litre', 0) <= 2.00]
            if preferred_bottles:
                # Return cheapest bottle under $2.00/L
                return min(preferred_bottles, key=lambda x: x['price_per_litre'])
            elif bottles:
                # Return cheapest bottle anyway
                return min(bottles, key=lambda x: x['price_per_litre'])
            elif cans:
                # Only return expensive cans if no bottles available
                return min(cans, key=lambda x: x['price_per_litre'])
            else:
                return None
    
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
    
    def get_price_comparison(self, products: List[Dict]) -> Dict:
        """Get detailed price comparison across retailers."""
        comparison = {
            'by_retailer': {},
            'cheapest_overall': None,
            'most_expensive': None,
            'average_price_per_litre': 0.0,
            'total_products': len(products)
        }
        
        if not products:
            return comparison
        
        # Group by retailer
        for product in products:
            retailer = product.get('retailer', 'unknown')
            if retailer not in comparison['by_retailer']:
                comparison['by_retailer'][retailer] = []
            comparison['by_retailer'][retailer].append(product)
        
        # Find cheapest and most expensive
        valid_products = [p for p in products if p.get('price_per_litre', 0) > 0]
        if valid_products:
            comparison['cheapest_overall'] = min(valid_products, key=lambda x: x['price_per_litre'])
            comparison['most_expensive'] = max(valid_products, key=lambda x: x['price_per_litre'])
            
            # Calculate average price per litre
            total_price = sum(p['price_per_litre'] for p in valid_products)
            comparison['average_price_per_litre'] = total_price / len(valid_products)
        
        return comparison
    
    def calculate_savings(self, best_deal: Dict, other_products: List[Dict]) -> List[Dict]:
        """Calculate savings compared to other products."""
        if not best_deal or not other_products:
            return []
        
        best_price_per_litre = best_deal.get('price_per_litre', 0)
        if best_price_per_litre == 0:
            return []
        
        savings = []
        for product in other_products:
            if product.get('price_per_litre', 0) > 0:
                savings_amount = product['price_per_litre'] - best_price_per_litre
                savings_percentage = (savings_amount / product['price_per_litre']) * 100
                
                savings.append({
                    'product': product,
                    'savings_amount': savings_amount,
                    'savings_percentage': savings_percentage
                })
        
        return sorted(savings, key=lambda x: x['savings_amount'], reverse=True)
    
    def format_price(self, price: float) -> str:
        """Format price for display."""
        return f"${price:.2f}"
    
    def format_size(self, size: str) -> str:
        """Format size for display."""
        if not size:
            return "Unknown"
        return size
    
    def get_retailer_emoji(self, retailer: str) -> str:
        """Get emoji for retailer."""
        emojis = {
            'coles': '🛒',
            'woolworths': '🛍️',
            'woolies': '🛍️',
            'amazon': '📦'
        }
        return emojis.get(retailer.lower(), '🏪')