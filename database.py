# database.py

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                subscription_type VARCHAR(50),
                subscription_start TIMESTAMP,
                subscription_end TIMESTAMP,
                is_active BOOLEAN DEFAULT FALSE
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS combos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                cookies TEXT NOT NULL,
                creations_count INTEGER DEFAULT 0,
                last_used TIMESTAMP
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id SERIAL PRIMARY KEY,
                combo_id INTEGER REFERENCES combos(id),
                business_id VARCHAR(255),
                invitation_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def add_user(self, telegram_id, username):
        self.cursor.execute("""
            INSERT INTO users (telegram_id, username)
            VALUES (%s, %s)
            ON CONFLICT (telegram_id) DO NOTHING
        """, (telegram_id, username))
        self.conn.commit()

    def get_user(self, telegram_id):
        self.cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        return self.cursor.fetchone()

    def activate_subscription(self, telegram_id, sub_type, start, end):
        self.cursor.execute("""
            UPDATE users SET 
                subscription_type = %s,
                subscription_start = %s,
                subscription_end = %s,
                is_active = TRUE
            WHERE telegram_id = %s
        """, (sub_type, start, end, telegram_id))
        self.conn.commit()

    def is_subscribed(self, telegram_id):
        user = self.get_user(telegram_id)
        if user and user['is_active']:
            from datetime import datetime
            return datetime.now() < user['subscription_end']
        return False

    def add_combo(self, user_id, cookies):
        self.cursor.execute("""
            INSERT INTO combos (user_id, cookies)
            VALUES (%s, %s)
        """, (user_id, cookies))
        self.conn.commit()

    def get_user_combos(self, user_id):
        self.cursor.execute("SELECT * FROM combos WHERE user_id = %s", (user_id,))
        return self.cursor.fetchall()

    def increment_creations(self, combo_id):
        self.cursor.execute("""
            UPDATE combos SET creations_count = creations_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (combo_id,))
        self.conn.commit()

    def add_business(self, combo_id, business_id, invitation_link):
        self.cursor.execute("""
            INSERT INTO businesses (combo_id, business_id, invitation_link)
            VALUES (%s, %s, %s)
        """, (combo_id, business_id, invitation_link))
        self.conn.commit()

    def get_user_businesses(self, user_id):
        self.cursor.execute("""
            SELECT b.* FROM businesses b
            JOIN combos c ON b.combo_id = c.id
            WHERE c.user_id = %s
        """, (user_id,))
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
