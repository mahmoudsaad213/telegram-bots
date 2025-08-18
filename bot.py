import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from database import db
from business_creator import BusinessCreator
from admin_panel import AdminPanel
from config import BOT_TOKEN, ADMIN_ID, PRICES

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class FBBusinessBot:
    def __init__(self):
        self.creator = BusinessCreator()
        self.admin = AdminPanel()
        self.application = None
        self.is_running = False
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        
        await db.add_user(user_id, username, first_name)
        
        keyboard = [
            [InlineKeyboardButton("🚀 ابدأ الإنشاء", callback_data="create_business")],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
            [InlineKeyboardButton("💎 اشتراك", callback_data="subscribe")]
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎉 *مرحبًا بك في بوت إنشاء الأعمال!* 🎉\n\n"
            "✨ إنشاء أعمال فيسبوك غير محدودة\n"
            "📧 تكامل تلقائي مع TempMail\n"
            "🔗 روابط دعوة فورية\n\n"
            "اختر خيارًا:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "create_business":
            has_subscription = await db.check_subscription(user_id)
            if not has_subscription and user_id != ADMIN_ID:
                keyboard = [[InlineKeyboardButton("💎 اشترك الآن", callback_data="subscribe")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ *الاشتراك مطلوب*\n\n"
                    "تحتاج إلى اشتراك نشط لاستخدام هذه الخدمة.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            await query.edit_message_text(
                "📝 *أرسل الكوكيز*\n\n"
                "أرسل كوكيز فيسبوك (واحد لكل سطر للحسابات المتعددة):\n\n"
                "الصيغة: `cookie1=value1; cookie2=value2; ...`",
                parse_mode='Markdown'
            )
            context.user_data['waiting_cookies'] = True
        
        elif data == "my_stats":
            stats = await db.get_user_stats(user_id)
            if stats:
                sub_text = "❌ لا يوجد اشتراك نشط"
                if stats['subscription_end']:
                    sub_text = f"✅ {stats['subscription_type']} - حتى {stats['subscription_end'].strftime('%Y-%m-%d')}"
                
                await query.edit_message_text(
                    f"📊 *إحصائياتك* 📊\n\n"
                    f"🏢 إجمالي الأعمال: {stats['total_businesses'] or 0}\n"
                    f"📋 إجمالي المهام: {stats['total_tasks'] or 0}\n"
                    f"💎 الاشتراك: {sub_text}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]])
                )
        
        elif data == "subscribe":
            keyboard = [
                [InlineKeyboardButton("💸 يومي - $1", callback_data="buy_daily")],
                [InlineKeyboardButton("💰 أسبوعي - $5", callback_data="buy_weekly")],
                [InlineKeyboardButton("💎 شهري - $15", callback_data="buy_monthly")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "💎 *اختر خطة الاشتراك* 💎\n\n"
                "🔸 يومي: وصول لمدة 24 ساعة\n"
                "🔸 أسبوعي: وصول لمدة 7 أيام + دعم مميز\n"
                "🔸 شهري: وصول لمدة 30 يوم + تحليلات متقدمة\n\n"
                "اضغط على الزر للاشتراك مباشرة:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif data.startswith("buy_"):
            plan_type = data.replace("buy_", "")
            price = PRICES[plan_type]
            
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=f"اشتراك {plan_type.title()}",
                description=f"وصول لـ {plan_type} لخدمة إنشاء الأعمال على فيسبوك",
                payload=f"subscription_{plan_type}_{user_id}",
                provider_token="",  # Telegram Stars
                currency="XTR",
                prices=[LabeledPrice("اشتراك", price)],
                photo_url="https://example.com/subscription_image.jpg",
                photo_width=512,
                photo_height=512
            )
        
        elif data == "admin_panel" and user_id == ADMIN_ID:
            await self.admin.show_admin_panel(query)
        
        elif data == "admin_stats":
            await self.admin.show_bot_stats(query)
        
        elif data.startswith("admin_users"):
            page = int(data.split("_")[-1]) if "_" in data else 1
            await self.admin.show_user_management(query, page)
        
        elif data.startswith("ban_user_"):
            target_user_id = int(data.split("_")[-1])
            await self.admin.ban_user(query, target_user_id)
        
        elif data.startswith("cancel_sub_"):
            target_user_id = int(data.split("_")[-1])
            await self.admin.cancel_subscription(query, target_user_id)
        
        elif data == "admin_subs":
            await self.admin.show_subscriptions(query)
        
        elif data == "back_to_start":
            keyboard = [
                [InlineKeyboardButton("🚀 ابدأ الإنشاء", callback_data="create_business")],
                [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
                [InlineKeyboardButton("💎 اشتراك", callback_data="subscribe")]
            ]
            if user_id == ADMIN_ID:
                keyboard.append([InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🎉 *مرحبًا بك في بوت إنشاء الأعمال!* 🎉\n\n"
                "اختر خيارًا:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get('waiting_cookies'):
            context.user_data['waiting_cookies'] = False
            cookies_text = update.message.text.strip()
            
            user_id = update.effective_user.id
            has_subscription = await db.check_subscription(user_id)
            
            if not has_subscription and user_id != ADMIN_ID:
                await update.message.reply_text("❌ الاشتراك مطلوب!")
                return
            
            cookies_list = [c.strip() for c in cookies_text.split('\n') if c.strip()]
            
            await update.message.reply_text(
                f"🔄 *بدأت المعالجة* 🔄\n\n"
                f"📝 إجمالي الحسابات: {len(cookies_list)}\n"
                f"⏳ يرجى الانتظار...",
                parse_mode='Markdown'
            )
            
            task_id = await db.create_task(user_id, cookies_text, len(cookies_list))
            
            asyncio.create_task(self.process_cookies(user_id, cookies_list, task_id))
    
    async def process_cookies(self, user_id, cookies_list, task_id):
        successful_businesses = []
        
        for i, cookies in enumerate(cookies_list, 1):
            try:
                success, biz_id, invitation_link, message = await self.creator.create_business(cookies)
                
                if success == "LIMIT_REACHED":
                    await db.update_task(task_id, status="limit_reached")
                    break
                elif success:
                    successful_businesses.append({
                        'business_id': biz_id,
                        'invitation_link': invitation_link
                    })
                    await db.add_business(user_id, biz_id, invitation_link)
                
                await db.update_task(task_id, completed=i, successful=len(successful_businesses))
                
            except Exception as e:
                logging.error(f"Error processing cookies {i}: {e}")
            
            await asyncio.sleep(random.randint(3, 8))
        
        if successful_businesses:
            message = f"🎉 *اكتملت المهمة بنجاح!* 🎉\n\n"
            message += f"✅ تم إنشاء: {len(successful_businesses)} أعمال\n\n"
            
            for i, business in enumerate(successful_businesses, 1):
                message += f"*العمل #{i}*\n"
                message += f"🆔 المعرف: `{business['business_id']}`\n"
                message += f"🔗 [رابط الدعوة]({business['invitation_link']})\n\n"
            
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 اكتملت المهمة! تم إنشاء {len(successful_businesses)} أعمال. تحقق من إحصائياتك للتفاصيل.",
                )
        
        await db.update_task(task_id, status="completed")
    
    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.pre_checkout_query
        await query.answer(ok=True)
    
    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        payload = update.message.successful_payment.invoice_payload
        user_id = update.effective_user.id
        plan_type = payload.split('_')[1]
        
        await db.add_subscription(user_id, plan_type)
        
        await update.message.reply_text(
            f"🎉 *تم تفعيل الاشتراك!* 🎉\n\n"
            f"💎 الخطة: {plan_type.title()}\n"
            f"🚀 يمكنك الآن إنشاء أعمال فيسبوك غير محدودة!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 ابدأ الآن", callback_data="create_business")]])
        )
    
    def run(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(PreCheckoutQueryHandler(self.precheckout_callback))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_callback))
        
        logging.info("🤖 Bot started successfully!")
        
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
        except Exception as e:
            logging.error(f"Bot polling error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        if self.application and self.is_running:
            logging.info("🛑 Shutting down bot...")
            try:
                if hasattr(self.application, 'stop'):
                    self.application.stop()
                if hasattr(self.application, 'shutdown'):
                    self.application.shutdown()
            except Exception as e:
                logging.error(f"Error during bot shutdown: {e}")
            finally:
                self.is_running = False
                logging.info("✅ Bot shutdown completed")
