import asyncpg
import asyncio
from datetime import datetime, timedelta
from config import DATABASE_URL
import logging

class Database:
    def __init__(self):
        self.pool = None
        
    async def init_pool(self):
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'fb_business_bot',
                }
            )
            await self.create_tables()
            logging.info("✅ Database connected successfully")
        except Exception as e:
            logging.error(f"❌ Database connection error: {e}")
            raise
            
    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    subscription_end TIMESTAMP,
                    subscription_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Business records table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS businesses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    business_id TEXT,
                    invitation_link TEXT,
                    status TEXT DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tasks table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    cookies TEXT,
                    status TEXT DEFAULT 'pending',
                    total_accounts INTEGER DEFAULT 0,
                    completed_accounts INTEGER DEFAULT 0,
                    successful_businesses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
    
    async def add_user(self, user_id, username=None, first_name=None):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name) 
                    VALUES ($1, $2, $3) 
                    ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
                ''', user_id, username, first_name)
        except Exception as e:
            logging.error(f"Error adding user {user_id}: {e}")
    
    async def check_subscription(self, user_id):
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    'SELECT subscription_end FROM users WHERE user_id = $1', 
                    user_id
                )
                if not row or not row['subscription_end']:
                    return False
                return row['subscription_end'] > datetime.now()
        except Exception as e:
            logging.error(f"Error checking subscription for {user_id}: {e}")
            return False
    
    async def add_subscription(self, user_id, subscription_type):
        try:
            days = {'daily': 1, 'weekly': 7, 'monthly': 30}
            end_date = datetime.now() + timedelta(days=days[subscription_type])
            
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE users SET 
                    subscription_end = $1, 
                    subscription_type = $2 
                    WHERE user_id = $3
                ''', end_date, subscription_type, user_id)
        except Exception as e:
            logging.error(f"Error adding subscription for {user_id}: {e}")
    
    async def add_business(self, user_id, business_id, invitation_link):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO businesses (user_id, business_id, invitation_link) 
                    VALUES ($1, $2, $3)
                ''', user_id, business_id, invitation_link)
        except Exception as e:
            logging.error(f"Error adding business for {user_id}: {e}")
    
    async def create_task(self, user_id, cookies, total_accounts):
        try:
            async with self.pool.acquire() as conn:
                task_id = await conn.fetchval('''
                    INSERT INTO tasks (user_id, cookies, total_accounts) 
                    VALUES ($1, $2, $3) RETURNING id
                ''', user_id, cookies, total_accounts)
                return task_id
        except Exception as e:
            logging.error(f"Error creating task for {user_id}: {e}")
            return None
    
    async def update_task(self, task_id, completed=None, successful=None, status=None):
        try:
            async with self.pool.acquire() as conn:
                if completed is not None:
                    await conn.execute(
                        'UPDATE tasks SET completed_accounts = $1 WHERE id = $2', 
                        completed, task_id
                    )
                if successful is not None:
                    await conn.execute(
                        'UPDATE tasks SET successful_businesses = $1 WHERE id = $2', 
                        successful, task_id
                    )
                if status is not None:
                    await conn.execute(
                        'UPDATE tasks SET status = $1 WHERE id = $2', 
                        status, task_id
                    )
        except Exception as e:
            logging.error(f"Error updating task {task_id}: {e}")
    
    async def get_user_stats(self, user_id):
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow('''
                    SELECT 
                        COUNT(DISTINCT t.id) as total_tasks,
                        COUNT(b.id) as total_businesses,
                        u.subscription_end,
                        u.subscription_type
                    FROM users u
                    LEFT JOIN tasks t ON u.user_id = t.user_id
                    LEFT JOIN businesses b ON u.user_id = b.user_id
                    WHERE u.user_id = $1
                    GROUP BY u.user_id, u.subscription_end, u.subscription_type
                ''', user_id)
        except Exception as e:
            logging.error(f"Error getting stats for {user_id}: {e}")
            return None
    
    async def close(self):
        """Gracefully close database connections"""
        if self.pool:
            try:
                await self.pool.close()
                logging.info("✅ Database connections closed")
            except Exception as e:
                logging.error(f"Error closing database: {e}")

db = Database()

