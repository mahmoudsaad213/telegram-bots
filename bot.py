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
            [InlineKeyboardButton("🚀 Start Creating", callback_data="create_business")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("💎 Subscribe", callback_data="subscribe")]
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎉 *Welcome to Facebook Business Creator Bot!*\n\n"
            "✨ Create unlimited Facebook business accounts\n"
            "📧 Auto TempMail integration\n"
            "🔗 Get invitation links instantly\n\n"
            "Choose an option below:",
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
                keyboard = [[InlineKeyboardButton("💎 Subscribe Now", callback_data="subscribe")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ *Subscription Required*\n\n"
                    "You need an active subscription to use this service.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            await query.edit_message_text(
                "📝 *Send Your Cookies*\n\n"
                "Send your Facebook cookies (one per line for multiple accounts):\n\n"
                "Format: `cookie1=value1; cookie2=value2; ...`",
                parse_mode='Markdown'
            )
            context.user_data['waiting_cookies'] = True
        
        elif data == "my_stats":
            stats = await db.get_user_stats(user_id)
            if stats:
                sub_text = "❌ No active subscription"
                if stats['subscription_end']:
                    sub_text = f"✅ {stats['subscription_type']} - Until {stats['subscription_end'].strftime('%Y-%m-%d')}"
                
                await query.edit_message_text(
                    f"📊 *Your Statistics*\n\n"
                    f"🏢 Total Businesses: {stats['total_businesses'] or 0}\n"
                    f"📋 Total Tasks: {stats['total_tasks'] or 0}\n"
                    f"💎 Subscription: {sub_text}",
                    parse_mode='Markdown'
                )
        
        elif data == "subscribe":
            keyboard = [
                [InlineKeyboardButton("1 Day - $1", callback_data="buy_daily")],
                [InlineKeyboardButton("1 Week - $5", callback_data="buy_weekly")],
                [InlineKeyboardButton("1 Month - $15", callback_data="buy_monthly")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "💎 *Choose Subscription Plan*\n\n"
                "🔸 Daily: Access for 24 hours\n"
                "🔸 Weekly: Access for 7 days\n"
                "🔸 Monthly: Access for 30 days",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif data.startswith("buy_"):
            plan_type = data.replace("buy_", "")
            price = PRICES[plan_type]
            
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=f"{plan_type.title()} Subscription",
                description=f"Facebook Business Creator - {plan_type} access",
                payload=f"subscription_{plan_type}_{user_id}",
                provider_token="",  # Telegram Stars
                currency="XTR",
                prices=[LabeledPrice("Subscription", price)]
            )
        
        elif data == "admin_panel" and user_id == ADMIN_ID:
            await self.admin.show_admin_panel(query)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get('waiting_cookies'):
            context.user_data['waiting_cookies'] = False
            cookies_text = update.message.text.strip()
            
            user_id = update.effective_user.id
            has_subscription = await db.check_subscription(user_id)
            
            if not has_subscription and user_id != ADMIN_ID:
                await update.message.reply_text("❌ Subscription required!")
                return
            
            # Process cookies
            cookies_list = [c.strip() for c in cookies_text.split('\n') if c.strip()]
            
            await update.message.reply_text(
                f"🔄 *Processing Started*\n\n"
                f"📝 Total Accounts: {len(cookies_list)}\n"
                f"⏳ Please wait...",
                parse_mode='Markdown'
            )
            
            # Create task
            task_id = await db.create_task(user_id, cookies_text, len(cookies_list))
            
            # Process in background
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
            
            # Small delay between requests
            await asyncio.sleep(random.randint(3, 8))
        
        # Send final results
        if successful_businesses:
            message = f"🎉 *Task Completed Successfully!*\n\n"
            message += f"✅ Created: {len(successful_businesses)} businesses\n\n"
            
            for i, business in enumerate(successful_businesses, 1):
                message += f"*Business #{i}*\n"
                message += f"🆔 ID: `{business['business_id']}`\n"
                message += f"🔗 [Invitation Link]({business['invitation_link']})\n\n"
            
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except:
                # Fallback if message is too long
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Task completed! Created {len(successful_businesses)} businesses. Check your stats for details.",
                )
        
        await db.update_task(task_id, status="completed")
    
    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.pre_checkout_query
        await query.answer(ok=True)
    
    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        payload = update.message.successful_payment.invoice_payload
        user_id = update.effective_user.id
        
        # Extract subscription type from payload
        plan_type = payload.split('_')[1]  # subscription_daily_12345 -> daily
        
        await db.add_subscription(user_id, plan_type)
        
        await update.message.reply_text(
            f"✅ *Subscription Activated!*\n\n"
            f"💎 Plan: {plan_type.title()}\n"
            f"🎉 You can now create unlimited Facebook businesses!",
            parse_mode='Markdown'
        )
    
    def run(self):
        """Start the bot with proper async handling"""
        if self.is_running:
            return
            
        self.is_running = True
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(PreCheckoutQueryHandler(self.precheckout_callback))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_callback))
        
        logging.info("🤖 Bot started successfully!")
        
        # Run with proper error handling
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
        """Gracefully shutdown the bot"""
        if self.application and self.is_running:
            logging.info("🛑 Shutting down bot...")
            try:
                # Stop the application gracefully
                if hasattr(self.application, 'stop'):
                    self.application.stop()
                if hasattr(self.application, 'shutdown'):
                    self.application.shutdown()
            except Exception as e:
                logging.error(f"Error during bot shutdown: {e}")
            finally:
                self.is_running = False
                logging.info("✅ Bot shutdown completed")
