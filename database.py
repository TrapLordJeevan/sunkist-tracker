"""
Database module for storing price data.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PriceDatabase:
    """SQLite database for storing price history."""
    
    def __init__(self, db_path: str = "prices.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    retailer TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    size_ml REAL NOT NULL,
                    price REAL NOT NULL,
                    price_per_litre REAL NOT NULL,
                    in_stock BOOLEAN NOT NULL,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_retailer 
                ON prices(date, retailer)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_name 
                ON prices(product_name)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def save_prices(self, prices: List[Dict], date: str = None) -> int:
        """Save a list of prices to the database."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        saved_count = 0
        
        with self._get_connection() as conn:
            for price in prices:
                try:
                    conn.execute("""
                        INSERT INTO prices 
                        (date, retailer, product_name, size_ml, price, price_per_litre, in_stock, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date,
                        price.get('retailer', ''),
                        price.get('name', ''),
                        price.get('size_ml', 0),
                        price.get('price', 0),
                        price.get('price_per_litre', 0),
                        price.get('in_stock', False),
                        price.get('url', '')
                    ))
                    saved_count += 1
                except sqlite3.Error as e:
                    logger.error(f"Error saving price: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"Saved {saved_count} prices to database")
        return saved_count
    
    def get_latest_prices(self, limit: int = 100, sort_by: str = 'newest') -> List[Dict]:
        """Get the latest prices from the database."""
        with self._get_connection() as conn:
            if sort_by == 'price_per_litre':
                cursor = conn.execute("""
                    SELECT * FROM prices 
                    ORDER BY price_per_litre ASC, created_at DESC 
                    LIMIT ?
                """, (limit,))
            else:  # newest
                cursor = conn.execute("""
                    SELECT * FROM prices 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_price_history(self, product_name: str, days: int = 30) -> List[Dict]:
        """Get price history for a specific product."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM prices 
                WHERE product_name LIKE ? 
                AND date >= date('now', '-{} days')
                ORDER BY date DESC, created_at DESC
            """.format(days), (f"%{product_name}%",))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_best_deals(self, limit: int = 10) -> List[Dict]:
        """Get the best deals (lowest price per litre)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM prices 
                WHERE in_stock = 1 
                AND price_per_litre > 0
                ORDER BY price_per_litre ASC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_retailer_stats(self) -> List[Dict]:
        """Get statistics by retailer."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    retailer,
                    COUNT(*) as total_products,
                    AVG(price_per_litre) as avg_price_per_litre,
                    MIN(price_per_litre) as min_price_per_litre,
                    MAX(price_per_litre) as max_price_per_litre
                FROM prices 
                WHERE date = date('now')
                GROUP BY retailer
            """)
            
            return [dict(row) for row in cursor.fetchall()]