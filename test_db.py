# test_db.py - اختبار الاتصال بقاعدة البيانات
import os
import sys

def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    print("🧪 بدء اختبار الاتصال بقاعدة البيانات...")
    
    # طباعة متغيرات البيئة (بدون كلمات المرور)
    print("\n📋 متغيرات البيئة:")
    print(f"PGHOST: {os.getenv('PGHOST', 'غير محدد')}")
    print(f"PGPORT: {os.getenv('PGPORT', 'غير محدد')}")
    print(f"PGDATABASE: {os.getenv('PGDATABASE', 'غير محدد')}")
    print(f"PGUSER: {os.getenv('PGUSER', 'غير محدد')}")
    print(f"PGPASSWORD: {'محدد' if os.getenv('PGPASSWORD') else 'غير محدد'}")
    print(f"DATABASE_URL: {'محدد' if os.getenv('DATABASE_URL') else 'غير محدد'}")
    
    try:
        # استيراد وإنشاء كائن قاعدة البيانات
        from database import Database
        
        print("\n🔄 إنشاء اتصال قاعدة البيانات...")
        db = Database()
        
        # اختبار إضافة مستخدم تجريبي
        print("\n🧪 اختبار إضافة مستخدم تجريبي...")
        test_user_id = 12345
        db.add_user(test_user_id, "test_user")
        
        # اختبار جلب المستخدم
        print("🧪 اختبار جلب المستخدم...")
        user = db.get_user(test_user_id)
        if user:
            print(f"✅ تم جلب المستخدم: {user}")
        else:
            print("❌ لم يتم العثور على المستخدم")
        
        # اختبار إضافة كومبو
        if user:
            print("🧪 اختبار إضافة كومبو...")
            db.add_combo(user['id'], "test@example.com:password123")
            
            # اختبار جلب الكومبوهات
            print("🧪 اختبار جلب الكومبوهات...")
            combos = db.get_combos(user['id'])
            print(f"✅ تم جلب {len(combos)} كومبو")
        
        # إغلاق الاتصال
        db.close()
        print("\n✅ جميع الاختبارات نجحت!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """اختبار متغيرات البيئة المطلوبة"""
    print("\n🧪 اختبار متغيرات البيئة...")
    
    required_vars = ['BOT_TOKEN']
    db_vars = ['PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    
    # اختبار المتغيرات المطلوبة
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # اختبار متغيرات قاعدة البيانات
    if not os.getenv('DATABASE_URL'):
        for var in db_vars:
            if not os.getenv(var):
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ متغيرات البيئة المفقودة: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ جميع متغيرات البيئة متوفرة")
        return True

if __name__ == "__main__":
    print("🚀 بدء اختبارات البوت...")
    
    # اختبار متغيرات البيئة
    env_ok = test_environment_variables()
    
    if env_ok:
        # اختبار قاعدة البيانات
        db_ok = test_database_connection()
        
        if db_ok:
            print("\n🎉 جميع الاختبارات نجحت! البوت جاهز للتشغيل.")
            sys.exit(0)
        else:
            print("\n💥 فشل اختبار قاعدة البيانات")
            sys.exit(1)
    else:
        print("\n💥 فشل اختبار متغيرات البيئة")
        sys.exit(1)
