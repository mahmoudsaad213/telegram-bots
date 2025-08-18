from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import db

class AdminPanel:
    async def show_admin_panel(self, query):
        keyboard = [
            [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("💎 Subscriptions", callback_data="admin_subs")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👑 *Admin Panel*\n\nSelect an option:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
