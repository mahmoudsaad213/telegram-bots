import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("Database connected successfully.")
            self.create_tables()
        except psycopg2.OperationalError as e:
            print(f"❌ Failed to connect to database: {e}")
            raise Exception(f"Database connection error: {e}")

    def create_tables(self):
        print("Creating tables...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                subscription_type TEXT,
                subscription_start TIMESTAMP,
                subscription_end TIMESTAMP,
                is_active BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS combos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                combo TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS businesses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                business_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
        print("Tables created successfully.")

    def add_user(self, telegram_id, username):
        try:
            self.cursor.execute("""
                INSERT INTO users (telegram_id, username)
                VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO NOTHING
            """, (telegram_id, username))
            self.conn.commit()
            print(f"User {telegram_id} added or already exists.")
        except Exception as e:
            print(f"Error adding user {telegram_id}: {e}")
            self.conn.rollback()

    def get_user(self, telegram_id):
        self.cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        return self.cursor.fetchone()

    def add_combo(self, user_id, combo):
        self.cursor.execute("""
            INSERT INTO combos (user_id, combo)
            VALUES (%s, %s)
        """, (user_id, combo))
        self.conn.commit()

    def get_combos(self, user_id):
        self.cursor.execute("SELECT * FROM combos WHERE user_id = %s", (user_id,))
        return self.cursor.fetchall()

    def add_business(self, user_id, business_name):
        self.cursor.execute("""
            INSERT INTO businesses (user_id, business_name)
            VALUES (%s, %s)
        """, (user_id, business_name))
        self.conn.commit()

    def get_businesses(self, user_id):
        self.cursor.execute("SELECT * FROM businesses WHERE user_id = %s", (user_id,))
        return self.cursor.fetchall()

    def get_all_users(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def activate_subscription(self, telegram_id, sub_type, duration_days):
        try:
            self.cursor.execute("""
                UPDATE users
                SET subscription_type = %s,
                    subscription_start = CURRENT_TIMESTAMP,
                    subscription_end = CURRENT_TIMESTAMP + INTERVAL '%s days',
                    is_active = TRUE
                WHERE telegram_id = %s
            """, (sub_type, duration_days, telegram_id))
            self.conn.commit()
            print(f"Activated {sub_type} subscription for user {telegram_id}.")
        except Exception as e:
            print(f"Error activating subscription for {telegram_id}: {e}")
            self.conn.rollback()

    def close(self):
        self.cursor.close()
        self.conn.close()
        print("Database connection closed.")
