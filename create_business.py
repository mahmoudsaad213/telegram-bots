# create_business.py - نسخة معدلة و محسنة

import re
import requests
import random
import json
import string
import time
from datetime import datetime
from urllib.parse import urlparse
from config import TEMPMAIL_BASE_URL, TEMPMAIL_HEADERS, MAX_CREATIONS_PER_COOKIE
from database import Database

def create_temp_email():
    """إنشاء بريد إلكتروني مؤقت جديد"""
    try:
        response = requests.post(f"{TEMPMAIL_BASE_URL}/addresses", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        email = data["data"]["email"]
        print(f"📧 تم إنشاء بريد إلكتروني مؤقت: {email}")
        return email
    except requests.RequestException as e:
        print(f"❌ خطأ في إنشاء البريد الإلكتروني: {e}")
        return None

def get_emails(email_address):
    """جلب الرسائل لبريد إلكتروني مؤقت"""
    try:
        response = requests.get(f"{TEMPMAIL_BASE_URL}/addresses/{email_address}/emails", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data["data"]
    except requests.RequestException as e:
        print(f"❌ خطأ في جلب الرسائل: {e}")
        return []

def read_email(email_uuid):
    """قراءة محتوى رسالة محددة"""
    try:
        response = requests.get(f"{TEMPMAIL_BASE_URL}/emails/{email_uuid}", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data["data"]
    except requests.RequestException as e:
        print(f"❌ خطأ في قراءة الرسالة: {e}")
        return None

def extract_invitation_link(email_body):
    """استخراج رابط الدعوة من محتوى الرسالة"""
    pattern = r'https://business\.facebook\.com/invitation/\?token=[^"\s]+'
    match = re.search(pattern, email_body)
    if match:
        return match.group(0)
    return None

def wait_for_invitation_email(email_address, timeout=300):
    """انتظار وصول رسالة دعوة واستخراج الرابط"""
    print(f"🔄 انتظار رسالة دعوة على: {email_address}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        emails = get_emails(email_address)
        if emails:
            for email_data in emails:
                if "facebook" in email_data.get('from', '').lower() or "invitation" in email_data.get('subject', '').lower():
                    print(f"📨 تم العثور على رسالة دعوة من: {email_data.get('from', 'N/A')}")
                    email_content = read_email(email_data['uuid'])
                    if email_content:
                        invitation_link = extract_invitation_link(email_content['body'])
                        if invitation_link:
                            print(f"🔗 تم استخراج رابط الدعوة!")
                            return invitation_link
        time.sleep(10)
    print("⏰ انتهى وقت الانتظار لرسالة الدعوة")
    return None

def generate_random_name():
    """إنشاء أسماء عشوائية واقعية"""
    first_names = ['Ahmed', 'Mohamed', 'Omar', 'Ali', 'Hassan', 'Mahmoud', 'Youssef', 'Khaled', 'Amr', 'Tamer', 
                   'John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Charles', 'Joseph', 'Thomas']
    last_names = ['Hassan', 'Mohamed', 'Ali', 'Ibrahim', 'Mahmoud', 'Youssef', 'Ahmed', 'Omar', 'Said', 'Farid',
                  'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    return random.choice(first_names), random.choice(last_names)

def generate_business_name():
    """إنشاء اسم عمل عشوائي"""
    business_prefixes = ['Tech', 'Digital', 'Smart', 'Pro', 'Elite', 'Global', 'Prime', 'Alpha', 'Meta', 'Cyber', 'Next', 'Future']
    business_suffixes = ['Solutions', 'Systems', 'Services', 'Group', 'Corp', 'Ltd', 'Inc', 'Agency', 'Studio', 'Labs', 'Works', 'Hub']
    random_num = random.randint(100, 999)
    name_formats = [
        f"{random.choice(business_prefixes)} {random.choice(business_suffixes)}",
        f"{random.choice(business_prefixes)}{random_num}",
        f"M{random_num} {random.choice(business_suffixes)}",
        f"Company {random_num}"
    ]
    return random.choice(name_formats)

def generate_random_user_agent():
    """إنشاء User-Agent عشوائي"""
    chrome_versions = ['131.0.0.0', '130.0.0.0', '129.0.0.0', '128.0.0.0']
    version = random.choice(chrome_versions)
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'

def extract_token_from_response(response):
    """استخراج رمز DTSGInitialData من الرد"""
    token_value = None
    pattern = re.compile(
        r'\["DTSGInitialData",\s*\[\],\s*\{\s*"token":\s*"([^"]+)"'
    )
    content = ""
    try:
        for chunk in response.iter_content(chunk_size=2048, decode_unicode=True):
            if chunk:
                content += chunk
                match = pattern.search(content)
                if match:
                    token_value = match.group(1)
                    return token_value
                if len(content) > 10000:
                    content = content[-1000:]
    except Exception as e:
        print(f"Error reading response: {e}")
    return token_value

def parse_cookies(cookies_input):
    """تحويل الكوكيز من نص إلى قاموس"""
    cookies = {}
    for part in cookies_input.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def get_user_id_from_cookies(cookies):
    """استخراج user ID من الكوكيز"""
    return cookies.get('c_user', "61573547480828")

def create_facebook_business_for_combo(cookies_input, db, combo_id, user_id):
    """
    إنشاء عمل تجاري على فيسبوك باستخدام الكوكيز.
    """
    print(f"\n🚀 بدء محاولة إنشاء عمل تجاري جديد للكومبو ID: {combo_id}")

    try:
        cookies = parse_cookies(cookies_input)
        user_agent = generate_random_user_agent()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # الخطوة 1: الوصول إلى Business Manager للحصول على الرمز
        print("1️⃣ جلب الرموز من صفحة Business Manager...")
        response = requests.get('https://business.facebook.com/overview/', headers=headers, cookies=cookies, stream=True, allow_redirects=True)
        token_value = extract_token_from_response(response)
        
        if not token_value:
            print("❌ فشل في استخراج رمز DTSG. قد تكون الكوكيز غير صالحة.")
            db.update_combo_status(combo_id, "invalid")
            return False, None, None

        # الخطوة 2: إرسال Mutation لإنشاء العمل التجاري
        print("2️⃣ إرسال طلب لإنشاء العمل التجاري...")

        business_name = generate_business_name()
        first_name, last_name = generate_random_name()
        admin_email = create_temp_email()

        if not admin_email:
            print("❌ فشل في إنشاء بريد إلكتروني مؤقت.")
            return False, None, None
            
        payload = {
            'fb_dtsg': token_value,
            'variables': json.dumps({
                'input': {
                    'name': business_name,
                    'is_primary_business': True,
                    'email': admin_email,
                    'onboarded_flow_entry_point': 'CLAIMED_BY_ONBOARDING',
                    'actor_id': get_user_id_from_cookies(cookies),
                    'client_mutation_id': str(int(time.time() * 1000))
                }
            }),
            'doc_id': '8746960145326508'
        }
        
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-FB-Friendly-Name': 'AdsBusinessAccountMutation',
            'Origin': 'https://business.facebook.com',
            'Referer': 'https://business.facebook.com/settings/info',
        })

        mutation_response = requests.post(
            'https://business.facebook.com/api/graphql/', 
            headers=headers, 
            cookies=cookies, 
            data=payload
        )
        
        mutation_response.raise_for_status()
        data = mutation_response.json()
        
        if 'errors' in data:
            error_message = data['errors'][0]['message']
            print(f"❌ خطأ في إنشاء العمل التجاري: {error_message}")
            if "limit reached" in error_message.lower():
                db.update_combo_status(combo_id, "limit_reached")
                return "LIMIT_REACHED", None, None
            else:
                return False, None, None
        
        biz_id = data['data']['ads_business_account_create']['business']['id']
        print(f"✅ تم إنشاء العمل التجاري بنجاح! ID: {biz_id}")

        # الخطوة 3: انتظار رابط الدعوة و استخراجه
        invitation_link = wait_for_invitation_email(admin_email)
        
        if invitation_link:
            db.add_business(combo_id, biz_id, invitation_link)
            db.increment_creations(combo_id)
            return True, biz_id, invitation_link
        else:
            db.update_combo_status(combo_id, "failed_no_link")
            return False, biz_id, None
                
    except requests.RequestException as e:
        print(f"❌ خطأ في طلب HTTP: {e}")
        db.update_combo_status(combo_id, "request_error")
        return False, None, None
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        db.update_combo_status(combo_id, "general_error")
        return False, None, None

def process_combo(user_telegram_id):
    """العملية الرئيسية للبدء في إنشاء الأعمال التجارية للكومبوهات المتاحة"""
    with Database() as db:
        user = db.get_user(user_telegram_id)
        if not user or not db.is_subscribed(user_telegram_id):
            return "No subscription or user not found."
        
        combos = db.get_user_combos(user['id'])
        if not combos:
            return "No combos found. Please add combos first."
        
        results = []
        
        for combo in combos:
            if combo['creations_count'] >= MAX_CREATIONS_PER_COOKIE:
                continue
            
            for _ in range(MAX_CREATIONS_PER_COOKIE - combo['creations_count']):
                success, biz_id, link = create_facebook_business_for_combo(combo['cookies'], db, combo['id'], user['id'])
                if success == "LIMIT_REACHED":
                    results.append(f"Limit reached for combo {combo['id']}")
                    break
                elif success:
                    results.append(f"Success: Business ID {biz_id}, Link: {link}")
                else:
                    results.append(f"Failed for combo {combo['id']}")
            
        return "\n".join(results)
