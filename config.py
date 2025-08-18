# config.py

import os

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8264460763:AAGaGR7IaKeUUQqaw2QD1_3dpX3rAoVTheI')

# Admin Telegram ID
ADMIN_ID = 5607097913

# Marketer Username
MARKETER_USERNAME = '@Bangladesh3456'

# Database Configuration for Postgres
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'facebook_business_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# TempMail API Configuration
TEMPMAIL_BASE_URL = "https://api.tempmail.co/v1"
TEMPMAIL_API_TOKEN = "114|DuFjCcsMwMfzwIAFvQQwTkt3Y7e6TQNigieKt3tZ7fca91d4"
TEMPMAIL_HEADERS = {"Authorization": f"Bearer {TEMPMAIL_API_TOKEN}"}

# Subscription Prices (in some currency, e.g., USD)
SUBSCRIPTION_PRICES = {
    'daily': 5,
    'weekly': 20,
    'monthly': 50
}

# Max creations per cookie
MAX_CREATIONS_PER_COOKIE = 5
