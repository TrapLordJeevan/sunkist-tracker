#!/usr/bin/env python3
"""
Scheduler for running daily price checks and sending email notifications.
"""

import asyncio
import json
import schedule
import time
from datetime import datetime
from main import SunkistTracker
from email_notifier import send_daily_update
import os

class PriceTrackerScheduler:
    """Handles scheduled price checks and notifications."""
    
    def __init__(self):
        self.results_file = 'latest_results.json'
        self.log_file = 'scheduler.log'
        
    def log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # Also write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
    
    async def run_price_check(self):
        """Run a complete price check and save results."""
        try:
            self.log("Starting scheduled price check...")
            
            # Run the price tracker
            tracker = SunkistTracker()
            results = await tracker.find_cheapest_sunkist()
            
            # Save results to file
            data = {
                'results': results,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.results_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.log(f"Price check completed. Found {self._count_products(results)} products.")
            
            # Send email notification
            if send_daily_update(results):
                self.log("Email notification sent successfully")
            else:
                self.log("Email notification failed or not configured")
            
            return results
            
        except Exception as e:
            self.log(f"Price check failed: {e}")
            return None
    
    def _count_products(self, results: dict) -> int:
        """Count total products found across all retailers."""
        total = 0
        for retailer_data in results.get('retailers', {}).values():
            if 'products' in retailer_data:
                total += len(retailer_data['products'])
        return total
    
    def schedule_daily_checks(self):
        """Set up daily price checks."""
        # Run at 8:00 AM every day
        schedule.every().day.at("08:00").do(self._run_scheduled_check)
        
        # Also run at 6:00 PM for evening update
        schedule.every().day.at("18:00").do(self._run_scheduled_check)
        
        self.log("Scheduled daily price checks at 8:00 AM and 6:00 PM")
    
    def _run_scheduled_check(self):
        """Wrapper to run scheduled check in asyncio."""
        asyncio.run(self.run_price_check())
    
    def run_scheduler(self):
        """Run the scheduler continuously."""
        self.log("Starting Sunkist Price Tracker Scheduler")
        self.log("Daily checks scheduled at 8:00 AM and 6:00 PM")
        self.log("Web interface available at http://localhost:5000")
        self.log("Press Ctrl+C to stop")
        
        # Run initial price check
        self.log("Running initial price check...")
        asyncio.run(self.run_price_check())
        
        # Start the scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.log("Scheduler stopped by user")
                break
            except Exception as e:
                self.log(f"Scheduler error: {e}")
                time.sleep(60)  # Wait a minute before retrying

def main():
    """Main function to run the scheduler."""
    scheduler = PriceTrackerScheduler()
    scheduler.schedule_daily_checks()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()