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
    bot.send_message(message.chat.id, "Welcome to Facebook Business Creator Bot!\\nPlease subscribe to use the features.", 
                     reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📝 Add Combo":
        bot.send_message(message.chat.id, "Please send the combos...")
        # Add your combo handling logic here
    elif message.text == "🚀 Create Businesses":
        # THIS IS THE CORRECTED LINE
        result = create_business.process_combo(message.from_user.id)
        bot.send_message(message.chat.id, result)
    elif message.text == "📊 My Businesses":
        # Add your businesses handling logic here
        bot.send_message(message.chat.id, "Showing your businesses...")
    elif message.text == "🔍 Check Subscription":
        # Add your subscription handling logic here
        bot.send_message(message.chat.id, "Checking your subscription...")
    elif message.text == "🛠 Admin Panel" and is_admin(message.from_user.id):
        handle_admin_panel(message)
    else:
        bot.send_message(message.chat.id, "Unknown command. Please use the menu buttons.")
    
@bot.message_handler(func=lambda message: message.text and message.text.startswith("Add Combo"))
def add_combo_handler(message):
    # This part handles the combo adding logic
    pass

@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
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
        bot.send_message(message.chat.id, f"Subscription for user {telegram_id} has been activated.")
    except ValueError:
        bot.send_message(message.chat.id, "Error: invalid format. Please try again.")
    finally:
        db.close()

bot.infinity_polling()
