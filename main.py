# main.py - COMPLETELY FIXED Channel Verification System

"""
🔥 Trade Genius Bot - FIXED v3.0
✅ Uses numeric ID for verification
✅ Any link format for display buttons
✅ Proper error handling
✅ All bugs fixed
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
        "feature": "Fixed Channel System v3.0"
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
    
    REFERRAL_VERIFICATION_DELAY = 2
    MAX_VERIFICATION_ATTEMPTS = 3

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
                return None
            return None
        except Exception as e:
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
            }
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
    
    def _make_safe_key(self, key):
        """Convert channel ID to Firebase-safe key"""
        return str(key).replace("-", "neg").replace(".", "_").replace("/", "_")
    
    def add_channel(self, channel_data):
        """Add a channel to database"""
        channel_id = channel_data.get("id", "")
        if not channel_id:
            return False
        
        safe_key = self._make_safe_key(channel_id)
        channel_data["safe_key"] = safe_key
        
        result = self._firebase_request("PUT", f"channels/{safe_key}", channel_data)
        
        if "channels" not in self.local_data:
            self.local_data["channels"] = {}
        self.local_data["channels"][safe_key] = channel_data
        self._save_local_backup()
        
        return result is not None or True
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels")
        if data:
            return data
        return self.local_data.get("channels", {})
    
    def delete_channel(self, safe_key):
        result = self._firebase_request("DELETE", f"channels/{safe_key}")
        
        if "channels" in self.local_data:
            self.local_data["channels"].pop(safe_key, None)
            self._save_local_backup()
        
        return True
    
    def get_user(self, user_id):
        user_id = str(user_id)
        data = self._firebase_request("GET", f"users/{user_id}")
        
        if data:
            return data
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
            "verification_attempts": 0
        }
        
        self._firebase_request("PUT", f"users/{user_id}", user_data)
        
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
        
        self._firebase_request("PATCH", f"users/{user_id}", updates)
        
        if "users" not in self.local_data:
            self.local_data["users"] = {}
        self.local_data["users"][user_id] = current
        self._save_local_backup()
        
        return True
    
    def mark_channel_joined(self, user_id, channel_key):
        user = self.get_user(user_id)
        if not user:
            return False
        
        if "channels_joined" not in user:
            user["channels_joined"] = {}
        
        user["channels_joined"][channel_key] = {
            "joined_at": datetime.now().isoformat(),
            "verified": True
        }
        
        return self.update_user(user_id, {"channels_joined": user["channels_joined"]})
    
    def mark_user_verified(self, user_id):
        return self.update_user(user_id, {
            "is_verified": True,
            "verified_at": datetime.now().isoformat()
        })
    
    def track_referral_attempt(self, user_id, referral_code, status):
        """Track referral attempts"""
        attempt_id = f"ATT{user_id}_{int(time.time())}"
        attempt_data = {
            "user_id": str(user_id),
            "referral_code": referral_code,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self._firebase_request("PUT", f"referral_attempts/{attempt_id}", attempt_data)
        return True
    
    def update_ai_button_name(self, new_name):
        data = {"ai_button_name": new_name}
        result = self._firebase_request("PATCH", "settings", data)
        self.local_data["settings"]["ai_button_name"] = new_name
        self._save_local_backup()
        return True
    
    def get_ai_button_name(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("ai_button_name", self.local_data.get("settings", {}).get("ai_button_name", Config.AI_BUTTON_NAME))
    
    def update_web_url(self, new_url):
        data = {"web_url": new_url}
        self._firebase_request("PATCH", "settings", data)
        self.local_data["settings"]["web_url"] = new_url
        self._save_local_backup()
        return True
    
    def get_web_url(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("web_url", self.local_data.get("settings", {}).get("web_url", Config.WEB_URL))
    
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
        data = self._firebase_request("GET", "users")
        if data:
            return data
        return self.local_data.get("users", {})
    
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
        
        self._firebase_request("PUT", f"referrals/{referral_id}", referral_data)
        return True

# ==================== TELEGRAM BOT API ====================
class TelegramBotAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.db = FirebaseDB()
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
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
            self.logger.error(f"API Error {e.code} ({method})")
            return None
        except Exception as e:
            self.logger.error(f"API Error ({method}): {e}")
            return None
    
    def get_chat(self, chat_id):
        """Get chat info"""
        try:
            return self._api_request("getChat", {"chat_id": chat_id})
        except:
            return None
    
    def get_chat_member(self, chat_id, user_id):
        """Check if user is member of a chat using NUMERIC ID"""
        try:
            data = {"chat_id": chat_id, "user_id": int(user_id)}
            return self._api_request("getChatMember", data)
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
        data = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            data["text"] = text
        return self._api_request("answerCallbackQuery", data)
    
    def get_updates(self, offset=None, timeout=60):
        data = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if offset:
            data["offset"] = offset
        return self._api_request("getUpdates", data) or []

# ==================== MAIN BOT CLASS ====================
class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBotAPI(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.user_states = {}
        self.pending_referrals = {}
    
    # ==================== CHANNEL VERIFICATION - FIXED ====================
    
    def check_user_membership(self, numeric_channel_id, user_id):
        """
        Check if user is member using NUMERIC channel ID only
        This is the ONLY way to check membership via Telegram API
        """
        try:
            # Ensure numeric channel ID
            channel_id = str(numeric_channel_id).strip()
            
            # Must be numeric (starts with - for supergroups/channels)
            if not channel_id.lstrip('-').isdigit():
                print(f"      ⚠️ Invalid ID format: {channel_id}")
                return False, "invalid_id"
            
            # Convert to int for API
            channel_id_int = int(channel_id)
            user_id_int = int(user_id)
            
            print(f"      📡 API Call: getChatMember({channel_id_int}, {user_id_int})")
            
            result = self.bot.get_chat_member(channel_id_int, user_id_int)
            
            if result:
                status = result.get("status", "")
                print(f"      📊 Status: {status}")
                
                if status in ["member", "administrator", "creator"]:
                    return True, status
                elif status == "left":
                    return False, "left"
                elif status == "kicked":
                    return False, "banned"
                else:
                    return False, status
            else:
                print(f"      ❌ No result from API")
                return False, "api_error"
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False, str(e)
    
    def check_user_channels(self, user_id):
        """Check if user has joined ALL required channels"""
        channels = self.db.get_channels()
        
        if not channels:
            print("✅ No channels configured")
            return True
        
        user = self.db.get_user(user_id)
        if not user:
            print(f"❌ User {user_id} not found")
            return False
        
        print(f"\n{'='*50}")
        print(f"🔍 Checking {len(channels)} channel(s) for user {user_id}")
        print(f"{'='*50}")
        
        all_joined = True
        failed_channels = []
        
        for channel_key, channel in channels.items():
            channel_name = channel.get("name", "Unknown")
            channel_id = channel.get("id", "")  # NUMERIC ID
            channel_link = channel.get("link", "")  # Display link
            
            print(f"\n📢 Channel: {channel_name}")
            print(f"   🔗 Link: {channel_link}")
            print(f"   🆔 ID: {channel_id}")
            
            if not channel_id:
                print(f"   ⚠️ No channel ID configured, skipping")
                continue
            
            # Check if already verified in cache
            joined_info = user.get("channels_joined", {}).get(channel_key, {})
            if joined_info.get("verified", False):
                joined_at = joined_info.get("joined_at", "")
                if joined_at:
                    try:
                        joined_time = datetime.fromisoformat(joined_at)
                        if (datetime.now() - joined_time).seconds < 600:  # 10 min cache
                            print(f"   ✅ Already verified (cached)")
                            continue
                    except:
                        pass
            
            # Check membership using NUMERIC ID
            is_member, status = self.check_user_membership(channel_id, user_id)
            
            if is_member:
                print(f"   ✅ User is {status}")
                self.db.mark_channel_joined(user_id, channel_key)
            else:
                print(f"   ❌ Not a member ({status})")
                all_joined = False
                failed_channels.append(channel_name)
                break  # Stop at first failure
            
            time.sleep(0.3)
        
        print(f"\n{'='*50}")
        if all_joined:
            print(f"🎉 All channels verified!")
        else:
            print(f"❌ Failed: {', '.join(failed_channels)}")
        print(f"{'='*50}\n")
        
        return all_joined
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    def show_add_channel(self, chat_id, message_id, user_id):
        """Show channel adding instructions"""
        msg = """➕ <b>Add New Channel</b>

Send channel details in <b>3 lines</b>:

<code>Channel Name
Channel Link  
Channel ID</code>

━━━━━━━━━━━━━━━━━━━━━━
<b>📌 EXAMPLE:</b>

<code>VIP Trading Group
https://t.me/+KxTBB1C2hyZlYTU1
-1001234567890</code>

━━━━━━━━━━━━━━━━━━━━━━
<b>📋 IMPORTANT NOTES:</b>

1️⃣ <b>Channel Link</b> = Any format:
   • https://t.me/+ABC... (invite)
   • https://t.me/username
   • @username

2️⃣ <b>Channel ID</b> = MUST be numeric!
   • Format: <code>-100XXXXXXXXXX</code>
   • Get from: @username_to_id_bot
   • Or: @getidsbot
   • Or: @RawDataBot

3️⃣ <b>Bot must be ADMIN</b> in channel!

⚠️ Without correct numeric ID, verification WON'T work!"""

        self.user_states[user_id] = {
            "state": "awaiting_channel",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        keyboard = self.generate_keyboard([("❌ Cancel", "admin_channels")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_add_channel(self, chat_id, user_id, text):
        """Process channel addition"""
        lines = text.strip().split('\n')
        
        if len(lines) < 3:
            return """❌ <b>Invalid Format</b>

Send in 3 lines:
1. Channel Name
2. Channel Link
3. Channel ID (numeric)

<b>Example:</b>
<code>My Channel
https://t.me/+ABC123
-1001234567890</code>"""
        
        channel_name = lines[0].strip()
        channel_link = lines[1].strip()
        channel_id = lines[2].strip()
        
        # Validate name
        if len(channel_name) < 2:
            return "❌ Channel name too short (min 2 chars)"
        
        # Validate link
        if not channel_link:
            return "❌ Channel link is required"
        
        # Validate ID - MUST be numeric
        clean_id = channel_id.lstrip('-')
        if not clean_id.isdigit():
            return f"""❌ <b>Invalid Channel ID</b>

You entered: <code>{channel_id}</code>

Channel ID must be numeric like:
<code>-1001234567890</code>

<b>How to get Channel ID:</b>
1. Add @username_to_id_bot to your channel
2. Forward any message to @getidsbot
3. Or use @RawDataBot"""
        
        # Make sure it starts with -100 for supergroups/channels
        if not channel_id.startswith('-100') and channel_id.startswith('-'):
            channel_id = '-100' + channel_id.lstrip('-')
        elif not channel_id.startswith('-'):
            channel_id = '-100' + channel_id
        
        # Test if bot can access this channel
        print(f"🔍 Testing channel access: {channel_id}")
        chat_info = self.bot.get_chat(int(channel_id))
        
        access_warning = ""
        chat_title = channel_name
        
        if chat_info:
            chat_title = chat_info.get("title", channel_name)
            print(f"   ✅ Channel accessible: {chat_title}")
        else:
            print(f"   ⚠️ Cannot access channel")
            access_warning = "\n\n⚠️ <b>Warning:</b> Bot cannot access this channel. Make sure bot is ADMIN!"
        
        # Ensure link is clickable
        display_link = channel_link
        if not display_link.startswith(('http://', 'https://')):
            if display_link.startswith('@'):
                display_link = f"https://t.me/{display_link[1:]}"
            elif display_link.startswith('t.me/'):
                display_link = f"https://{display_link}"
            else:
                display_link = f"https://t.me/{display_link}"
        
        # Determine link type
        if '+' in channel_link or 'joinchat' in channel_link:
            link_type = "invite"
        elif '/c/' in channel_link:
            link_type = "private"
        else:
            link_type = "public"
        
        # Save channel
        channel_data = {
            "name": channel_name,
            "link": display_link,
            "original_link": channel_link,
            "id": channel_id,
            "link_type": link_type,
            "chat_title": chat_title,
            "added_by": str(user_id),
            "added_at": datetime.now().isoformat()
        }
        
        result = self.db.add_channel(channel_data)
        
        if result:
            emoji = "🔐" if link_type == "invite" else "📢"
            return f"""✅ <b>Channel Added!</b>

{emoji} <b>Name:</b> {channel_name}
📛 <b>Title:</b> {chat_title}
🔗 <b>Link:</b> <code>{channel_link}</code>
🆔 <b>ID:</b> <code>{channel_id}</code>
📋 <b>Type:</b> {link_type.upper()}{access_warning}

Users must now join this channel!"""
        else:
            return "❌ Failed to save. Try again."
    
    def show_channel_list(self, chat_id, message_id, user_id):
        """Show list of channels"""
        channels = self.db.get_channels()
        
        if not channels:
            msg = """📢 <b>No Channels</b>

No channels configured.
Add channels to require verification."""
            buttons = [("➕ Add Channel", "admin_add_channel"), ("🔙 Back", "admin_channels")]
        else:
            msg = f"📢 <b>Channels ({len(channels)})</b>\n\n"
            buttons = []
            
            for i, (key, ch) in enumerate(channels.items(), 1):
                name = ch.get("name", f"Channel {i}")
                link = ch.get("original_link", ch.get("link", "N/A"))
                ch_id = ch.get("id", "N/A")
                link_type = ch.get("link_type", "public")
                emoji = "🔐" if link_type == "invite" else "📢"
                
                msg += f"{i}. {emoji} <b>{name}</b>\n"
                msg += f"   🔗 <code>{link}</code>\n"
                msg += f"   🆔 <code>{ch_id}</code>\n\n"
                
                buttons.append((f"❌ Del {i}", f"admin_delete_channel_{key}"))
            
            buttons.append(("➕ Add More", "admin_add_channel"))
            buttons.append(("🔙 Back", "admin_channels"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_screen(self, chat_id, user_id, username):
        """Show verification screen to user"""
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, None, user_id)
            return
        
        msg = """🔐 <b>Verification Required</b>

Join ALL channels below to continue:"""
        
        buttons = []
        
        for key, ch in channels.items():
            name = ch.get("name", "Channel")
            link = ch.get("link", "")
            link_type = ch.get("link_type", "public")
            
            if not link:
                continue
            
            # Clean name
            clean_name = name.replace("📢", "").replace("🔔", "").strip()
            if not clean_name:
                clean_name = "Join Channel"
            
            emoji = "🔐" if link_type == "invite" else "📢"
            button_text = f"{emoji} {clean_name}"
            
            # URL button
            buttons.append({"text": button_text, "url": link})
            
            msg += f"\n• {emoji} <b>{clean_name}</b>"
        
        buttons.append(("✅ VERIFY NOW", "check_verification"))
        
        msg += """

━━━━━━━━━━━━━━━━━━━━━━
<b>Instructions:</b>
1️⃣ Click each button to join
2️⃣ Wait 5-10 seconds
3️⃣ Click VERIFY NOW"""
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id, message_id, user_id):
        """Handle verify button click"""
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ Error. Please /start again.")
            return
        
        # Update attempts
        attempts = user.get("verification_attempts", 0) + 1
        self.db.update_user(user_id, {"verification_attempts": attempts})
        
        # Check channels
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            # Process referral
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, user.get("username", "User"))
            
            self.show_verification_success(chat_id, message_id, user_id)
        else:
            self.show_verification_failed(chat_id, message_id, attempts)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        """Show success message"""
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verification Successful!</b>

Welcome @{username}!

🎉 Start earning ₹{Config.REWARD_PER_REFERRAL} per referral!"""
        
        buttons = [
            ("🔗 Referral Link", "my_referral"),
            ("📊 Dashboard", "dashboard"),
            ("🏠 Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        
        if message_id:
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
        else:
            self.bot.send_message(chat_id, msg, keyboard)
    
    def show_verification_failed(self, chat_id, message_id, attempts):
        """Show failure message"""
        msg = f"""❌ <b>Verification Failed</b>

You haven't joined all channels.

<b>Steps:</b>
1. Click each channel button
2. Join the channel/group
3. Wait 10 seconds
4. Click VERIFY again

<b>Attempt:</b> {attempts}

⚠️ Make sure you actually JOINED, not just viewed!"""
        
        buttons = [
            ("🔄 Try Again", "check_verification"),
            ("📋 Show Channels", "show_channels_again")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def generate_keyboard(self, buttons, columns=2):
        """Generate inline keyboard"""
        keyboard = []
        row = []
        
        for i, btn in enumerate(buttons):
            if isinstance(btn, tuple):
                text, callback = btn
                row.append({"text": text, "callback_data": callback})
            elif isinstance(btn, dict):
                row.append(btn)
            
            if len(row) == columns or i == len(buttons) - 1:
                if row:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        return {"inline_keyboard": keyboard}
    
    def get_main_menu_buttons(self, user_id):
        """Get main menu buttons"""
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        ai_name = self.db.get_ai_button_name()
        
        buttons = [
            ("🔗 Referral Link", "my_referral"),
            ("📊 Dashboard", "dashboard"),
            ("💳 Withdraw", "withdraw"),
            (ai_name, "open_web"),
            ("📜 Terms", "terms_conditions"),
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support"),
        ]
        
        if is_admin:
            buttons.append(("👑 Admin", "admin_panel"))
        
        return buttons
    
    # ==================== COMMAND HANDLERS ====================
    
    def start_command(self, chat_id, user_id, username, first_name, last_name, args):
        """Handle /start command"""
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username, first_name, last_name)
        
        # Admin bypass
        if str(user_id) == Config.ADMIN_USER_ID:
            if not user.get("is_verified"):
                self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            self.show_welcome_screen(chat_id, user_id, user)
            return
        
        # Store referral
        if args and len(args) > 0:
            referral_code = args[0]
            self.pending_referrals[str(user_id)] = {
                "referral_code": referral_code,
                "attempts": 0
            }
            self.db.track_referral_attempt(user_id, referral_code, "pending")
        
        channels = self.db.get_channels()
        
        # No channels
        if not channels:
            if not user.get("is_verified"):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user)
            return
        
        # Already verified
        if user.get("is_verified"):
            self.show_welcome_screen(chat_id, user_id, user)
            return
        
        # Check channels
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user)
        else:
            self.show_verification_screen(chat_id, user_id, username)
    
    def show_welcome_screen(self, chat_id, user_id, user):
        """Show welcome/main screen"""
        if not user:
            user = self.db.get_user(user_id)
        if not user:
            return
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 Admin" if is_admin else ""
        verified = "✅" if user.get("is_verified") else "❌"
        
        msg = f"""👋 <b>Welcome to TradeGenius07!</b>{admin_text}

👤 {user.get('username', 'User')} {verified}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>

💰 Balance: ₹{user.get('pending_balance', 0)}
👥 Referrals: {user.get('referrals', 0)}

Earn ₹{Config.REWARD_PER_REFERRAL} per referral!"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def process_pending_referral(self, user_id, username):
        """Process pending referral"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_referrals:
            return False
        
        pending = self.pending_referrals[user_id_str]
        referral_code = pending["referral_code"]
        
        user = self.db.get_user(user_id)
        if user and user.get("referral_claimed"):
            del self.pending_referrals[user_id_str]
            return True
        
        time.sleep(1)
        
        success = self.process_referral(user_id, username, referral_code)
        
        if success:
            del self.pending_referrals[user_id_str]
            self.db.track_referral_attempt(user_id, referral_code, "success")
        
        return success
    
    def process_referral(self, user_id, username, referral_code):
        """Process referral reward"""
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        if user.get("referral_claimed"):
            return True
        
        referrer_id, referrer = self.db.find_user_by_referral_code(referral_code)
        
        if not referrer or not referrer_id:
            return False
        
        if referrer_id == str(user_id):
            return False
        
        if not referrer.get("is_verified"):
            return False
        
        self.db.create_referral_record(user_id, referrer_id, "completed")
        
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL
        
        if new_refs == 10:
            reward += Config.BONUS_AT_10_REFERRALS
        
        self.db.update_user(referrer_id, {
            "referrals": new_refs,
            "pending_balance": referrer.get("pending_balance", 0) + reward,
            "total_earnings": referrer.get("total_earnings", 0) + reward
        })
        
        self.db.update_user(user_id, {
            "referrer": referrer_id,
            "referral_claimed": True,
            "referral_claimed_at": datetime.now().isoformat()
        })
        
        try:
            self.bot.send_message(
                referrer_id,
                f"🎉 <b>New Referral!</b>\n\n@{username} joined!\n💰 +₹{reward}\n👥 Total: {new_refs}"
            )
        except:
            pass
        
        return True
    
    # ==================== MESSAGE HANDLER ====================
    
    def handle_user_message(self, chat_id, user_id, text):
        """Handle text messages"""
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state.get("state") == "awaiting_channel":
            msg = self.process_add_channel(chat_id, user_id, text)
            buttons = [("📢 View", "admin_view_channels"), ("🔙 Back", "admin_channels")]
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
            del self.user_states[user_id]
        
        elif state.get("state") == "awaiting_upi":
            upi_id = text.strip()
            if '@' in upi_id and len(upi_id) > 5:
                self.db.update_upi_id(user_id, upi_id)
                msg = f"✅ UPI saved: <code>{upi_id}</code>"
                buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
            else:
                msg = "❌ Invalid UPI. Format: <code>name@bank</code>"
                buttons = [("❌ Cancel", "withdraw")]
            
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
            if '@' in upi_id:
                del self.user_states[user_id]
        
        elif state.get("state") == "awaiting_rejection_reason":
            self.process_rejection(user_id, text)
        
        elif state.get("state") == "awaiting_web_url":
            url = text.strip()
            if url.startswith(('http://', 'https://')):
                self.db.update_web_url(url)
                msg = f"✅ URL updated: {url}"
            else:
                msg = "❌ Must start with https://"
            
            buttons = [("🔙 Back", "admin_panel")]
            keyboard = self.generate_keyboard(buttons, 1)
            self.bot.send_message(chat_id, msg, keyboard)
            del self.user_states[user_id]
        
        elif state.get("state") == "awaiting_ai_button_name":
            name = text.strip()
            if 0 < len(name) <= 20:
                self.db.update_ai_button_name(name)
                msg = f"✅ Button name: {name}"
            else:
                msg = "❌ 1-20 characters only"
            
            buttons = [("🔙 Back", "admin_panel")]
            keyboard = self.generate_keyboard(buttons, 1)
            self.bot.send_message(chat_id, msg, keyboard)
            del self.user_states[user_id]
        
        elif text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                message = parts[1]
                users = self.db.get_all_users()
                total = len(users) if users else 0
                
                self.bot.send_message(chat_id, f"📢 Broadcasting to {total}...")
                
                success = 0
                for uid in users.keys():
                    try:
                        self.bot.send_message(uid, f"📢 {message}")
                        success += 1
                        time.sleep(0.1)
                    except:
                        pass
                
                self.bot.send_message(chat_id, f"✅ Sent: {success}/{total}")
    
    # ==================== CALLBACK HANDLER ====================
    
    def handle_callback(self, chat_id, message_id, user_id, cb_data):
        """Handle callback queries"""
        cb_id = cb_data["id"]
        callback = cb_data.get("data", "")
        
        self.bot.answer_callback_query(cb_id)
        
        user = self.db.get_user(user_id) or {}
        
        # Always allowed
        if callback == "check_verification":
            self.check_verification(chat_id, message_id, user_id)
            return
        
        if callback == "show_channels_again":
            self.show_verification_screen(chat_id, user_id, user.get("username", "User"))
            return
        
        # Admin check
        if callback == "admin_panel" and str(user_id) != Config.ADMIN_USER_ID:
            self.bot.edit_message_text(chat_id, message_id, "⛔ Access Denied")
            return
        
        # Verification check
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified"):
            if callback not in ["terms_conditions"]:
                msg = "❌ Please verify first!"
                keyboard = self.generate_keyboard([("✅ VERIFY", "check_verification")], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        # Route callbacks
        if callback == "main_menu":
            self.show_main_menu(chat_id, message_id, user_id, user)
        
        elif callback == "my_referral":
            self.show_referral_link(chat_id, message_id, user_id, user)
        
        elif callback == "dashboard":
            self.show_dashboard(chat_id, message_id, user_id, user)
        
        elif callback == "withdraw":
            self.show_withdraw_menu(chat_id, message_id, user_id, user)
        
        elif callback == "setup_upi":
            self.setup_upi(chat_id, message_id, user_id)
        
        elif callback == "request_withdraw":
            self.request_withdrawal(chat_id, message_id, user_id, user)
        
        elif callback == "withdraw_history":
            self.show_history(chat_id, message_id, user_id)
        
        elif callback == "open_web":
            self.show_web_button(chat_id, message_id)
        
        elif callback == "terms_conditions":
            self.show_terms(chat_id, message_id)
        
        elif callback == "how_it_works":
            self.show_how_it_works(chat_id, message_id)
        
        elif callback == "rewards":
            self.show_rewards(chat_id, message_id)
        
        elif callback == "support":
            self.show_support(chat_id, message_id)
        
        elif callback == "admin_panel":
            self.show_admin_panel(chat_id, message_id, user_id)
        
        elif callback.startswith("admin_"):
            if str(user_id) == Config.ADMIN_USER_ID:
                self.handle_admin_callback(chat_id, message_id, user_id, callback)
    
    # ==================== USER SCREENS ====================
    
    def show_main_menu(self, chat_id, message_id, user_id, user):
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = " 👑" if is_admin else ""
        
        msg = f"""🏠 <b>Menu</b>{admin_text}

💰 ₹{user.get('pending_balance', 0)}
👥 {user.get('referrals', 0)} referrals"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_referral_link(self, chat_id, message_id, user_id, user):
        code = user.get("referral_code", "")
        if not code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.db.update_user(user_id, {"referral_code": code})
        
        link = f"https://t.me/{Config.BOT_USERNAME}?start={code}"
        
        msg = f"""🔗 <b>Your Referral Link</b>

<code>{link}</code>

💰 Earn ₹{Config.REWARD_PER_REFERRAL}/referral!

👥 Referrals: {user.get('referrals', 0)}
💰 Earned: ₹{user.get('total_earnings', 0)}"""
        
        share_url = f"https://t.me/share/url?url={quote(link)}"
        
        buttons = [
            {"text": "📤 Share", "url": share_url},
            ("📊 Dashboard", "dashboard"),
            ("🏠 Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_dashboard(self, chat_id, message_id, user_id, user):
        v = "✅" if user.get("is_verified") else "❌"
        
        msg = f"""📊 <b>Dashboard</b>

👤 {user.get('username', 'User')} {v}
🔗 <code>{user.get('referral_code', 'N/A')}</code>
📱 {user.get('upi_id') or 'Not set'}

👥 Referrals: {user.get('referrals', 0)}
💰 Balance: ₹{user.get('pending_balance', 0)}
💸 Total: ₹{user.get('total_earnings', 0)}
✅ Withdrawn: ₹{user.get('withdrawn', 0)}"""
        
        buttons = [
            ("💳 Withdraw", "withdraw"),
            ("🔗 Link", "my_referral"),
            ("🏠 Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdraw_menu(self, chat_id, message_id, user_id, user):
        balance = user.get("pending_balance", 0)
        upi = user.get("upi_id", "")
        
        if not upi:
            msg = f"❌ <b>Setup UPI first</b>\n\nBalance: ₹{balance}\nMin: ₹{Config.MINIMUM_WITHDRAWAL}"
            buttons = [("📱 Setup UPI", "setup_upi"), ("🏠 Menu", "main_menu")]
        
        elif balance >= Config.MINIMUM_WITHDRAWAL:
            msg = f"💳 <b>Withdraw</b>\n\n💰 ₹{balance}\n📱 {upi}"
            buttons = [
                ("✅ Request", "request_withdraw"),
                ("✏️ Change UPI", "setup_upi"),
                ("🏠 Menu", "main_menu")
            ]
        else:
            need = Config.MINIMUM_WITHDRAWAL - balance
            refs = (need + Config.REWARD_PER_REFERRAL - 1) // Config.REWARD_PER_REFERRAL
            msg = f"❌ <b>Need ₹{need} more</b>\n\n💰 ₹{balance}\nMin: ₹{Config.MINIMUM_WITHDRAWAL}\n\nGet {refs} more referrals!"
            buttons = [("🔗 Get Link", "my_referral"), ("🏠 Menu", "main_menu")]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def setup_upi(self, chat_id, message_id, user_id):
        msg = "📱 <b>Send UPI ID</b>\n\nFormat: <code>name@bank</code>"
        
        self.user_states[user_id] = {
            "state": "awaiting_upi",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        keyboard = self.generate_keyboard([("❌ Cancel", "withdraw")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def request_withdrawal(self, chat_id, message_id, user_id, user):
        balance = user.get("pending_balance", 0)
        upi = user.get("upi_id", "")
        
        if balance < Config.MINIMUM_WITHDRAWAL or not upi:
            self.show_withdraw_menu(chat_id, message_id, user_id, user)
            return
        
        wd_id = f"WD{random.randint(100000, 999999)}"
        
        self.db.create_withdrawal(wd_id, {
            "user_id": str(user_id),
            "username": user.get("username", ""),
            "amount": balance,
            "upi_id": upi,
            "status": "pending",
            "requested_at": datetime.now().isoformat()
        })
        
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + balance
        })
        
        self.bot.send_message(
            Config.ADMIN_USER_ID,
            f"🆕 <b>Withdrawal</b>\n\n@{user.get('username', 'N/A')}\n₹{balance}\n{upi}\n{wd_id}"
        )
        
        msg = f"✅ <b>Submitted</b>\n\n📋 {wd_id}\n💰 ₹{balance}\n⏳ 24-72 hours"
        
        keyboard = self.generate_keyboard([("📜 History", "withdraw_history"), ("🏠 Menu", "main_menu")], 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_history(self, chat_id, message_id, user_id):
        wds = self.db.get_withdrawals()
        user_wds = {k: v for k, v in wds.items() if v and v.get("user_id") == str(user_id)}
        
        if not user_wds:
            msg = "📜 No withdrawals yet"
        else:
            msg = "📜 <b>History</b>\n\n"
            for wd_id, wd in sorted(user_wds.items(), key=lambda x: x[1].get("requested_at", ""), reverse=True)[:10]:
                status = wd.get("status", "pending")
                emoji = "✅" if status == "completed" else "❌" if status == "rejected" else "⏳"
                msg += f"{emoji} ₹{wd.get('amount', 0)} - {status}\n"
        
        keyboard = self.generate_keyboard([("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")], 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_web_button(self, chat_id, message_id):
        url = self.db.get_web_url()
        name = self.db.get_ai_button_name()
        
        buttons = [{"text": name, "url": url}, ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, "🤖 <b>AI Assistant</b>\n\nClick below:", keyboard)
    
    def show_terms(self, chat_id, message_id):
        msg = f"""📜 <b>Terms</b>

• Join all channels
• No self-referrals
• Min withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}
• Fraud = Ban"""
        
        keyboard = self.generate_keyboard([("✅ OK", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_how_it_works(self, chat_id, message_id):
        msg = f"""📢 <b>How It Works</b>

1️⃣ Join channels
2️⃣ Get referral link
3️⃣ Share with friends
4️⃣ Earn ₹{Config.REWARD_PER_REFERRAL}/referral
5️⃣ Withdraw to UPI"""
        
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_rewards(self, chat_id, message_id):
        msg = f"""🎁 <b>Rewards</b>

💰 ₹{Config.REWARD_PER_REFERRAL}/referral
🔥 +₹{Config.BONUS_AT_10_REFERRALS} bonus at 10 refs!

5 refs = ₹{5 * Config.REWARD_PER_REFERRAL}
10 refs = ₹{10 * Config.REWARD_PER_REFERRAL + Config.BONUS_AT_10_REFERRALS}"""
        
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_support(self, chat_id, message_id):
        msg = f"📞 <b>Support</b>\n\n{Config.SUPPORT_CHANNEL}"
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== ADMIN FUNCTIONS ====================
    
    def show_admin_panel(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        channels = self.db.get_channels()
        pending = self.db.get_withdrawals("pending")
        
        msg = f"""👑 <b>Admin</b>

👥 Users: {len(users) if users else 0}
📢 Channels: {len(channels) if channels else 0}
💳 Pending: {len(pending) if pending else 0}"""
        
        buttons = [
            ("📊 Stats", "admin_stats"),
            ("💳 Withdrawals", "admin_withdrawals"),
            ("📢 Channels", "admin_channels"),
            ("🌐 Web URL", "admin_web_url"),
            ("🤖 AI Button", "admin_ai_button"),
            ("👥 Users", "admin_users"),
            ("🏠 Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_admin_callback(self, chat_id, message_id, user_id, callback):
        if callback == "admin_stats":
            users = self.db.get_all_users() or {}
            channels = self.db.get_channels() or {}
            total = sum(u.get("total_earnings", 0) for u in users.values() if u)
            verified = sum(1 for u in users.values() if u and u.get("is_verified"))
            
            msg = f"""📊 <b>Stats</b>

👥 Total: {len(users)}
✅ Verified: {verified}
📢 Channels: {len(channels)}
💰 Total Earned: ₹{total}"""
            
            buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
        
        elif callback == "admin_channels":
            channels = self.db.get_channels()
            count = len(channels) if channels else 0
            
            msg = f"""📢 <b>Channels ({count})</b>

Bot must be ADMIN in channels!"""
            
            buttons = [
                ("➕ Add", "admin_add_channel"),
                ("👁 View", "admin_view_channels"),
                ("🔙 Back", "admin_panel")
            ]
        
        elif callback == "admin_add_channel":
            self.show_add_channel(chat_id, message_id, user_id)
            return
        
        elif callback == "admin_view_channels":
            self.show_channel_list(chat_id, message_id, user_id)
            return
        
        elif callback.startswith("admin_delete_channel_"):
            key = callback.replace("admin_delete_channel_", "")
            self.db.delete_channel(key)
            msg = "✅ Deleted"
            buttons = [("📢 View", "admin_view_channels"), ("🔙 Back", "admin_channels")]
        
        elif callback == "admin_withdrawals":
            pending = self.db.get_withdrawals("pending")
            
            if not pending:
                msg = "💳 No pending withdrawals"
                buttons = [("🔄 Refresh", "admin_withdrawals"), ("🔙 Back", "admin_panel")]
            else:
                msg = "💳 <b>Pending</b>\n\n"
                buttons = []
                
                for i, (wd_id, wd) in enumerate(pending.items(), 1):
                    if wd:
                        msg += f"{i}. ₹{wd.get('amount', 0)} @{wd.get('username', 'N/A')}\n   📱 {wd.get('upi_id', 'N/A')}\n\n"
                        buttons.append((f"✅{i}", f"admin_approve_{wd_id}"))
                        buttons.append((f"❌{i}", f"admin_reject_{wd_id}"))
                
                buttons.append(("🔄 Refresh", "admin_withdrawals"))
                buttons.append(("🔙 Back", "admin_panel"))
        
        elif callback.startswith("admin_approve_"):
            wd_id = callback.replace("admin_approve_", "")
            wds = self.db.get_withdrawals()
            wd = wds.get(wd_id) if wds else None
            
            if wd:
                self.db.update_withdrawal_status(wd_id, "completed")
                self.bot.send_message(wd["user_id"], f"✅ ₹{wd['amount']} approved!")
                msg = f"✅ Approved ₹{wd['amount']}"
            else:
                msg = "❌ Not found"
            
            buttons = [("💳 Back", "admin_withdrawals")]
        
        elif callback.startswith("admin_reject_"):
            wd_id = callback.replace("admin_reject_", "")
            wds = self.db.get_withdrawals()
            wd = wds.get(wd_id) if wds else None
            
            if wd:
                self.user_states[user_id] = {
                    "state": "awaiting_rejection_reason",
                    "wd_id": wd_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "target_user": wd.get("user_id"),
                    "amount": wd.get("amount", 0)
                }
                msg = f"❌ Rejecting ₹{wd.get('amount', 0)}\n\nSend reason:"
                buttons = [("❌ Cancel", "admin_withdrawals")]
            else:
                msg = "❌ Not found"
                buttons = [("💳 Back", "admin_withdrawals")]
        
        elif callback == "admin_web_url":
            url = self.db.get_web_url()
            msg = f"🌐 <b>Web URL</b>\n\n{url}"
            buttons = [("✏️ Update", "admin_update_web_url"), ("🔙 Back", "admin_panel")]
        
        elif callback == "admin_update_web_url":
            self.user_states[user_id] = {"state": "awaiting_web_url", "chat_id": chat_id, "message_id": message_id}
            msg = "Send new URL (https://...):"
            buttons = [("❌ Cancel", "admin_panel")]
        
        elif callback == "admin_ai_button":
            name = self.db.get_ai_button_name()
            msg = f"🤖 <b>AI Button</b>\n\n{name}"
            buttons = [("✏️ Update", "admin_update_ai_button"), ("🔙 Back", "admin_panel")]
        
        elif callback == "admin_update_ai_button":
            self.user_states[user_id] = {"state": "awaiting_ai_button_name", "chat_id": chat_id, "message_id": message_id}
            msg = "Send new button name (max 20 chars):"
            buttons = [("❌ Cancel", "admin_panel")]
        
        elif callback == "admin_users":
            users = self.db.get_all_users() or {}
            
            sorted_users = sorted(
                [(uid, u) for uid, u in users.items() if u],
                key=lambda x: x[1].get("referrals", 0),
                reverse=True
            )[:10]
            
            msg = "👥 <b>Top Users</b>\n\n"
            for i, (uid, u) in enumerate(sorted_users, 1):
                v = "✅" if u.get("is_verified") else "❌"
                msg += f"{i}. {v} {u.get('username', 'N/A')} - {u.get('referrals', 0)} refs\n"
            
            buttons = [("🔄 Refresh", "admin_users"), ("🔙 Back", "admin_panel")]
        
        else:
            return
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_rejection(self, admin_id, reason):
        if admin_id not in self.user_states:
            return
        
        state = self.user_states[admin_id]
        if state.get("state") != "awaiting_rejection_reason":
            return
        
        wd_id = state["wd_id"]
        target_user = state["target_user"]
        amount = state["amount"]
        
        self.db.update_withdrawal_status(wd_id, "rejected", reason)
        
        # Return balance
        user = self.db.get_user(target_user)
        if user:
            self.db.update_user(target_user, {"pending_balance": user.get("pending_balance", 0) + amount})
        
        self.bot.send_message(target_user, f"❌ ₹{amount} rejected\n\nReason: {reason}\n\n₹{amount} returned.")
        
        msg = "✅ Rejected & notified"
        keyboard = self.generate_keyboard([("💳 Back", "admin_withdrawals")], 1)
        self.bot.edit_message_text(state["chat_id"], state["message_id"], msg, keyboard)
        
        del self.user_states[admin_id]
    
    # ==================== BOT RUNNER ====================
    
    def run_bot(self):
        print("=" * 50)
        print("🤖 Trade Genius Bot v3.0 - FIXED")
        print("=" * 50)
        print(f"👑 Admin: {Config.ADMIN_USER_ID}")
        
        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
        time.sleep(2)
        
        channels = self.db.get_channels()
        print(f"📢 Channels: {len(channels) if channels else 0}")
        
        if channels:
            for key, ch in channels.items():
                print(f"   • {ch.get('name', 'N/A')} | ID: {ch.get('id', 'N/A')}")
        
        print("=" * 50)
        print("✅ Bot running!")
        print("=" * 50)
        
        self.offset = 0
        errors = 0
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset)
                
                if updates is None:
                    errors += 1
                    if errors > 5:
                        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
                        errors = 0
                        time.sleep(5)
                    else:
                        time.sleep(2)
                    continue
                
                errors = 0
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    try:
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
                                    args = text.split()[1:] if len(text.split()) > 1 else []
                                    self.start_command(chat_id, user_id, username, first_name, last_name, args)
                                
                                elif text.startswith("/admin") and str(user_id) == Config.ADMIN_USER_ID:
                                    self.show_admin_panel(chat_id, msg["message_id"], user_id)
                                
                                else:
                                    self.handle_user_message(chat_id, user_id, text)
                        
                        elif "callback_query" in update:
                            cb = update["callback_query"]
                            self.handle_callback(
                                cb["message"]["chat"]["id"],
                                cb["message"]["message_id"],
                                cb["from"]["id"],
                                cb
                            )
                    
                    except Exception as e:
                        print(f"❌ Update error: {e}")
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopped")
                self.running = False
                
            except Exception as e:
                print(f"❌ Error: {e}")
                errors += 1
                time.sleep(5)

# ==================== START ====================
def run_both():
    bot = TradeGeniusBot()
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Flask on port 5000")
    bot.run_bot()

if __name__ == "__main__":
    print("🔥 Trade Genius Bot v3.0")
    run_both()