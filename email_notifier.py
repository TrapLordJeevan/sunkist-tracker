#!/usr/bin/env python3
"""
Email notification system for Sunkist Price Tracker.
Sends daily price updates via email.
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List
import os

class EmailNotifier:
    """Handles email notifications for price updates."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.recipient = os.getenv('RECIPIENT_EMAIL', self.email)
        
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.email and self.password)
    
    def send_price_update(self, results: Dict) -> bool:
        """Send price update email."""
        if not self.is_configured():
            print("⚠️  Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
            return False
        
        try:
            # Create email content
            subject = f"Daily Sunkist Price Update - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._create_html_email(results)
            text_content = self._create_text_email(results)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = self.recipient
            
            # Add both text and HTML versions
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            print(f"Price update email sent to {self.recipient}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _create_html_email(self, results: Dict) -> str:
        """Create HTML email content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b, #feca57); color: white; padding: 20px; text-align: center; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .product {{ background: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                .price {{ color: #28a745; font-weight: bold; font-size: 1.2em; }}
                .retailer {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
                .best-deal {{ background: #d4edda; border-left-color: #28a745; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
        <div class="header">
            <h1>Daily Sunkist Price Update</h1>
            <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
            
            <div class="container">
        """
        
        # Best deals section
        if results.get('best_deals'):
                html += """
                    <div class="section">
                        <h2>Best Deals Today</h2>
            """
            if results['best_deals'].get('cheapest_can'):
                html += f'<div class="product best-deal"><strong>Best Can Deal:</strong> {results["best_deals"]["cheapest_can"]}</div>'
            if results['best_deals'].get('cheapest_bottle'):
                html += f'<div class="product best-deal"><strong>Best Bottle Deal:</strong> {results["best_deals"]["cheapest_bottle"]}</div>'
            html += "</div>"
        
        # Retailer sections
        html += '<div class="section"><h2>📊 All Products by Retailer</h2>'
        
        for retailer, data in results.get('retailers', {}).items():
            html += f'<div class="retailer">{retailer.title()}</div>'
            
            if data.get('error'):
                html += f'<div class="error">❌ {data["error"]}</div>'
            else:
                products = data.get('products', [])
                for product in products[:5]:  # Show top 5 products per retailer
                    status = "In Stock" if product.get('in_stock') else "Out of Stock"
                    html += f"""
                        <div class="product">
                            <strong>{product['name']}</strong><br>
                            <span class="price">${product['price']:.2f}</span> ({product['size']}) - ${product['price_per_litre']:.2f}/L<br>
                            {status}
                        </div>
                    """
        
        html += """
                </div>
                
                <div class="section">
                    <p><strong>💡 Tip:</strong> Visit your price tracker dashboard for the complete list and to manually refresh prices.</p>
                    <p><em>This is an automated daily update from your Sunkist Price Tracker.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_email(self, results: Dict) -> str:
        """Create plain text email content."""
        text = f"""
🥤 DAILY SUNKIST PRICE UPDATE
{datetime.now().strftime('%A, %B %d, %Y')}
{'=' * 50}

"""
        
        # Best deals
        if results.get('best_deals'):
            text += "🏆 BEST DEALS TODAY:\n"
            if results['best_deals'].get('cheapest_can'):
                text += f"Best Can Deal: {results['best_deals']['cheapest_can']}\n"
            if results['best_deals'].get('cheapest_bottle'):
                text += f"Best Bottle Deal: {results['best_deals']['cheapest_bottle']}\n"
            text += "\n"
        
        # All products
        text += "ALL PRODUCTS BY RETAILER:\n"
        text += "-" * 30 + "\n"
        
        for retailer, data in results.get('retailers', {}).items():
            text += f"\n{retailer.upper()}:\n"
            
            if data.get('error'):
                text += f"Error: {data['error']}\n"
            else:
                products = data.get('products', [])
                for product in products[:5]:  # Show top 5 products per retailer
                    status = "In Stock" if product.get('in_stock') else "Out of Stock"
                    text += f"• {product['name']}\n"
                    text += f"  ${product['price']:.2f} ({product['size']}) - ${product['price_per_litre']:.2f}/L\n"
                    text += f"  {status}\n\n"
        
        text += """
💡 TIP: Visit your price tracker dashboard for the complete list and to manually refresh prices.

This is an automated daily update from your Sunkist Price Tracker.
        """
        
        return text

def send_daily_update(results: Dict) -> bool:
    """Convenience function to send daily update."""
    notifier = EmailNotifier()
    return notifier.send_price_update(results)

if __name__ == "__main__":
    # Test email configuration
    notifier = EmailNotifier()
    if notifier.is_configured():
        print("✅ Email is configured")
        print(f"📧 From: {notifier.email}")
        print(f"📧 To: {notifier.recipient}")
    else:
        print("❌ Email not configured")
        print("Set these environment variables:")
        print("  EMAIL_ADDRESS=your-email@gmail.com")
        print("  EMAIL_PASSWORD=your-app-password")
        print("  RECIPIENT_EMAIL=recipient@example.com (optional)")