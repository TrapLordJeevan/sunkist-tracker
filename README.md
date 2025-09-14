# Sunkist Price Tracker

Price tracking for Sunkist Zero Sugar, Fanta Zero Sugar, and Pepsi Max Mango across Coles, Woolworths, and Amazon.

## Quick Start

### 1. Installation
```bash
git clone https://github.com/your-username/sunkist-tracker.git
cd sunkist-tracker
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp env.example .env
# Edit .env with your email credentials
```

### 3. Run Price Scrape
```bash
python main.py
```

### 4. Start Web Interface
```bash
python web_app.py
```
Visit: `http://localhost:5000`

### 5. Send Email Notifications
```bash
python email_notifier.py
```

## Docker Setup

```bash
# Copy environment file
cp env.example .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Usage Examples

### Basic Price Check
```bash
python main.py
```

### Web Dashboard
```bash
python web_app.py
# Open http://localhost:5000
```

### Daily Scheduling
```bash
python scheduler.py
```

### Email Notifications
```bash
# Set environment variables
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"

# Test email
python email_notifier.py
```

## Configuration

### Environment Variables
- `EMAIL_ADDRESS`: Your Gmail address
- `EMAIL_PASSWORD`: Gmail App Password (16 characters)
- `RECIPIENT_EMAIL`: Where to send notifications
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Price Preferences
- Cans: Preferred up to $2.50/L
- Bottles: Acceptable up to $2.00/L
- Excludes: Syrups, concentrates, mixes

### Products Tracked
- Sunkist Zero Sugar (all flavors)
- Fanta Zero Sugar (all flavors)
- Pepsi Max Mango

## Database

Prices are stored in SQLite (`prices.db`) with fields:
- Date, retailer, product name
- Size (ml), price, price per litre
- Stock status, product URL

## API Endpoints

- `GET /api/results` - Latest price results
- `POST /api/refresh` - Trigger price check
- `GET /api/status` - Service status

## Testing

```bash
pip install pytest
pytest tests/
```

## Ubuntu Server Deployment

```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
./manage.sh start
```

## Cron Job Example

```bash
# Add to crontab for daily checks at 8 AM and 6 PM
0 8,18 * * * /usr/bin/python /path/to/sunkist-tracker/main.py >> /var/log/sunkist.log 2>&1
```