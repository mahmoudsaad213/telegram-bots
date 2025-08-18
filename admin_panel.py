from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import db

class AdminPanel:
    async def show_admin_panel(self, query):
        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("💎 إدارة الاشتراكات", callback_data="admin_subs")],
            [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👑 *لوحة تحكم الأدمن* 👑\n\nاختر خيارًا:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def show_bot_stats(self, query):
        stats = await db.get_bot_stats()
        message = (
            f"📊 *إحصائيات البوت* 📊\n\n"
            f"👥 إجمالي المستخدمين: {stats['total_users']}\n"
            f"🏢 إجمالي الأعمال: {stats['total_businesses']}\n"
            f"📋 إجمالي المهام: {stats['total_tasks']}\n"
            f"💎 المشتركين النشطين: {stats['active_subscribers']}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def show_user_management(self, query, page=1, per_page=5):
        users = await db.get_users_list(page, per_page)
        message = "👥 *إدارة المستخدمين* 👥\n\n"
        keyboard = []

        for user in users:
            sub_status = "✅ نشط" if user['subscription_end'] and user['subscription_end'] > datetime.now() else "❌ غير نشط"
            days_left = (user['subscription_end'] - datetime.now()).days if user['subscription_end'] else 0
            message += (
                f"🆔 ID: `{user['user_id']}`\n"
                f"👤 @{user['username'] or 'غير معروف'}\n"
                f"💎 الاشتراك: {sub_status} ({days_left} أيام متبقية)\n"
                f"🏢 الأعمال: {user['total_businesses']}\n\n"
            )
            keyboard.append([
                InlineKeyboardButton(f"🚫 حظر @{user['username'] or user['user_id']}", callback_data=f"ban_user_{user['user_id']}"),
                InlineKeyboardButton(f"🗑 إلغاء اشتراك", callback_data=f"cancel_sub_{user['user_id']}")
            ])

        # إضافة أزرار التصفح
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_users_{page-1}"))
        if len(users) == per_page:
            nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"admin_users_{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

    async def ban_user(self, query, user_id):
        await db.ban_user(user_id)
        await query.edit_message_text(
            f"🚫 تم حظر المستخدم `{user_id}` بنجاح!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")]])
        )

    async def cancel_subscription(self, query, user_id):
        await db.cancel_subscription(user_id)
        await query.edit_message_text(
            f"🗑 تم إلغاء اشتراك المستخدم `{user_id}` بنجاح!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")]])
        )

    async def show_subscriptions(self, query):
        subs = await db.get_active_subscriptions()
        message = "💎 *الاشتراكات النشطة* 💎\n\n"
        keyboard = []

        for sub in subs:
            days_left = (sub['subscription_end'] - datetime.now()).days
            message += (
                f"🆔 ID: `{sub['user_id']}`\n"
                f"👤 @{sub['username'] or 'غير معروف'}\n"
                f"📅 نوع الاشتراك: {sub['subscription_type']}\n"
                f"⏳ متبقي: {days_left} يوم\n\n"
            )
            keyboard.append([InlineKeyboardButton(f"🗑 إلغاء اشتراك", callback_data=f"cancel_sub_{sub['user_id']}")])

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
