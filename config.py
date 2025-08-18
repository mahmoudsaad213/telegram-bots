import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = "8264460763:AAGaGR7IaKeUUQqaw2QD1_3dpX3rAoVTheI"
ADMIN_ID = 5895491379

# Database Configuration (Railway Postgres)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fbbot')

# TempMail Configuration
TEMPMAIL_BASE_URL = "https://api.tempmail.co/v1"
TEMPMAIL_API_TOKEN = "114|DuFjCcsMwMfzwIAFvQQwTkt3Y7e6TQNigieKt3tZ7fca91d4"

# Subscription Prices (in cents for Telegram Stars)
PRICES = {
    'daily': 100,    # 1 day
    'weekly': 500,   # 7 days  
    'monthly': 1500  # 30 days
}
