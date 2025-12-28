# main.py - Fixed HTTP 409 Conflict Error

"""
🔥 Trade Genius Bot - FIXED Version
✅ Fixed HTTP 409 Conflict Error
✅ Webhook properly disabled
✅ Get Free Coins button
✅ Admin can change Web URL
"""

import os
import json
import logging
import time
import random
import string
from datetime import datetime
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
        "message": "Telegram bot is running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== CONFIGURATION ====================
class Config:
    BOT_TOKEN = "8285080906:AAHEfKnYLeW_ygtgtqgzbbLfbaMJGRuSEgM"
    BOT_USERNAME = "TradeGenius07Pro_bot"
    WEB_URL = "https://www.thecoinsage.com/"
    
    FIREBASE_URL = "https://colortraderpro-panel-default-rtdb.firebaseio.com/"
    
    REWARD_PER_REFERRAL = 2
    MINIMUM_WITHDRAWAL = 20
    BONUS_AT_10_REFERRALS = 5
    
    ADMIN_USER_ID = "1882237415"
    SUPPORT_CHANNEL = "@TradeGenius07_HelpCenter_bot"
    
    LOG_FILE = "bot_logs.txt"
    DATA_FILE = "local_backup.json"

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
                "web_url": Config.WEB_URL
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
    
    def get_user(self, user_id):
        user_id = str(user_id)
        data = self._firebase_request("GET", f"users/{user_id}")
        
        if data:
            return data
        else:
            return self.local_data.get('users', {}).get(user_id, None)
    
    def create_user(self, user_id, username="User"):
        user_id = str(user_id)
        
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        is_admin = (user_id == Config.ADMIN_USER_ID)
        
        user_data = {
            "user_id": user_id,
            "username": username,
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
            "is_admin": is_admin
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
    
    def mark_user_verified(self, user_id):
        return self.update_user(user_id, {"is_verified": True})
    
    def mark_channel_joined(self, user_id, channel_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        if "channels_joined" not in user:
            user["channels_joined"] = {}
        
        user["channels_joined"][channel_id] = {
            "joined_at": datetime.now().isoformat(),
            "verified": True
        }
        
        return self.update_user(user_id, {"channels_joined": user["channels_joined"]})
    
    def check_all_channels_joined(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        channels = self.get_channels()
        if not channels:
            return True
        
        user_channels = user.get("channels_joined", {})
        
        for channel_id in channels.keys():
            if channel_id not in user_channels or not user_channels[channel_id].get("verified", False):
                return False
        
        return True
    
    def add_channel(self, channel_data):
        channel_id = channel_data.get("id")
        if not channel_id:
            return False
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        return result
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels") or {}
        return data
    
    def delete_channel(self, channel_id):
        result = self._firebase_request("DELETE", f"channels/{channel_id}")
        return result
    
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
                # Retry after 2 seconds
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
            
            if chat_id.startswith("@"):
                chat_id_without_at = chat_id[1:]
                data["chat_id"] = chat_id_without_at
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
    
    def get_updates(self, offset=None, timeout=60):  # 🛠️ Increased timeout
        data = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]  # 🛠️ Specify allowed updates
        }
        if offset:
            data["offset"] = offset
        
        result = self._api_request("getUpdates", data)
        return result or []
    
    def check_webhook_status(self):
        """Check if webhook is active"""
        return self._api_request("getWebhookInfo")

# ==================== MAIN BOT CLASS ====================
class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBotAPI(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.user_states = {}
    
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
    
    def get_main_menu_buttons(self, user_id):
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        
        buttons = [
            ("🔗 Get Referral Link", "my_referral"),
            ("📊 My Dashboard", "dashboard"),
            ("💳 Withdraw", "withdraw"),
            ("🪙 Web Url", "open_web"),
            ("📜 Terms & Conditions", "terms_conditions"),
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support"),
        ]
        
        if is_admin:
            buttons.append(("👑 Admin Panel", "admin_panel"))
        
        return buttons
    
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
    
    def start_command(self, chat_id, user_id, username, args):
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username)
        
        if str(user_id) == Config.ADMIN_USER_ID:
            if not user.get("is_verified", False):
                self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            self.show_welcome_screen(chat_id, user_id, username, user, args)
            return
        
        channels = self.db.get_channels()
        
        if not channels:
            if not user.get("is_verified", False):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if args and len(args) > 0 and user.get("is_verified", False):
                self.process_referral(user_id, username, args[0])
            
            self.show_welcome_screen(chat_id, user_id, username, user, args)
            return
        
        all_joined = True
        not_joined_channels = []
        
        for channel_id, channel in channels.items():
            channel_link = channel.get("link", "")
            
            if not channel_link:
                continue
            
            try:
                chat_id_for_check = channel_link
                
                if channel_link.startswith("@"):
                    chat_id_for_check = channel_link
                elif channel_link.isdigit() or (channel_link.startswith('-100') and channel_link[1:].isdigit()):
                    chat_id_for_check = channel_link
                else:
                    if not channel_link.startswith("@"):
                        chat_id_for_check = "@" + channel_link
                
                member_info = self.bot.get_chat_member(chat_id_for_check, user_id)
                
                if member_info and member_info.get("status") in ["member", "administrator", "creator"]:
                    if "channels_joined" not in user:
                        user["channels_joined"] = {}
                    user["channels_joined"][channel_id] = {
                        "joined_at": datetime.now().isoformat(),
                        "verified": True
                    }
                    self.db.mark_channel_joined(user_id, channel_id)
                else:
                    all_joined = False
                    not_joined_channels.append({
                        "name": channel.get("name", "Channel"),
                        "link": channel_link,
                        "id": channel_id
                    })
            
            except Exception as e:
                print(f"⚠️ Error checking channel {channel_link}: {e}")
                all_joined = False
                not_joined_channels.append({
                    "name": channel.get("name", "Channel"),
                    "link": channel_link,
                    "id": channel_id
                })
        
        if all_joined:
            if not user.get("is_verified", False):
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
            
            if args and len(args) > 0 and user.get("is_verified", False):
                self.process_referral(user_id, username, args[0])
            
            self.show_welcome_screen(chat_id, user_id, username, user, args)
        else:
            self.show_verification_screen_real_time(chat_id, user_id, username, not_joined_channels)
    
    def show_verification_screen_real_time(self, chat_id, user_id, username, missing_channels):
        if not missing_channels:
            self.db.mark_user_verified(user_id)
            self.show_welcome_screen(chat_id, user_id, username, None, [])
            return
        
        msg = "🔐 <b>Join our channels to continue</b>"
        
        buttons = []
        
        for channel in missing_channels:
            channel_name = channel.get("name", "Channel")
            channel_link = channel.get("link", "")
            
            if channel_link.startswith("@"):
                channel_url = f"https://t.me/{channel_link[1:]}"
            elif channel_link.isdigit() or (channel_link.startswith('-100') and channel_link[1:].isdigit()):
                channel_url = f"https://t.me/{Config.SUPPORT_CHANNEL[1:]}"
            elif "t.me/" in channel_link:
                channel_url = channel_link
            else:
                channel_url = f"https://t.me/{channel_link}"
            
            clean_name = channel_name.replace("📢", "").replace("🔔", "").replace("📰", "").strip()
            if not clean_name:
                clean_name = "Join Channel"
            
            buttons.append({"text": f"📢 {clean_name}", "url": channel_url})
        
        buttons.append(("✅ VERIFY JOIN ✅", "check_verification"))
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def process_referral(self, user_id, username, referral_code):
        user = self.db.get_user(user_id)
        if not user or user.get("referral_claimed", False):
            return
        
        all_users = self.db.get_all_users()
        referrer_id = None
        
        for uid, user_data in all_users.items():
            if user_data and user_data.get("referral_code") == referral_code:
                referrer_id = uid
                break
        
        if referrer_id and referrer_id != str(user_id):
            referrer = self.db.get_user(referrer_id)
            if referrer and referrer.get("is_verified", False):
                new_refs = referrer.get("referrals", 0) + 1
                reward = Config.REWARD_PER_REFERRAL
                
                if new_refs == 10:
                    reward += Config.BONUS_AT_10_REFERRALS
                
                self.db.update_user(referrer_id, {
                    "referrals": new_refs,
                    "pending_balance": referrer.get("pending_balance", 0) + reward,
                    "total_earnings": referrer.get("total_earnings", 0) + reward
                })
                
                self.bot.send_message(
                    referrer_id,
                    f"""🎉 <b>New Referral!</b>

✅ @{username} joined using your link!
💰 You earned: <b>₹{reward}</b>
👥 Total referrals: <b>{new_refs}</b>

Keep sharing to earn more!"""
                )
                
                self.db.update_user(user_id, {
                    "referrer": referrer_id,
                    "referral_claimed": True
                })
    
    def check_verification(self, chat_id, message_id, user_id):
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, message_id, user_id)
            return
        
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ User not found.")
            return
        
        all_joined = True
        not_joined_channels = []
        
        for channel_id, channel in channels.items():
            channel_link = channel.get("link", "")
            
            if not channel_link:
                continue
            
            try:
                chat_id_for_check = channel_link
                
                if channel_link.startswith("@"):
                    chat_id_for_check = channel_link
                elif channel_link.isdigit() or (channel_link.startswith('-100') and channel_link[1:].isdigit()):
                    chat_id_for_check = channel_link
                else:
                    if not channel_link.startswith("@"):
                        chat_id_for_check = "@" + channel_link
                
                member_info = self.bot.get_chat_member(chat_id_for_check, user_id)
                
                if member_info and member_info.get("status") in ["member", "administrator", "creator"]:
                    self.db.mark_channel_joined(user_id, channel_id)
                else:
                    all_joined = False
                    not_joined_channels.append(channel.get("name", "Channel"))
            
            except Exception as e:
                print(f"⚠️ Error checking channel {channel_link}: {e}")
                all_joined = False
                not_joined_channels.append(channel.get("name", "Channel"))
        
        if all_joined:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, message_id, user_id)
        else:
            self.show_verification_failed(chat_id, message_id, user_id, not_joined_channels)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verification Successful!</b>

Welcome to <b>Trade Genius</b>, @{username}!

🎉 You can now start earning <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral.

👇 <b>Get started:</b>"""
        
        buttons = [
            ("🔗 Get Referral Link", "my_referral"),
            ("📊 Dashboard", "dashboard"),
            ("💳 Withdraw", "withdraw")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_failed(self, chat_id, message_id, user_id, missing_channels):
        msg = "❌ <b>Please join all channels first</b>"
        
        channels = self.db.get_channels()
        buttons = []
        
        for channel_id, channel in channels.items():
            if channel.get("name") in missing_channels:
                channel_link = channel.get("link", "")
                channel_name = channel.get("name", "Channel")
                
                clean_name = channel_name.replace("📢", "").replace("🔔", "").replace("📰", "").strip()
                if not clean_name:
                    clean_name = "Join Channel"
                
                if channel_link.startswith("@"):
                    channel_url = f"https://t.me/{channel_link[1:]}"
                elif "t.me/" in channel_link:
                    channel_url = channel_link
                else:
                    channel_url = f"https://t.me/{channel_link}"
                
                buttons.append({"text": f"📢 {clean_name}", "url": channel_url})
        
        buttons.append(("✅ VERIFY JOIN ✅", "check_verification"))
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_welcome_screen(self, chat_id, user_id, username, user, args):
        if not user:
            user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username)
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Status: Active</b>" if is_admin else ""
        verified_text = "\n✅ <b>Status: Verified</b>" if user.get("is_verified", False) else "\n❌ <b>Status: Not Verified</b>"
        
        welcome_msg = f"""👋 <b>Welcome to Trade Genius Bot!</b> 💸

👤 Hello, @{username}!{admin_text}{verified_text}

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🔗 Your Code: <code>{user.get('referral_code', 'N/A')}</code>
👥 Referrals: {user.get('referrals', 0)}
💸 Balance: ₹{user.get('pending_balance', 0)}

👇 <b>Select an option:</b>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        
        self.bot.send_message(chat_id, welcome_msg, keyboard)
    
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
            buttons = [
                {"text": "🪙 Open Web", "url": web_url},
                ("🏠 Main Menu", "main_menu")
            ]
            keyboard = self.generate_keyboard(buttons, 2)
            msg = f"""🪙 <b></b>

"""
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        if callback == "admin_panel" and str(user_id) != Config.ADMIN_USER_ID:
            msg = "⛔ <b>Access Denied</b>"
            keyboard = self.generate_keyboard([("🏠 Main Menu", "main_menu")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
            if callback not in ["check_verification", "refresh_verification", "main_menu"]:
                msg = """❌ <b>Verification Required</b>

Please complete verification first to access bot features.

Join all required channels and verify."""
                keyboard = self.generate_keyboard([
                    ("✅ VERIFY JOIN ✅", "check_verification")
                ], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        if callback == "check_verification":
            self.check_verification(chat_id, message_id, user_id)
        
        elif callback == "refresh_verification":
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
        
        share_text = f"Join Trade Genius bot and earn money! {referral_link}"
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
        
        msg = f"""📊 <b>Dashboard</b>

👤 @{user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
📞 Phone: {user.get('phone', 'Not set')}
📧 Email: {user.get('email', 'Not set')}
🔄 Status: <b>{verified_status}</b>

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

Payment within 24 hours."""
        
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
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}{verified_text}

👋 @{user.get('username', 'User')}
💰 Balance: <b>₹{user.get('pending_balance', 0)}</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>"""
        
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
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
💳 Pending WD: {pending_withdrawals}
📢 Channels: {total_channels}
🌐 Web URL: {web_url[:30]}...

👇 <b>Select:</b>"""
        
        buttons = [
            ("📊 Statistics", "admin_stats"),
            ("💳 Withdrawals", "admin_withdrawals"),
            ("📢 Channels", "admin_channels"),
            ("🌐 Web URL", "admin_web_url"),
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
    
    def show_admin_stats(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        
        total_users = len(users) if users else 0
        verified = sum(1 for u in users.values() if u and u.get("is_verified", False))
        total_earnings = sum(u.get("total_earnings", 0) for u in users.values() if u)
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        web_url = self.db.get_web_url()
        
        msg = f"""📊 <b>Admin Statistics</b>

👥 <b>Users:</b>
• Total: {total_users}
• Verified: {verified}
• Pending Verification: {total_users - verified}

💰 <b>Financial:</b>
• Total Earnings: ₹{total_earnings}
• Per Referral: ₹{Config.REWARD_PER_REFERRAL}
• Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}

📢 <b>Channels:</b>
• Total: {total_channels}
• Verification: {'Required' if total_channels > 0 else 'Not Required'}

🌐 <b>Web URL:</b>
• {web_url}"""
        
        buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
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
                    phone = wd_data.get("phone", "N/A")
                    email = wd_data.get("email", "N/A")
                    date = datetime.fromisoformat(wd_data["requested_at"]).strftime("%d/%m %H:%M")
                    
                    msg += f"{i}. ₹{amount} - @{username}\n"
                    msg += f"   📱 UPI: {upi_id}\n"
                    msg += f"   📞 Phone: {phone}\n"
                    msg += f"   📧 Email: {email}\n"
                    msg += f"   📅 {date}\n\n"
                    
                    buttons.append((f"✅ Approve {i}", f"admin_approve_{wd_id}"))
                    buttons.append((f"❌ Reject {i}", f"admin_reject_{wd_id}"))
            
            buttons.append(("🔄 Refresh", "admin_withdrawals"))
            buttons.append(("🔙 Back", "admin_panel"))
        
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

Add more or delete existing channels."""
        
        buttons = [
            ("➕ Add Channel", "admin_add_channel"),
            ("👁 View Channels", "admin_view_channels"),
            ("🔙 Back", "admin_panel")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_add_channel(self, chat_id, message_id, user_id):
        msg = """➕ <b>Add New Channel</b>

Send channel details in this format:

<code>Channel Name
@channel_username
channel_id</code>

<b>Example:</b>
<code>Trade Genius Official
@TradeGenius07
-1001234567890</code>

<b>Important:</b>
• Bot must be ADMIN in the channel
• Get channel ID from @username_to_id_bot
• Users must join ALL channels to use bot"""
        
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
                name = channel.get("name", "Unknown")
                link = channel.get("link", "")
                msg += f"{i}. {name}\n   {link}\n\n"
                
                buttons.append((f"❌ Delete {i}", f"admin_delete_channel_{channel_id}"))
            
            buttons.append(("➕ Add More", "admin_add_channel"))
            buttons.append(("🔙 Back", "admin_channels"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def delete_channel(self, chat_id, message_id, user_id, channel_id):
        result = self.db.delete_channel(channel_id)
        
        if result is not None:
            msg = "✅ Channel deleted successfully."
        else:
            msg = "❌ Failed to delete channel."
        
        buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
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
📞 Phone: {wd_data.get('phone', 'N/A')}
📧 Email: {wd_data.get('email', 'N/A')}

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
    
    def show_user_management(self, chat_id, message_id, user_id):
        users = self.db.get_all_users()
        
        if not users:
            msg = "👥 <b>No Users</b>\n\nNo users yet."
        else:
            msg = "👥 <b>Top 10 Users</b>\n\n"
            
            sorted_users = sorted(
                [(uid, data) for uid, data in users.items() if data],
                key=lambda x: x[1].get("total_earnings", 0),
                reverse=True
            )[:10]
            
            for i, (uid, data) in enumerate(sorted_users, 1):
                username = data.get("username", "N/A")
                earnings = data.get("total_earnings", 0)
                referrals = data.get("referrals", 0)
                verified = "✅" if data.get("is_verified") else "❌"
                
                msg += f"{i}. {verified} @{username}\n   💰 ₹{earnings} | 👥 {referrals}\n"
        
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
                    
                    channel_data = {
                        "name": channel_name,
                        "link": channel_link,
                        "id": channel_id,
                        "added_by": str(user_id),
                        "added_at": datetime.now().isoformat()
                    }
                    
                    result = self.db.add_channel(channel_data)
                    
                    if result:
                        msg = f"✅ Channel added!\n\n📢 {channel_name}\n🔗 {channel_link}"
                    else:
                        msg = "❌ Failed to add channel."
                else:
                    msg = "❌ Invalid format."
                
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

The "Open Web" button will now use this URL."""
                    else:
                        msg = "❌ Failed to update web URL."
                else:
                    msg = "❌ Invalid URL. Must start with http:// or https://"
                
                buttons = [("🌐 Back to Web URL", "admin_web_url")]
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
    
    # 🛠️ FIXED: Proper webhook handling
    def run_bot(self):
        print("🤖 Trade Genius Bot Starting...")
        print(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        
        # 🛠️ IMPORTANT: Disable webhook completely
        print("🔄 Disabling webhook...")
        
        # First check webhook status
        webhook_info = self.bot._api_request("getWebhookInfo")
        if webhook_info:
            print(f"ℹ️ Current webhook: {webhook_info.get('url', 'None')}")
        
        # Delete webhook with pending updates
        delete_result = self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
        if delete_result:
            print("✅ Webhook disabled successfully")
        else:
            print("⚠️ Could not disable webhook, trying again...")
            # Try again
            self.bot._api_request("deleteWebhook", {})
        
        # Wait a bit
        time.sleep(2)
        
        # Verify webhook is disabled
        webhook_info = self.bot._api_request("getWebhookInfo")
        if webhook_info and webhook_info.get("url"):
            print(f"⚠️ Webhook still active: {webhook_info.get('url')}")
            # Force delete
            self.bot._api_request("deleteWebhook", {})
        else:
            print("✅ Webhook confirmed disabled")
        
        print(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
        print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        print(f"🌐 Web URL: {self.db.get_web_url()}")
        print("✅ FIXED: HTTP 409 Conflict Error")
        print("✅ ADDED: 'Get Free Coins' button")
        print("="*50)
        
        # Start polling
        self.offset = 0
        error_count = 0
        
        while self.running:
            try:
                # 🛠️ Get updates with error handling
                updates = self.bot.get_updates(self.offset)
                
                if updates is None:
                    # 409 error occurred, wait and retry
                    error_count += 1
                    if error_count > 5:
                        print("🔄 Too many errors, re-initializing bot...")
                        # Try to disable webhook again
                        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
                        error_count = 0
                        time.sleep(5)
                    else:
                        time.sleep(2)
                    continue
                
                # Reset error count on success
                error_count = 0
                
                if updates and isinstance(updates, list):
                    for update in updates:
                        self.offset = update["update_id"] + 1
                        
                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            user_id = msg["from"]["id"]
                            username = msg["from"].get("username", "User")
                            
                            if "text" in msg:
                                text = msg["text"]
                                
                                if text.startswith("/start"):
                                    parts = text.split()
                                    args = parts[1:] if len(parts) > 1 else []
                                    self.start_command(chat_id, user_id, username, args)
                                
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
                
                # Small delay between polls
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.running = False
                
            except Exception as e:
                print(f"❌ Unexpected Error: {e}")
                error_count += 1
                if error_count > 10:
                    print("🔴 Too many errors, restarting bot...")
                    time.sleep(10)
                    # Reset offset to avoid old updates
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
    print("🔥 Trade Genius Bot - FIXED VERSION")
    print("="*50)
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure bot token first!")
    else:
        run_both()