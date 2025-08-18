import re
import requests
import random
import json
import time
import asyncio
from config import TEMPMAIL_BASE_URL, TEMPMAIL_API_TOKEN

TEMPMAIL_HEADERS = {"Authorization": f"Bearer {TEMPMAIL_API_TOKEN}"}

class BusinessCreator:
    def __init__(self):
        pass
    
    async def create_temp_email(self):
        try:
            response = requests.post(f"{TEMPMAIL_BASE_URL}/addresses", headers=TEMPMAIL_HEADERS)
            response.raise_for_status()
            data = response.json()
            return data["data"]["email"]
        except:
            return None
    
    async def wait_for_invitation_email(self, email_address, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{TEMPMAIL_BASE_URL}/addresses/{email_address}/emails", headers=TEMPMAIL_HEADERS)
                emails = response.json()["data"]
                
                for email_data in emails:
                    if "facebook" in email_data['from'].lower():
                        # Read email content
                        email_response = requests.get(f"{TEMPMAIL_BASE_URL}/emails/{email_data['uuid']}", headers=TEMPMAIL_HEADERS)
                        email_content = email_response.json()["data"]
                        
                        # Extract invitation link
                        pattern = r'https://business\.facebook\.com/invitation/\?token=[^"\s]+'
                        match = re.search(pattern, email_content['body'])
                        if match:
                            return match.group(0)
            except:
                pass
            
            await asyncio.sleep(10)
        return None
    
    def generate_random_data(self):
        first_names = ['Ahmed', 'Mohamed', 'Omar', 'Ali', 'Hassan', 'John', 'Michael', 'David']
        last_names = ['Hassan', 'Mohamed', 'Ali', 'Smith', 'Johnson', 'Williams']
        business_prefixes = ['Tech', 'Digital', 'Smart', 'Pro', 'Elite', 'Global']
        business_suffixes = ['Solutions', 'Systems', 'Services', 'Corp', 'Ltd', 'Inc']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        business_name = f"{random.choice(business_prefixes)} {random.choice(business_suffixes)} {random.randint(100, 999)}"
        
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com']
        email = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 9999)}@{random.choice(domains)}"
        
        return first_name, last_name, business_name, email
    
    def extract_token_from_response(self, response):
        pattern = re.compile(r'\["DTSGInitialData",\s*\[\],\s*\{\s*"token":\s*"([^"]+)"')
        try:
            content = ""
            for chunk in response.iter_content(chunk_size=2048, decode_unicode=True):
                if chunk:
                    content += chunk
                    match = pattern.search(content)
                    if match:
                        return match.group(1)
                if len(content) > 10000:
                    content = content[-1000:]
        except:
            pass
        return None
    
    def parse_cookies(self, cookies_input):
        cookies = {}
        for part in cookies_input.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    def get_user_id_from_cookies(self, cookies):
        return cookies.get('c_user', "61573547480828")
    
    async def create_business(self, cookies_text):
        try:
            cookies = self.parse_cookies(cookies_text)
            user_id = self.get_user_id_from_cookies(cookies)
            
            # Create temporary email
            admin_email = await self.create_temp_email()
            if not admin_email:
                return False, None, None, "Failed to create temporary email"
            
            # Generate random data
            first_name, last_name, business_name, email = self.generate_random_data()
            
            # Get token
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            response = requests.get('https://business.facebook.com/overview', cookies=cookies, headers=headers, timeout=30)
            if response.status_code != 200:
                return False, None, None, "Invalid cookies"
            
            token_value = self.extract_token_from_response(response)
            if not token_value:
                return False, None, None, "Token extraction failed"
            
            # Create business
            create_headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-friendly-name': 'useBusinessCreationMutationMutation',
                'x-fb-lsd': token_value,
            }
            
            variables_data = {
                "input": {
                    "client_mutation_id": str(random.randint(1, 999)),
                    "actor_id": user_id,
                    "business_name": business_name,
                    "user_first_name": first_name,
                    "user_last_name": last_name,
                    "user_email": email,
                    "creation_source": "BM_HOME_BUSINESS_CREATION_IN_SCOPE_SELECTOR",
                    "entry_point": "UNIFIED_GLOBAL_SCOPE_SELECTOR"
                }
            }
            
            data = {
                'av': user_id,
                '__user': user_id,
                'fb_dtsg': token_value,
                'variables': json.dumps(variables_data, separators=(',', ':')),
                'doc_id': '10024830640911292',
            }
            
            response_create = requests.post('https://business.facebook.com/api/graphql/', cookies=cookies, headers=create_headers, data=data, timeout=30)
            
            # Parse response
            response_text = response_create.text
            if response_text.startswith('for (;;);'):
                response_text = response_text[9:]
            
            response_json = json.loads(response_text)
            
            # Check for limit error
            if 'errors' in response_json:
                for error in response_json['errors']:
                    if 'حد عدد الأنشطة التجارية' in error.get('description', ''):
                        return "LIMIT_REACHED", None, None, "Business limit reached"
                return False, None, None, "Business creation failed"
            
            if 'data' not in response_json:
                return False, None, None, "Unexpected response"
            
            biz_id = response_json['data']['bizkit_create_business']['id']
            
            # Setup business with admin email
            setup_success = await self.setup_business_review(cookies, token_value, user_id, biz_id, admin_email)
            if not setup_success:
                return False, biz_id, None, "Setup failed"
            
            # Wait for invitation email
            invitation_link = await self.wait_for_invitation_email(admin_email)
            
            return True, biz_id, invitation_link, "Success"
            
        except Exception as e:
            return False, None, None, f"Error: {str(e)}"
    
    async def setup_business_review(self, cookies, token_value, user_id, biz_id, admin_email):
        try:
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-friendly-name': 'BizKitBusinessSetupReviewCardMutation',
                'x-fb-lsd': token_value,
            }
            
            data = {
                'av': user_id,
                '__user': user_id,
                'fb_dtsg': token_value,
                'variables': f'{{"businessId":"{biz_id}","entryPoint":"BIZWEB_BIZ_SETUP_REVIEW_CARD","inviteUsers":[{{"email":"{admin_email}","roles":["ADMIN"]}}],"personalPageIdsToBeClaimed":[],"directPageUsers":[],"flowType":"BUSINESS_CREATION_IN_FBS"}}',
                'doc_id': '9845682502146236',
            }
            
            response = requests.post('https://business.facebook.com/api/graphql/', cookies=cookies, headers=headers, data=data, timeout=30)
            
            response_text = response.text
            if response_text.startswith('for (;;);'):
                response_text = response_text[9:]
            
            response_json = json.loads(response_text)
            return 'errors' not in response_json
            
        except:
            return False
