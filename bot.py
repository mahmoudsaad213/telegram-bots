from telebot import TeleBot, types
from config import BOT_TOKEN, ADMIN_ID, MARKETER_USERNAME, SUBSCRIPTION_PRICES
from database import Database
import create_business

bot = TeleBot(BOT_TOKEN)

def is_admin(user_id):
    print(f"Checking admin: user_id={user_id}, ADMIN_ID={ADMIN_ID}")
    return user_id == ADMIN_ID

def get_main_menu(user_id):
    print(f"Building main menu for user_id={user_id}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Add Combo"))
    markup.add(types.KeyboardButton("🚀 Create Businesses"))
    markup.add(types.KeyboardButton("📊 My Businesses"))
    markup.add(types.KeyboardButton("🔍 Check Subscription"))
    if is_admin(user_id):
        markup.add(types.KeyboardButton("🛠 Admin Panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    db = Database()
    db.add_user(message.from_user.id, message.from_user.username)
    db.close()
    bot.send_message(message.chat.id, "Welcome to Facebook Business Creator Bot!\nPlease subscribe to use the features.", 
                     reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📝 Add Combo":
        bot.send_message(message.chat.id, "Please send the combos (email:password) separated by ;;")
        bot.register_next_step_handler(message, process_add_combo)
    elif message.text == "🚀 Create Businesses":
        create_businesses(message)
    elif message.text == "📊 My Businesses":
        my_businesses(message)
    elif message.text == "🔍 Check Subscription":
        check_sub(message)
    elif message.text == "🛠 Admin Panel" and is_admin(message.from_user.id):
        admin_panel(message)

def process_add_combo(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    combos = message.text.split(';;')
    for combo in combos:
        db.add_combo(user['id'], combo.strip())
    bot.send_message(message.chat.id, f"Added {len(combos)} combos.", 
                    reply_markup=get_main_menu(message.from_user.id))
    db.close()

def create_businesses(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    if not user or not user['is_active']:
        bot.send_message(message.chat.id, f"Please subscribe to create businesses. Contact {MARKETER_USERNAME} for payment.", 
                         reply_markup=get_subscription_menu())
        db.close()
        return
    combos = db.get_combos(user['id'])
    if not combos:
        bot.send_message(message.chat.id, "No combos found. Please add combos first.", 
                        reply_markup=get_main_menu(message.from_user.id))
        db.close()
        return
    for combo in combos:
        try:
            result = create_business.create_business(combo['combo'])
            db.add_business(user['id'], result['name'])
            bot.send_message(message.chat.id, f"Created business: {result['name']}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Error creating business: {str(e)}")
    bot.send_message(message.chat.id, "Business creation completed.", 
                    reply_markup=get_main_menu(message.from_user.id))
    db.close()

def my_businesses(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    businesses = db.get_businesses(user['id'])
    if not businesses:
        bot.send_message(message.chat.id, "No businesses found.", 
                        reply_markup=get_main_menu(message.from_user.id))
    else:
        response = "Your businesses:\n" + "\n".join([b['business_name'] for b in businesses])
        bot.send_message(message.chat.id, response, reply_markup=get_main_menu(message.from_user.id))
    db.close()

def check_sub(message):
    db = Database()
    user = db.get_user(message.from_user.id)
    if user and user['is_active']:
        bot.send_message(message.chat.id, f"Subscription: {user['subscription_type']}\nExpires: {user['subscription_end']}", 
                         reply_markup=get_main_menu(message.from_user.id))
    else:
        bot.send_message(message.chat.id, f"No active subscription. Contact {MARKETER_USERNAME} for payment.", 
                         reply_markup=get_subscription_menu())
    db.close()

def get_subscription_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Daily - $5", callback_data="sub_daily"))
    markup.add(types.InlineKeyboardButton("Weekly - $20", callback_data="sub_weekly"))
    markup.add(types.InlineKeyboardButton("Monthly - $50", callback_data="sub_monthly"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_'))
def handle_subscription(call):
    sub_type = call.data.split('_')[1]
    price = SUBSCRIPTION_PRICES[sub_type]
    bot.send_message(call.message.chat.id, f"To subscribe {sub_type}, pay ${price} to {MARKETER_USERNAME} and send proof to admin.")

def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Activate User", callback_data="admin_activate"))
    markup.add(types.InlineKeyboardButton("List Users", callback_data="admin_list"))
    bot.send_message(message.chat.id, "Admin Panel", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_action(call):
    db = Database()
    if call.data == "admin_list":
        users = db.get_all_users()
        response = "Users:\n" + "\n".join([f"ID: {u['telegram_id']}, Sub: {u['subscription_type'] or 'None'}" for u in users])
        bot.send_message(call.message.chat.id, response)
    elif call.data == "admin_activate":
        bot.send_message(call.message.chat.id, "Please send: telegram_id,sub_type,duration (e.g., 123456789,daily,1)")
        bot.register_next_step_handler(call.message, process_activate_user)
    db.close()

def process_activate_user(message):
    db = Database()
    try:
        telegram_id, sub_type, duration = message.text.split(',')
        duration = int(duration)
        if sub_type not in SUBSCRIPTION_PRICES:
            bot.send_message(message.chat.id, "Error: invalid subscription type")
            db.close()
            return
        db.activate_subscription(int(telegram_id), sub_type, duration)
        bot.send_message(message.chat.id, f"Activated {sub_type} for user {telegram_id} until {duration} days from now.", 
                        reply_markup=get_main_menu(message.from_user.id))
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
    db.close()

bot.polling()
