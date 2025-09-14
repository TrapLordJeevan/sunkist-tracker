# Sunkist Price Tracker

Price tracking for Sunkist Zero Sugar, Fanta Zero Sugar, and Pepsi Max Mango across Coles, Woolworths, and Amazon.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Web Interface

```bash
python web_app.py
```

Visit: `http://localhost:5000`

## Email Notifications

Set environment variables:
```bash
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
```

## Ubuntu Server

```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
./manage.sh start
```

## Configuration

- Cans: Preferred up to $2.50/L
- Bottles: Acceptable up to $2.00/L
- Excludes: Syrups, concentrates, mixes