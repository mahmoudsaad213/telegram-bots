# create_business.py

import re
import requests
import random
import json
import string
import time
from datetime import datetime
from config import TEMPMAIL_BASE_URL, TEMPMAIL_HEADERS, MAX_CREATIONS_PER_COOKIE
from database import Database

def create_temp_email():
    try:
        response = requests.post(f"{TEMPMAIL_BASE_URL}/addresses", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        email = data["data"]["email"]
        print(f"📧 Created temporary email: {email}")
        return email
    except requests.RequestException as e:
        print(f"❌ Error creating email: {e}")
        return None

def get_emails(email_address):
    try:
        response = requests.get(f"{TEMPMAIL_BASE_URL}/addresses/{email_address}/emails", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data["data"]
    except requests.RequestException as e:
        print(f"❌ Error fetching emails: {e}")
        return []

def read_email(email_uuid):
    try:
        response = requests.get(f"{TEMPMAIL_BASE_URL}/emails/{email_uuid}", headers=TEMPMAIL_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data["data"]
    except requests.RequestException as e:
        print(f"❌ Error reading email: {e}")
        return None

def extract_invitation_link(email_body):
    pattern = r'https://business\.facebook\.com/invitation/\?token=[^"\s]+'
    match = re.search(pattern, email_body)
    if match:
        return match.group(0)
    return None

def wait_for_invitation_email(email_address, timeout=300):
    print(f"🔄 Waiting for invitation email on: {email_address}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        emails = get_emails(email_address)
        if emails:
            for email_data in emails:
                if "facebook" in email_data['from'].lower() or "invitation" in email_data['subject'].lower():
                    print(f"📨 Found invitation email from: {email_data['from']}")
                    email_content = read_email(email_data['uuid'])
                    if email_content:
                        invitation_link = extract_invitation_link(email_content['body'])
                        if invitation_link:
                            print(f"🔗 Invitation link extracted!")
                            return invitation_link
        time.sleep(10)
    print("⏰ Timeout waiting for invitation email")
    return None

def generate_random_name():
    first_names = ['Ahmed', 'Mohamed', 'Omar', 'Ali', 'Hassan', 'Mahmoud', 'Youssef', 'Khaled', 'Amr', 'Tamer', 
                   'John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Charles', 'Joseph', 'Thomas']
    last_names = ['Hassan', 'Mohamed', 'Ali', 'Ibrahim', 'Mahmoud', 'Youssef', 'Ahmed', 'Omar', 'Said', 'Farid',
                  'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    return random.choice(first_names), random.choice(last_names)

def generate_random_email(first_name, last_name):
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com']
    random_num = random.randint(100, 9999)
    email_formats = [
        f"{first_name.lower()}{last_name.lower()}{random_num}@{random.choice(domains)}",
        f"{first_name.lower()}{random_num}@{random.choice(domains)}",
        f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}",
        f"{first_name.lower()}{last_name.lower()}@{random.choice(domains)}",
        f"{first_name.lower()}_{last_name.lower()}{random_num}@{random.choice(domains)}"
    ]
    return random.choice(email_formats)

def generate_business_name():
    business_prefixes = ['Tech', 'Digital', 'Smart', 'Pro', 'Elite', 'Global', 'Prime', 'Alpha', 'Meta', 'Cyber', 'Next', 'Future']
    business_suffixes = ['Solutions', 'Systems', 'Services', 'Group', 'Corp', 'Ltd', 'Inc', 'Agency', 'Studio', 'Labs', 'Works', 'Hub']
    random_num = random.randint(100, 999)
    name_formats = [
        f"{random.choice(business_prefixes)} {random.choice(business_suffixes)} {random_num}",
        f"{random.choice(business_prefixes)}{random_num}",
        f"M{random_num} {random.choice(business_suffixes)}",
        f"{random.choice(business_prefixes)} {random_num}",
        f"Company {random_num}"
    ]
    return random.choice(name_formats)

def generate_random_user_agent():
    chrome_versions = ['131.0.0.0', '130.0.0.0', '129.0.0.0', '128.0.0.0']
    version = random.choice(chrome_versions)
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'

def extract_token_from_response(response):
    token_value = None
    pattern = re.compile(r'\["DTSGInitialData",\s*\[\],\s*\{\s*"token":\s*"([^"]+)"')
    content = ""
    for chunk in response.iter_content(chunk_size=2048, decode_unicode=True):
        if chunk:
            content += chunk
            match = pattern.search(content)
            if match:
                token_value = match.group(1)
                return token_value
            if len(content) > 10000:
                content = content[-1000:]
    return token_value

def parse_cookies(cookies_input):
    cookies = {}
    for part in cookies_input.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def get_user_id_from_cookies(cookies):
    if 'c_user' in cookies:
        return cookies['c_user']
    return "61573547480828"

def setup_business_review(cookies, token_value, user_id, biz_id, admin_email):
    print(f"\n📋 Setting up business review for Business ID: {biz_id}")
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://business.facebook.com',
        'priority': 'u=1, i',
        'referer': 'https://business.facebook.com/billing_hub/payment_settings/?asset_id=&payment_account_id=',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-full-version-list': '"Not)A;Brand";v="8.0.0.0", "Chromium";v="138.0.7204.184", "Google Chrome";v="138.0.7204.184"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-asbd-id': '359341',
        'x-bh-flowsessionid': 'upl_wizard_1755490133794_62e6e455-e443-49db-aeba-58f23a27ec01',
        'x-fb-friendly-name': 'BizKitBusinessSetupReviewCardMutation',
        'x-fb-lsd': token_value,
        'x-fb-upl-sessionid': 'upl_1755490133794_11c3faff-8830-427d-b820-0c4366afac9d',
    }

    params = {
        '_callFlowletID': '0',
        '_triggerFlowletID': '6821',
        'qpl_active_e2e_trace_ids': '',
    }

    data = {
        'av': user_id,
        '__aaid': '0',
        '__user': user_id,
        '__a': '1',
        '__req': '1c',
        '__hs': '20318.BP:DEFAULT.2.0...0',
        'dpr': '1',
        '__ccg': 'EXCELLENT',
        '__rev': '1026002495',
        '__s': 'si7vjs:iccgau:4k38c3',
        '__hsi': '7539772710483233608',
        '__dyn': '7xeUmxa2C5rgydwCwRyU8EKmhe2Om2q1DxiFGxK7oG484S4UKewSAAzpoixW4E726US2Sfxq4U5i4824yoyaxG4o4B0l898885G0Eo9FE4WqbwLghwLyaxBa2dmm11K6U8o2lxep122y5oeEjx63K2y1py-0DU2qwgEhxWbwQwnHxC0Bo9k2B2V8cE98451KfwXxq1-orx2ewyx6i2GU8U-U98C2i48nwCAzEowwwTxu1cwh8S1qxa3O6UW4UnwhFA0FUkx22W11wCz84e2K7EOicwVyES2e0UFU6K19xq1owqp8aE4KeyE9Eco9U4S7ErwMxN0lF9UcE3xwtU5K2G0BE88twba3i15xBxa2u1aw',
        '__hsdp': '85v92crRg8pkFxqe5ybjyk8jdAQO5WQm2G3qm2a9StAK2KK1txC_xAC4y4KIqilJjCZKcCy8GE49BGze5ahk1exugG8ukidxe2504Fg2EadzE9UWFFEgwNqzpEb4EgG-ezFjzczF2CQA4l1gUjxK5k2d8kieFD18EYE9FE1uU5S1Gwto5q0lGl6e0dLw0X1Kq9ym2aiQezUpAximbCjw0xfw',
        '__hblp': '0Rwbu3G6U4W1gw48w54w75xGE1oA0OA2q7pUdUCbwoobU88aWwjUdE6i1Gw8y1ZwVK0FE9U3oG1tw7jG1iw8uE3PwkU2kzonwYwrE6C1ZwiUeo1vo6i17xO4Uiy9ES6awno1kElwlEao3BwtEG3-7EhwHwmoaE9bwIAgK8x2l4xii9wwxq5GwwyEO1OyawhVE88lg4Cex-1dwSw9C3G2mi0ha0DE98iBx23a11w_xJa2W9BwBCxm2Kq4EswMyomwwwkEgwxg9Ulxm5qGqqUy2it0iUaoyazE4u2G6E4-az85e78cECayEjwrFEq_82aRwXKUSmWyGK7FWhd5gC9zdfU8rG4KE7-3zwGwfe2q68cA5A58b8gy837wxwmo2WwFwnFUc-m2O5o8oS9xWi2OnwIDwko8U8EW1wxV1C229xG7p8owNxydg6x0DwNiw8u3uui',
        'fb_dtsg': token_value,
        'jazoest': '25376',
        'lsd': token_value,
        '__spin_r': '1026002495',
        '__spin_b': 'trunk',
        '__spin_t': '1755490133',
        '__jssesw': '1',
        'qpl_active_flow_ids': '1001927540,558500776',
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'BizKitBusinessSetupReviewCardMutation',
        'variables': f'{{"businessId":"{biz_id}","entryPoint":"BIZWEB_BIZ_SETUP_REVIEW_CARD","inviteUsers":[{{"email":"{admin_email}","roles":["ADMIN"]}}],"personalPageIdsToBeClaimed":[],"directPageUsers":[],"flowType":"BUSINESS_CREATION_IN_FBS"}}',
        'server_timestamps': 'true',
        'doc_id': '9845682502146236',
        'fb_api_analytics_tags': '["qpl_active_flow_ids=1001927540,558500776"]',
    }

    try:
        response = requests.post(
            'https://business.facebook.com/api/graphql/', 
            params=params, 
            cookies=cookies, 
            headers=headers, 
            data=data,
            timeout=30
        )
        
        response_text = response.text
        if response_text.startswith('for (;;);'):
            response_text = response_text[9:]
        response_json = json.loads(response_text)
        
        if 'errors' in response_json:
            print("\n❌ Failed to complete business setup:")
            for error in response_json['errors']:
                print(f"- {error.get('message', 'Unknown error')}")
            return False
        elif 'error' in response_json:
            error_code = response_json.get('error', 'Unknown')
            error_desc = response_json.get('errorDescription', 'Unknown error')
            print(f"\n❌ Setup Error {error_code}: {error_desc}")
            return False
        elif 'data' in response_json:
            print("\n✅ Business setup completed successfully!")
            return True
        else:
            print(f"\n⚠️ Unexpected setup response format")
            return False
                
    except Exception as e:
        print(f"❌ Error in setup: {e}")
        return False

def create_facebook_business_for_combo(cookies_str, db, combo_id, user_id):
    cookies = parse_cookies(cookies_str)
    user_id_fb = get_user_id_from_cookies(cookies)
    
    admin_email = create_temp_email()
    if not admin_email:
        return False, None, None
    
    first_name, last_name = generate_random_name()
    email = generate_random_email(first_name, last_name)
    business_name = generate_business_name()
    user_agent = generate_random_user_agent()
    
    headers_initial = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }

    try:
        response = requests.get(
            'https://business.facebook.com/overview',
            cookies=cookies,
            headers=headers_initial,
            stream=True,
            timeout=30,
            allow_redirects=True
        )
        
        if response.status_code != 200:
            return False, None, None

        token_value = extract_token_from_response(response)
        
        if not token_value:
            return False, None, None
        
        time.sleep(2)

        headers_create = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://business.facebook.com',
            'referer': 'https://business.facebook.com/overview',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': user_agent,
            'x-asbd-id': str(random.randint(359340, 359350)),
            'x-fb-friendly-name': 'useBusinessCreationMutationMutation',
            'x-fb-lsd': token_value,
        }

        variables_data = {
            "input": {
                "client_mutation_id": str(random.randint(1, 999)),
                "actor_id": user_id_fb,
                "business_name": business_name,
                "user_first_name": first_name,
                "user_last_name": last_name,
                "user_email": email,
                "creation_source": "BM_HOME_BUSINESS_CREATION_IN_SCOPE_SELECTOR",
                "entry_point": "UNIFIED_GLOBAL_SCOPE_SELECTOR"
            }
        }

        data_create = {
            'av': user_id_fb,
            '__user': user_id_fb,
            '__a': '1',
            '__req': str(random.randint(10, 30)),
            '__hs': f'{random.randint(20000, 25000)}.BP:DEFAULT.2.0...0',
            'dpr': '1',
            '__ccg': 'MODERATE',
            '__rev': str(random.randint(1026001750, 1026001760)),
            '__s': f'{random.choice(["3arcua", "4brcub", "5csdvc"])}:{random.choice(["iccgau", "jddgbv", "kddgbv"])}:{random.choice(["myl46k", "nzm47l", "ozm48m"])}',
            '__hsi': str(random.randint(7539741099426225680, 7539741099426225690)),
            '__comet_req': '15',
            'fb_dtsg': token_value,
            'jazoest': str(random.randint(25540, 25550)),
            'lsd': token_value,
            '__spin_r': str(random.randint(1026001750, 1026001760)),
            '__spin_b': 'trunk',
            '__spin_t': str(int(time.time())),
            '__jssesw': '1',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'useBusinessCreationMutationMutation',
            'variables': json.dumps(variables_data, separators=(',', ':')),
            'server_timestamps': 'true',
            'doc_id': '10024830640911292',
        }

        response_create = requests.post(
            'https://business.facebook.com/api/graphql/', 
            cookies=cookies, 
            headers=headers_create, 
            data=data_create,
            timeout=30
        )
        
        response_text = response_create.text
        if response_text.startswith('for (;;);'):
            response_text = response_text[9:]
        response_json = json.loads(response_text)
        
        if 'errors' in response_json:
            for error in response_json['errors']:
                error_msg = error.get('message', '')
                if 'field_exception' in error_msg or 'حد عدد الأنشطة التجارية' in error.get('description', ''):
                    return "LIMIT_REACHED", None, None
            return False, None, None
                
        elif 'error' in response_json:
            return False, None, None
                
        elif 'data' in response_json:
            biz_id = response_json['data']['bizkit_create_business']['id']
            setup_success = setup_business_review(cookies, token_value, user_id_fb, biz_id, admin_email)
            if setup_success:
                invitation_link = wait_for_invitation_email(admin_email)
                if invitation_link:
                    db.add_business(combo_id, biz_id, invitation_link)
                    db.increment_creations(combo_id)
                    return True, biz_id, invitation_link
            return False, biz_id, None
        else:
            return False, None, None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None, None

def process_combo(user_telegram_id):
    db = Database()
    user = db.get_user(user_telegram_id)
    if not user or not db.is_subscribed(user_telegram_id):
        db.close()
        return "No subscription or user not found."
    
    combos = db.get_user_combos(user['id'])
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
            time.sleep(random.randint(5, 10))
    
    db.close()
    return "\n".join(results)
