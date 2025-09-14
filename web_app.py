#!/usr/bin/env python3
"""
Web interface for Sunkist Price Tracker.
Run this on your Ubuntu server to view results via web browser.
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from database import PriceDatabase
from logger_config import setup_logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to store latest results
latest_results = None
last_updated = None
database = PriceDatabase()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', 
                         results=latest_results, 
                         last_updated=last_updated)

@app.route('/api/results')
def api_results():
    """API endpoint to get latest results."""
    return jsonify({
        'results': latest_results,
        'last_updated': last_updated,
        'status': 'success' if latest_results else 'no_data'
    })

@app.route('/api/refresh', methods=['POST'])
def refresh_results():
    """Manually trigger a price check."""
    global latest_results, last_updated
    
    try:
        # Lazy import to avoid Selenium import issues at startup
        from main import SunkistTracker
        
        # Run the price tracker
        tracker = SunkistTracker()
        results = asyncio.run(tracker.find_cheapest_sunkist())
        
        latest_results = results
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            'status': 'success',
            'message': 'Price check completed',
            'last_updated': last_updated
        })
    except Exception as e:
        logger.error(f"Error in refresh: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/status')
def status():
    """Check if the service is running."""
    return jsonify({
        'status': 'running',
        'last_updated': last_updated,
        'has_data': latest_results is not None
    })

@app.route('/api/history')
def price_history():
    """Get price history from database."""
    try:
        limit = request.args.get('limit', 100, type=int)
        sort_by = request.args.get('sort', 'newest')  # newest, price_per_litre
        
        if sort_by == 'price_per_litre':
            products = database.get_latest_prices(limit, sort_by='price_per_litre')
        else:
            products = database.get_latest_prices(limit, sort_by='newest')
            
        return jsonify({
            'status': 'success',
            'products': products,
            'count': len(products),
            'sort_by': sort_by
        })
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/best-deals')
def best_deals():
    """Get best deals from database."""
    try:
        limit = request.args.get('limit', 10, type=int)
        deals = database.get_best_deals(limit)
        return jsonify({
            'status': 'success',
            'deals': deals,
            'count': len(deals)
        })
    except Exception as e:
        logger.error(f"Error getting best deals: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Load existing results if available
    results_file = 'latest_results.json'
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                latest_results = data.get('results')
                last_updated = data.get('last_updated')
        except:
            pass
    
    print("🌐 Starting Sunkist Price Tracker Web Interface...")
    print("📱 Access at: http://localhost:5000")
    print("📊 API endpoints:")
    print("   - GET  /api/results  - Get latest results")
    print("   - POST /api/refresh  - Trigger price check")
    print("   - GET  /api/status   - Check service status")
    
    app.run(host='0.0.0.0', port=5000, debug=False)