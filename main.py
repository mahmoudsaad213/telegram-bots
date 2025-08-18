import asyncio
import logging
import signal
import sys
from bot import FBBusinessBot
from database import db

# Global bot instance for cleanup
bot_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
    if bot_instance:
        bot_instance.shutdown()
    sys.exit(0)

async def init_app():
    """Initialize the application"""
    try:
        await db.init_pool()
        logging.info("✅ Database initialized")
        return True
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main entry point"""
    global bot_instance
    
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize database in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initialize database
        init_success = loop.run_until_complete(init_app())
        if not init_success:
            return
        
        # Create and start bot
        bot_instance = FBBusinessBot()
        logging.info("🤖 Starting bot...")
        bot_instance.run()
        
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
    except Exception as e:
        logging.error(f"❌ Critical error: {e}")
    finally:
        # Cleanup
        try:
            if db.pool:
                loop.run_until_complete(db.close())
            loop.close()
        except:
            pass
        logging.info("✅ Cleanup completed")

if __name__ == "__main__":
    main()
