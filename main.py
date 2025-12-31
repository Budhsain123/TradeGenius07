# main.py - Full Channel Link Support with All Link Types

"""
🔥 Trade Genius Bot - FULL CHANNEL LINK SUPPORT
✅ Supports ALL Telegram link types
✅ Public/Private/Invite links
✅ Multiple link formats per channel
✅ Button shows original link
✅ Smart verification system
"""

import os
import json
import logging
import time
import random
import string
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote

# ==================== FLASK SERVER FOR RENDER ====================
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "TradeGeniusBot",
        "message": "Telegram bot is running",
        "feature": "Full Channel Link Support v2.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== CONFIGURATION ====================
class Config:
    BOT_TOKEN = "8560550222:AAFYTkiQMa_ElkH1dBKhKdGUceKs9R5p9Xk"
    BOT_USERNAME = "TradeGenius07RewardsHub_bot"
    WEB_URL = "https://www.nextwin.great-site.net/"
    AI_BUTTON_NAME = "🤖 AI Chat"
    
    FIREBASE_URL = "https://colortraderpro-panel-default-rtdb.firebaseio.com/"
    
    REWARD_PER_REFERRAL = 2
    MINIMUM_WITHDRAWAL = 20
    BONUS_AT_10_REFERRALS = 5
    
    ADMIN_USER_ID = "1882237415"
    SUPPORT_CHANNEL = "@TradeGenius07_HelpCenter_bot"
    
    LOG_FILE = "bot_logs.txt"
    DATA_FILE = "local_backup.json"
    
    # Referral verification settings
    REFERRAL_VERIFICATION_DELAY = 2
    MAX_VERIFICATION_ATTEMPTS = 3
    
    # Channel verification settings
    CHANNEL_CHECK_TIMEOUT = 10
    MAX_CHANNEL_RETRIES = 2

# ==================== HTTP HELPER ====================
import urllib.request
import urllib.error

class HTTPHelper:
    @staticmethod
    def make_request(url, method="GET", data=None, headers=None, timeout=30):
        try:
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            if data and isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            response = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(response.read().decode('utf-8'))
            
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print(f"⚠️ HTTP 409 Conflict: {e}")
                return None
            print(f"HTTP Error {e.code}: {e}")
            return None
        except Exception as e:
            print(f"HTTP Error: {e}")
            return None

# ==================== FIREBASE HELPER ====================
class FirebaseDB:
    def __init__(self):
        self.base_url = Config.FIREBASE_URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        print(f"🔥 Firebase URL: {self.base_url}")
        self.local_data = self._load_local_backup()
    
    def _load_local_backup(self):
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "users": {}, 
            "withdrawals": {}, 
            "referrals": {},
            "channels": {},
            "settings": {
                "reward_per_referral": Config.REWARD_PER_REFERRAL,
                "minimum_withdrawal": Config.MINIMUM_WITHDRAWAL,
                "web_url": Config.WEB_URL,
                "ai_button_name": Config.AI_BUTTON_NAME
            },
            "referral_attempts": {},
            "channel_attempts": {}
        }
    
    def _save_local_backup(self):
        try:
            with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.local_data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _firebase_request(self, method, path, data=None):
        try:
            if path.startswith('/'):
                path = path[1:]
            
            url = self.base_url + path + ".json"
            return HTTPHelper.make_request(url, method, data)
            
        except Exception as e:
            print(f"❌ Firebase Error: {e}")
            return None
    
    # Channel management methods
    def add_channel(self, channel_data):
        channel_id = channel_data.get("id")
        if not channel_id:
            return False
        
        # Ensure link is stored in original format
        if "original_link" not in channel_data:
            channel_data["original_link"] = channel_data.get("link", "")
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        
        if result is not None:
            if "channels" not in self.local_data:
                self.local_data["channels"] = {}
            self.local_data["channels"][channel_id] = channel_data
            self._save_local_backup()
        
        return result
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels") or {}
        return data
    
    def delete_channel(self, channel_id):
        result = self._firebase_request("DELETE", f"channels/{channel_id}")
        
        if result is not None:
            if "channels" in self.local_data:
                self.local_data["channels"].pop(channel_id, None)
                self._save_local_backup()
        
        return result
    
    def get_channel(self, channel_id):
        data = self._firebase_request("GET", f"channels/{channel_id}")
        
        if data:
            return data
        else:
            return self.local_data.get('channels', {}).get(channel_id, None)
    
    # User management methods
    def get_user(self, user_id):
        user_id = str(user_id)
        data = self._firebase_request("GET", f"users/{user_id}")
        
        if data:
            return data
        else:
            return self.local_data.get('users', {}).get(user_id, None)
    
    def create_user(self, user_id, username="User", first_name="", last_name=""):
        user_id = str(user_id)
        
        if not username or username == "User":
            if first_name:
                username = first_name
                if last_name:
                    username += f" {last_name}"
            else:
                username = f"User_{user_id[-6:]}"
        
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        is_admin = (user_id == Config.ADMIN_USER_ID)
        
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name or "",
            "last_name": last_name or "",
            "referral_code": referral_code,
            "referrals": 0,
            "total_earnings": 0,
            "pending_balance": 0,
            "withdrawn": 0,
            "referrer": None,
            "referral_claimed": False,
            "upi_id": "",
            "phone": "",
            "email": "",
            "is_verified": is_admin,
            "channels_joined": {},
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "is_admin": is_admin,
            "verification_attempts": 0,
            "channel_check_history": {}
        }
        
        result = self._firebase_request("PUT", f"users/{user_id}", user_data)
        
        if "users" not in self.local_data:
            self.local_data["users"] = {}
        self.local_data["users"][user_id] = user_data
        self._save_local_backup()
        
        return user_data
    
    def update_user(self, user_id, updates):
        user_id = str(user_id)
        current = self.get_user(user_id)
        
        if not current:
            return False
        
        current.update(updates)
        current["last_active"] = datetime.now().isoformat()
        
        result = self._firebase_request("PATCH", f"users/{user_id}", updates)
        
        if "users" not in self.local_data:
            self.local_data["users"] = {}
        self.local_data["users"][user_id] = current
        self._save_local_backup()
        
        return True if result else False
    
    def mark_channel_joined(self, user_id, channel_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        if "channels_joined" not in user:
            user["channels_joined"] = {}
        
        user["channels_joined"][channel_id] = {
            "joined_at": datetime.now().isoformat(),
            "verified": True,
            "verified_at": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat()
        }
        
        return self.update_user(user_id, {"channels_joined": user["channels_joined"]})
    
    def mark_user_verified(self, user_id):
        return self.update_user(user_id, {
            "is_verified": True,
            "verified_at": datetime.now().isoformat()
        })
    
    # Other methods remain the same
    def update_ai_button_name(self, new_name):
        data = {"ai_button_name": new_name}
        result = self._firebase_request("PATCH", "settings", data)
        
        if result:
            self.local_data["settings"]["ai_button_name"] = new_name
            self._save_local_backup()
        return result
    
    def get_ai_button_name(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("ai_button_name", Config.AI_BUTTON_NAME)
    
    def update_web_url(self, new_url):
        data = {"web_url": new_url}
        result = self._firebase_request("PATCH", "settings", data)
        
        if result:
            self.local_data["settings"]["web_url"] = new_url
            self._save_local_backup()
        return result
    
    def get_web_url(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("web_url", Config.WEB_URL)
    
    def create_withdrawal(self, withdrawal_id, data):
        result = self._firebase_request("PUT", f"withdrawals/{withdrawal_id}", data)
        return result
    
    def get_withdrawals(self, status=None):
        withdrawals = self._firebase_request("GET", "withdrawals") or {}
        
        if status:
            return {w_id: w for w_id, w in withdrawals.items() if w and w.get("status") == status}
        return withdrawals
    
    def update_withdrawal_status(self, withdrawal_id, status, admin_note=""):
        updates = {"status": status, "processed_at": datetime.now().isoformat()}
        if admin_note:
            updates["admin_note"] = admin_note
        
        return self._firebase_request("PATCH", f"withdrawals/{withdrawal_id}", updates)
    
    def update_upi_id(self, user_id, upi_id):
        return self.update_user(user_id, {"upi_id": upi_id})
    
    def get_all_users(self):
        return self._firebase_request("GET", "users") or {}
    
    def find_user_by_referral_code(self, referral_code):
        users = self.get_all_users()
        for user_id, user_data in users.items():
            if user_data and user_data.get("referral_code") == referral_code:
                return user_id, user_data
        return None, None
    
    def create_referral_record(self, new_user_id, referrer_id, status="pending"):
        referral_id = f"REF{new_user_id}_{int(time.time())}"
        
        referral_data = {
            "new_user_id": str(new_user_id),
            "referrer_id": str(referrer_id),
            "status": status,
            "created_at": datetime.now().isoformat(),
            "reward_amount": Config.REWARD_PER_REFERRAL if status == "completed" else 0,
            "verified": status == "completed"
        }
        
        result = self._firebase_request("PUT", f"referrals/{referral_id}", referral_data)
        return result

# ==================== TELEGRAM BOT API ====================
class TelegramBotAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.db = FirebaseDB()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _api_request(self, method, data=None):
        try:
            url = self.base_url + method
            
            if data:
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('result') if result.get('ok') else None
                
        except urllib.error.HTTPError as e:
            if e.code == 409:
                self.logger.warning(f"API 409 Conflict ({method}) - Retrying...")
                time.sleep(2)
                return None
            self.logger.error(f"API Error {e.code} ({method}): {e}")
            return None
        except Exception as e:
            self.logger.error(f"API Error ({method}): {e}")
            return None
    
    def get_chat_member(self, chat_id, user_id):
        try:
            data = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            result = self._api_request("getChatMember", data)
            
            if result:
                return result
            
            # Try alternative formats
            if isinstance(chat_id, str):
                if chat_id.startswith("@"):
                    chat_id_without_at = chat_id[1:]
                    data["chat_id"] = chat_id_without_at
                    return self._api_request("getChatMember", data)
                elif chat_id.startswith("https://t.me/"):
                    # Extract username from URL
                    username = chat_id.replace("https://t.me/", "").split('/')[0]
                    if username.startswith("@"):
                        data["chat_id"] = username
                    else:
                        data["chat_id"] = f"@{username}"
                    return self._api_request("getChatMember", data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"getChatMember Error: {e}")
            return None
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=True):
        try:
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview
            }
            
            if reply_markup:
                data["reply_markup"] = reply_markup
            
            return self._api_request("sendMessage", data)
            
        except Exception as e:
            self.logger.error(f"sendMessage Error: {e}")
            return None
    
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        try:
            data = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = reply_markup
            
            return self._api_request("editMessageText", data)
            
        except Exception as e:
            self.logger.error(f"editMessageText Error: {e}")
            return None
    
    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        
        if text:
            data["text"] = text
        
        return self._api_request("answerCallbackQuery", data)
    
    def get_updates(self, offset=None, timeout=60):
        data = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]
        }
        if offset:
            data["offset"] = offset
        
        result = self._api_request("getUpdates", data)
        return result or []
    
    def check_webhook_status(self):
        return self._api_request("getWebhookInfo")

# ==================== MAIN BOT CLASS ====================
class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBotAPI(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.user_states = {}
        self.pending_referrals = {}
        self.channel_cache = {}
    
    # ==================== CHANNEL LINK HANDLING ====================
    
    def extract_chat_id_from_link(self, link):
        """
        Extract chat ID from ANY Telegram link format
        Returns chat_id that can be used with getChatMember API
        """
        if not link:
            return None
        
        link = link.strip()
        
        print(f"🔗 Processing link: {link}")
        
        # If it's already a numeric channel ID
        if link.isdigit() or (link.startswith('-100') and link[1:].isdigit()):
            print(f"  → Numeric ID: {link}")
            return link
        
        # If it's already in @username format
        if link.startswith('@'):
            print(f"  → Username format: {link}")
            return link
        
        # Special handling for invite links
        if link.startswith('https://t.me/+') or '/joinchat/' in link:
            print(f"  → Invite link detected: {link}")
            return link
        
        # Parse URL
        patterns = [
            # https://t.me/username
            r'https?://(?:www\.)?t\.me/([A-Za-z0-9_]+)(?:/\d+)?/?$',
            
            # https://t.me/c/chat_id/post_id
            r'https?://(?:www\.)?t\.me/c/(\d+)(?:/\d+)?/?$',
            
            # t.me/username (without https)
            r'^t\.me/([A-Za-z0-9_]+)(?:/\d+)?/?$',
            
            # telegram.me/username
            r'https?://(?:www\.)?telegram\.me/([A-Za-z0-9_]+)(?:/\d+)?/?$',
            
            # Just username (no prefix)
            r'^([A-Za-z0-9_]{5,32})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                extracted = match.group(1)
                
                # For private channel (c/ format)
                if pattern == r'https?://(?:www\.)?t\.me/c/(\d+)(?:/\d+)?/?$':
                    if extracted.isdigit():
                        chat_id = f"-100{extracted}"
                        print(f"  → Private channel ID: {chat_id}")
                        return chat_id
                
                # For public channels/usernames
                elif extracted.isdigit():
                    # It's a numeric username (rare but possible)
                    return f"@{extracted}"
                else:
                    # It's a regular username
                    return f"@{extracted}"
        
        # If nothing matches, try to extract from any URL
        if 't.me/' in link:
            parts = link.split('t.me/')
            if len(parts) > 1:
                potential = parts[1].split('/')[0].split('?')[0]
                if potential:
                    print(f"  → Extracted from URL: @{potential}")
                    return f"@{potential}"
        
        print(f"  → Could not extract, using as-is: {link}")
        return link
    
    def clean_channel_link(self, link):
        """Clean and standardize channel link for display"""
        if not link:
            return link
        
        link = link.strip().replace(' ', '')
        
        # Keep invite links as they are
        if link.startswith('https://t.me/+'):
            return link
        
        # Keep private channel links as they are
        if '/c/' in link:
            return link
        
        # Keep joinchat links as they are
        if '/joinchat/' in link:
            return link
        
        # For @username format
        if link.startswith('@'):
            return f"https://t.me/{link[1:]}"
        
        # For t.me/ format
        if link.startswith('t.me/'):
            return f"https://{link}"
        
        # For plain usernames (no http, no @)
        if not link.startswith(('http://', 'https://', '@', 't.me/')):
            # Check if it's a channel ID
            if link.isdigit() or (link.startswith('-100') and link[1:].isdigit()):
                return link
            else:
                return f"https://t.me/{link}"
        
        return link
    
    def get_channel_display_info(self, channel_link):
        """Get display information for a channel link"""
        if not channel_link:
            return {"url": "#", "emoji": "📢", "type": "unknown"}
        
        # Determine emoji based on link type
        if channel_link.startswith('https://t.me/+') or '/joinchat/' in channel_link:
            emoji = "🔐"
            link_type = "invite"
        elif '/c/' in channel_link:
            emoji = "🛡️"
            link_type = "private"
        elif '@' in channel_link and not channel_link.startswith('https://'):
            emoji = "📢"
            link_type = "public"
            # Convert to clickable URL
            if channel_link.startswith('@'):
                channel_link = f"https://t.me/{channel_link[1:]}"
        elif channel_link.startswith(('https://t.me/', 't.me/')):
            emoji = "📢"
            link_type = "public"
        else:
            emoji = "📢"
            link_type = "public"
        
        # Ensure it's a clickable URL
        display_url = channel_link
        if not display_url.startswith(('http://', 'https://')):
            if display_url.startswith('@'):
                display_url = f"https://t.me/{display_url[1:]}"
            elif display_url.startswith('t.me/'):
                display_url = f"https://{display_url}"
            else:
                display_url = f"https://t.me/{display_url}"
        
        return {
            "url": display_url,
            "emoji": emoji,
            "type": link_type,
            "original": channel_link
        }
    
    def check_user_channels(self, user_id):
        """Check if user has joined all channels - ULTRA IMPROVED"""
        channels = self.db.get_channels()
        
        if not channels:
            print("✅ No channels configured, skipping check")
            return True
        
        user = self.db.get_user(user_id)
        if not user:
            print(f"❌ User {user_id} not found")
            return False
        
        user_id_str = str(user_id)
        all_joined = True
        failed_channels = []
        
        print(f"\n🔍 Checking channels for user {user_id_str}")
        print(f"📊 Total channels to check: {len(channels)}")
        
        for channel_index, (channel_id, channel) in enumerate(channels.items(), 1):
            channel_name = channel.get("name", f"Channel_{channel_id}")
            channel_link = channel.get("link", "")
            original_link = channel.get("original_link", channel_link)
            
            print(f"\n{channel_index}. Checking: {channel_name}")
            print(f"   Link: {original_link}")
            
            if not channel_link:
                print("   ⚠️ No link, skipping")
                continue
            
            # Skip if already verified recently
            if user.get("channels_joined", {}).get(channel_id, {}).get("verified", False):
                last_check = user["channels_joined"][channel_id].get("last_check", "")
                if last_check:
                    try:
                        last_check_time = datetime.fromisoformat(last_check)
                        if (datetime.now() - last_check_time).seconds < 300:  # 5 minutes
                            print("   ✅ Already verified (recent)")
                            continue
                    except:
                        pass
            
            # Extract chat ID for API call
            chat_id_for_check = self.extract_chat_id_from_link(original_link)
            
            if not chat_id_for_check:
                print(f"   ❌ Could not extract chat ID")
                all_joined = False
                failed_channels.append(channel_name)
                continue
            
            print(f"   → Using chat ID: {chat_id_for_check}")
            
            try:
                # Try to check membership
                member_info = self.bot.get_chat_member(chat_id_for_check, user_id)
                
                if member_info and member_info.get("status") in ["member", "administrator", "creator"]:
                    print(f"   ✅ User is a member")
                    self.db.mark_channel_joined(user_id, channel_id)
                    
                    # Update cache
                    cache_key = f"{user_id_str}_{channel_id}"
                    self.channel_cache[cache_key] = {
                        "status": "joined",
                        "timestamp": time.time(),
                        "channel_name": channel_name
                    }
                    
                elif member_info and member_info.get("status") == "left":
                    print(f"   ❌ User has left the channel")
                    all_joined = False
                    failed_channels.append(channel_name)
                    break
                else:
                    print(f"   ❌ User is not a member (status: {member_info.get('status') if member_info else 'None'})")
                    all_joined = False
                    failed_channels.append(channel_name)
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Error checking membership: {e}")
                
                # Special handling for invite links
                if original_link.startswith('https://t.me/+') or '/joinchat/' in original_link:
                    print(f"   ℹ️ Invite link detected, can't verify automatically")
                    print(f"   👉 User must click the link to join")
                    all_joined = False
                    failed_channels.append(f"{channel_name} (invite required)")
                    break
                else:
                    # Try alternative check
                    print(f"   🔄 Trying alternative check...")
                    time.sleep(1)
                    
                    # Try with just the username
                    if 't.me/' in original_link:
                        parts = original_link.split('t.me/')
                        if len(parts) > 1:
                            username = parts[1].split('/')[0]
                            if username and not username.startswith(('c/', '+')):
                                alternative_id = f"@{username}"
                                print(f"   → Trying with: {alternative_id}")
                                try:
                                    member_info = self.bot.get_chat_member(alternative_id, user_id)
                                    if member_info and member_info.get("status") in ["member", "administrator", "creator"]:
                                        print(f"   ✅ User is a member (alternative check)")
                                        self.db.mark_channel_joined(user_id, channel_id)
                                        continue
                                except Exception as e2:
                                    print(f"   ⚠️ Alternative check failed: {e2}")
                    
                    all_joined = False
                    failed_channels.append(channel_name)
                    break
            
            # Small delay between checks
            if channel_index < len(channels):
                time.sleep(0.5)
        
        if all_joined:
            print(f"\n🎉 All {len(channels)} channels verified!")
        else:
            print(f"\n❌ Verification failed for channels: {', '.join(failed_channels)}")
        
        return all_joined
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    def show_add_channel(self, chat_id, message_id, user_id):
        msg = """➕ <b>Add New Channel</b>

Send channel details in this format:

<code>Channel Name
Channel Link
Channel ID</code>

<b>Examples:</b>

1. <b>Public Channel (Any format):</b>
<code>TradeGenius Help
https://t.me/TradeGenius07_HelpCenter_bot
-1001234567890</code>

<code>Support Channel
@TradeGenius07_HelpCenter_bot  
-1001234567890</code>

<code>News Channel
t.me/TradeGeniusNews
-1001234567890</code>

2. <b>Private Channel:</b>
<code>VIP Group
https://t.me/c/1234567890/123
-1001234567890</code>

3. <b>Invite Link:</b>
<code>Premium Group
https://t.me/+ABCdefGHIjklMNOpq
-1001234567890</code>

<b>Supported Link Types:</b>
✅ https://t.me/username
✅ @username
✅ t.me/username  
✅ https://t.me/c/1234567890 (private)
✅ https://t.me/+invite_code
✅ Channel ID (-1001234567890)
✅ Any valid Telegram link

<b>Important:</b>
• Bot must be ADMIN in public channels
• Get channel ID from @username_to_id_bot
• Users must join ALL channels to use bot
• Invite links will show as clickable buttons"""

        self.user_states[user_id] = {
            "state": "awaiting_channel",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "admin_channels")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_channel_list(self, chat_id, message_id, user_id):
        channels = self.db.get_channels()
        
        if not channels:
            msg = "📢 <b>No Channels</b>\n\nNo channels added yet.\nUsers will NOT see verification screen."
            buttons = [("➕ Add Channel", "admin_add_channel"), ("🔙 Back", "admin_channels")]
        else:
            msg = "📢 <b>Current Channels</b>\n\nUsers must join ALL these channels:\n"
            buttons = []
            
            for i, (channel_id, channel) in enumerate(channels.items(), 1):
                name = channel.get("name", f"Channel_{i}")
                link = channel.get("original_link", channel.get("link", "No link"))
                
                # Get display info
                display_info = self.get_channel_display_info(link)
                emoji = display_info["emoji"]
                
                msg += f"{i}. {emoji} <b>{name}</b>\n"
                msg += f"   🔗 <code>{link}</code>\n"
                msg += f"   🆔 <code>{channel_id}</code>\n\n"
                
                buttons.append((f"❌ Delete {i}", f"admin_delete_channel_{channel_id}"))
            
            buttons.append(("➕ Add More", "admin_add_channel"))
            buttons.append(("🔙 Back", "admin_channels"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_screen_real_time(self, chat_id, user_id, username):
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, None, user_id)
            return
        
        msg = "🔐 <b>Join our channels to continue</b>\n\nPlease join ALL channels below:"
        
        buttons = []
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            original_link = channel.get("original_link", channel.get("link", ""))
            
            if not original_link:
                continue
            
            # Get display information
            display_info = self.get_channel_display_info(original_link)
            
            clean_name = channel_name.replace("📢", "").replace("🔔", "").replace("📰", "").strip()
            if not clean_name:
                clean_name = "Join Channel"
            
            button_text = f"{display_info['emoji']} {clean_name}"
            
            # Add button with URL
            buttons.append({
                "text": button_text,
                "url": display_info["url"]
            })
            
            # Add type indicator to message
            msg += f"\n{display_info['emoji']} <b>{clean_name}</b>"
            if display_info['type'] == 'invite':
                msg += " (Click to join)"
            elif display_info['type'] == 'private':
                msg += " (Private channel)"
        
        buttons.append(("✅ I'VE JOINED ALL - VERIFY NOW", "check_verification"))
        
        msg += "\n\n⚠️ <b>Important:</b>\n• Join ALL channels\n• Click VERIFY after joining\n• Wait 10 seconds after joining"
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    # ==================== MESSAGE HANDLING ====================
    
    def handle_user_message(self, chat_id, user_id, text):
        if user_id in self.user_states:
            state = self.user_states[user_id]
            
            if state.get("state") == "awaiting_upi":
                upi_id = text.strip()
                
                if '@' in upi_id and len(upi_id) > 5:
                    self.db.update_upi_id(user_id, upi_id)
                    
                    msg = f"""✅ <b>UPI ID Saved</b>

📱 Your UPI ID: <code>{upi_id}</code>

You can now request withdrawals."""
                    
                    buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
                    keyboard = self.generate_keyboard(buttons, 2)
                    self.bot.send_message(chat_id, msg, keyboard)
                    
                    self.bot.edit_message_text(
                        state["chat_id"],
                        state["message_id"],
                        "✅ UPI ID setup completed!",
                        self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
                    )
                    
                    del self.user_states[user_id]
                else:
                    msg = "❌ Invalid UPI ID.\n\nUse: <code>username@upi</code>"
                    self.bot.send_message(chat_id, msg)
            
            elif state.get("state") == "awaiting_channel":
                lines = text.strip().split('\n')
                if len(lines) >= 3:
                    channel_name = lines[0].strip()
                    channel_link = lines[1].strip()
                    channel_id = lines[2].strip()
                    
                    # Clean and validate the link
                    cleaned_link = self.clean_channel_link(channel_link)
                    
                    # Test the link format
                    chat_id_for_check = self.extract_chat_id_from_link(channel_link)
                    if not chat_id_for_check:
                        msg = f"""❌ <b>Invalid Channel Link</b>

The link you provided cannot be processed:
<code>{channel_link}</code>

Please use a valid Telegram channel link."""
                        self.bot.send_message(chat_id, msg)
                        return
                    
                    channel_data = {
                        "name": channel_name,
                        "link": cleaned_link,
                        "original_link": channel_link,  # Store original
                        "id": channel_id,
                        "added_by": str(user_id),
                        "added_at": datetime.now().isoformat(),
                        "link_type": self.get_channel_display_info(channel_link)["type"]
                    }
                    
                    result = self.db.add_channel(channel_data)
                    
                    if result:
                        display_info = self.get_channel_display_info(channel_link)
                        msg = f"""✅ <b>Channel Added Successfully!</b>

📢 <b>{channel_name}</b>
{display_info['emoji']} <b>Link Type:</b> {display_info['type'].upper()}
🔗 <b>Link:</b> <code>{channel_link}</code>
🆔 <b>ID:</b> <code>{channel_id}</code>

✅ Users will see this channel in verification."""
                    else:
                        msg = "❌ Failed to add channel. Please try again."
                else:
                    msg = """❌ <b>Invalid Format</b>

Please send in 3 lines:
1. Channel Name
2. Channel Link
3. Channel ID

Example:
<code>My Channel
https://t.me/my_channel
-1001234567890</code>"""
                
                buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
                keyboard = self.generate_keyboard(buttons, 2)
                self.bot.send_message(chat_id, msg, keyboard)
                del self.user_states[user_id]
            
            elif state.get("state") == "awaiting_rejection_reason":
                self.process_rejection_reason(user_id, text)
            
            elif state.get("state") == "awaiting_web_url":
                new_url = text.strip()
                
                if new_url.startswith("http://") or new_url.startswith("https://"):
                    result = self.db.update_web_url(new_url)
                    
                    if result:
                        msg = f"""✅ <b>Web URL Updated</b>

New URL: <code>{new_url}</code>

The AI button will now use this URL."""
                    else:
                        msg = "❌ Failed to update web URL."
                else:
                    msg = "❌ Invalid URL. Must start with http:// or https://"
                
                buttons = [("🌐 Back to Web URL", "admin_web_url")]
                keyboard = self.generate_keyboard(buttons, 1)
                self.bot.send_message(chat_id, msg, keyboard)
                del self.user_states[user_id]
            
            elif state.get("state") == "awaiting_ai_button_name":
                new_name = text.strip()
                
                if len(new_name) <= 20 and len(new_name) > 0:
                    result = self.db.update_ai_button_name(new_name)
                    
                    if result:
                        msg = f"""✅ <b>AI Button Name Updated</b>

New Name: <code>{new_name}</code>

The AI button in main menu will now show this name.
It will update for all users immediately."""
                    else:
                        msg = "❌ Failed to update AI button name."
                else:
                    msg = "❌ Invalid name. Must be 1-20 characters."
                
                buttons = [("🤖 Back to AI Button", "admin_ai_button")]
                keyboard = self.generate_keyboard(buttons, 1)
                self.bot.send_message(chat_id, msg, keyboard)
                del self.user_states[user_id]
        
        elif text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                message = parts[1]
                users = self.db.get_all_users()
                
                if not users:
                    self.bot.send_message(chat_id, "❌ No users.")
                    return
                
                total = len(users)
                self.bot.send_message(chat_id, f"📢 Broadcasting to {total} users...")
                
                success = 0
                for uid in users.keys():
                    try:
                        self.bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{message}")
                        success += 1
                        time.sleep(0.1)
                    except:
                        continue
                
                self.bot.send_message(chat_id, f"✅ Sent: {success}/{total} users")
    
    # ==================== CORE BOT FUNCTIONS ====================
    
    def start_command(self, chat_id, user_id, username, first_name, last_name, args):
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username, first_name, last_name)
        
        if str(user_id) == Config.ADMIN_USER_ID:
            if not user.get("is_verified", False):
                self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            self.show_welcome_screen(chat_id, user_id, user, args)
            return
        
        # Store referral code if provided
        referral_code = args[0] if args and len(args) > 0 else None
        if referral_code:
            self.pending_referrals[str(user_id)] = {
                "referral_code": referral_code,
                "attempts": 0,
                "last_attempt": datetime.now().isoformat()
            }
            
            self.db.track_referral_attempt(user_id, referral_code, "pending_verification")
        
        channels = self.db.get_channels()
        
        if not channels:
            if not user.get("is_verified", False):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if user.get("is_verified", False) and str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user, args)
            return
        
        # Check channel membership
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            if not user.get("is_verified", False):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if user.get("is_verified", False) and str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user, args)
        else:
            self.show_verification_screen_real_time(chat_id, user_id, username)
    
    def check_verification(self, chat_id, message_id, user_id):
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ User not found.")
            return
        
        attempts = user.get("verification_attempts", 0) + 1
        self.db.update_user(user_id, {"verification_attempts": attempts})
        
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            username = user.get("username", "User")
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_verification_success(chat_id, message_id, user_id)
        else:
            self.show_verification_failed(chat_id, message_id, user_id)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verification Successful!</b>

Welcome to <b>TradeGenius07 Bot</b>, @{username}!

🎉 You can now start earning <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral.

👇 <b>Get started:</b>"""
        
        buttons = [
            ("🔗 Get Referral Link", "my_referral"),
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        
        if message_id:
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
        else:
            self.bot.send_message(chat_id, msg, keyboard)
    
    def show_verification_failed(self, chat_id, message_id, user_id):
        msg = """❌ <b>Verification Failed</b>

You haven't joined all channels yet.

<b>Please:</b>
1. Join ALL channels from the list
2. Wait 10 seconds after joining
3. Click VERIFY again

<b>For invite links:</b>
• Click the invite link button
• Join the channel
• Come back and click VERIFY

If already joined, wait a moment and try again."""
        
        buttons = [
            ("🔄 Try Again", "check_verification"),
            ("📋 Show Channels", "show_channels_again")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def generate_keyboard(self, buttons, columns=2):
        keyboard = []
        row = []
        
        for i, button in enumerate(buttons):
            if isinstance(button, tuple):
                text, callback = button
                row.append({"text": text, "callback_data": callback})
            elif isinstance(button, dict):
                row.append(button)
            else:
                continue
            
            if len(row) == columns or i == len(buttons) - 1:
                keyboard.append(row)
                row = []
        
        return {"inline_keyboard": keyboard}
    
    # ==================== REST OF THE METHODS (SAME AS BEFORE) ====================
    
    def get_main_menu_buttons(self, user_id):
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        
        ai_button_name = self.db.get_ai_button_name()
        
        buttons = [
            ("🔗 Get Referral Link", "my_referral"),
            ("📊 My Dashboard", "dashboard"),
            ("💳 Withdraw", "withdraw"),
            (ai_button_name, "open_web"),
            ("📜 Terms & Conditions", "terms_conditions"),
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support"),
        ]
        
        if is_admin:
            buttons.append(("👑 Admin Panel", "admin_panel"))
        
        return buttons
    
    def show_welcome_screen(self, chat_id, user_id, user, args):
        if not user:
            user = self.db.get_user(user_id)
        
        if not user:
            return
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Status: Active</b>" if is_admin else ""
        verified_text = "\n✅ <b>Status: Verified</b>" if user.get("is_verified", False) else "\n❌ <b>Status: Not Verified</b>"
        
        referral_status = ""
        if user.get("referrer"):
            referral_status = f"\n👥 Referred by: User_{user['referrer'][-6:]}"
        elif user.get("referral_claimed", False):
            referral_status = "\n✅ Referral already claimed"
        
        welcome_msg = f"""👋 <b>Welcome to TradeGenius07 Bot!</b> 💸

👤 Hello, {user.get('username', 'User')}!{admin_text}{verified_text}{referral_status}

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🔗 Your Code: <code>{user.get('referral_code', 'N/A')}</code>
👥 Referrals: {user.get('referrals', 0)}
💸 Balance: ₹{user.get('pending_balance', 0)}

👇 <b>Select an option:</b>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        
        self.bot.send_message(chat_id, welcome_msg, keyboard)
    
    def process_pending_referral(self, user_id, username):
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_referrals:
            return False
        
        pending = self.pending_referrals[user_id_str]
        referral_code = pending["referral_code"]
        
        if pending.get("attempts", 0) >= Config.MAX_VERIFICATION_ATTEMPTS:
            del self.pending_referrals[user_id_str]
            return False
        
        user = self.db.get_user(user_id)
        if user and user.get("referral_claimed", False):
            del self.pending_referrals[user_id_str]
            return True
        
        time.sleep(Config.REFERRAL_VERIFICATION_DELAY)
        
        success = self.process_referral(user_id, username, referral_code)
        
        if success:
            del self.pending_referrals[user_id_str]
            self.db.track_referral_attempt(user_id, referral_code, "success")
            return True
        else:
            pending["attempts"] = pending.get("attempts", 0) + 1
            pending["last_attempt"] = datetime.now().isoformat()
            self.db.track_referral_attempt(user_id, referral_code, f"failed_attempt_{pending['attempts']}")
            
            if pending["attempts"] >= Config.MAX_VERIFICATION_ATTEMPTS:
                del self.pending_referrals[user_id_str]
            
            return False
    
    def process_referral(self, user_id, username, referral_code):
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        if user.get("referral_claimed", False):
            print(f"⚠️ User {user_id} already claimed referral")
            return True
        
        referrer_id, referrer = self.db.find_user_by_referral_code(referral_code)
        
        if not referrer or not referrer_id:
            print(f"❌ Referral code not found: {referral_code}")
            return False
        
        if referrer_id == str(user_id):
            print(f"❌ Self-referral attempt by {user_id}")
            return False
        
        if not referrer.get("is_verified", False):
            print(f"❌ Referrer {referrer_id} not verified")
            return False
        
        self.db.create_referral_record(user_id, referrer_id, "completed")
        
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL
        
        if new_refs == 10:
            reward += Config.BONUS_AT_10_REFERRALS
        
        updates = {
            "referrals": new_refs,
            "pending_balance": referrer.get("pending_balance", 0) + reward,
            "total_earnings": referrer.get("total_earnings", 0) + reward
        }
        
        self.db.update_user(referrer_id, updates)
        
        self.db.update_user(user_id, {
            "referrer": referrer_id,
            "referral_claimed": True,
            "referral_claimed_at": datetime.now().isoformat()
        })
        
        try:
            self.bot.send_message(
                referrer_id,
                f"""🎉 <b>New Referral Success!</b>

✅ @{username} joined using your link!
💰 You earned: <b>₹{reward}</b>
👥 Total referrals: <b>{new_refs}</b>

Keep sharing to earn more!"""
            )
        except Exception as e:
            print(f"⚠️ Failed to notify referrer: {e}")
        
        print(f"✅ Referral processed: {user_id} -> {referrer_id} (₹{reward})")
        return True
    
    # ==================== CALLBACK HANDLING ====================
    
    def handle_callback(self, chat_id, message_id, user_id, callback_data):
        callback_query_id = callback_data["id"]
        callback = callback_data.get("data", "")
        
        self.bot.answer_callback_query(callback_query_id)
        
        user = self.db.get_user(user_id) or {}
        
        if callback == "terms_conditions":
            self.show_terms_conditions(chat_id, message_id, user_id)
            return
        
        if callback == "open_web":
            web_url = self.db.get_web_url()
            ai_button_name = self.db.get_ai_button_name()
            
            buttons = [
                {"text": ai_button_name, "url": web_url},
                ("🏠 Main Menu", "main_menu")
            ]
            keyboard = self.generate_keyboard(buttons, 2)
            msg = f"""🤖 <b>AI Assistant</b>

🔓 Tap the Button Below to Unlock Access..."""
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        if callback == "show_channels_again":
            self.show_verification_screen_real_time(chat_id, user_id, user.get("username", "User"))
            return
        
        # Admin checks
        if callback == "admin_panel" and str(user_id) != Config.ADMIN_USER_ID:
            msg = "⛔ <b>Access Denied</b>"
            keyboard = self.generate_keyboard([("🏠 Main Menu", "main_menu")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        # Verification check for non-admin users
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
            if callback not in ["check_verification", "show_channels_again", "main_menu"]:
                msg = """❌ <b>Verification Required</b>

Please complete verification first to access bot features.

Join all required channels and verify."""
                keyboard = self.generate_keyboard([
                    ("✅ VERIFY NOW", "check_verification")
                ], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        # Handle other callbacks
        if callback == "check_verification":
            self.check_verification(chat_id, message_id, user_id)
        
        elif callback == "main_menu":
            self.show_main_menu(chat_id, message_id, user_id, user)
        
        elif callback == "my_referral":
            self.show_referral_link(chat_id, message_id, user_id, user)
        
        elif callback == "dashboard":
            self.show_dashboard(chat_id, message_id, user_id, user)
        
        elif callback == "withdraw":
            self.show_withdraw_menu(chat_id, message_id, user_id, user)
        
        elif callback == "setup_upi":
            self.setup_upi_id(chat_id, message_id, user_id)
        
        elif callback == "request_withdraw":
            self.request_withdrawal(chat_id, message_id, user_id, user)
        
        elif callback == "withdraw_history":
            self.show_withdrawal_history(chat_id, message_id, user_id)
        
        elif callback == "admin_panel":
            self.show_admin_panel(chat_id, message_id, user_id)
        
        elif callback.startswith("admin_"):
            if str(user_id) != Config.ADMIN_USER_ID:
                return
            self.handle_admin_callback(chat_id, message_id, user_id, callback)
        
        elif callback in ["how_it_works", "rewards", "support"]:
            self.handle_info_callback(chat_id, message_id, user_id, callback)
    
    # ==================== ADMIN FUNCTIONS ====================
    
    def delete_channel(self, chat_id, message_id, user_id, channel_id):
        result = self.db.delete_channel(channel_id)
        
        if result is not None:
            msg = "✅ Channel deleted successfully."
        else:
            msg = "❌ Failed to delete channel."
        
        buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_rejection_reason(self, admin_id, reason):
        if admin_id not in self.user_states:
            return
        
        state = self.user_states[admin_id]
        if state.get("state") != "awaiting_rejection_reason":
            return
        
        withdrawal_id = state["withdrawal_id"]
        user_id = state["user_id"]
        amount = state["amount"]
        
        self.db.update_withdrawal_status(withdrawal_id, "rejected", f"Rejected: {reason}")
        
        user = self.db.get_user(user_id)
        if user:
            new_balance = user.get("pending_balance", 0) + amount
            self.db.update_user(user_id, {"pending_balance": new_balance})
        
        user_msg = f"""❌ <b>Withdrawal Rejected</b>

💰 Amount: <b>₹{amount}</b>
📋 ID: <code>{withdrawal_id}</code>
📝 Reason: {reason}

Amount returned to your balance.
Contact support if you have questions."""
        
        self.bot.send_message(user_id, user_msg)
        
        msg = f"""❌ <b>Withdrawal Rejected</b>

🆔 {withdrawal_id}
👤 User notified
💰 ₹{amount} returned
📝 Reason: {reason}"""
        
        buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        
        self.bot.edit_message_text(
            state["chat_id"], 
            state["message_id"], 
            msg, 
            keyboard
        )
        
        del self.user_states[admin_id]
    
    # ==================== OTHER METHODS (SIMILAR TO BEFORE) ====================
    
    def show_terms_conditions(self, chat_id, message_id, user_id):
        terms_text = """📜 <b>Terms & Conditions</b>

✅ <b>By using this bot, you agree to:</b>

1. <b>Join all channels</b> to earn points
2. Each user can earn points from <b>ONLY ONE referrer</b>
3. <b>No self-referrals</b> allowed
4. Points and coupons are <b>non-transferable</b>
5. <b>Fraudulent activity</b> will result in permanent ban

📝 <b>Additional Terms:</b>
• Minimum withdrawal: ₹20
• UPI is the only withdrawal method
• Payments processed within 24 hours
• Admin reserves right to modify terms
• You must be 18+ to use this service

<i>Last Updated: {}</i>""".format(datetime.now().strftime("%d %B %Y"))
        
        buttons = [
            ("✅ I Understand", "main_menu"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, terms_text, keyboard)
    
    def show_referral_link(self, chat_id, message_id, user_id, user):
        referral_code = user.get("referral_code", "")
        if not referral_code:
            referral_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            self.db.update_user(user_id, {"referral_code": referral_code})
        
        referral_link = f"https://t.me/{Config.BOT_USERNAME}?start={referral_code}"
        
        msg = f"""🔗 <b>Your Referral Link</b>

<code>{referral_link}</code>

💰 <b>Earn ₹{Config.REWARD_PER_REFERRAL} per referral</b>

📊 <b>Your Stats:</b>
👥 Referrals: {user.get('referrals', 0)}
💰 Pending: ₹{user.get('pending_balance', 0)}
💸 Total: ₹{user.get('total_earnings', 0)}

Share with friends and earn!"""
        
        share_text = f"Join TradeGenius07 bot and earn money! {referral_link}"
        share_url = f"https://t.me/share/url?url={quote(referral_link)}&text={quote(share_text)}"
        
        buttons = [
            {"text": "📤 Share", "url": share_url},
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_dashboard(self, chat_id, message_id, user_id, user):
        verified_status = "✅ Verified" if user.get("is_verified", False) else "❌ Not Verified"
        
        referral_info = ""
        if user.get("referrer"):
            referral_info = f"\n👥 Referred by: User_{user['referrer'][-6:]}"
        elif user.get("referral_claimed", False):
            referral_info = "\n✅ Referral claimed"
        
        msg = f"""📊 <b>Dashboard</b>

👤 {user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
🔄 Status: <b>{verified_status}</b>{referral_info}

📈 <b>Statistics:</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
💰 Pending: <b>₹{user.get('pending_balance', 0)}</b>
💸 Total Earned: <b>₹{user.get('total_earnings', 0)}</b>
✅ Withdrawn: <b>₹{user.get('withdrawn', 0)}</b>"""
        
        buttons = [
            ("💳 Withdraw", "withdraw"),
            ("🔗 Get Link", "my_referral"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdraw_menu(self, chat_id, message_id, user_id, user):
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if not upi_id:
            msg = f"""❌ <b>UPI ID Required</b>

You need to set up your UPI ID first.
UPI ID format: <code>username@upi</code>

Current balance: <b>₹{pending}</b>
Minimum withdrawal: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>"""
            
            buttons = [
                ("📱 Setup UPI ID", "setup_upi"),
                ("📊 Dashboard", "dashboard"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        elif pending >= Config.MINIMUM_WITHDRAWAL:
            msg = f"""💳 <b>Withdraw Funds</b>

💰 Available: <b>₹{pending}</b>
💰 Minimum: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📱 Your UPI: <code>{upi_id}</code>
📞 Phone: {user.get('phone', 'Not set')}
📧 Email: {user.get('email', 'Not set')}

🏦 <b>Payment Method:</b>
• UPI Only (Google Pay, PhonePe, Paytm)

⚠️ Payment processed within 24 hours"""
            
            buttons = [
                ("✅ Request Withdrawal", "request_withdraw"),
                ("✏️ Change UPI", "setup_upi"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        else:
            needed = Config.MINIMUM_WITHDRAWAL - pending
            referrals_needed = (needed + Config.REWARD_PER_REFERRAL - 1) // Config.REWARD_PER_REFERRAL
            
            msg = f"""❌ <b>Insufficient Balance</b>

💰 Available: <b>₹{pending}</b>
💰 Required: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📊 Need: <b>₹{needed}</b> more

🔗 Get {referrals_needed} more referrals to withdraw."""
            
            buttons = [
                ("🔗 Referral Link", "my_referral"),
                ("📊 Dashboard", "dashboard"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def setup_upi_id(self, chat_id, message_id, user_id):
        msg = """📱 <b>Setup UPI ID</b>

Send your UPI ID in this format:
<code>username@upi</code>

<b>Examples:</b>
• <code>john.doe@okaxis</code>
• <code>janesmith@ybl</code>
• <code>rohitkumar@paytm</code>

⚠️ Withdrawals will be sent to this UPI ID."""
        
        self.user_states[user_id] = {
            "state": "awaiting_upi",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "withdraw")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def request_withdrawal(self, chat_id, message_id, user_id, user):
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if pending < Config.MINIMUM_WITHDRAWAL:
            msg = "❌ Insufficient balance."
            keyboard = self.generate_keyboard([("🏠 Main Menu", "main_menu")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        if not upi_id:
            msg = "❌ UPI ID not set."
            keyboard = self.generate_keyboard([("📱 Setup UPI", "setup_upi")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        withdrawal_id = f"WD{random.randint(100000, 999999)}"
        
        withdrawal_data = {
            "user_id": str(user_id),
            "username": user.get("username", ""),
            "amount": pending,
            "upi_id": upi_id,
            "phone": user.get("phone", ""),
            "email": user.get("email", ""),
            "payment_method": "upi",
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "withdrawal_id": withdrawal_id,
            "form_type": "upi/mono"
        }
        
        self.db.create_withdrawal(withdrawal_id, withdrawal_data)
        
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + pending
        })
        
        admin_msg = f"""🆕 <b>WITHDRAWAL REQUEST</b>

👤 User: @{user.get('username', 'N/A')}
💰 Amount: <b>₹{pending}</b>
📱 UPI ID: <code>{upi_id}</code>
📞 Phone: {user.get('phone', 'N/A')}
📧 Email: {user.get('email', 'N/A')}
📋 ID: {withdrawal_id}
⏰ Time: {datetime.now().strftime('%H:%M %d/%m')}
📄 Form Type: UPI/Mono Form

Click /admin to manage."""
        
        self.bot.send_message(Config.ADMIN_USER_ID, admin_msg)
        
        confirm_msg = f"""✅ <b>Request Submitted</b>

📋 ID: <code>{withdrawal_id}</code>
💰 Amount: <b>₹{pending}</b>
📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
🔄 Status: <b>Pending</b>
⏳ Payouts Are Processed Within 24–72 Hours
🏦 Payouts Are Not Processed On Public And Bank Holidays."""
        
        buttons = [
            ("📜 Check Status", "withdraw_history"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, confirm_msg, keyboard)
    
    def show_withdrawal_history(self, chat_id, message_id, user_id):
        withdrawals = self.db.get_withdrawals()
        user_wds = {}
        
        for w_id, w_data in withdrawals.items():
            if w_data and w_data.get("user_id") == str(user_id):
                user_wds[w_id] = w_data
        
        if not user_wds:
            msg = "📜 <b>Withdrawal History</b>\n\nNo withdrawals yet."
        else:
            msg = "📜 <b>Withdrawal History</b>\n\n"
            
            sorted_wds = sorted(
                user_wds.items(),
                key=lambda x: x[1].get("requested_at", ""),
                reverse=True
            )[:10]
            
            for w_id, w_data in sorted_wds:
                date = datetime.fromisoformat(w_data["requested_at"]).strftime("%d/%m %H:%M")
                amount = w_data.get("amount", 0)
                status = w_data.get("status", "pending")
                
                if status == "completed":
                    status_emoji = "✅"
                elif status == "rejected":
                    status_emoji = "❌"
                else:
                    status_emoji = "⏳"
                
                msg += f"{status_emoji} ₹{amount} - {date} ({status})\n"
        
        buttons = [
            ("💰 Withdraw", "withdraw"),
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_main_menu(self, chat_id, message_id, user_id, user):
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Mode</b>" if is_admin else ""
        verified_text = "\n✅ <b>Verified</b>" if user.get("is_verified", False) else "\n❌ <b>Not Verified</b>"
        
        ai_button_name = self.db.get_ai_button_name()
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}{verified_text}

👋 {user.get('username', 'User')}
💰 Balance: <b>₹{user.get('pending_balance', 0)}</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_admin_panel(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        total_users = len(users) if users else 0
        
        withdrawals = self.db.get_withdrawals("pending")
        pending_withdrawals = len(withdrawals) if withdrawals else 0
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        # Count different channel types
        channel_types = {}
        for channel_id, channel in channels.items():
            link_type = channel.get("link_type", "unknown")
            channel_types[link_type] = channel_types.get(link_type, 0) + 1
        
        channel_type_info = ""
        for ctype, count in channel_types.items():
            channel_type_info += f"\n• {ctype}: {count}"
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
💳 Pending WD: {pending_withdrawals}
📢 Channels: {total_channels}{channel_type_info}
🌐 Web URL: {web_url[:30]}...
🤖 AI Button: {ai_button_name}

👇 <b>Select:</b>"""
        
        buttons = [
            ("📊 Statistics", "admin_stats"),
            ("💳 Withdrawals", "admin_withdrawals"),
            ("📢 Channels", "admin_channels"),
            ("🌐 Web URL", "admin_web_url"),
            ("🤖 AI Button", "admin_ai_button"),
            ("👥 Users", "admin_users"),
            ("📢 Broadcast", "admin_broadcast"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_admin_callback(self, chat_id, message_id, user_id, callback):
        if callback == "admin_stats":
            self.show_admin_stats(chat_id, message_id, user_id)
        
        elif callback == "admin_withdrawals":
            self.show_withdrawal_management(chat_id, message_id, user_id)
        
        elif callback == "admin_channels":
            self.show_channel_management(chat_id, message_id, user_id)
        
        elif callback == "admin_web_url":
            self.show_web_url_management(chat_id, message_id, user_id)
        
        elif callback == "admin_ai_button":
            self.show_ai_button_management(chat_id, message_id, user_id)
        
        elif callback == "admin_users":
            self.show_user_management(chat_id, message_id, user_id)
        
        elif callback == "admin_broadcast":
            self.show_broadcast_menu(chat_id, message_id, user_id)
        
        elif callback == "admin_add_channel":
            self.show_add_channel(chat_id, message_id, user_id)
        
        elif callback == "admin_view_channels":
            self.show_channel_list(chat_id, message_id, user_id)
        
        elif callback.startswith("admin_delete_channel_"):
            channel_id = callback.replace("admin_delete_channel_", "")
            self.delete_channel(chat_id, message_id, user_id, channel_id)
        
        elif callback.startswith("admin_approve_"):
            wd_id = callback.replace("admin_approve_", "")
            self.approve_withdrawal(chat_id, message_id, user_id, wd_id)
        
        elif callback.startswith("admin_reject_"):
            wd_id = callback.replace("admin_reject_", "")
            self.reject_withdrawal(chat_id, message_id, user_id, wd_id)
        
        elif callback == "admin_update_web_url":
            self.show_update_web_url(chat_id, message_id, user_id)
        
        elif callback == "admin_update_ai_button":
            self.show_update_ai_button(chat_id, message_id, user_id)
    
    def show_admin_stats(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        
        total_users = len(users) if users else 0
        verified = sum(1 for u in users.values() if u and u.get("is_verified", False))
        total_earnings = sum(u.get("total_earnings", 0) for u in users.values() if u)
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        # Count channel types
        public_count = sum(1 for c in channels.values() if c and c.get("link_type") == "public")
        private_count = sum(1 for c in channels.values() if c and c.get("link_type") == "private")
        invite_count = sum(1 for c in channels.values() if c and c.get("link_type") == "invite")
        
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        msg = f"""📊 <b>Admin Statistics</b>

👥 <b>Users:</b>
• Total: {total_users}
• Verified: {verified}
• Pending: {total_users - verified}

💰 <b>Financial:</b>
• Total Earnings: ₹{total_earnings}
• Per Referral: ₹{Config.REWARD_PER_REFERRAL}
• Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}

📢 <b>Channels:</b>
• Total: {total_channels}
• Public: {public_count}
• Private: {private_count}
• Invite Links: {invite_count}

🌐 <b>Web URL:</b>
• {web_url}

🤖 <b>AI Button:</b>
• {ai_button_name}

🔄 <b>Channel Link Support:</b>
✅ All Telegram link formats
✅ Public/Private channels
✅ Invite links
✅ Multiple link formats per channel"""
        
        buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_channel_management(self, chat_id, message_id, user_id):
        channels = self.db.get_channels()
        
        if not channels:
            msg = """📢 <b>Channel Management</b>

No channels added yet.
Users will NOT see verification screen.

Add channels to require users to join before using bot."""
        else:
            msg = f"""📢 <b>Channel Management</b>

{len(channels)} channel(s) added.
Users MUST join these channels to use bot.

<b>Features:</b>
✅ Supports ALL Telegram link types
✅ Public/Private/Invite links
✅ Button shows original link
✅ Smart verification system

Add more or delete existing channels."""
        
        buttons = [
            ("➕ Add Channel", "admin_add_channel"),
            ("👁 View Channels", "admin_view_channels"),
            ("🔙 Back", "admin_panel")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== OTHER ADMIN METHODS ====================
    
    def show_withdrawal_management(self, chat_id, message_id, user_id):
        withdrawals = self.db.get_withdrawals("pending")
        
        if not withdrawals:
            msg = "💳 <b>Pending Withdrawals</b>\n\nNo pending requests."
            buttons = [("🔄 Refresh", "admin_withdrawals"), ("🔙 Back", "admin_panel")]
        else:
            msg = "💳 <b>Pending Withdrawals</b>\n\n"
            buttons = []
            
            for i, (wd_id, wd_data) in enumerate(withdrawals.items(), 1):
                if wd_data:
                    username = wd_data.get("username", "N/A")
                    amount = wd_data.get("amount", 0)
                    upi_id = wd_data.get("upi_id", "N/A")
                    date = datetime.fromisoformat(wd_data["requested_at"]).strftime("%d/%m %H:%M")
                    
                    msg += f"{i}. ₹{amount} - @{username}\n"
                    msg += f"   📱 UPI: {upi_id}\n"
                    msg += f"   📅 {date}\n\n"
                    
                    buttons.append((f"✅ Approve {i}", f"admin_approve_{wd_id}"))
                    buttons.append((f"❌ Reject {i}", f"admin_reject_{wd_id}"))
            
            buttons.append(("🔄 Refresh", "admin_withdrawals"))
            buttons.append(("🔙 Back", "admin_panel"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def approve_withdrawal(self, chat_id, message_id, user_id, withdrawal_id):
        withdrawals = self.db.get_withdrawals()
        wd_data = withdrawals.get(withdrawal_id) if withdrawals else None
        
        if not wd_data:
            msg = f"❌ Withdrawal {withdrawal_id} not found."
        else:
            self.db.update_withdrawal_status(withdrawal_id, "completed", f"Approved by admin {user_id}")
            
            user_msg = f"""✅ <b>Withdrawal Approved!</b>

💰 Amount: <b>₹{wd_data['amount']}</b>
📋 ID: <code>{withdrawal_id}</code>
📱 UPI: <code>{wd_data.get('upi_id', 'N/A')}</code>

Payment processed successfully! Funds will reach you within 24 hours."""
            
            self.bot.send_message(wd_data["user_id"], user_msg)
            msg = f"✅ Withdrawal {withdrawal_id} approved.\n\nUser notified."
        
        buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def reject_withdrawal(self, chat_id, message_id, user_id, withdrawal_id):
        withdrawals = self.db.get_withdrawals()
        wd_data = withdrawals.get(withdrawal_id) if withdrawals else None
        
        if not wd_data:
            msg = f"❌ Withdrawal {withdrawal_id} not found."
            buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
            keyboard = self.generate_keyboard(buttons, 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        self.user_states[user_id] = {
            "state": "awaiting_rejection_reason",
            "withdrawal_id": withdrawal_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "user_id": wd_data.get("user_id"),
            "amount": wd_data.get("amount", 0)
        }
        
        msg = f"""❌ <b>Reject Withdrawal</b>

🆔 {withdrawal_id}
👤 User: @{wd_data.get('username', 'N/A')}
💰 Amount: ₹{wd_data.get('amount', 0)}
📱 UPI: {wd_data.get('upi_id', 'N/A')}
📞 Phone: {wd_data.get('phone', 'N/A')}

Send rejection reason:"""
        
        buttons = [("❌ Cancel", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_user_management(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        
        if not users:
            msg = "👥 <b>No Users</b>\n\nNo users yet."
        else:
            msg = "👥 <b>Top 10 Users by Referrals</b>\n\n"
            
            sorted_users = sorted(
                [(uid, data) for uid, data in users.items() if data],
                key=lambda x: x[1].get("referrals", 0),
                reverse=True
            )[:10]
            
            for i, (uid, data) in enumerate(sorted_users, 1):
                username = data.get("username", f"User_{uid[-6:]}")
                earnings = data.get("total_earnings", 0)
                referrals = data.get("referrals", 0)
                verified = "✅" if data.get("is_verified") else "❌"
                
                msg += f"{i}. {verified} {username}\n   💰 ₹{earnings} | 👥 {referrals}\n"
        
        buttons = [("🔄 Refresh", "admin_users"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_broadcast_menu(self, chat_id, message_id, user_id):
        msg = """📢 <b>Broadcast Message</b>

Use /broadcast command:

<code>/broadcast Your message here</code>

Example:
<code>/broadcast New update available!</code>"""
        
        buttons = [("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_ai_button_management(self, chat_id, message_id, user_id):
        ai_button_name = self.db.get_ai_button_name()
        web_url = self.db.get_web_url()
        
        msg = f"""🤖 <b>AI Button Management</b>

Current AI Button Name:
<code>{ai_button_name}</code>

Current Web URL:
<code>{web_url}</code>

Click below to update AI button name."""
        
        buttons = [
            ("✏️ Update Button Name", "admin_update_ai_button"),
            ("🌐 Update Web URL", "admin_update_web_url"),
            ("🔙 Back", "admin_panel")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_update_ai_button(self, chat_id, message_id, user_id):
        current_name = self.db.get_ai_button_name()
        
        msg = f"""✏️ <b>Update AI Button Name</b>

Current: <code>{current_name}</code>

Send new AI button name:
Example: <code>🤖 AI Chat</code> or <code>🚀 Open AI</code>

⚠️ Max 20 characters, include emoji for better look."""
        
        self.user_states[user_id] = {
            "state": "awaiting_ai_button_name",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "admin_ai_button")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_web_url_management(self, chat_id, message_id, user_id):
        web_url = self.db.get_web_url()
        
        msg = f"""🌐 <b>Web URL Management</b>

Current Web URL:
<code>{web_url}</code>

Click below to update the web URL."""
        
        buttons = [
            ("✏️ Update Web URL", "admin_update_web_url"),
            ("🔙 Back", "admin_panel")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_update_web_url(self, chat_id, message_id, user_id):
        current_url = self.db.get_web_url()
        
        msg = f"""✏️ <b>Update Web URL</b>

Current: <code>{current_url}</code>

Send new web URL:
Example: <code>https://example.com</code>

⚠️ Must start with https://"""
        
        self.user_states[user_id] = {
            "state": "awaiting_web_url",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "admin_web_url")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_info_callback(self, chat_id, message_id, user_id, callback):
        if callback == "how_it_works":
            msg = f"""📢 <b>How It Works</b>

1️⃣ <b>Join Channels</b> (If Required)
   Complete verification first

2️⃣ <b>Get Referral Link</b>
   Share with friends

3️⃣ <b>Earn Money</b>
   Get ₹{Config.REWARD_PER_REFERRAL} per referral

4️⃣ <b>Setup UPI & Withdraw</b>
   Minimum ₹{Config.MINIMUM_WITHDRAWAL} to withdraw"""
        
        elif callback == "rewards":
            msg = f"""🎁 <b>Rewards System</b>

💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}
🔥 10 Referrals Bonus: +₹{Config.BONUS_AT_10_REFERRALS}
👑 Top Referrer: Special Reward

📊 Example Earnings:
• 5 referrals = ₹{Config.REWARD_PER_REFERRAL * 5}
• 10 referrals = ₹{Config.REWARD_PER_REFERRAL * 10 + Config.BONUS_AT_10_REFERRALS}
• 20 referrals = ₹{Config.REWARD_PER_REFERRAL * 20 + (Config.BONUS_AT_10_REFERRALS * 2)}"""
        
        elif callback == "support":
            msg = f"""📞 <b>Support</b>

Channel: {Config.SUPPORT_CHANNEL}

We're here to help!"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== BOT RUNNER ====================
    
    def run_bot(self):
        print("="*60)
        print("🤖 Trade Genius Bot - FULL CHANNEL LINK SUPPORT")
        print("="*60)
        print(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        
        print("\n🔄 Disabling webhook...")
        webhook_info = self.bot._api_request("getWebhookInfo")
        if webhook_info:
            print(f"ℹ️ Current webhook: {webhook_info.get('url', 'None')}")
        
        delete_result = self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
        if delete_result:
            print("✅ Webhook disabled successfully")
        else:
            print("⚠️ Could not disable webhook, trying again...")
            self.bot._api_request("deleteWebhook", {})
        
        time.sleep(2)
        
        print("\n✅ Bot Features:")
        print("   • Supports ALL Telegram link formats")
        print("   • Public/Private/Invite links")
        print("   • Multiple links per channel")
        print("   • Smart verification system")
        print(f"   • Reward per referral: ₹{Config.REWARD_PER_REFERRAL}")
        print(f"   • Min withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        print(f"   • Web URL: {web_url}")
        print(f"   • AI Button: {ai_button_name}")
        
        channels = self.db.get_channels()
        if channels:
            print(f"\n📢 Channels configured: {len(channels)}")
            for i, (channel_id, channel) in enumerate(channels.items(), 1):
                link_type = channel.get("link_type", "unknown")
                print(f"   {i}. {channel.get('name', 'Unnamed')} ({link_type})")
        
        print("="*60)
        print("✅ Bot is ready and running!")
        print("="*60)
        
        self.offset = 0
        error_count = 0
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset)
                
                if updates is None:
                    error_count += 1
                    if error_count > 5:
                        print("🔄 Too many errors, re-initializing bot...")
                        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
                        error_count = 0
                        time.sleep(5)
                    else:
                        time.sleep(2)
                    continue
                
                error_count = 0
                
                if updates and isinstance(updates, list):
                    for update in updates:
                        self.offset = update["update_id"] + 1
                        
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            user_id = msg["from"]["id"]
                            username = msg["from"].get("username", "")
                            first_name = msg["from"].get("first_name", "")
                            last_name = msg["from"].get("last_name", "")
                            
                            if "text" in msg:
                                text = msg["text"]
                                
                                if text.startswith("/start"):
                                    parts = text.split()
                                    args = parts[1:] if len(parts) > 1 else []
                                    self.start_command(chat_id, user_id, username, first_name, last_name, args)
                                
                                elif text.startswith("/admin") and str(user_id) == Config.ADMIN_USER_ID:
                                    self.show_admin_panel(chat_id, msg["message_id"], user_id)
                                
                                else:
                                    self.handle_user_message(chat_id, user_id, text)
                        
                        elif "callback_query" in update:
                            cb = update["callback_query"]
                            chat_id = cb["message"]["chat"]["id"]
                            message_id = cb["message"]["message_id"]
                            user_id = cb["from"]["id"]
                            
                            self.handle_callback(chat_id, message_id, user_id, cb)
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.running = False
                
            except Exception as e:
                print(f"❌ Unexpected Error: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
                if error_count > 10:
                    print("🔴 Too many errors, restarting bot...")
                    time.sleep(10)
                    self.offset = 0
                    error_count = 0
                else:
                    time.sleep(5)

# ==================== START BOTH SERVERS ====================
def run_both():
    bot = TradeGeniusBot()
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Flask server started on port 5000")
    print("🤖 Starting Telegram bot...")
    
    bot.run_bot()

# ==================== START BOT ====================
if __name__ == "__main__":
    print("🔥 Trade Genius Bot - Full Channel Link Support v2.0")
    print("="*60)
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure bot token first!")
    else:
        run_both()