#!/usr/bin/env python3
"""
Web interface for Sunkist Price Tracker.
Run this on your Ubuntu server to view results via web browser.
"""

import asyncio
import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from main import SunkistTracker

app = Flask(__name__)

# Global variable to store latest results
latest_results = None
last_updated = None

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