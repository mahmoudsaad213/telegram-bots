# database.py - محدث لحل مشاكل الاتصال
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import sys

# استيراد إعدادات قاعدة البيانات
try:
    from config import DATABASE_URL, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
except ImportError:
    print("❌ خطأ في استيراد إعدادات قاعدة البيانات")
    sys.exit(1)

class Database:
    def __init__(self, max_retries=3, retry_delay=2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """الاتصال بقاعدة البيانات مع إعادة المحاولة"""
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔄 محاولة الاتصال بقاعدة البيانات (المحاولة {attempt}/{self.max_retries})")
                
                # استخدام DATABASE_URL إذا كان متوفراً (الطريقة المفضلة لـ Railway)
                if 'DATABASE_URL' in globals() and DATABASE_URL:
                    print("🔗 الاتصال باستخدام DATABASE_URL")
                    self.conn = psycopg2.connect(DATABASE_URL)
                else:
                    print("🔗 الاتصال باستخدام البيانات المنفصلة")
                    self.conn = psycopg2.connect(
                        host=DB_HOST,
                        port=DB_PORT,
                        dbname=DB_NAME,
                        user=DB_USER,
                        password=DB_PASSWORD,
                        sslmode='require'  # مطلوب للاتصال الآمن مع Railway
                    )
                
                # اختبار الاتصال
                self.conn.set_session(autocommit=False)
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                
                # اختبار بسيط للاتصال
                self.cursor.execute("SELECT 1")
                self.cursor.fetchone()
                
                print("✅ تم الاتصال بقاعدة البيانات بنجاح")
                self.create_tables()
                return
                
            except psycopg2.OperationalError as e:
                print(f"❌ فشل الاتصال (المحاولة {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ انتظار {self.retry_delay} ثانية قبل المحاولة التالية...")
                    time.sleep(self.retry_delay)
                else:
                    print("❌ فشل في جميع محاولات الاتصال")
                    raise Exception(f"فشل الاتصال بقاعدة البيانات بعد {self.max_retries} محاولات: {e}")
            
            except Exception as e:
                print(f"❌ خطأ غير متوقع: {e}")
                raise

    def create_tables(self):
        """إنشاء الجداول المطلوبة"""
        try:
            print("🔧 إنشاء الجداول...")
            
            # إنشاء جدول المستخدمين
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    subscription_type TEXT,
                    subscription_start TIMESTAMP,
                    subscription_end TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # إنشاء جدول الكومبوهات
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS combos (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    combo TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # إنشاء جدول الأعمال
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    business_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # إنشاء فهارس لتحسين الأداء
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_combos_user_id ON combos(user_id);
                CREATE INDEX IF NOT EXISTS idx_businesses_user_id ON businesses(user_id);
            """)
            
            self.conn.commit()
            print("✅ تم إنشاء الجداول بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {e}")
            self.conn.rollback()
            raise

    def execute_with_retry(self, query, params=None, fetch=False):
        """تنفيذ استعلام مع إعادة المحاولة في حالة انقطاع الاتصال"""
        for attempt in range(1, 3):  # محاولتان فقط للاستعلامات
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                
                if fetch:
                    if 'fetchall' in str(fetch):
                        return self.cursor.fetchall()
                    else:
                        return self.cursor.fetchone()
                
                self.conn.commit()
                return True
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                print(f"❌ انقطع الاتصال، محاولة إعادة الاتصال... (المحاولة {attempt})")
                if attempt < 2:
                    try:
                        self.connect()  # إعادة الاتصال
                    except:
                        pass
                else:
                    raise e
            except Exception as e:
                self.conn.rollback()
                raise e

    def add_user(self, telegram_id, username):
        """إضافة مستخدم جديد"""
        try:
            query = """
                INSERT INTO users (telegram_id, username)
                VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET
                username = EXCLUDED.username
            """
            self.execute_with_retry(query, (telegram_id, username))
            print(f"✅ تم إضافة/تحديث المستخدم {telegram_id}")
        except Exception as e:
            print(f"❌ خطأ في إضافة المستخدم {telegram_id}: {e}")

    def get_user(self, telegram_id):
        """الحصول على بيانات المستخدم"""
        try:
            query = "SELECT * FROM users WHERE telegram_id = %s"
            return self.execute_with_retry(query, (telegram_id,), fetch=True)
        except Exception as e:
            print(f"❌ خطأ في جلب المستخدم {telegram_id}: {e}")
            return None

    def add_combo(self, user_id, combo):
        """إضافة كومبو جديد"""
        try:
            query = "INSERT INTO combos (user_id, combo) VALUES (%s, %s)"
            self.execute_with_retry(query, (user_id, combo))
        except Exception as e:
            print(f"❌ خطأ في إضافة الكومبو: {e}")

    def get_combos(self, user_id):
        """الحصول على كومبوهات المستخدم"""
        try:
            query = "SELECT * FROM combos WHERE user_id = %s"
            return self.execute_with_retry(query, (user_id,), fetch='fetchall') or []
        except Exception as e:
            print(f"❌ خطأ في جلب الكومبوهات: {e}")
            return []

    def add_business(self, user_id, business_name):
        """إضافة عمل جديد"""
        try:
            query = "INSERT INTO businesses (user_id, business_name) VALUES (%s, %s)"
            self.execute_with_retry(query, (user_id, business_name))
        except Exception as e:
            print(f"❌ خطأ في إضافة العمل: {e}")

    def get_businesses(self, user_id):
        """الحصول على أعمال المستخدم"""
        try:
            query = "SELECT * FROM businesses WHERE user_id = %s ORDER BY created_at DESC"
            return self.execute_with_retry(query, (user_id,), fetch='fetchall') or []
        except Exception as e:
            print(f"❌ خطأ في جلب الأعمال: {e}")
            return []

    def get_all_users(self):
        """الحصول على جميع المستخدمين (للمدير)"""
        try:
            query = "SELECT * FROM users ORDER BY created_at DESC"
            return self.execute_with_retry(query, fetch='fetchall') or []
        except Exception as e:
            print(f"❌ خطأ في جلب المستخدمين: {e}")
            return []

    def activate_subscription(self, telegram_id, sub_type, duration_days):
        """تفعيل اشتراك المستخدم"""
        try:
            query = """
                UPDATE users
                SET subscription_type = %s,
                    subscription_start = CURRENT_TIMESTAMP,
                    subscription_end = CURRENT_TIMESTAMP + INTERVAL '%s days',
                    is_active = TRUE
                WHERE telegram_id = %s
            """
            self.execute_with_retry(query, (sub_type, duration_days, telegram_id))
            print(f"✅ تم تفعيل اشتراك {sub_type} للمستخدم {telegram_id}")
        except Exception as e:
            print(f"❌ خطأ في تفعيل الاشتراك: {e}")

    def check_subscription_status(self):
        """فحص وتحديث حالة الاشتراكات المنتهية"""
        try:
            query = """
                UPDATE users 
                SET is_active = FALSE 
                WHERE subscription_end < CURRENT_TIMESTAMP AND is_active = TRUE
            """
            self.execute_with_retry(query)
            print("✅ تم فحص وتحديث حالة الاشتراكات")
        except Exception as e:
            print(f"❌ خطأ في فحص الاشتراكات: {e}")

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            print("✅ تم إغلاق اتصال قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في إغلاق الاتصال: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
