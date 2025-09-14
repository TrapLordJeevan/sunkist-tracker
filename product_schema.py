"""
Standard product schema and validation.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ProductSchema:
    """Standard product schema for consistent data across scrapers."""
    
    REQUIRED_FIELDS = {
        'store': str,
        'name': str,
        'size_ml': (int, float),
        'pack_qty': (int, float),
        'price': (int, float),
        'price_per_litre': (int, float),
        'url': str,
        'in_stock': bool
    }
    
    @classmethod
    def validate_product(cls, product: Dict[str, Any]) -> bool:
        """Validate that a product dict has all required fields with correct types."""
        if not isinstance(product, dict):
            logger.error(f"Product is not a dict: {type(product)}")
            return False
        
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if field not in product:
                logger.error(f"Missing required field '{field}' in product: {product.get('name', 'Unknown')}")
                return False
            
            value = product[field]
            if not isinstance(value, expected_type):
                logger.error(f"Field '{field}' has wrong type. Expected {expected_type}, got {type(value)}")
                return False
            
            # Additional validation
            if field in ['price', 'price_per_litre', 'size_ml', 'pack_qty'] and value < 0:
                logger.error(f"Field '{field}' cannot be negative: {value}")
                return False
        
        return True
    
    @classmethod
    def normalize_product(cls, raw_product: Dict[str, Any], store: str) -> Optional[Dict[str, Any]]:
        """Normalize a raw product dict to the standard schema."""
        try:
            # Extract and normalize fields
            normalized = {
                'store': store,
                'name': str(raw_product.get('name', '')).strip(),
                'size_ml': cls._extract_size_ml(raw_product.get('size', '')),
                'pack_qty': cls._extract_pack_qty(raw_product.get('size', ''), raw_product.get('name', '')),
                'price': float(raw_product.get('price', 0)),
                'price_per_litre': float(raw_product.get('price_per_litre', 0)),
                'url': str(raw_product.get('url', '')).strip(),
                'in_stock': bool(raw_product.get('in_stock', False))
            }
            
            # Validate the normalized product
            if cls.validate_product(normalized):
                return normalized
            else:
                logger.error(f"Failed to validate normalized product: {normalized}")
                return None
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error normalizing product: {e}")
            return None
    
    @classmethod
    def _extract_size_ml(cls, size_text: str) -> float:
        """Extract size in ml from size text."""
        if not size_text:
            return 0.0
        
        import re
        
        # Look for ml patterns
        ml_match = re.search(r'(\d+(?:\.\d+)?)\s*ml', size_text.lower())
        if ml_match:
            return float(ml_match.group(1))
        
        # Look for L patterns and convert to ml
        l_match = re.search(r'(\d+(?:\.\d+)?)\s*l(?:itre)?', size_text.lower())
        if l_match:
            return float(l_match.group(1)) * 1000
        
        return 0.0
    
    @classmethod
    def _extract_pack_qty(cls, size_text: str, name_text: str) -> int:
        """Extract pack quantity from size or name text."""
        if not size_text and not name_text:
            return 1
        
        import re
        
        # Look for pack patterns in size
        pack_patterns = [
            r'pack\s*of\s*(\d+)',
            r'(\d+)\s*x\s*\d+',
            r'(\d+)\s*pack'
        ]
        
        for pattern in pack_patterns:
            match = re.search(pattern, size_text.lower())
            if match:
                return int(match.group(1))
        
        # Look for pack patterns in name
        for pattern in pack_patterns:
            match = re.search(pattern, name_text.lower())
            if match:
                return int(match.group(1))
        
        return 1