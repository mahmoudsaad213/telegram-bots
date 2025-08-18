import os

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8264460763:AAGaGR7IaKeUUQqaw2QD1_3dpX3rAoVTheI')

# Admin Telegram ID (Updated to correct ID)
ADMIN_ID = 5895491379

# Marketer Username (غيّر دا لو عايز يوزر مسوق مختلف)
MARKETER_USERNAME = '@Bangladesh3456'  # ضع يوزر المسوق الحقيقي هنا

# Database Configuration for PostgreSQL (using Railway environment variables)
DB_HOST = os.getenv('PGHOST', 'localhost')
DB_PORT = os.getenv('PGPORT', '5432')
DB_NAME = os.getenv('PGDATABASE', 'railway')
DB_USER = os.getenv('PGUSER', 'postgres')
DB_PASSWORD = os.getenv('PGPASSWORD', 'qlTkLeMzBjsFmOJKisdMpyNeFCZopdQm')

# TempMail API Configuration
TEMPMAIL_BASE_URL = "https://api.tempmail.co/v1"
TEMPMAIL_API_TOKEN = os.getenv('TEMPMAIL_API_TOKEN', '114|DuFjCcsMwMfzwIAFvQQwTkt3Y7e6TQNigieKt3tZ7fca91d4')
TEMPMAIL_HEADERS = {"Authorization": f"Bearer {TEMPMAIL_API_TOKEN}"}

# Subscription Prices (in some currency, e.g., USD)
SUBSCRIPTION_PRICES = {
    'daily': 5,
    'weekly': 20,
    'monthly': 50
}

# Max creations per cookie
MAX_CREATIONS_PER_COOKIE = 5
# Max creations per cookie
MAX_CREATIONS_PER_COOKIE = 5
