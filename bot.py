# bot.py

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from config import BOT_TOKEN, ADMIN_ID, MARKETER_USERNAME, SUBSCRIPTION_PRICES
from database import Database
from create_business import process_combo

bot = telebot.TeleBot(BOT_TOKEN)

# Helper Functions
def is_admin(user_id):
    return user_id == ADMIN_ID

def get_subscription_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Daily Subscription", callback_data="sub_daily"))
    markup.add(InlineKeyboardButton("Weekly Subscription", callback_data="sub_weekly"))
    markup.add(InlineKeyboardButton("Monthly Subscription", callback_data="sub_monthly"))
    return markup

def get_main_menu(user_id):  # أضفنا user_id كمعامل
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📝 Add Combo"))
    markup.add(KeyboardButton("🚀 Create Businesses"))
    markup.add(KeyboardButton("📊 My Businesses"))
    markup.add(KeyboardButton("🔍 Check Subscription"))
    if is_admin(user_id):  # استخدمنا user_id بدل ADMIN_ID
        markup.add(KeyboardButton("🛠 Admin Panel"))
    return markup

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    db = Database()
    db.add_user(message.from_user.id, message.from_user.username)
    db.close()
    bot.send_message(message.chat.id, "Welcome to Facebook Business Creator Bot!\nPlease subscribe to use the features.", reply_markup=get_subscription_keyboard())

# Subscription Callbacks
@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_'))
def handle_subscription(call):
    sub_type = call.data.split('_')[1]
    price = SUBSCRIPTION_PRICES[sub_type]
    bot.answer_callback_query(call.id, f"You selected {sub_type} subscription for ${price}. Contact {MARKETER_USERNAME} for payment.")
    bot.send_message(call.message.chat.id, f"To subscribe {sub_type}, pay ${price} to {MARKETER_USERNAME} and send proof to admin.")

# Add Combo
@bot.message_handler(func=lambda message: message.text == "📝 Add Combo")
def add_combo(message):
    db = Database()
    if not db.is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "You need an active subscription.")
        db.close()
        return
    bot.send_message(message.chat.id, "Send your combo cookies (one per line or separated by ;;).")
    bot.register_next_step_handler(message, process_add_combo)

def process_add_combo(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    combos = message.text.split(';;')  # Assuming ;; separator for multiple
    for combo in combos:
        db.add_combo(user['id'], combo.strip())
    bot.send_message(message.chat.id, f"Added {len(combos)} combos.", reply_markup=get_main_menu())
    db.close()

# Create Businesses
@bot.message_handler(func=lambda message: message.text == "🚀 Create Businesses")
def create_businesses(message):
    if not Database().is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "You need an active subscription.")
        return
    bot.send_message(message.chat.id, "Processing your combos... This may take time.")
    result = process_combo(message.from_user.id)
    bot.send_message(message.chat.id, f"Results:\n{result}", reply_markup=get_main_menu())

# My Businesses
@bot.message_handler(func=lambda message: message.text == "📊 My Businesses")
def my_businesses(message):
    db = Database()
    if not db.is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "You need an active subscription.")
        db.close()
        return
    user = db.get_user(message.from_user.id)
    businesses = db.get_user_businesses(user['id'])
    if not businesses:
        bot.send_message(message.chat.id, "No businesses created yet.")
    else:
        msg = "Your Businesses:\n"
        for biz in businesses:
            msg += f"ID: {biz['business_id']}, Link: {biz['invitation_link']}\n"
        bot.send_message(message.chat.id, msg)
    db.close()

# Check Subscription
@bot.message_handler(func=lambda message: message.text == "🔍 Check Subscription")
def check_sub(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    if user and user['is_active']:
        end = user['subscription_end']
        bot.send_message(message.chat.id, f"Your {user['subscription_type']} subscription ends on {end}.")
    else:
        bot.send_message(message.chat.id, "No active subscription.")
    db.close()

# Admin Panel
@bot.message_handler(func=lambda message: message.text == "🛠 Admin Panel" and is_admin(message.from_user.id))
def admin_panel(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Activate User", callback_data="admin_activate"))
    markup.add(InlineKeyboardButton("List Users", callback_data="admin_list"))
    bot.send_message(message.chat.id, "Admin Panel", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_actions(call):
    if call.data == "admin_list":
        db = Database()
        db.cursor.execute("SELECT * FROM users")
        users = db.cursor.fetchall()
        msg = "Users:\n"
        for u in users:
            msg += f"ID: {u['telegram_id']}, Sub: {u['subscription_type'] or 'None'}\n"
        bot.send_message(call.message.chat.id, msg)
        db.close()
    elif call.data == "admin_activate":
        bot.send_message(call.message.chat.id, "Send user Telegram ID, sub_type (daily/weekly/monthly), duration in days.")
        bot.register_next_step_handler(call.message, process_activate)

def process_activate(message):
    try:
        parts = message.text.split(',')
        telegram_id = int(parts[0].strip())
        sub_type = parts[1].strip()
        duration = int(parts[2].strip())
        start = datetime.now()
        end = start + timedelta(days=duration)
        db = Database()
        db.activate_subscription(telegram_id, sub_type, start, end)
        bot.send_message(message.chat.id, f"Activated {sub_type} for user {telegram_id} until {end}.")
        db.close()
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

if __name__ == "__main__":
    bot.infinity_polling()
