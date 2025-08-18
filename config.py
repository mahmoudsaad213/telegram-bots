# config.py - محدث لحل مشاكل الاتصال
import os

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8264460763:AAGaGR7IaKeUUQqaw2QD1_3dpX3rAoVTheI')

# Admin Telegram ID
ADMIN_ID = 5895491379

# Marketer Username
MARKETER_USERNAME = '@Bangladesh3456'

# Database Configuration for PostgreSQL (Railway)
# Railway يوفر DATABASE_URL مباشرة
DATABASE_URL = os.getenv('DATABASE_URL')

# إذا لم يوجد DATABASE_URL، استخدم المتغيرات المنفصلة
if not DATABASE_URL:
    DB_HOST = os.getenv('PGHOST', 'localhost')
    DB_PORT = os.getenv('PGPORT', '5432')
    DB_NAME = os.getenv('PGDATABASE', 'railway')
    DB_USER = os.getenv('PGUSER', 'postgres')
    DB_PASSWORD = os.getenv('PGPASSWORD', 'qlTkLeMzBjsFmOJKisdMpyNeFCZopdQm')
else:
    # استخراج البيانات من DATABASE_URL
    import urllib.parse as urlparse
    url = urlparse.urlparse(DATABASE_URL)
    DB_HOST = url.hostname
    DB_PORT = url.port or 5432
    DB_NAME = url.path[1:]  # إزالة الشرطة المائلة الأولى
    DB_USER = url.username
    DB_PASSWORD = url.password

# TempMail API Configuration
TEMPMAIL_BASE_URL = "https://api.tempmail.co/v1"
TEMPMAIL_API_TOKEN = os.getenv('TEMPMAIL_API_TOKEN', '114|DuFjCcsMwMfzwIAFvQQwTkt3Y7e6TQNigieKt3tZ7fca91d4')
TEMPMAIL_HEADERS = {"Authorization": f"Bearer {TEMPMAIL_API_TOKEN}"}

# Subscription Prices
SUBSCRIPTION_PRICES = {
    'daily': 5,
    'weekly': 20,
    'monthly': 50
}

# Max creations per cookie
MAX_CREATIONS_PER_COOKIE = 5
