# main.py - Simplified Channel Link System with Auto-Detection

"""
🔥 Trade Genius Bot - SIMPLIFIED CHANNEL SYSTEM
✅ Only Link + Name required
✅ Auto-detects channel type
✅ Smart verification for public channels
✅ Manual verification option for invite links
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
        "feature": "Simplified Channel System v3.0"
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
    
    def add_channel(self, channel_data):
        """Add channel with auto-generated ID"""
        channel_id = f"CH{int(time.time())}_{random.randint(1000, 9999)}"
        channel_data["id"] = channel_id
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        
        if result is not None:
            if "channels" not in self.local_data:
                self.local_data["channels"] = {}
            self.local_data["channels"][channel_id] = channel_data
            self._save_local_backup()
            return channel_id
        
        return None
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels") or {}
        return data
    
    def delete_channel(self, channel_id):
        result = self._firebase_request("DELETE", f"channels/{channel_id}")
        
        if "channels" in self.local_data:
            self.local_data["channels"].pop(channel_id, None)
            self._save_local_backup()
        
        return True
    
    def get_channel(self, channel_id):
        data = self._firebase_request("GET", f"channels/{channel_id}")
        
        if data:
            return data
        else:
            return self.local_data.get('channels', {}).get(channel_id, None)
    
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
        
        return True
    
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
    
    def track_referral_attempt(self, user_id, referral_code, status):
        attempt_id = f"ATT{user_id}_{int(time.time())}"
        attempt_data = {
            "user_id": str(user_id),
            "referral_code": referral_code,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        return self._firebase_request("PUT", f"referral_attempts/{attempt_id}", attempt_data)
    
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
                time.sleep(2)
                return None
            return None
        except Exception as e:
            return None
    
    def get_chat(self, chat_id):
        """Get chat info to validate channel"""
        try:
            data = {"chat_id": chat_id}
            result = self._api_request("getChat", data)
            return result
        except Exception as e:
            return None
    
    def get_chat_member(self, chat_id, user_id):
        """Check if user is member of chat"""
        try:
            data = {
                "chat_id": chat_id,
                "user_id": user_id
            }
            result = self._api_request("getChatMember", data)
            return result
        except Exception as e:
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
    
    # ==================== SIMPLIFIED CHANNEL LINK SYSTEM ====================
    
    def parse_channel_link(self, link):
        """
        Parse any Telegram channel link and extract info
        Returns dict with: type, username, chat_id, display_url, can_verify
        """
        if not link:
            return None
        
        link = link.strip()
        result = {
            "original_link": link,
            "type": "unknown",
            "username": None,
            "chat_id": None,
            "display_url": link,
            "can_verify": False
        }
        
        # Type 1: Invite links (https://t.me/+CODE or /joinchat/)
        if '+' in link or '/joinchat/' in link:
            result["type"] = "invite"
            result["display_url"] = link if link.startswith('http') else f"https://t.me/{link.replace('t.me/', '')}"
            result["can_verify"] = False  # Cannot verify invite links without numeric ID
            return result
        
        # Type 2: Private channel (https://t.me/c/NUMERIC_ID)
        private_match = re.search(r't\.me/c/(\d+)', link)
        if private_match:
            numeric_id = private_match.group(1)
            result["type"] = "private"
            result["chat_id"] = f"-100{numeric_id}"
            result["display_url"] = link if link.startswith('http') else f"https://{link}"
            result["can_verify"] = True  # Can verify if bot is admin
            return result
        
        # Type 3: Numeric channel ID directly
        if link.startswith('-100') and link[1:].replace('-', '').isdigit():
            result["type"] = "private"
            result["chat_id"] = link
            result["can_verify"] = True
            return result
        
        # Type 4: @username format
        if link.startswith('@'):
            username = link[1:]
            result["type"] = "public"
            result["username"] = username
            result["chat_id"] = f"@{username}"
            result["display_url"] = f"https://t.me/{username}"
            result["can_verify"] = True
            return result
        
        # Type 5: https://t.me/username or t.me/username
        username_match = re.search(r't\.me/([A-Za-z][A-Za-z0-9_]{3,30}[A-Za-z0-9])(?:/|$|\?)', link)
        if username_match:
            username = username_match.group(1)
            # Make sure it's not a special path
            if username.lower() not in ['joinchat', 'c', 'addstickers', 'share']:
                result["type"] = "public"
                result["username"] = username
                result["chat_id"] = f"@{username}"
                result["display_url"] = f"https://t.me/{username}"
                result["can_verify"] = True
                return result
        
        # Type 6: Just username (no @ or http)
        if re.match(r'^[A-Za-z][A-Za-z0-9_]{3,30}[A-Za-z0-9]$', link):
            result["type"] = "public"
            result["username"] = link
            result["chat_id"] = f"@{link}"
            result["display_url"] = f"https://t.me/{link}"
            result["can_verify"] = True
            return result
        
        # Default: treat as display-only link
        if not link.startswith('http'):
            result["display_url"] = f"https://t.me/{link.replace('t.me/', '')}"
        
        return result
    
    def check_user_in_channel(self, user_id, channel_data):
        """
        Check if user is member of a channel
        Returns: True (joined), False (not joined), None (cannot verify)
        """
        chat_id = channel_data.get("chat_id")
        can_verify = channel_data.get("can_verify", False)
        
        if not can_verify or not chat_id:
            # Cannot verify - return None (will be treated as "trust user")
            return None
        
        try:
            member_info = self.bot.get_chat_member(chat_id, user_id)
            
            if member_info:
                status = member_info.get("status", "")
                if status in ["member", "administrator", "creator"]:
                    return True
                elif status in ["left", "kicked"]:
                    return False
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking membership: {e}")
            return None
    
    def check_user_channels(self, user_id):
        """Check if user has joined all required channels"""
        channels = self.db.get_channels()
        
        if not channels:
            print("✅ No channels configured, auto-verifying")
            return True
        
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        user_id_str = str(user_id)
        all_joined = True
        unjoined_channels = []
        
        print(f"\n🔍 Checking {len(channels)} channels for user {user_id_str}")
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            link_info = channel.get("link_info", {})
            
            # Check if already verified recently (within 5 minutes)
            user_channel_data = user.get("channels_joined", {}).get(channel_id, {})
            if user_channel_data.get("verified", False):
                last_check = user_channel_data.get("last_check", "")
                if last_check:
                    try:
                        last_check_time = datetime.fromisoformat(last_check)
                        if (datetime.now() - last_check_time).seconds < 300:
                            print(f"  ✅ {channel_name}: Already verified (cached)")
                            continue
                    except:
                        pass
            
            # Check membership
            is_member = self.check_user_in_channel(user_id, link_info)
            
            if is_member is True:
                print(f"  ✅ {channel_name}: User is member")
                self.db.mark_channel_joined(user_id, channel_id)
            elif is_member is False:
                print(f"  ❌ {channel_name}: User NOT member")
                all_joined = False
                unjoined_channels.append(channel_name)
            else:
                # Cannot verify (invite link) - check if user claims to have joined
                if user_channel_data.get("user_confirmed", False):
                    print(f"  ⚠️ {channel_name}: Invite link - user confirmed")
                    continue
                else:
                    print(f"  ⚠️ {channel_name}: Invite link - needs user confirmation")
                    all_joined = False
                    unjoined_channels.append(f"{channel_name} (click to join)")
        
        if all_joined:
            print(f"🎉 All channels verified for user {user_id_str}")
        else:
            print(f"❌ Unjoined channels: {', '.join(unjoined_channels)}")
        
        return all_joined
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    def show_add_channel(self, chat_id, message_id, user_id):
        """Show simplified add channel screen"""
        msg = """➕ <b>Add New Channel</b>

Send channel info in this simple format:

<code>Channel Name
Channel Link</code>

<b>Examples:</b>

<code>My Updates Channel
https://t.me/mychannel</code>

<code>VIP Group
https://t.me/+ABCdef123456</code>

<code>News Channel
@newschannel</code>

<b>Supported Links:</b>
✅ https://t.me/username
✅ https://t.me/+invitecode
✅ @username
✅ t.me/username

⚠️ <b>Note:</b>
• For PUBLIC channels: Bot can auto-verify membership
• For INVITE links: Users must confirm they joined
• Bot must be ADMIN in channel for verification to work"""

        self.user_states[user_id] = {
            "state": "awaiting_channel",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "admin_channels")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_add_channel(self, chat_id, user_id, text):
        """Process adding a new channel"""
        lines = text.strip().split('\n')
        
        if len(lines) < 2:
            msg = """❌ <b>Invalid Format</b>

Please send in 2 lines:
1. Channel Name
2. Channel Link

Example:
<code>My Channel
https://t.me/mychannel</code>"""
            self.bot.send_message(chat_id, msg)
            return
        
        channel_name = lines[0].strip()
        channel_link = lines[1].strip()
        
        # Parse the link
        link_info = self.parse_channel_link(channel_link)
        
        if not link_info:
            msg = "❌ Could not parse channel link. Please check and try again."
            self.bot.send_message(chat_id, msg)
            return
        
        # Create channel data
        channel_data = {
            "name": channel_name,
            "link": link_info["display_url"],
            "original_link": channel_link,
            "link_info": link_info,
            "added_by": str(user_id),
            "added_at": datetime.now().isoformat()
        }
        
        # Test if we can access the channel (for public channels)
        if link_info["can_verify"] and link_info["chat_id"]:
            test_result = self.bot.get_chat(link_info["chat_id"])
            if test_result:
                channel_data["verified_access"] = True
                channel_data["chat_title"] = test_result.get("title", channel_name)
            else:
                channel_data["verified_access"] = False
        
        # Save channel
        channel_id = self.db.add_channel(channel_data)
        
        if channel_id:
            # Prepare success message
            type_emoji = {
                "public": "📢",
                "private": "🔐",
                "invite": "🔗",
                "unknown": "📋"
            }.get(link_info["type"], "📋")
            
            verify_status = "✅ Can auto-verify" if link_info["can_verify"] else "⚠️ Manual confirmation only"
            
            msg = f"""✅ <b>Channel Added Successfully!</b>

{type_emoji} <b>Name:</b> {channel_name}
🔗 <b>Link:</b> <code>{channel_link}</code>
📋 <b>Type:</b> {link_info["type"].upper()}
🔄 <b>Verification:</b> {verify_status}
🆔 <b>ID:</b> <code>{channel_id}</code>

Users will now see this channel in verification screen."""
        else:
            msg = "❌ Failed to add channel. Please try again."
        
        buttons = [
            ("➕ Add Another", "admin_add_channel"),
            ("📢 View All Channels", "admin_view_channels"),
            ("🔙 Back", "admin_channels")
        ]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def show_channel_list(self, chat_id, message_id, user_id):
        """Show list of all channels"""
        channels = self.db.get_channels()
        
        if not channels:
            msg = """📢 <b>No Channels</b>

No channels added yet.
Users will NOT see verification screen.

Add channels to require users to join before using bot."""
            buttons = [
                ("➕ Add Channel", "admin_add_channel"),
                ("🔙 Back", "admin_channels")
            ]
        else:
            msg = f"📢 <b>Channels ({len(channels)})</b>\n\n"
            buttons = []
            
            for i, (channel_id, channel) in enumerate(channels.items(), 1):
                name = channel.get("name", f"Channel {i}")
                link = channel.get("link", "No link")
                link_info = channel.get("link_info", {})
                link_type = link_info.get("type", "unknown")
                can_verify = link_info.get("can_verify", False)
                
                type_emoji = {
                    "public": "📢",
                    "private": "🔐",
                    "invite": "🔗",
                    "unknown": "📋"
                }.get(link_type, "📋")
                
                verify_icon = "✅" if can_verify else "⚠️"
                
                msg += f"{i}. {type_emoji} <b>{name}</b>\n"
                msg += f"   🔗 {link}\n"
                msg += f"   {verify_icon} {'Auto-verify' if can_verify else 'Manual'}\n\n"
                
                buttons.append((f"❌ Delete {i}", f"admin_delete_channel_{channel_id}"))
            
            buttons.append(("➕ Add More", "admin_add_channel"))
            buttons.append(("🔙 Back", "admin_channels"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_screen(self, chat_id, user_id, username):
        """Show channel verification screen to user"""
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, None, user_id)
            return
        
        msg = """🔐 <b>Channel Verification Required</b>

Please join ALL channels below to continue:

"""
        
        buttons = []
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            link = channel.get("link", "")
            link_info = channel.get("link_info", {})
            link_type = link_info.get("type", "unknown")
            
            type_emoji = {
                "public": "📢",
                "private": "🔐",
                "invite": "🔗"
            }.get(link_type, "📢")
            
            msg += f"{type_emoji} <b>{channel_name}</b>\n"
            
            if link:
                buttons.append({
                    "text": f"{type_emoji} Join {channel_name}",
                    "url": link
                })
        
        # Add verify button
        buttons.append(("✅ I'VE JOINED ALL - VERIFY NOW", "check_verification"))
        
        msg += """
⚠️ <b>Important:</b>
1. Click each button to join the channel
2. Wait 5-10 seconds after joining
3. Click "VERIFY NOW" button

If verification fails, make sure you've joined ALL channels."""
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id, message_id, user_id):
        """Check if user has joined all channels"""
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ User not found. Please /start again.")
            return
        
        # Update attempt count
        attempts = user.get("verification_attempts", 0) + 1
        self.db.update_user(user_id, {"verification_attempts": attempts})
        
        # Check channels
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            
            # Process pending referral
            username = user.get("username", "User")
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_verification_success(chat_id, message_id, user_id)
        else:
            # Check if there are only invite-link channels
            channels = self.db.get_channels()
            only_invite = all(
                ch.get("link_info", {}).get("type") == "invite" 
                for ch in channels.values()
            )
            
            if only_invite and attempts >= 2:
                # Trust user for invite-only channels after 2 attempts
                self.db.mark_user_verified(user_id)
                
                # Mark all channels as user-confirmed
                for channel_id in channels.keys():
                    self.db.mark_channel_joined(user_id, channel_id)
                
                username = user.get("username", "User")
                if str(user_id) in self.pending_referrals:
                    self.process_pending_referral(user_id, username)
                
                self.show_verification_success(chat_id, message_id, user_id)
            else:
                self.show_verification_failed(chat_id, message_id, user_id, attempts)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        """Show success message after verification"""
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verification Successful!</b>

Welcome <b>{username}</b>! 🎉

You now have full access to TradeGenius07 Bot.

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🎁 Bonus at 10 referrals: +₹{Config.BONUS_AT_10_REFERRALS}

Get started by sharing your referral link!"""
        
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
    
    def show_verification_failed(self, chat_id, message_id, user_id, attempts):
        """Show failed verification message"""
        channels = self.db.get_channels()
        
        msg = f"""❌ <b>Verification Failed</b>

You haven't joined all required channels yet.
Attempt: {attempts}/5

<b>Please:</b>
1. Click each channel button below
2. Make sure you JOINED (not just viewed)
3. Wait 10 seconds
4. Click VERIFY again

"""
        
        buttons = []
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            link = channel.get("link", "")
            link_info = channel.get("link_info", {})
            
            type_emoji = "📢" if link_info.get("type") == "public" else "🔗"
            
            if link:
                buttons.append({
                    "text": f"{type_emoji} Join {channel_name}",
                    "url": link
                })
        
        buttons.append(("✅ VERIFY AGAIN", "check_verification"))
        buttons.append(("🔄 Start Over", "start_over"))
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== KEYBOARD HELPER ====================
    
    def generate_keyboard(self, buttons, columns=2):
        """Generate inline keyboard from button list"""
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
        
        if row:
            keyboard.append(row)
        
        return {"inline_keyboard": keyboard}
    
    # ==================== MESSAGE HANDLING ====================
    
    def handle_user_message(self, chat_id, user_id, text):
        """Handle text messages from users"""
        if user_id in self.user_states:
            state = self.user_states[user_id]
            
            if state.get("state") == "awaiting_upi":
                self.process_upi_setup(chat_id, user_id, text, state)
            
            elif state.get("state") == "awaiting_channel":
                self.process_add_channel(chat_id, user_id, text)
            
            elif state.get("state") == "awaiting_rejection_reason":
                self.process_rejection_reason(user_id, text)
            
            elif state.get("state") == "awaiting_web_url":
                self.process_web_url_update(chat_id, user_id, text)
            
            elif state.get("state") == "awaiting_ai_button_name":
                self.process_ai_button_update(chat_id, user_id, text)
        
        elif text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
            self.process_broadcast(chat_id, text)
    
    def process_upi_setup(self, chat_id, user_id, text, state):
        """Process UPI ID setup"""
        upi_id = text.strip()
        
        if '@' in upi_id and len(upi_id) > 5:
            self.db.update_upi_id(user_id, upi_id)
            
            msg = f"""✅ <b>UPI ID Saved</b>

📱 Your UPI ID: <code>{upi_id}</code>

You can now request withdrawals."""
            
            buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
            
            del self.user_states[user_id]
        else:
            msg = "❌ Invalid UPI ID format.\n\nCorrect format: <code>name@upi</code>\nExample: <code>john@okaxis</code>"
            self.bot.send_message(chat_id, msg)
    
    def process_web_url_update(self, chat_id, user_id, text):
        """Process web URL update"""
        new_url = text.strip()
        
        if new_url.startswith("http://") or new_url.startswith("https://"):
            result = self.db.update_web_url(new_url)
            
            if result:
                msg = f"✅ Web URL updated to:\n<code>{new_url}</code>"
            else:
                msg = "❌ Failed to update web URL."
        else:
            msg = "❌ Invalid URL. Must start with http:// or https://"
        
        buttons = [("🔙 Back", "admin_web_url")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def process_ai_button_update(self, chat_id, user_id, text):
        """Process AI button name update"""
        new_name = text.strip()
        
        if 0 < len(new_name) <= 25:
            result = self.db.update_ai_button_name(new_name)
            
            if result:
                msg = f"✅ AI Button name updated to:\n<code>{new_name}</code>"
            else:
                msg = "❌ Failed to update AI button name."
        else:
            msg = "❌ Name must be 1-25 characters."
        
        buttons = [("🔙 Back", "admin_ai_button")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def process_broadcast(self, chat_id, text):
        """Process broadcast message"""
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            message = parts[1]
            users = self.db.get_all_users()
            
            if not users:
                self.bot.send_message(chat_id, "❌ No users to broadcast to.")
                return
            
            total = len(users)
            self.bot.send_message(chat_id, f"📢 Broadcasting to {total} users...")
            
            success = 0
            for uid in users.keys():
                try:
                    self.bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{message}")
                    success += 1
                    time.sleep(0.05)
                except:
                    continue
            
            self.bot.send_message(chat_id, f"✅ Broadcast complete: {success}/{total} users")
        else:
            self.bot.send_message(chat_id, "Usage: /broadcast Your message here")
    
    # ==================== START COMMAND ====================
    
    def start_command(self, chat_id, user_id, username, first_name, last_name, args):
        """Handle /start command"""
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username, first_name, last_name)
        
        # Admin bypass
        if str(user_id) == Config.ADMIN_USER_ID:
            if not user.get("is_verified", False):
                self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            self.show_welcome_screen(chat_id, user_id, user, args)
            return
        
        # Store referral code if provided
        referral_code = args[0] if args else None
        if referral_code and not user.get("referral_claimed", False):
            self.pending_referrals[str(user_id)] = {
                "referral_code": referral_code,
                "attempts": 0,
                "last_attempt": datetime.now().isoformat()
            }
            self.db.track_referral_attempt(user_id, referral_code, "pending_verification")
        
        channels = self.db.get_channels()
        
        if not channels:
            # No channels configured
            if not user.get("is_verified", False):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user, args)
            return
        
        # Check if already verified
        if user.get("is_verified", False):
            self.show_welcome_screen(chat_id, user_id, user, args)
            return
        
        # Check channel membership
        all_joined = self.check_user_channels(user_id)
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            user["is_verified"] = True
            
            if str(user_id) in self.pending_referrals:
                self.process_pending_referral(user_id, username)
            
            self.show_welcome_screen(chat_id, user_id, user, args)
        else:
            self.show_verification_screen(chat_id, user_id, username)
    
    def show_welcome_screen(self, chat_id, user_id, user, args):
        """Show welcome screen"""
        if not user:
            user = self.db.get_user(user_id)
        
        if not user:
            return
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Status: Active</b>" if is_admin else ""
        
        referral_status = ""
        if user.get("referrer"):
            referral_status = f"\n👥 Referred by: User_{user['referrer'][-6:]}"
        
        welcome_msg = f"""👋 <b>Welcome to TradeGenius07 Bot!</b> 💸

👤 Hello, {user.get('username', 'User')}!{admin_text}
✅ <b>Status: Verified</b>{referral_status}

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🔗 Your Code: <code>{user.get('referral_code', 'N/A')}</code>
👥 Referrals: {user.get('referrals', 0)}
💸 Balance: ₹{user.get('pending_balance', 0)}

👇 <b>Select an option:</b>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        
        self.bot.send_message(chat_id, welcome_msg, keyboard)
    
    def get_main_menu_buttons(self, user_id):
        """Get main menu buttons"""
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
    
    # ==================== REFERRAL PROCESSING ====================
    
    def process_pending_referral(self, user_id, username):
        """Process pending referral after verification"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_referrals:
            return False
        
        pending = self.pending_referrals[user_id_str]
        referral_code = pending["referral_code"]
        
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
            if pending["attempts"] >= Config.MAX_VERIFICATION_ATTEMPTS:
                del self.pending_referrals[user_id_str]
            return False
    
    def process_referral(self, user_id, username, referral_code):
        """Process referral reward"""
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        if user.get("referral_claimed", False):
            return True
        
        referrer_id, referrer = self.db.find_user_by_referral_code(referral_code)
        
        if not referrer or not referrer_id:
            return False
        
        if referrer_id == str(user_id):
            return False
        
        if not referrer.get("is_verified", False):
            return False
        
        # Create referral record
        self.db.create_referral_record(user_id, referrer_id, "completed")
        
        # Calculate reward
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL
        
        if new_refs == 10:
            reward += Config.BONUS_AT_10_REFERRALS
        
        # Update referrer
        updates = {
            "referrals": new_refs,
            "pending_balance": referrer.get("pending_balance", 0) + reward,
            "total_earnings": referrer.get("total_earnings", 0) + reward
        }
        self.db.update_user(referrer_id, updates)
        
        # Update new user
        self.db.update_user(user_id, {
            "referrer": referrer_id,
            "referral_claimed": True,
            "referral_claimed_at": datetime.now().isoformat()
        })
        
        # Notify referrer
        try:
            bonus_text = f"\n🎁 BONUS: +₹{Config.BONUS_AT_10_REFERRALS} for 10 referrals!" if new_refs == 10 else ""
            
            self.bot.send_message(
                referrer_id,
                f"""🎉 <b>New Referral Success!</b>

✅ @{username} joined using your link!
💰 You earned: <b>₹{reward}</b>
👥 Total referrals: <b>{new_refs}</b>{bonus_text}

Keep sharing to earn more!"""
            )
        except:
            pass
        
        return True
    
    # ==================== CALLBACK HANDLING ====================
    
    def handle_callback(self, chat_id, message_id, user_id, callback_data):
        """Handle callback queries"""
        callback_query_id = callback_data["id"]
        callback = callback_data.get("data", "")
        
        self.bot.answer_callback_query(callback_query_id)
        
        user = self.db.get_user(user_id) or {}
        
        # Handle verification callbacks
        if callback == "check_verification":
            self.check_verification(chat_id, message_id, user_id)
            return
        
        if callback == "start_over":
            self.show_verification_screen(chat_id, user_id, user.get("username", "User"))
            return
        
        # Handle terms (no verification required)
        if callback == "terms_conditions":
            self.show_terms_conditions(chat_id, message_id, user_id)
            return
        
        # Handle web button
        if callback == "open_web":
            self.show_web_button(chat_id, message_id)
            return
        
        # Admin panel access check
        if callback == "admin_panel":
            if str(user_id) != Config.ADMIN_USER_ID:
                self.bot.answer_callback_query(callback_query_id, "⛔ Access Denied", True)
                return
            self.show_admin_panel(chat_id, message_id, user_id)
            return
        
        # Verification check for regular users
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
            if callback not in ["check_verification", "start_over", "main_menu"]:
                msg = "❌ Please complete channel verification first."
                buttons = [("✅ Verify Now", "check_verification")]
                keyboard = self.generate_keyboard(buttons, 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        # Handle other callbacks
        if callback == "main_menu":
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
        
        elif callback.startswith("admin_"):
            if str(user_id) != Config.ADMIN_USER_ID:
                return
            self.handle_admin_callback(chat_id, message_id, user_id, callback)
        
        elif callback in ["how_it_works", "rewards", "support"]:
            self.handle_info_callback(chat_id, message_id, user_id, callback)
    
    def show_web_button(self, chat_id, message_id):
        """Show web button with URL"""
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        buttons = [
            {"text": f"🚀 {ai_button_name}", "url": web_url},
            ("🏠 Main Menu", "main_menu")
        ]
        keyboard = self.generate_keyboard(buttons, 1)
        
        msg = f"""🤖 <b>{ai_button_name}</b>

Click the button below to access:"""
        
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== USER FEATURES ====================
    
    def show_main_menu(self, chat_id, message_id, user_id, user):
        """Show main menu"""
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Mode</b>" if is_admin else ""
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}

👋 {user.get('username', 'User')}
💰 Balance: <b>₹{user.get('pending_balance', 0)}</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_referral_link(self, chat_id, message_id, user_id, user):
        """Show referral link"""
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
        
        share_text = f"Join TradeGenius07 bot and earn! {referral_link}"
        share_url = f"https://t.me/share/url?url={quote(referral_link)}&text={quote(share_text)}"
        
        buttons = [
            {"text": "📤 Share Link", "url": share_url},
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_dashboard(self, chat_id, message_id, user_id, user):
        """Show user dashboard"""
        msg = f"""📊 <b>Dashboard</b>

👤 {user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
✅ Status: Verified

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
        """Show withdrawal menu"""
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if not upi_id:
            msg = f"""❌ <b>UPI ID Required</b>

Set up your UPI ID first to withdraw.

Current balance: <b>₹{pending}</b>
Minimum withdrawal: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>"""
            
            buttons = [
                ("📱 Setup UPI ID", "setup_upi"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        elif pending >= Config.MINIMUM_WITHDRAWAL:
            msg = f"""💳 <b>Withdraw Funds</b>

💰 Available: <b>₹{pending}</b>
💰 Minimum: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📱 Your UPI: <code>{upi_id}</code>

⚠️ Payment processed within 24-72 hours"""
            
            buttons = [
                ("✅ Request Withdrawal", "request_withdraw"),
                ("✏️ Change UPI", "setup_upi"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        else:
            needed = Config.MINIMUM_WITHDRAWAL - pending
            referrals_needed = -(-needed // Config.REWARD_PER_REFERRAL)
            
            msg = f"""❌ <b>Insufficient Balance</b>

💰 Available: <b>₹{pending}</b>
💰 Required: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📊 Need: <b>₹{needed}</b> more ({referrals_needed} referrals)"""
            
            buttons = [
                ("🔗 Get Referral Link", "my_referral"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def setup_upi_id(self, chat_id, message_id, user_id):
        """Setup UPI ID"""
        msg = """📱 <b>Setup UPI ID</b>

Send your UPI ID:
<code>name@upi</code>

Examples:
• <code>john@okaxis</code>
• <code>jane@ybl</code>
• <code>user@paytm</code>"""
        
        self.user_states[user_id] = {
            "state": "awaiting_upi",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        buttons = [("❌ Cancel", "withdraw")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def request_withdrawal(self, chat_id, message_id, user_id, user):
        """Process withdrawal request"""
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if pending < Config.MINIMUM_WITHDRAWAL or not upi_id:
            msg = "❌ Cannot process withdrawal."
            keyboard = self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        withdrawal_id = f"WD{random.randint(100000, 999999)}"
        
        withdrawal_data = {
            "user_id": str(user_id),
            "username": user.get("username", ""),
            "amount": pending,
            "upi_id": upi_id,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "withdrawal_id": withdrawal_id
        }
        
        self.db.create_withdrawal(withdrawal_id, withdrawal_data)
        
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + pending
        })
        
        # Notify admin
        admin_msg = f"""🆕 <b>NEW WITHDRAWAL</b>

👤 @{user.get('username', 'N/A')}
💰 Amount: <b>₹{pending}</b>
📱 UPI: <code>{upi_id}</code>
📋 ID: {withdrawal_id}"""
        
        self.bot.send_message(Config.ADMIN_USER_ID, admin_msg)
        
        # Confirm to user
        msg = f"""✅ <b>Withdrawal Requested</b>

📋 ID: <code>{withdrawal_id}</code>
💰 Amount: <b>₹{pending}</b>
⏳ Processing: 24-72 hours"""
        
        buttons = [
            ("📜 Check Status", "withdraw_history"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdrawal_history(self, chat_id, message_id, user_id):
        """Show withdrawal history"""
        withdrawals = self.db.get_withdrawals()
        user_wds = {k: v for k, v in withdrawals.items() if v and v.get("user_id") == str(user_id)}
        
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
                
                emoji = {"completed": "✅", "rejected": "❌"}.get(status, "⏳")
                msg += f"{emoji} ₹{amount} - {date} ({status})\n"
        
        buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_terms_conditions(self, chat_id, message_id, user_id):
        """Show terms and conditions"""
        msg = f"""📜 <b>Terms & Conditions</b>

1. Join all required channels
2. One referral reward per user
3. No self-referrals allowed
4. Minimum withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}
5. Payments via UPI only
6. Processing time: 24-72 hours
7. Fraud = permanent ban

<i>Updated: {datetime.now().strftime("%d %B %Y")}</i>"""
        
        buttons = [("✅ I Understand", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_info_callback(self, chat_id, message_id, user_id, callback):
        """Handle info callbacks"""
        if callback == "how_it_works":
            msg = f"""📢 <b>How It Works</b>

1️⃣ Join required channels
2️⃣ Get your referral link
3️⃣ Share with friends
4️⃣ Earn ₹{Config.REWARD_PER_REFERRAL} per referral
5️⃣ Withdraw via UPI"""
        
        elif callback == "rewards":
            msg = f"""🎁 <b>Rewards</b>

💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}
🎁 10 Referrals Bonus: +₹{Config.BONUS_AT_10_REFERRALS}

Example:
• 5 refs = ₹{Config.REWARD_PER_REFERRAL * 5}
• 10 refs = ₹{Config.REWARD_PER_REFERRAL * 10 + Config.BONUS_AT_10_REFERRALS}"""
        
        elif callback == "support":
            msg = f"""📞 <b>Support</b>

Contact: {Config.SUPPORT_CHANNEL}"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== ADMIN FUNCTIONS ====================
    
    def show_admin_panel(self, chat_id, message_id, user_id):
        """Show admin panel"""
        users = self.db.get_all_users()
        total_users = len(users) if users else 0
        
        withdrawals = self.db.get_withdrawals("pending")
        pending_wds = len(withdrawals) if withdrawals else 0
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        msg = f"""👑 <b>Admin Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
💳 Pending WD: {pending_wds}
📢 Channels: {total_channels}"""
        
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
        """Handle admin callbacks"""
        if callback == "admin_stats":
            self.show_admin_stats(chat_id, message_id)
        
        elif callback == "admin_withdrawals":
            self.show_withdrawal_management(chat_id, message_id)
        
        elif callback == "admin_channels":
            self.show_channel_management(chat_id, message_id)
        
        elif callback == "admin_add_channel":
            self.show_add_channel(chat_id, message_id, user_id)
        
        elif callback == "admin_view_channels":
            self.show_channel_list(chat_id, message_id, user_id)
        
        elif callback.startswith("admin_delete_channel_"):
            channel_id = callback.replace("admin_delete_channel_", "")
            self.delete_channel(chat_id, message_id, channel_id)
        
        elif callback == "admin_web_url":
            self.show_web_url_management(chat_id, message_id, user_id)
        
        elif callback == "admin_update_web_url":
            self.show_update_web_url(chat_id, message_id, user_id)
        
        elif callback == "admin_ai_button":
            self.show_ai_button_management(chat_id, message_id, user_id)
        
        elif callback == "admin_update_ai_button":
            self.show_update_ai_button(chat_id, message_id, user_id)
        
        elif callback == "admin_users":
            self.show_user_management(chat_id, message_id)
        
        elif callback == "admin_broadcast":
            self.show_broadcast_menu(chat_id, message_id)
        
        elif callback.startswith("admin_approve_"):
            wd_id = callback.replace("admin_approve_", "")
            self.approve_withdrawal(chat_id, message_id, wd_id)
        
        elif callback.startswith("admin_reject_"):
            wd_id = callback.replace("admin_reject_", "")
            self.reject_withdrawal(chat_id, message_id, user_id, wd_id)
    
    def show_admin_stats(self, chat_id, message_id):
        """Show admin statistics"""
        users = self.db.get_all_users()
        total = len(users) if users else 0
        verified = sum(1 for u in users.values() if u and u.get("is_verified")) if users else 0
        total_earnings = sum(u.get("total_earnings", 0) for u in users.values() if u) if users else 0
        
        channels = self.db.get_channels()
        ch_count = len(channels) if channels else 0
        
        msg = f"""📊 <b>Statistics</b>

👥 Total Users: {total}
✅ Verified: {verified}
❌ Pending: {total - verified}
💰 Total Earnings: ₹{total_earnings}
📢 Channels: {ch_count}"""
        
        buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_channel_management(self, chat_id, message_id):
        """Show channel management"""
        channels = self.db.get_channels()
        count = len(channels) if channels else 0
        
        msg = f"""📢 <b>Channel Management</b>

{count} channel(s) configured.

• Add: Only Name + Link needed
• Auto-detect channel type
• Smart verification system"""
        
        buttons = [
            ("➕ Add Channel", "admin_add_channel"),
            ("📋 View Channels", "admin_view_channels"),
            ("🔙 Back", "admin_panel")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def delete_channel(self, chat_id, message_id, channel_id):
        """Delete a channel"""
        self.db.delete_channel(channel_id)
        msg = "✅ Channel deleted successfully."
        
        buttons = [("📋 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdrawal_management(self, chat_id, message_id):
        """Show pending withdrawals"""
        withdrawals = self.db.get_withdrawals("pending")
        
        if not withdrawals:
            msg = "💳 <b>Pending Withdrawals</b>\n\nNo pending requests."
            buttons = [("🔄 Refresh", "admin_withdrawals"), ("🔙 Back", "admin_panel")]
        else:
            msg = "💳 <b>Pending Withdrawals</b>\n\n"
            buttons = []
            
            for i, (wd_id, wd) in enumerate(withdrawals.items(), 1):
                if wd:
                    msg += f"{i}. ₹{wd.get('amount', 0)} - @{wd.get('username', 'N/A')}\n"
                    msg += f"   UPI: {wd.get('upi_id', 'N/A')}\n\n"
                    
                    buttons.append((f"✅ Approve {i}", f"admin_approve_{wd_id}"))
                    buttons.append((f"❌ Reject {i}", f"admin_reject_{wd_id}"))
            
            buttons.append(("🔄 Refresh", "admin_withdrawals"))
            buttons.append(("🔙 Back", "admin_panel"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def approve_withdrawal(self, chat_id, message_id, wd_id):
        """Approve withdrawal"""
        withdrawals = self.db.get_withdrawals()
        wd = withdrawals.get(wd_id) if withdrawals else None
        
        if not wd:
            msg = "❌ Withdrawal not found."
        else:
            self.db.update_withdrawal_status(wd_id, "completed")
            
            self.bot.send_message(
                wd["user_id"],
                f"""✅ <b>Withdrawal Approved!</b>

💰 Amount: ₹{wd['amount']}
📱 UPI: {wd.get('upi_id', 'N/A')}

Payment will be processed soon!"""
            )
            
            msg = f"✅ Withdrawal {wd_id} approved."
        
        buttons = [("💳 Back", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def reject_withdrawal(self, chat_id, message_id, admin_id, wd_id):
        """Reject withdrawal"""
        withdrawals = self.db.get_withdrawals()
        wd = withdrawals.get(wd_id) if withdrawals else None
        
        if not wd:
            msg = "❌ Withdrawal not found."
            buttons = [("💳 Back", "admin_withdrawals")]
            keyboard = self.generate_keyboard(buttons, 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        self.user_states[admin_id] = {
            "state": "awaiting_rejection_reason",
            "withdrawal_id": wd_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "user_id": wd.get("user_id"),
            "amount": wd.get("amount", 0)
        }
        
        msg = f"""❌ <b>Reject Withdrawal</b>

ID: {wd_id}
Amount: ₹{wd.get('amount', 0)}

Send rejection reason:"""
        
        buttons = [("❌ Cancel", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_rejection_reason(self, admin_id, reason):
        """Process rejection with reason"""
        if admin_id not in self.user_states:
            return
        
        state = self.user_states[admin_id]
        if state.get("state") != "awaiting_rejection_reason":
            return
        
        wd_id = state["withdrawal_id"]
        user_id = state["user_id"]
        amount = state["amount"]
        
        self.db.update_withdrawal_status(wd_id, "rejected", reason)
        
        # Return balance
        user = self.db.get_user(user_id)
        if user:
            new_balance = user.get("pending_balance", 0) + amount
            self.db.update_user(user_id, {"pending_balance": new_balance})
        
        # Notify user
        self.bot.send_message(
            user_id,
            f"""❌ <b>Withdrawal Rejected</b>

💰 Amount: ₹{amount}
📝 Reason: {reason}

Amount returned to your balance."""
        )
        
        msg = f"❌ Withdrawal rejected. User notified."
        buttons = [("💳 Back", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        
        self.bot.edit_message_text(state["chat_id"], state["message_id"], msg, keyboard)
        
        del self.user_states[admin_id]
    
    def show_user_management(self, chat_id, message_id):
        """Show top users"""
        users = self.db.get_all_users()
        
        if not users:
            msg = "👥 <b>Users</b>\n\nNo users yet."
        else:
            msg = "👥 <b>Top 10 Users</b>\n\n"
            
            sorted_users = sorted(
                [(uid, u) for uid, u in users.items() if u],
                key=lambda x: x[1].get("referrals", 0),
                reverse=True
            )[:10]
            
            for i, (uid, u) in enumerate(sorted_users, 1):
                v = "✅" if u.get("is_verified") else "❌"
                msg += f"{i}. {v} {u.get('username', 'N/A')} - {u.get('referrals', 0)} refs\n"
        
        buttons = [("🔄 Refresh", "admin_users"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_broadcast_menu(self, chat_id, message_id):
        """Show broadcast instructions"""
        msg = """📢 <b>Broadcast</b>

Use: /broadcast Your message

Example:
<code>/broadcast Hello everyone!</code>"""
        
        buttons = [("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_web_url_management(self, chat_id, message_id, user_id):
        """Show web URL management"""
        web_url = self.db.get_web_url()
        
        msg = f"""🌐 <b>Web URL</b>

Current: <code>{web_url}</code>"""
        
        buttons = [
            ("✏️ Update URL", "admin_update_web_url"),
            ("🔙 Back", "admin_panel")
        ]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_update_web_url(self, chat_id, message_id, user_id):
        """Show update web URL prompt"""
        self.user_states[user_id] = {
            "state": "awaiting_web_url",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        msg = "Send new web URL (must start with https://):"
        buttons = [("❌ Cancel", "admin_web_url")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_ai_button_management(self, chat_id, message_id, user_id):
        """Show AI button management"""
        ai_name = self.db.get_ai_button_name()
        
        msg = f"""🤖 <b>AI Button</b>

Current: <code>{ai_name}</code>"""
        
        buttons = [
            ("✏️ Update Name", "admin_update_ai_button"),
            ("🔙 Back", "admin_panel")
        ]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_update_ai_button(self, chat_id, message_id, user_id):
        """Show update AI button prompt"""
        self.user_states[user_id] = {
            "state": "awaiting_ai_button_name",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        msg = "Send new AI button name (max 25 chars):"
        buttons = [("❌ Cancel", "admin_ai_button")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ==================== BOT RUNNER ====================
    
    def run_bot(self):
        """Run the bot"""
        print("="*60)
        print("🤖 TradeGenius Bot - Simplified Channel System v3.0")
        print("="*60)
        print(f"👑 Admin: {Config.ADMIN_USER_ID}")
        
        # Disable webhook
        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
        time.sleep(2)
        
        print("\n✅ Features:")
        print("   • Simplified channel addition (Name + Link only)")
        print("   • Auto-detects channel type")
        print("   • Smart verification for public channels")
        print("   • Manual confirmation for invite links")
        
        channels = self.db.get_channels()
        if channels:
            print(f"\n📢 Channels: {len(channels)}")
            for i, (cid, ch) in enumerate(channels.items(), 1):
                link_info = ch.get("link_info", {})
                print(f"   {i}. {ch.get('name')} ({link_info.get('type', 'unknown')})")
        
        print("="*60)
        print("✅ Bot is running!")
        print("="*60)
        
        self.offset = 0
        error_count = 0
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset)
                
                if updates is None:
                    error_count += 1
                    if error_count > 5:
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
                        
                        except Exception as e:
                            print(f"Error processing update: {e}")
                            continue
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped")
                self.running = False
                
            except Exception as e:
                print(f"❌ Error: {e}")
                error_count += 1
                if error_count > 10:
                    time.sleep(10)
                    self.offset = 0
                    error_count = 0
                else:
                    time.sleep(5)

# ==================== MAIN ====================
def run_both():
    bot = TradeGeniusBot()
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Flask server started")
    print("🤖 Starting Telegram bot...")
    
    bot.run_bot()

if __name__ == "__main__":
    print("🔥 TradeGenius Bot v3.0 - Simplified Channel System")
    print("="*60)
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure bot token first!")
    else:
        run_both()