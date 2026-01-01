# main.py - FIXED Channel Verification System v4.0

"""
🔥 Trade Genius Bot - FIXED CHANNEL SYSTEM
✅ Uses NUMERIC ID for verification (REQUIRED)
✅ Uses ANY link format for display buttons
✅ Proper invite link handling
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

# ==================== FLASK SERVER ====================
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "TradeGeniusBot",
        "version": "4.0 - Fixed"
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
            return None
        except Exception as e:
            return None

# ==================== FIREBASE HELPER ====================
class FirebaseDB:
    def __init__(self):
        self.base_url = Config.FIREBASE_URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        print(f"🔥 Firebase: {self.base_url}")
        self.local_data = self._load_local_backup()
    
    def _load_local_backup(self):
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {"users": {}, "withdrawals": {}, "referrals": {}, "channels": {}, "settings": {}}
    
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
        except:
            return None
    
    def _safe_key(self, key):
        """Convert to Firebase-safe key"""
        return str(key).replace("-", "neg").replace(".", "_").replace("/", "_").replace("+", "plus")
    
    # Channel methods
    def add_channel(self, channel_data):
        channel_id = channel_data.get("id", "")
        if not channel_id:
            return False
        
        safe_key = self._safe_key(channel_id)
        channel_data["safe_key"] = safe_key
        
        result = self._firebase_request("PUT", f"channels/{safe_key}", channel_data)
        
        if "channels" not in self.local_data:
            self.local_data["channels"] = {}
        self.local_data["channels"][safe_key] = channel_data
        self._save_local_backup()
        
        return True
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels")
        if data:
            return data
        return self.local_data.get("channels", {})
    
    def delete_channel(self, safe_key):
        self._firebase_request("DELETE", f"channels/{safe_key}")
        if "channels" in self.local_data:
            self.local_data["channels"].pop(safe_key, None)
            self._save_local_backup()
        return True
    
    # User methods
    def get_user(self, user_id):
        user_id = str(user_id)
        data = self._firebase_request("GET", f"users/{user_id}")
        if data:
            return data
        return self.local_data.get('users', {}).get(user_id, None)
    
    def create_user(self, user_id, username="User", first_name="", last_name=""):
        user_id = str(user_id)
        
        if not username or username == "User":
            username = first_name if first_name else f"User_{user_id[-6:]}"
            if last_name:
                username += f" {last_name}"
        
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
            "is_verified": is_admin,
            "channels_joined": {},
            "created_at": datetime.now().isoformat(),
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
        return self.update_user(user_id, {"is_verified": True, "verified_at": datetime.now().isoformat()})
    
    def track_referral_attempt(self, user_id, referral_code, status):
        """Track referral attempt"""
        attempt_id = f"ATT{user_id}_{int(time.time())}"
        data = {
            "user_id": str(user_id),
            "referral_code": referral_code,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self._firebase_request("PUT", f"referral_attempts/{attempt_id}", data)
        return True
    
    # Settings methods
    def get_ai_button_name(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("ai_button_name", Config.AI_BUTTON_NAME)
    
    def update_ai_button_name(self, name):
        self._firebase_request("PATCH", "settings", {"ai_button_name": name})
        return True
    
    def get_web_url(self):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("web_url", Config.WEB_URL)
    
    def update_web_url(self, url):
        self._firebase_request("PATCH", "settings", {"web_url": url})
        return True
    
    # Withdrawal methods
    def create_withdrawal(self, wd_id, data):
        return self._firebase_request("PUT", f"withdrawals/{wd_id}", data)
    
    def get_withdrawals(self, status=None):
        wds = self._firebase_request("GET", "withdrawals") or {}
        if status:
            return {k: v for k, v in wds.items() if v and v.get("status") == status}
        return wds
    
    def update_withdrawal_status(self, wd_id, status, note=""):
        updates = {"status": status, "processed_at": datetime.now().isoformat()}
        if note:
            updates["admin_note"] = note
        return self._firebase_request("PATCH", f"withdrawals/{wd_id}", updates)
    
    def update_upi_id(self, user_id, upi):
        return self.update_user(user_id, {"upi_id": upi})
    
    def get_all_users(self):
        data = self._firebase_request("GET", "users")
        if data:
            return data
        return self.local_data.get("users", {})
    
    def find_user_by_referral_code(self, code):
        users = self.get_all_users()
        for uid, data in users.items():
            if data and data.get("referral_code") == code:
                return uid, data
        return None, None
    
    def create_referral_record(self, new_user, referrer, status):
        ref_id = f"REF{new_user}_{int(time.time())}"
        data = {
            "new_user_id": str(new_user),
            "referrer_id": str(referrer),
            "status": status,
            "created_at": datetime.now().isoformat(),
            "reward_amount": Config.REWARD_PER_REFERRAL if status == "completed" else 0
        }
        self._firebase_request("PUT", f"referrals/{ref_id}", data)
        return True

# ==================== TELEGRAM API ====================
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
        """Get chat info to verify bot has access"""
        return self._api_request("getChat", {"chat_id": chat_id})
    
    def get_chat_member(self, chat_id, user_id):
        """Check membership using NUMERIC chat_id"""
        try:
            return self._api_request("getChatMember", {"chat_id": int(chat_id), "user_id": int(user_id)})
        except:
            return None
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._api_request("sendMessage", data)
    
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._api_request("editMessageText", data)
    
    def answer_callback_query(self, cb_id, text=None, show_alert=False):
        data = {"callback_query_id": cb_id, "show_alert": show_alert}
        if text:
            data["text"] = text
        return self._api_request("answerCallbackQuery", data)
    
    def get_updates(self, offset=None, timeout=60):
        data = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if offset:
            data["offset"] = offset
        return self._api_request("getUpdates", data) or []

# ==================== MAIN BOT ====================
class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBotAPI(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.user_states = {}
        self.pending_referrals = {}
    
    # ==================== FIXED CHANNEL VERIFICATION ====================
    
    def check_user_membership(self, numeric_channel_id, user_id):
        """
        Check if user is member using NUMERIC channel ID
        This is the ONLY way to verify membership via Telegram API
        """
        try:
            # Clean and validate the channel ID
            channel_id = str(numeric_channel_id).strip()
            
            # Must be numeric
            if not channel_id.lstrip('-').isdigit():
                print(f"      ⚠️ Not a numeric ID: {channel_id}")
                return False, "invalid_id_format"
            
            channel_id_int = int(channel_id)
            user_id_int = int(user_id)
            
            print(f"      📡 Checking: getChatMember({channel_id_int}, {user_id_int})")
            
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
                return False, "api_failed"
                
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
            channel_id = channel.get("id", "")  # NUMERIC ID - THIS IS WHAT WE USE
            channel_link = channel.get("link", "")  # For display only
            
            print(f"\n📢 {channel_name}")
            print(f"   🔗 Link: {channel_link}")
            print(f"   🆔 ID: {channel_id}")
            
            # MUST have numeric channel ID
            if not channel_id:
                print(f"   ⚠️ No channel ID configured!")
                print(f"   💡 Add channel with numeric ID like: -1001234567890")
                continue
            
            # Validate it's numeric
            if not str(channel_id).lstrip('-').isdigit():
                print(f"   ⚠️ Invalid ID format: {channel_id}")
                print(f"   💡 ID must be numeric like: -1001234567890")
                continue
            
            # Check if recently verified (cache)
            joined_info = user.get("channels_joined", {}).get(channel_key, {})
            if joined_info.get("verified", False):
                joined_at = joined_info.get("joined_at", "")
                if joined_at:
                    try:
                        jtime = datetime.fromisoformat(joined_at)
                        if (datetime.now() - jtime).seconds < 600:  # 10 min cache
                            print(f"   ✅ Cached as verified")
                            continue
                    except:
                        pass
            
            # Check membership using NUMERIC ID
            is_member, status = self.check_user_membership(channel_id, user_id)
            
            if is_member:
                print(f"   ✅ Verified: {status}")
                self.db.mark_channel_joined(user_id, channel_key)
            else:
                print(f"   ❌ Not member: {status}")
                all_joined = False
                failed_channels.append(channel_name)
                break
            
            time.sleep(0.3)
        
        print(f"\n{'='*50}")
        if all_joined:
            print("🎉 All channels verified!")
        else:
            print(f"❌ Failed: {', '.join(failed_channels)}")
        print(f"{'='*50}\n")
        
        return all_joined
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    def show_add_channel(self, chat_id, message_id, user_id):
        """Show channel add instructions"""
        msg = """➕ <b>Add New Channel</b>

Send in <b>3 lines</b>:

<code>Channel Name
Channel Link
Channel ID</code>

━━━━━━━━━━━━━━━━━━━━━━
<b>📌 EXAMPLE:</b>

<code>VIP Trading Group
https://t.me/+KxTBB1C2hyZlYTU1
-1002123456789</code>

━━━━━━━━━━━━━━━━━━━━━━
<b>⚠️ IMPORTANT:</b>

1️⃣ <b>Channel Link</b> = For join button
   • Any format: https://t.me/+ABC...
   • Or: @username
   • Or: https://t.me/username

2️⃣ <b>Channel ID</b> = For verification
   • MUST be numeric: <code>-1001234567890</code>
   • Get from: @username_to_id_bot
   • Or: @getidsbot
   • Or: @RawDataBot

3️⃣ <b>Bot must be ADMIN</b> in the channel!

━━━━━━━━━━━━━━━━━━━━━━
❌ Without numeric ID, verification WON'T work!
Invite links cannot be used for verification."""

        self.user_states[user_id] = {"state": "awaiting_channel", "chat_id": chat_id, "message_id": message_id}
        
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
3. Channel ID (numeric!)

Example:
<code>My Channel
https://t.me/+ABC123
-1001234567890</code>"""
        
        channel_name = lines[0].strip()
        channel_link = lines[1].strip()
        channel_id = lines[2].strip()
        
        # Validate name
        if len(channel_name) < 2:
            return "❌ Channel name too short"
        
        # Validate link
        if not channel_link:
            return "❌ Channel link required"
        
        # Validate ID - MUST BE NUMERIC
        clean_id = channel_id.lstrip('-')
        if not clean_id.isdigit():
            return f"""❌ <b>Invalid Channel ID!</b>

You entered: <code>{channel_id}</code>

Channel ID MUST be numeric like:
<code>-1001234567890</code>

<b>How to get it:</b>
1. Forward a message from channel to @getidsbot
2. Or add @username_to_id_bot to channel
3. Or use @RawDataBot

⚠️ Invite links like https://t.me/+ABC CANNOT be used as ID!"""
        
        # Format channel ID correctly
        if not channel_id.startswith('-'):
            channel_id = '-100' + channel_id
        elif channel_id.startswith('-') and not channel_id.startswith('-100'):
            channel_id = '-100' + channel_id.lstrip('-')
        
        # Test bot access
        print(f"🔍 Testing access to channel: {channel_id}")
        chat_info = self.bot.get_chat(int(channel_id))
        
        warning = ""
        chat_title = channel_name
        
        if chat_info:
            chat_title = chat_info.get("title", channel_name)
            print(f"   ✅ Access OK: {chat_title}")
        else:
            print(f"   ⚠️ Cannot access channel")
            warning = "\n\n⚠️ <b>Warning:</b> Bot cannot access this channel. Make sure bot is ADMIN!"
        
        # Make link clickable
        display_link = channel_link
        if not display_link.startswith(('http://', 'https://')):
            if display_link.startswith('@'):
                display_link = f"https://t.me/{display_link[1:]}"
            elif display_link.startswith('t.me/'):
                display_link = f"https://{display_link}"
            elif not display_link.startswith('+'):
                display_link = f"https://t.me/{display_link}"
        
        # Determine type
        if '+' in channel_link or 'joinchat' in channel_link:
            link_type = "invite"
        else:
            link_type = "public"
        
        # Save
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
        
        self.db.add_channel(channel_data)
        
        emoji = "🔐" if link_type == "invite" else "📢"
        return f"""✅ <b>Channel Added!</b>

{emoji} <b>Name:</b> {channel_name}
📛 <b>Title:</b> {chat_title}
🔗 <b>Link:</b> <code>{channel_link}</code>
🆔 <b>ID:</b> <code>{channel_id}</code>
📋 <b>Type:</b> {link_type.upper()}{warning}

Users must join this channel!"""
    
    def show_channel_list(self, chat_id, message_id, user_id):
        """List channels"""
        channels = self.db.get_channels()
        
        if not channels:
            msg = "📢 <b>No Channels</b>\n\nAdd channels to require verification."
            buttons = [("➕ Add", "admin_add_channel"), ("🔙 Back", "admin_channels")]
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
                
                buttons.append((f"❌ {i}", f"admin_delete_channel_{key}"))
            
            buttons.append(("➕ Add", "admin_add_channel"))
            buttons.append(("🔙 Back", "admin_channels"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_screen(self, chat_id, user_id, username):
        """Show verification screen"""
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, None, user_id)
            return
        
        msg = """🔐 <b>Verification Required</b>

Join ALL channels below:"""
        
        buttons = []
        
        for key, ch in channels.items():
            name = ch.get("name", "Channel")
            link = ch.get("link", "")
            link_type = ch.get("link_type", "public")
            
            if not link:
                continue
            
            clean_name = name.replace("📢", "").replace("🔔", "").strip() or "Join"
            emoji = "🔐" if link_type == "invite" else "📢"
            
            buttons.append({"text": f"{emoji} {clean_name}", "url": link})
            msg += f"\n• {emoji} <b>{clean_name}</b>"
        
        buttons.append(("✅ VERIFY NOW", "check_verification"))
        
        msg += """

━━━━━━━━━━━━━━━━━━━━━━
<b>Steps:</b>
1️⃣ Click each button to join
2️⃣ Wait 5-10 seconds
3️⃣ Click VERIFY"""
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id, message_id, user_id):
        """Handle verify click"""
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ Error. /start again.")
            return
        
        attempts = user.get("verification_attempts", 0) + 1
        self.db.update_user(user_id, {"verification_attempts": attempts})
        
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, user.get("username", "User"))
            
            self.show_verification_success(chat_id, message_id, user_id)
        else:
            self.show_verification_failed(chat_id, message_id, attempts)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verified!</b>

Welcome @{username}!
Earn ₹{Config.REWARD_PER_REFERRAL} per referral!"""
        
        buttons = [("🔗 Referral Link", "my_referral"), ("📊 Dashboard", "dashboard"), ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 2)
        
        if message_id:
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
        else:
            self.bot.send_message(chat_id, msg, keyboard)
    
    def show_verification_failed(self, chat_id, message_id, attempts):
        msg = f"""❌ <b>Verification Failed</b>

You haven't joined all channels.

<b>Steps:</b>
1. Click each channel button
2. ACTUALLY JOIN (not just view)
3. Wait 10 seconds
4. Click VERIFY

Attempt: {attempts}

⚠️ Make sure you joined, not just viewed!"""
        
        buttons = [("🔄 Try Again", "check_verification"), ("📋 Channels", "show_channels_again")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== UTILITY ====================
    
    def generate_keyboard(self, buttons, columns=2):
        keyboard = []
        row = []
        
        for i, btn in enumerate(buttons):
            if isinstance(btn, tuple):
                row.append({"text": btn[0], "callback_data": btn[1]})
            elif isinstance(btn, dict):
                row.append(btn)
            
            if len(row) == columns or i == len(buttons) - 1:
                if row:
                    keyboard.append(row)
                row = []
        
        return {"inline_keyboard": keyboard}
    
    def get_menu_buttons(self, user_id):
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
    
    # ==================== COMMANDS ====================
    
    def start_command(self, chat_id, user_id, username, first_name, last_name, args):
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username, first_name, last_name)
        
        # Admin bypass
        if str(user_id) == Config.ADMIN_USER_ID:
            if not user.get("is_verified"):
                self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            self.show_welcome(chat_id, user_id, user)
            return
        
        # Store referral
        if args:
            self.pending_referrals[str(user_id)] = {"referral_code": args[0], "attempts": 0}
            self.db.track_referral_attempt(user_id, args[0], "pending")
        
        channels = self.db.get_channels()
        
        if not channels:
            if not user.get("is_verified"):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome(chat_id, user_id, user)
            return
        
        if user.get("is_verified"):
            self.show_welcome(chat_id, user_id, user)
            return
        
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome(chat_id, user_id, user)
        else:
            self.show_verification_screen(chat_id, user_id, username)
    
    def show_welcome(self, chat_id, user_id, user):
        if not user:
            user = self.db.get_user(user_id)
        if not user:
            return
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_txt = " 👑" if is_admin else ""
        verified = "✅" if user.get("is_verified") else "❌"
        
        msg = f"""👋 <b>Welcome to TradeGenius07!</b>{admin_txt}

{verified} {user.get('username', 'User')}
🔗 <code>{user.get('referral_code', 'N/A')}</code>

💰 Balance: ₹{user.get('pending_balance', 0)}
👥 Referrals: {user.get('referrals', 0)}

Earn ₹{Config.REWARD_PER_REFERRAL}/referral!"""
        
        buttons = self.get_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def process_pending_referral(self, user_id, username):
        uid = str(user_id)
        if uid not in self.pending_referrals:
            return False
        
        pending = self.pending_referrals[uid]
        code = pending["referral_code"]
        
        user = self.db.get_user(user_id)
        if user and user.get("referral_claimed"):
            del self.pending_referrals[uid]
            return True
        
        time.sleep(1)
        success = self.process_referral(user_id, username, code)
        
        if success:
            del self.pending_referrals[uid]
            self.db.track_referral_attempt(user_id, code, "success")
        
        return success
    
    def process_referral(self, user_id, username, code):
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        if user.get("referral_claimed"):
            return True
        
        referrer_id, referrer = self.db.find_user_by_referral_code(code)
        
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
            self.bot.send_message(referrer_id, f"🎉 @{username} joined!\n+₹{reward}\nTotal: {new_refs} refs")
        except:
            pass
        
        return True
    
    # ==================== MESSAGE HANDLER ====================
    
    def handle_message(self, chat_id, user_id, text):
        if user_id not in self.user_states:
            if text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
                parts = text.split(maxsplit=1)
                if len(parts) > 1:
                    users = self.db.get_all_users()
                    self.bot.send_message(chat_id, f"📢 Sending to {len(users)}...")
                    success = 0
                    for uid in users:
                        try:
                            self.bot.send_message(uid, f"📢 {parts[1]}")
                            success += 1
                            time.sleep(0.1)
                        except:
                            pass
                    self.bot.send_message(chat_id, f"✅ {success}/{len(users)}")
            return
        
        state = self.user_states[user_id]
        
        if state.get("state") == "awaiting_channel":
            msg = self.process_add_channel(chat_id, user_id, text)
            buttons = [("📢 View", "admin_view_channels"), ("🔙 Back", "admin_channels")]
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
            del self.user_states[user_id]
        
        elif state.get("state") == "awaiting_upi":
            upi = text.strip()
            if '@' in upi and len(upi) > 5:
                self.db.update_upi_id(user_id, upi)
                msg = f"✅ UPI saved: <code>{upi}</code>"
                buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
                del self.user_states[user_id]
            else:
                msg = "❌ Invalid. Format: name@bank"
                buttons = [("❌ Cancel", "withdraw")]
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
        
        elif state.get("state") == "awaiting_rejection_reason":
            self.process_rejection(user_id, text)
        
        elif state.get("state") == "awaiting_web_url":
            url = text.strip()
            if url.startswith(('http://', 'https://')):
                self.db.update_web_url(url)
                msg = f"✅ URL: {url}"
            else:
                msg = "❌ Must start with https://"
            self.bot.send_message(chat_id, msg, self.generate_keyboard([("🔙 Back", "admin_panel")], 1))
            del self.user_states[user_id]
        
        elif state.get("state") == "awaiting_ai_button_name":
            name = text.strip()
            if 0 < len(name) <= 20:
                self.db.update_ai_button_name(name)
                msg = f"✅ Button: {name}"
            else:
                msg = "❌ 1-20 chars only"
            self.bot.send_message(chat_id, msg, self.generate_keyboard([("🔙 Back", "admin_panel")], 1))
            del self.user_states[user_id]
    
    # ==================== CALLBACK HANDLER ====================
    
    def handle_callback(self, chat_id, message_id, user_id, cb):
        cb_id = cb["id"]
        callback = cb.get("data", "")
        
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
                keyboard = self.generate_keyboard([("✅ VERIFY", "check_verification")], 1)
                self.bot.edit_message_text(chat_id, message_id, "❌ Verify first!", keyboard)
                return
        
        # Route
        if callback == "main_menu":
            self.show_main_menu(chat_id, message_id, user_id, user)
        elif callback == "my_referral":
            self.show_referral(chat_id, message_id, user_id, user)
        elif callback == "dashboard":
            self.show_dashboard(chat_id, message_id, user_id, user)
        elif callback == "withdraw":
            self.show_withdraw(chat_id, message_id, user_id, user)
        elif callback == "setup_upi":
            self.setup_upi(chat_id, message_id, user_id)
        elif callback == "request_withdraw":
            self.request_withdrawal(chat_id, message_id, user_id, user)
        elif callback == "withdraw_history":
            self.show_history(chat_id, message_id, user_id)
        elif callback == "open_web":
            self.show_web(chat_id, message_id)
        elif callback == "terms_conditions":
            self.show_terms(chat_id, message_id)
        elif callback == "how_it_works":
            self.show_how(chat_id, message_id)
        elif callback == "rewards":
            self.show_rewards(chat_id, message_id)
        elif callback == "support":
            self.show_support(chat_id, message_id)
        elif callback == "admin_panel":
            self.show_admin(chat_id, message_id, user_id)
        elif callback.startswith("admin_"):
            if str(user_id) == Config.ADMIN_USER_ID:
                self.handle_admin(chat_id, message_id, user_id, callback)
    
    # ==================== USER SCREENS ====================
    
    def show_main_menu(self, chat_id, message_id, user_id, user):
        is_admin = str(user_id) == Config.ADMIN_USER_ID
        v = "✅" if user.get("is_verified") else "❌"
        
        msg = f"""🏠 <b>Menu</b>{' 👑' if is_admin else ''}

{v} {user.get('username', 'User')}
💰 ₹{user.get('pending_balance', 0)}
👥 {user.get('referrals', 0)} refs"""
        
        keyboard = self.generate_keyboard(self.get_menu_buttons(user_id), 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_referral(self, chat_id, message_id, user_id, user):
        code = user.get("referral_code", "")
        if not code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.db.update_user(user_id, {"referral_code": code})
        
        link = f"https://t.me/{Config.BOT_USERNAME}?start={code}"
        
        msg = f"""🔗 <b>Your Link</b>

<code>{link}</code>

₹{Config.REWARD_PER_REFERRAL}/referral!

👥 {user.get('referrals', 0)} refs
💰 ₹{user.get('total_earnings', 0)} earned"""
        
        share = f"https://t.me/share/url?url={quote(link)}"
        buttons = [{"text": "📤 Share", "url": share}, ("📊 Dashboard", "dashboard"), ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_dashboard(self, chat_id, message_id, user_id, user):
        v = "✅" if user.get("is_verified") else "❌"
        
        msg = f"""📊 <b>Dashboard</b>

{v} {user.get('username', 'User')}
🔗 <code>{user.get('referral_code', 'N/A')}</code>
📱 {user.get('upi_id') or 'Not set'}

👥 {user.get('referrals', 0)} refs
💰 ₹{user.get('pending_balance', 0)} pending
💸 ₹{user.get('total_earnings', 0)} total
✅ ₹{user.get('withdrawn', 0)} withdrawn"""
        
        buttons = [("💳 Withdraw", "withdraw"), ("🔗 Link", "my_referral"), ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdraw(self, chat_id, message_id, user_id, user):
        bal = user.get("pending_balance", 0)
        upi = user.get("upi_id", "")
        
        if not upi:
            msg = f"❌ <b>Setup UPI first</b>\n\nBalance: ₹{bal}\nMin: ₹{Config.MINIMUM_WITHDRAWAL}"
            buttons = [("📱 Setup UPI", "setup_upi"), ("🏠 Menu", "main_menu")]
        elif bal >= Config.MINIMUM_WITHDRAWAL:
            msg = f"💳 <b>Withdraw</b>\n\n💰 ₹{bal}\n📱 {upi}"
            buttons = [("✅ Request", "request_withdraw"), ("✏️ UPI", "setup_upi"), ("🏠 Menu", "main_menu")]
        else:
            need = Config.MINIMUM_WITHDRAWAL - bal
            refs = (need + Config.REWARD_PER_REFERRAL - 1) // Config.REWARD_PER_REFERRAL
            msg = f"❌ Need ₹{need} more ({refs} refs)"
            buttons = [("🔗 Link", "my_referral"), ("🏠 Menu", "main_menu")]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def setup_upi(self, chat_id, message_id, user_id):
        msg = "📱 Send UPI ID:\n<code>name@bank</code>"
        self.user_states[user_id] = {"state": "awaiting_upi"}
        keyboard = self.generate_keyboard([("❌ Cancel", "withdraw")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def request_withdrawal(self, chat_id, message_id, user_id, user):
        bal = user.get("pending_balance", 0)
        upi = user.get("upi_id", "")
        
        if bal < Config.MINIMUM_WITHDRAWAL or not upi:
            self.show_withdraw(chat_id, message_id, user_id, user)
            return
        
        wd_id = f"WD{random.randint(100000, 999999)}"
        
        self.db.create_withdrawal(wd_id, {
            "user_id": str(user_id),
            "username": user.get("username", ""),
            "amount": bal,
            "upi_id": upi,
            "status": "pending",
            "requested_at": datetime.now().isoformat()
        })
        
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + bal
        })
        
        self.bot.send_message(Config.ADMIN_USER_ID, f"🆕 ₹{bal}\n@{user.get('username','N/A')}\n{upi}\n{wd_id}")
        
        msg = f"✅ <b>Submitted</b>\n\n{wd_id}\n₹{bal}\n24-72 hours"
        keyboard = self.generate_keyboard([("📜 History", "withdraw_history"), ("🏠 Menu", "main_menu")], 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_history(self, chat_id, message_id, user_id):
        wds = self.db.get_withdrawals()
        user_wds = {k: v for k, v in wds.items() if v and v.get("user_id") == str(user_id)}
        
        if not user_wds:
            msg = "📜 No history"
        else:
            msg = "📜 <b>History</b>\n\n"
            for wd_id, wd in sorted(user_wds.items(), key=lambda x: x[1].get("requested_at", ""), reverse=True)[:10]:
                s = wd.get("status", "pending")
                e = "✅" if s == "completed" else "❌" if s == "rejected" else "⏳"
                msg += f"{e} ₹{wd.get('amount', 0)} - {s}\n"
        
        keyboard = self.generate_keyboard([("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")], 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_web(self, chat_id, message_id):
        url = self.db.get_web_url()
        name = self.db.get_ai_button_name()
        buttons = [{"text": name, "url": url}, ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, "🤖 Click below:", keyboard)
    
    def show_terms(self, chat_id, message_id):
        msg = f"📜 <b>Terms</b>\n\n• Join channels\n• No self-referrals\n• Min ₹{Config.MINIMUM_WITHDRAWAL}"
        keyboard = self.generate_keyboard([("✅ OK", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_how(self, chat_id, message_id):
        msg = f"📢 <b>How</b>\n\n1. Join channels\n2. Get link\n3. Share\n4. Earn ₹{Config.REWARD_PER_REFERRAL}/ref"
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_rewards(self, chat_id, message_id):
        msg = f"🎁 <b>Rewards</b>\n\n₹{Config.REWARD_PER_REFERRAL}/ref\n+₹{Config.BONUS_AT_10_REFERRALS} at 10 refs!"
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_support(self, chat_id, message_id):
        msg = f"📞 {Config.SUPPORT_CHANNEL}"
        keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== ADMIN ====================
    
    def show_admin(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        channels = self.db.get_channels()
        pending = self.db.get_withdrawals("pending")
        
        msg = f"""👑 <b>Admin</b>

👥 {len(users) if users else 0}
📢 {len(channels) if channels else 0}
💳 {len(pending) if pending else 0} pending"""
        
        buttons = [
            ("📊 Stats", "admin_stats"),
            ("💳 Withdrawals", "admin_withdrawals"),
            ("📢 Channels", "admin_channels"),
            ("🌐 URL", "admin_web_url"),
            ("🤖 Button", "admin_ai_button"),
            ("👥 Users", "admin_users"),
            ("🏠 Menu", "main_menu")
        ]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_admin(self, chat_id, message_id, user_id, callback):
        if callback == "admin_stats":
            users = self.db.get_all_users() or {}
            channels = self.db.get_channels() or {}
            total = sum(u.get("total_earnings", 0) for u in users.values() if u)
            verified = sum(1 for u in users.values() if u and u.get("is_verified"))
            
            msg = f"📊 <b>Stats</b>\n\n👥 {len(users)} ({verified} verified)\n📢 {len(channels)} channels\n💰 ₹{total} total"
            buttons = [("🔄", "admin_stats"), ("🔙", "admin_panel")]
        
        elif callback == "admin_channels":
            channels = self.db.get_channels()
            msg = f"📢 <b>Channels ({len(channels) if channels else 0})</b>"
            buttons = [("➕ Add", "admin_add_channel"), ("👁 View", "admin_view_channels"), ("🔙", "admin_panel")]
        
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
            buttons = [("📢 View", "admin_view_channels"), ("🔙", "admin_channels")]
        
        elif callback == "admin_withdrawals":
            pending = self.db.get_withdrawals("pending")
            if not pending:
                msg = "💳 No pending"
                buttons = [("🔄", "admin_withdrawals"), ("🔙", "admin_panel")]
            else:
                msg = "💳 <b>Pending</b>\n\n"
                buttons = []
                for i, (wd_id, wd) in enumerate(pending.items(), 1):
                    if wd:
                        msg += f"{i}. ₹{wd.get('amount',0)} @{wd.get('username','N/A')}\n   {wd.get('upi_id','N/A')}\n\n"
                        buttons.append((f"✅{i}", f"admin_approve_{wd_id}"))
                        buttons.append((f"❌{i}", f"admin_reject_{wd_id}"))
                buttons.append(("🔄", "admin_withdrawals"))
                buttons.append(("🔙", "admin_panel"))
        
        elif callback.startswith("admin_approve_"):
            wd_id = callback.replace("admin_approve_", "")
            wds = self.db.get_withdrawals()
            wd = wds.get(wd_id) if wds else None
            if wd:
                self.db.update_withdrawal_status(wd_id, "completed")
                self.bot.send_message(wd["user_id"], f"✅ ₹{wd['amount']} approved!")
                msg = "✅ Approved"
            else:
                msg = "❌ Not found"
            buttons = [("💳", "admin_withdrawals")]
        
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
                    "target": wd.get("user_id"),
                    "amount": wd.get("amount", 0)
                }
                msg = f"Send rejection reason for ₹{wd.get('amount', 0)}:"
                buttons = [("❌ Cancel", "admin_withdrawals")]
            else:
                msg = "❌ Not found"
                buttons = [("💳", "admin_withdrawals")]
        
        elif callback == "admin_web_url":
            url = self.db.get_web_url()
            msg = f"🌐 <b>URL</b>\n\n{url}"
            buttons = [("✏️", "admin_update_web_url"), ("🔙", "admin_panel")]
        
        elif callback == "admin_update_web_url":
            self.user_states[user_id] = {"state": "awaiting_web_url"}
            msg = "Send new URL:"
            buttons = [("❌", "admin_panel")]
        
        elif callback == "admin_ai_button":
            name = self.db.get_ai_button_name()
            msg = f"🤖 <b>Button</b>\n\n{name}"
            buttons = [("✏️", "admin_update_ai_button"), ("🔙", "admin_panel")]
        
        elif callback == "admin_update_ai_button":
            self.user_states[user_id] = {"state": "awaiting_ai_button_name"}
            msg = "Send new name (max 20):"
            buttons = [("❌", "admin_panel")]
        
        elif callback == "admin_users":
            users = self.db.get_all_users() or {}
            sorted_u = sorted([(k, v) for k, v in users.items() if v], key=lambda x: x[1].get("referrals", 0), reverse=True)[:10]
            
            msg = "👥 <b>Top Users</b>\n\n"
            for i, (uid, u) in enumerate(sorted_u, 1):
                v = "✅" if u.get("is_verified") else "❌"
                msg += f"{i}. {v} {u.get('username','N/A')} - {u.get('referrals',0)} refs\n"
            
            buttons = [("🔄", "admin_users"), ("🔙", "admin_panel")]
        
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
        target = state["target"]
        amount = state["amount"]
        
        self.db.update_withdrawal_status(wd_id, "rejected", reason)
        
        user = self.db.get_user(target)
        if user:
            self.db.update_user(target, {"pending_balance": user.get("pending_balance", 0) + amount})
        
        self.bot.send_message(target, f"❌ ₹{amount} rejected\n{reason}\n\nReturned to balance.")
        
        keyboard = self.generate_keyboard([("💳", "admin_withdrawals")], 1)
        self.bot.edit_message_text(state["chat_id"], state["message_id"], "✅ Rejected", keyboard)
        
        del self.user_states[admin_id]
    
    # ==================== RUN ====================
    
    def run_bot(self):
        print("=" * 50)
        print("🤖 Trade Genius Bot v4.0 - FIXED")
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
        print("✅ Running!")
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
                            
                            if "text" in msg:
                                text = msg["text"]
                                
                                if text.startswith("/start"):
                                    args = text.split()[1:] if len(text.split()) > 1 else []
                                    self.start_command(
                                        chat_id, user_id,
                                        msg["from"].get("username", ""),
                                        msg["from"].get("first_name", ""),
                                        msg["from"].get("last_name", ""),
                                        args
                                    )
                                elif text.startswith("/admin") and str(user_id) == Config.ADMIN_USER_ID:
                                    self.show_admin(chat_id, msg["message_id"], user_id)
                                else:
                                    self.handle_message(chat_id, user_id, text)
                        
                        elif "callback_query" in update:
                            cb = update["callback_query"]
                            self.handle_callback(
                                cb["message"]["chat"]["id"],
                                cb["message"]["message_id"],
                                cb["from"]["id"],
                                cb
                            )
                    except Exception as e:
                        print(f"❌ Error: {e}")
                
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
    
    print("🌐 Flask on 5000")
    bot.run_bot()

if __name__ == "__main__":
    print("🔥 Trade Genius Bot v4.0")
    run_both()