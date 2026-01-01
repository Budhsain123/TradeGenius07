# main.py - Trade Genius Bot - Fully Fixed Version

import os
import json
import time
import random
import string
import threading
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import quote
from flask import Flask, jsonify

# ==================== FLASK SERVER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "online", "bot": "TradeGeniusBot", "message": "Bot is running"})

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

# ==================== HTTP HELPER ====================
class HTTPHelper:
    @staticmethod
    def request(url, method="GET", data=None, timeout=30):
        try:
            headers = {'Content-Type': 'application/json'}
            if data and isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            response = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code != 409:
                print(f"HTTP Error {e.code}: {e}")
            return None
        except Exception as e:
            print(f"HTTP Error: {e}")
            return None

# ==================== FIREBASE DATABASE ====================
class FirebaseDB:
    def __init__(self):
        self.base_url = Config.FIREBASE_URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        self.local_data = self._load_local()
        print(f"🔥 Firebase Connected: {self.base_url}")
    
    def _load_local(self):
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "users": {},
            "withdrawals": {},
            "channels": {},
            "settings": {
                "web_url": Config.WEB_URL,
                "ai_button_name": Config.AI_BUTTON_NAME
            }
        }
    
    def _save_local(self):
        try:
            with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.local_data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _firebase_request(self, method, path, data=None):
        try:
            path = path.lstrip('/')
            url = self.base_url + path + ".json"
            return HTTPHelper.request(url, method, data)
        except Exception as e:
            print(f"Firebase Error: {e}")
            return None
    
    # Settings Methods
    def get_setting(self, key, default=None):
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get(key, self.local_data.get("settings", {}).get(key, default))
    
    def set_setting(self, key, value):
        result = self._firebase_request("PATCH", "settings", {key: value})
        if "settings" not in self.local_data:
            self.local_data["settings"] = {}
        self.local_data["settings"][key] = value
        self._save_local()
        return result
    
    # User Methods
    def get_user(self, user_id):
        user_id = str(user_id)
        data = self._firebase_request("GET", f"users/{user_id}")
        if data:
            return data
        return self.local_data.get('users', {}).get(user_id)
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        user_id = str(user_id)
        
        # Generate display name
        if not username or username.strip() == "":
            if first_name:
                username = first_name
                if last_name:
                    username += f" {last_name}"
            else:
                username = f"User_{user_id[-6:]}"
        
        # Generate referral code
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
            "is_admin": is_admin
        }
        
        self._firebase_request("PUT", f"users/{user_id}", user_data)
        
        if "users" not in self.local_data:
            self.local_data["users"] = {}
        self.local_data["users"][user_id] = user_data
        self._save_local()
        
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
        self._save_local()
        return True
    
    def find_user_by_referral_code(self, code):
        users = self._firebase_request("GET", "users") or {}
        for uid, data in users.items():
            if data and data.get("referral_code") == code:
                return uid, data
        return None, None
    
    def get_all_users(self):
        return self._firebase_request("GET", "users") or {}
    
    # Channel Methods
    def add_channel(self, channel_data):
        channel_id = channel_data.get("id")
        if not channel_id:
            return None
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        
        if "channels" not in self.local_data:
            self.local_data["channels"] = {}
        self.local_data["channels"][channel_id] = channel_data
        self._save_local()
        
        return result
    
    def get_channels(self):
        data = self._firebase_request("GET", "channels")
        if data:
            return data
        return self.local_data.get("channels", {})
    
    def delete_channel(self, channel_id):
        result = self._firebase_request("DELETE", f"channels/{channel_id}")
        
        if "channels" in self.local_data and channel_id in self.local_data["channels"]:
            del self.local_data["channels"][channel_id]
            self._save_local()
        
        return result
    
    # Withdrawal Methods
    def create_withdrawal(self, wd_id, data):
        return self._firebase_request("PUT", f"withdrawals/{wd_id}", data)
    
    def get_withdrawals(self, status=None):
        withdrawals = self._firebase_request("GET", "withdrawals") or {}
        if status:
            return {k: v for k, v in withdrawals.items() if v and v.get("status") == status}
        return withdrawals
    
    def update_withdrawal(self, wd_id, status, note=""):
        updates = {
            "status": status,
            "processed_at": datetime.now().isoformat()
        }
        if note:
            updates["admin_note"] = note
        return self._firebase_request("PATCH", f"withdrawals/{wd_id}", updates)

# ==================== TELEGRAM BOT API ====================
class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.db = FirebaseDB()
    
    def api_request(self, method, data=None):
        try:
            url = self.base_url + method
            if data:
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    return result.get('result')
                else:
                    print(f"API Error: {result}")
                    return None
        except urllib.error.HTTPError as e:
            if e.code == 409:
                time.sleep(2)
            else:
                print(f"API Error {e.code}: {e}")
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
    
    def get_chat_member(self, chat_id, user_id):
        """Check if user is member of a chat/channel"""
        try:
            # Try with original chat_id
            result = self.api_request("getChatMember", {
                "chat_id": chat_id,
                "user_id": user_id
            })
            
            if result:
                return result
            
            # Try with @ prefix for public channels
            if isinstance(chat_id, str) and not chat_id.startswith("-") and not chat_id.startswith("@"):
                result = self.api_request("getChatMember", {
                    "chat_id": "@" + chat_id,
                    "user_id": user_id
                })
                if result:
                    return result
            
            return None
        except Exception as e:
            print(f"getChatMember Error: {e}")
            return None
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self.api_request("sendMessage", data)
    
    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self.api_request("editMessageText", data)
    
    def answer_callback(self, callback_id, text=None, show_alert=False):
        data = {"callback_query_id": callback_id, "show_alert": show_alert}
        if text:
            data["text"] = text
        return self.api_request("answerCallbackQuery", data)
    
    def get_updates(self, offset=None, timeout=60):
        data = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]
        }
        if offset:
            data["offset"] = offset
        result = self.api_request("getUpdates", data)
        return result if result else []

# ==================== MAIN BOT CLASS ====================
class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBot(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.user_states = {}
        self.pending_referrals = {}
    
    def create_keyboard(self, buttons, columns=2):
        """Create inline keyboard from button list"""
        keyboard = []
        row = []
        
        for i, button in enumerate(buttons):
            if isinstance(button, tuple):
                # Regular callback button
                text, callback = button
                row.append({"text": text, "callback_data": callback})
            elif isinstance(button, dict):
                # URL button or custom button
                row.append(button)
            
            if len(row) == columns or i == len(buttons) - 1:
                if row:
                    keyboard.append(row)
                row = []
        
        return {"inline_keyboard": keyboard}
    
    def get_main_menu_buttons(self, user_id):
        """Get main menu buttons"""
        ai_name = self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME)
        
        buttons = [
            ("🔗 Get Referral Link", "referral"),
            ("📊 My Dashboard", "dashboard"),
            ("💳 Withdraw", "withdraw"),
            (ai_name, "open_web"),
            ("📜 Terms & Conditions", "terms"),
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support")
        ]
        
        if str(user_id) == Config.ADMIN_USER_ID:
            buttons.append(("👑 Admin Panel", "admin_panel"))
        
        return buttons
    
    def check_user_joined_channels(self, user_id):
        """Check if user has joined all required channels"""
        channels = self.db.get_channels()
        
        # If no channels, user is verified
        if not channels:
            print(f"✅ No channels to verify for user {user_id}")
            return True
        
        print(f"🔍 Checking {len(channels)} channels for user {user_id}")
        
        for channel_id, channel in channels.items():
            is_private = channel.get("is_private", False)
            
            if is_private:
                # Private channel - use chat_id
                chat_id = channel.get("chat_id")
                if not chat_id:
                    print(f"⚠️ Private channel {channel_id} has no chat_id")
                    continue
            else:
                # Public channel - use username
                username = channel.get("username", "")
                if not username:
                    print(f"⚠️ Public channel {channel_id} has no username")
                    continue
                chat_id = "@" + username if not username.startswith("@") else username
            
            try:
                print(f"🔍 Checking channel: {chat_id}")
                member_info = self.bot.get_chat_member(chat_id, user_id)
                
                if member_info:
                    status = member_info.get("status", "")
                    print(f"📊 User status in {chat_id}: {status}")
                    
                    if status in ["member", "administrator", "creator"]:
                        # User is member, mark as joined
                        self.db.update_user(user_id, {
                            f"channels_joined.{channel_id}": {
                                "joined_at": datetime.now().isoformat(),
                                "verified": True
                            }
                        })
                    else:
                        print(f"❌ User not member of {chat_id}")
                        return False
                else:
                    print(f"❌ Could not check membership for {chat_id}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error checking channel {chat_id}: {e}")
                return False
        
        print(f"✅ User {user_id} verified all channels")
        return True
    
    def process_referral(self, user_id, username, referral_code):
        """Process referral and credit rewards"""
        user = self.db.get_user(user_id)
        if not user:
            return False
        
        # Already claimed referral
        if user.get("referral_claimed"):
            print(f"⚠️ User {user_id} already claimed referral")
            return True
        
        # Find referrer
        referrer_id, referrer = self.db.find_user_by_referral_code(referral_code)
        
        if not referrer or not referrer_id:
            print(f"❌ Referral code not found: {referral_code}")
            return False
        
        # Prevent self-referral
        if referrer_id == str(user_id):
            print(f"❌ Self-referral attempt by {user_id}")
            return False
        
        # Check if referrer is verified
        if not referrer.get("is_verified"):
            print(f"❌ Referrer {referrer_id} not verified")
            return False
        
        # Calculate reward
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL
        
        # Bonus at 10 referrals
        if new_refs == 10:
            reward += Config.BONUS_AT_10_REFERRALS
        
        # Update referrer
        self.db.update_user(referrer_id, {
            "referrals": new_refs,
            "pending_balance": referrer.get("pending_balance", 0) + reward,
            "total_earnings": referrer.get("total_earnings", 0) + reward
        })
        
        # Update new user
        self.db.update_user(user_id, {
            "referrer": referrer_id,
            "referral_claimed": True,
            "referral_claimed_at": datetime.now().isoformat()
        })
        
        # Notify referrer
        display_name = username if username else f"User_{str(user_id)[-6:]}"
        try:
            self.bot.send_message(
                referrer_id,
                f"""🎉 <b>New Referral Success!</b>

✅ {display_name} joined using your link!
💰 You earned: <b>₹{reward}</b>
👥 Total referrals: <b>{new_refs}</b>

Keep sharing to earn more!"""
            )
        except Exception as e:
            print(f"⚠️ Failed to notify referrer: {e}")
        
        print(f"✅ Referral processed: {user_id} -> {referrer_id} (₹{reward})")
        return True
    
    def show_verification_screen(self, chat_id, user_id):
        """Show channel join verification screen"""
        channels = self.db.get_channels()
        
        if not channels:
            # No channels to verify
            self.db.update_user(user_id, {"is_verified": True})
            user = self.db.get_user(user_id)
            self.show_welcome(chat_id, user_id, user)
            return
        
        msg = """🔐 <b>Verification Required</b>

To use this bot, please join ALL our channels below:

⚠️ <b>Important:</b>
• Click each button to join
• After joining ALL channels, click "✅ VERIFY NOW"
• Wait 5-10 seconds after joining before verifying"""
        
        buttons = []
        
        for channel_id, channel in channels.items():
            name = channel.get("name", "Channel")
            link = channel.get("link", "")
            
            if link:
                buttons.append({"text": f"📢 {name}", "url": link})
        
        buttons.append(("✅ I'VE JOINED ALL - VERIFY NOW", "verify_channels"))
        
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def verify_channels(self, chat_id, message_id, user_id):
        """Verify user has joined all channels"""
        user = self.db.get_user(user_id)
        if not user:
            self.bot.send_message(chat_id, "❌ User not found. Please /start again.")
            return
        
        # Check all channels
        all_joined = self.check_user_joined_channels(user_id)
        
        if all_joined:
            # Mark user as verified
            self.db.update_user(user_id, {"is_verified": True})
            
            # Process pending referral
            user_id_str = str(user_id)
            if user_id_str in self.pending_referrals:
                referral_code = self.pending_referrals.pop(user_id_str)
                username = user.get("username", "")
                self.process_referral(user_id, username, referral_code)
            
            # Show success
            msg = f"""✅ <b>Verification Successful!</b>

Welcome to <b>TradeGenius07 Bot</b>!

🎉 You can now start earning <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral.

👇 <b>Get started:</b>"""
            
            buttons = [
                ("🔗 Get Referral Link", "referral"),
                ("📊 Dashboard", "dashboard"),
                ("🏠 Main Menu", "main_menu")
            ]
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        else:
            # Verification failed
            msg = """❌ <b>Verification Failed</b>

You haven't joined all channels yet.

<b>Please:</b>
1️⃣ Join ALL channels from the buttons above
2️⃣ Wait 10 seconds after joining
3️⃣ Click VERIFY again

⚠️ Make sure you've joined EVERY channel!"""
            
            buttons = [
                ("🔄 Try Again", "verify_channels"),
                ("📋 Show Channels", "show_channels")
            ]
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_welcome(self, chat_id, user_id, user):
        """Show welcome screen"""
        if not user:
            user = self.db.get_user(user_id)
        if not user:
            return
        
        is_admin = str(user_id) == Config.ADMIN_USER_ID
        admin_text = "\n👑 <b>Admin Status: Active</b>" if is_admin else ""
        verified_text = "✅ Verified" if user.get("is_verified") else "❌ Not Verified"
        
        username = user.get("username", f"User_{str(user_id)[-6:]}")
        
        msg = f"""👋 <b>Welcome to TradeGenius07 Bot!</b> 💸

👤 Hello, {username}!{admin_text}
🔄 Status: <b>{verified_text}</b>

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🔗 Your Code: <code>{user.get('referral_code', 'N/A')}</code>
👥 Referrals: {user.get('referrals', 0)}
💸 Balance: ₹{user.get('pending_balance', 0)}

👇 <b>Select an option:</b>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def handle_start(self, chat_id, user_id, username, first_name, last_name, args):
        """Handle /start command"""
        # Get or create user
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username, first_name, last_name)
            print(f"✅ New user created: {user_id}")
        
        is_admin = str(user_id) == Config.ADMIN_USER_ID
        
        # Admin is always verified
        if is_admin and not user.get("is_verified"):
            self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
        
        # Store referral code if provided
        referral_code = args[0] if args else None
        if referral_code:
            self.pending_referrals[str(user_id)] = referral_code
            print(f"📝 Stored referral code for {user_id}: {referral_code}")
        
        # Check if channels exist
        channels = self.db.get_channels()
        
        if not channels:
            # No channels required
            if not user.get("is_verified"):
                self.db.update_user(user_id, {"is_verified": True})
                user["is_verified"] = True
            
            # Process referral immediately
            if str(user_id) in self.pending_referrals:
                code = self.pending_referrals.pop(str(user_id))
                self.process_referral(user_id, username, code)
            
            self.show_welcome(chat_id, user_id, user)
            return
        
        # Admin skips verification
        if is_admin:
            if str(user_id) in self.pending_referrals:
                code = self.pending_referrals.pop(str(user_id))
                self.process_referral(user_id, username, code)
            self.show_welcome(chat_id, user_id, user)
            return
        
        # Check if already verified
        if user.get("is_verified"):
            # Process any pending referral
            if str(user_id) in self.pending_referrals:
                code = self.pending_referrals.pop(str(user_id))
                self.process_referral(user_id, username, code)
            self.show_welcome(chat_id, user_id, user)
            return
        
        # Check if user joined all channels
        all_joined = self.check_user_joined_channels(user_id)
        
        if all_joined:
            self.db.update_user(user_id, {"is_verified": True})
            user["is_verified"] = True
            
            if str(user_id) in self.pending_referrals:
                code = self.pending_referrals.pop(str(user_id))
                self.process_referral(user_id, username, code)
            
            self.show_welcome(chat_id, user_id, user)
        else:
            # Show verification screen
            self.show_verification_screen(chat_id, user_id)
    
    def handle_callback(self, chat_id, message_id, user_id, callback_data):
        """Handle callback queries"""
        callback_id = callback_data.get("id")
        data = callback_data.get("data", "")
        
        # Answer callback
        self.bot.answer_callback(callback_id)
        
        # Get user
        user = self.db.get_user(user_id) or {}
        is_admin = str(user_id) == Config.ADMIN_USER_ID
        
        # Verification related callbacks - always allowed
        if data in ["verify_channels", "show_channels"]:
            if data == "verify_channels":
                self.verify_channels(chat_id, message_id, user_id)
            else:
                self.show_verification_screen(chat_id, user_id)
            return
        
        # Check verification for non-admin users
        if not is_admin and not user.get("is_verified"):
            if data != "main_menu":
                msg = """❌ <b>Verification Required</b>

Please complete verification first to access bot features.

Join all required channels and verify."""
                
                buttons = [("✅ VERIFY NOW", "show_channels")]
                keyboard = self.create_keyboard(buttons, 1)
                self.bot.edit_message(chat_id, message_id, msg, keyboard)
                return
        
        # Handle different callbacks
        if data == "main_menu":
            self.show_main_menu(chat_id, message_id, user_id, user)
        
        elif data == "referral":
            self.show_referral(chat_id, message_id, user_id, user)
        
        elif data == "dashboard":
            self.show_dashboard(chat_id, message_id, user_id, user)
        
        elif data == "withdraw":
            self.show_withdraw(chat_id, message_id, user_id, user)
        
        elif data == "setup_upi":
            self.setup_upi(chat_id, message_id, user_id)
        
        elif data == "request_withdraw":
            self.request_withdrawal(chat_id, message_id, user_id, user)
        
        elif data == "withdraw_history":
            self.show_withdraw_history(chat_id, message_id, user_id)
        
        elif data == "open_web":
            self.show_web_button(chat_id, message_id)
        
        elif data == "terms":
            self.show_terms(chat_id, message_id)
        
        elif data == "how_it_works":
            self.show_how_it_works(chat_id, message_id)
        
        elif data == "rewards":
            self.show_rewards(chat_id, message_id)
        
        elif data == "support":
            self.show_support(chat_id, message_id)
        
        elif data == "admin_panel" and is_admin:
            self.show_admin_panel(chat_id, message_id, user_id)
        
        elif data.startswith("admin_") and is_admin:
            self.handle_admin_callback(chat_id, message_id, user_id, data)
    
    def show_main_menu(self, chat_id, message_id, user_id, user):
        """Show main menu"""
        is_admin = str(user_id) == Config.ADMIN_USER_ID
        admin_text = "\n👑 <b>Admin Mode</b>" if is_admin else ""
        
        username = user.get("username", f"User_{str(user_id)[-6:]}")
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}

👋 {username}
💰 Balance: <b>₹{user.get('pending_balance', 0)}</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_referral(self, chat_id, message_id, user_id, user):
        """Show referral link"""
        referral_code = user.get("referral_code", "")
        if not referral_code:
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.db.update_user(user_id, {"referral_code": referral_code})
        
        referral_link = f"https://t.me/{Config.BOT_USERNAME}?start={referral_code}"
        
        msg = f"""🔗 <b>Your Referral Link</b>

<code>{referral_link}</code>

💰 <b>Earn ₹{Config.REWARD_PER_REFERRAL} per referral!</b>

📊 <b>Your Stats:</b>
👥 Referrals: {user.get('referrals', 0)}
💰 Pending: ₹{user.get('pending_balance', 0)}
💸 Total Earned: ₹{user.get('total_earnings', 0)}

Share this link with friends and earn!"""
        
        share_text = f"Join TradeGenius07 and earn money! {referral_link}"
        share_url = f"https://t.me/share/url?url={quote(referral_link)}&text={quote(share_text)}"
        
        buttons = [
            {"text": "📤 Share Link", "url": share_url},
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_dashboard(self, chat_id, message_id, user_id, user):
        """Show dashboard"""
        verified = "✅ Verified" if user.get("is_verified") else "❌ Not Verified"
        
        msg = f"""📊 <b>Dashboard</b>

👤 {user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
🔄 Status: <b>{verified}</b>

📈 <b>Statistics:</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
💰 Pending: <b>₹{user.get('pending_balance', 0)}</b>
💸 Total Earned: <b>₹{user.get('total_earnings', 0)}</b>
✅ Withdrawn: <b>₹{user.get('withdrawn', 0)}</b>"""
        
        buttons = [
            ("💳 Withdraw", "withdraw"),
            ("🔗 Get Link", "referral"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_withdraw(self, chat_id, message_id, user_id, user):
        """Show withdraw menu"""
        balance = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if not upi_id:
            msg = f"""❌ <b>UPI ID Required</b>

You need to set up your UPI ID first.
UPI ID format: <code>username@upi</code>

💰 Current balance: <b>₹{balance}</b>
💰 Minimum withdrawal: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>"""
            
            buttons = [
                ("📱 Setup UPI ID", "setup_upi"),
                ("📊 Dashboard", "dashboard"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        elif balance >= Config.MINIMUM_WITHDRAWAL:
            msg = f"""💳 <b>Withdraw Funds</b>

💰 Available: <b>₹{balance}</b>
💰 Minimum: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📱 Your UPI: <code>{upi_id}</code>

🏦 <b>Payment Method:</b> UPI Only

⚠️ Payments processed within 24-72 hours"""
            
            buttons = [
                ("✅ Request Withdrawal", "request_withdraw"),
                ("✏️ Change UPI", "setup_upi"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        else:
            needed = Config.MINIMUM_WITHDRAWAL - balance
            refs_needed = (needed + Config.REWARD_PER_REFERRAL - 1) // Config.REWARD_PER_REFERRAL
            
            msg = f"""❌ <b>Insufficient Balance</b>

💰 Available: <b>₹{balance}</b>
💰 Required: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📊 Need: <b>₹{needed}</b> more

🔗 Get {refs_needed} more referral(s) to withdraw."""
            
            buttons = [
                ("🔗 Referral Link", "referral"),
                ("📜 History", "withdraw_history"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def setup_upi(self, chat_id, message_id, user_id):
        """Setup UPI ID"""
        self.user_states[user_id] = {
            "state": "awaiting_upi",
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        msg = """📱 <b>Setup UPI ID</b>

Send your UPI ID in this format:
<code>username@upi</code>

<b>Examples:</b>
• <code>john.doe@okaxis</code>
• <code>9876543210@ybl</code>
• <code>myname@paytm</code>

⚠️ Withdrawals will be sent to this UPI ID."""
        
        buttons = [("❌ Cancel", "withdraw")]
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def request_withdrawal(self, chat_id, message_id, user_id, user):
        """Request withdrawal"""
        balance = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if balance < Config.MINIMUM_WITHDRAWAL:
            self.show_withdraw(chat_id, message_id, user_id, user)
            return
        
        if not upi_id:
            self.show_withdraw(chat_id, message_id, user_id, user)
            return
        
        # Create withdrawal
        wd_id = f"WD{random.randint(100000, 999999)}"
        
        wd_data = {
            "user_id": str(user_id),
            "username": user.get("username", ""),
            "amount": balance,
            "upi_id": upi_id,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "withdrawal_id": wd_id
        }
        
        self.db.create_withdrawal(wd_id, wd_data)
        
        # Update user balance
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + balance
        })
        
        # Notify admin
        admin_msg = f"""🆕 <b>NEW WITHDRAWAL REQUEST</b>

👤 User: @{user.get('username', 'N/A')}
💰 Amount: <b>₹{balance}</b>
📱 UPI: <code>{upi_id}</code>
📋 ID: {wd_id}
⏰ Time: {datetime.now().strftime('%H:%M %d/%m/%Y')}

Use /admin to manage."""
        
        self.bot.send_message(Config.ADMIN_USER_ID, admin_msg)
        
        # Confirm to user
        msg = f"""✅ <b>Withdrawal Request Submitted!</b>

📋 ID: <code>{wd_id}</code>
💰 Amount: <b>₹{balance}</b>
📱 UPI: <code>{upi_id}</code>
📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
🔄 Status: <b>Pending</b>

⏳ Payouts processed within 24-72 hours.
🏦 Not processed on bank holidays."""
        
        buttons = [
            ("📜 Check Status", "withdraw_history"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_withdraw_history(self, chat_id, message_id, user_id):
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
            
            for wd_id, wd in sorted_wds:
                status = wd.get("status", "pending")
                amount = wd.get("amount", 0)
                
                emoji = {"completed": "✅", "rejected": "❌"}.get(status, "⏳")
                msg += f"{emoji} ₹{amount} - {status.upper()}\n"
        
        buttons = [
            ("💳 Withdraw", "withdraw"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_web_button(self, chat_id, message_id):
        """Show web button"""
        web_url = self.db.get_setting("web_url", Config.WEB_URL)
        ai_name = self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME)
        
        msg = """🤖 <b>AI Assistant</b>

🔓 Tap the button below to access:"""
        
        buttons = [
            {"text": ai_name, "url": web_url},
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_terms(self, chat_id, message_id):
        """Show terms and conditions"""
        msg = f"""📜 <b>Terms & Conditions</b>

✅ <b>By using this bot, you agree to:</b>

1. <b>Join all channels</b> to earn points
2. Each user can earn from <b>ONLY ONE referrer</b>
3. <b>No self-referrals</b> allowed
4. Points are <b>non-transferable</b>
5. <b>Fraud = Permanent Ban</b>

📝 <b>Withdrawal Terms:</b>
• Minimum: ₹{Config.MINIMUM_WITHDRAWAL}
• Method: UPI Only
• Processing: 24-72 hours
• Must be 18+ to use

<i>Last Updated: {datetime.now().strftime('%d %B %Y')}</i>"""
        
        buttons = [("✅ I Understand", "main_menu")]
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_how_it_works(self, chat_id, message_id):
        """Show how it works"""
        msg = f"""📢 <b>How It Works</b>

1️⃣ <b>Join Channels</b>
   Complete verification first

2️⃣ <b>Get Your Referral Link</b>
   Share with friends & family

3️⃣ <b>Earn Money</b>
   Get ₹{Config.REWARD_PER_REFERRAL} for each referral

4️⃣ <b>Withdraw</b>
   Minimum ₹{Config.MINIMUM_WITHDRAWAL} via UPI

It's that simple! Start earning now! 🚀"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_rewards(self, chat_id, message_id):
        """Show rewards info"""
        msg = f"""🎁 <b>Rewards System</b>

💰 <b>Per Referral:</b> ₹{Config.REWARD_PER_REFERRAL}
🔥 <b>10 Referrals Bonus:</b> +₹{Config.BONUS_AT_10_REFERRALS}
👑 <b>Top Referrer:</b> Special Rewards

📊 <b>Example Earnings:</b>
• 5 referrals = ₹{Config.REWARD_PER_REFERRAL * 5}
• 10 referrals = ₹{Config.REWARD_PER_REFERRAL * 10 + Config.BONUS_AT_10_REFERRALS}
• 20 referrals = ₹{Config.REWARD_PER_REFERRAL * 20 + Config.BONUS_AT_10_REFERRALS}
• 50 referrals = ₹{Config.REWARD_PER_REFERRAL * 50 + Config.BONUS_AT_10_REFERRALS}

Start sharing and earning today! 💸"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_support(self, chat_id, message_id):
        """Show support info"""
        msg = f"""📞 <b>Support</b>

Need help? Contact us:

📢 Support: {Config.SUPPORT_CHANNEL}

We're here to help! 🤝"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.create_keyboard(buttons, 1)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def show_admin_panel(self, chat_id, message_id, user_id):
        """Show admin panel"""
        users = self.db.get_all_users()
        total_users = len(users) if users else 0
        
        pending_wds = self.db.get_withdrawals("pending")
        pending_count = len(pending_wds) if pending_wds else 0
        
        channels = self.db.get_channels()
        channel_count = len(channels) if channels else 0
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Statistics:</b>
👥 Total Users: {total_users}
💳 Pending Withdrawals: {pending_count}
📢 Channels: {channel_count}

👇 <b>Select an option:</b>"""
        
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
        
        keyboard = self.create_keyboard(buttons, 2)
        self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def handle_admin_callback(self, chat_id, message_id, user_id, data):
        """Handle admin callbacks"""
        
        if data == "admin_stats":
            users = self.db.get_all_users()
            total = len(users) if users else 0
            verified = sum(1 for u in users.values() if u and u.get("is_verified")) if users else 0
            earnings = sum(u.get("total_earnings", 0) for u in users.values() if u) if users else 0
            
            channels = self.db.get_channels()
            
            msg = f"""📊 <b>Admin Statistics</b>

👥 <b>Users:</b>
• Total: {total}
• Verified: {verified}
• Pending: {total - verified}

💰 <b>Financial:</b>
• Total Earnings: ₹{earnings}
• Per Referral: ₹{Config.REWARD_PER_REFERRAL}
• Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}

📢 <b>Channels:</b> {len(channels) if channels else 0}"""
            
            buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_withdrawals":
            wds = self.db.get_withdrawals("pending")
            
            if not wds:
                msg = "💳 <b>Pending Withdrawals</b>\n\nNo pending requests."
                buttons = [("🔄 Refresh", "admin_withdrawals"), ("🔙 Back", "admin_panel")]
            else:
                msg = "💳 <b>Pending Withdrawals</b>\n\n"
                buttons = []
                
                for i, (wd_id, wd) in enumerate(wds.items(), 1):
                    if wd:
                        msg += f"{i}. ₹{wd.get('amount', 0)} - @{wd.get('username', 'N/A')}\n"
                        msg += f"   📱 UPI: {wd.get('upi_id', 'N/A')}\n\n"
                        
                        buttons.extend([
                            (f"✅ Approve {i}", f"admin_approve_{wd_id}"),
                            (f"❌ Reject {i}", f"admin_reject_{wd_id}")
                        ])
                
                buttons.extend([("🔄 Refresh", "admin_withdrawals"), ("🔙 Back", "admin_panel")])
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_channels":
            channels = self.db.get_channels()
            count = len(channels) if channels else 0
            
            msg = f"""📢 <b>Channel Management</b>

{count} channel(s) configured.

Add channels to require users to join before using the bot."""
            
            buttons = [
                ("➕ Add Channel", "admin_add_channel"),
                ("👁 View Channels", "admin_view_channels"),
                ("🔙 Back", "admin_panel")
            ]
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_add_channel":
            msg = """➕ <b>Add New Channel</b>

<b>📢 For PUBLIC Channel:</b>
Send 2 lines:
<code>Channel Name
username</code>

Example:
<code>Trade Genius Updates
TradeGenius07</code>

<b>🔒 For PRIVATE Channel:</b>
Send 3 lines:
<code>Channel Name
https://t.me/+XXXXX
-100XXXXXXXXX</code>

⚠️ <b>Important:</b>
• Bot must be ADMIN in the channel
• For private channels, get chat_id by forwarding a message from channel to @userinfobot"""
            
            self.user_states[user_id] = {
                "state": "awaiting_channel",
                "chat_id": chat_id,
                "message_id": message_id
            }
            
            buttons = [("❌ Cancel", "admin_channels")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_view_channels":
            channels = self.db.get_channels()
            
            if not channels:
                msg = "📢 <b>No Channels</b>\n\nNo channels added yet."
                buttons = [("➕ Add Channel", "admin_add_channel"), ("🔙 Back", "admin_channels")]
            else:
                msg = "📢 <b>Current Channels</b>\n\n"
                buttons = []
                
                for i, (cid, ch) in enumerate(channels.items(), 1):
                    name = ch.get("name", "Unknown")
                    is_private = ch.get("is_private", False)
                    
                    if is_private:
                        link = ch.get("link", "Private")
                        msg += f"{i}. 🔒 <b>{name}</b>\n   {link}\n\n"
                    else:
                        username = ch.get("username", "")
                        msg += f"{i}. 📢 <b>{name}</b>\n   @{username}\n\n"
                    
                    buttons.append((f"❌ Delete {i}", f"admin_delete_channel_{cid}"))
                
                buttons.extend([("➕ Add More", "admin_add_channel"), ("🔙 Back", "admin_channels")])
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data.startswith("admin_delete_channel_"):
            channel_id = data.replace("admin_delete_channel_", "")
            self.db.delete_channel(channel_id)
            
            msg = "✅ Channel deleted successfully."
            buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data.startswith("admin_approve_"):
            wd_id = data.replace("admin_approve_", "")
            wds = self.db.get_withdrawals()
            wd = wds.get(wd_id) if wds else None
            
            if wd:
                self.db.update_withdrawal(wd_id, "completed", f"Approved by admin")
                
                # Notify user
                self.bot.send_message(
                    wd["user_id"],
                    f"""✅ <b>Withdrawal Approved!</b>

💰 Amount: <b>₹{wd['amount']}</b>
📋 ID: <code>{wd_id}</code>
📱 UPI: <code>{wd.get('upi_id', 'N/A')}</code>

Payment sent! Check your UPI within 24 hours."""
                )
                
                msg = f"✅ Withdrawal {wd_id} approved. User notified."
            else:
                msg = f"❌ Withdrawal {wd_id} not found."
            
            buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data.startswith("admin_reject_"):
            wd_id = data.replace("admin_reject_", "")
            wds = self.db.get_withdrawals()
            wd = wds.get(wd_id) if wds else None
            
            if not wd:
                msg = f"❌ Withdrawal {wd_id} not found."
                buttons = [("💳 Back", "admin_withdrawals")]
                keyboard = self.create_keyboard(buttons, 1)
                self.bot.edit_message(chat_id, message_id, msg, keyboard)
                return
            
            self.user_states[user_id] = {
                "state": "awaiting_rejection_reason",
                "withdrawal_id": wd_id,
                "user_id": wd["user_id"],
                "amount": wd["amount"],
                "chat_id": chat_id,
                "message_id": message_id
            }
            
            msg = f"""❌ <b>Reject Withdrawal</b>

📋 ID: {wd_id}
👤 User: @{wd.get('username', 'N/A')}
💰 Amount: ₹{wd['amount']}
📱 UPI: {wd.get('upi_id', 'N/A')}

Send rejection reason:"""
            
            buttons = [("❌ Cancel", "admin_withdrawals")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_web_url":
            url = self.db.get_setting("web_url", Config.WEB_URL)
            
            msg = f"""🌐 <b>Web URL Management</b>

Current URL:
<code>{url}</code>"""
            
            buttons = [
                ("✏️ Update URL", "admin_set_web_url"),
                ("🔙 Back", "admin_panel")
            ]
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_set_web_url":
            self.user_states[user_id] = {
                "state": "awaiting_web_url",
                "chat_id": chat_id,
                "message_id": message_id
            }
            
            msg = """🌐 <b>Update Web URL</b>

Send new URL (must start with https://):"""
            
            buttons = [("❌ Cancel", "admin_web_url")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_ai_button":
            name = self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME)
            
            msg = f"""🤖 <b>AI Button Management</b>

Current Name:
<code>{name}</code>"""
            
            buttons = [
                ("✏️ Update Name", "admin_set_ai_button"),
                ("🔙 Back", "admin_panel")
            ]
            
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_set_ai_button":
            self.user_states[user_id] = {
                "state": "awaiting_ai_button_name",
                "chat_id": chat_id,
                "message_id": message_id
            }
            
            msg = """🤖 <b>Update AI Button Name</b>

Send new name (max 20 characters):
Example: 🤖 AI Chat"""
            
            buttons = [("❌ Cancel", "admin_ai_button")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_users":
            users = self.db.get_all_users()
            
            if not users:
                msg = "👥 <b>No Users</b>"
            else:
                msg = "👥 <b>Top 10 Users by Referrals</b>\n\n"
                
                sorted_users = sorted(
                    [(k, v) for k, v in users.items() if v],
                    key=lambda x: x[1].get("referrals", 0),
                    reverse=True
                )[:10]
                
                for i, (uid, u) in enumerate(sorted_users, 1):
                    verified = "✅" if u.get("is_verified") else "❌"
                    msg += f"{i}. {verified} {u.get('username', 'User')}\n"
                    msg += f"   💰 ₹{u.get('total_earnings', 0)} | 👥 {u.get('referrals', 0)}\n"
            
            buttons = [("🔄 Refresh", "admin_users"), ("🔙 Back", "admin_panel")]
            keyboard = self.create_keyboard(buttons, 2)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
        
        elif data == "admin_broadcast":
            msg = """📢 <b>Broadcast Message</b>

Use command:
<code>/broadcast Your message here</code>

Example:
<code>/broadcast 🎉 New feature available!</code>"""
            
            buttons = [("🔙 Back", "admin_panel")]
            keyboard = self.create_keyboard(buttons, 1)
            self.bot.edit_message(chat_id, message_id, msg, keyboard)
    
    def handle_message(self, chat_id, user_id, text):
        """Handle user messages"""
        
        # Check if user is in a state
        if user_id in self.user_states:
            state = self.user_states[user_id]
            state_type = state.get("state")
            
            if state_type == "awaiting_upi":
                upi_id = text.strip()
                
                if '@' in upi_id and len(upi_id) >= 5:
                    self.db.update_user(user_id, {"upi_id": upi_id})
                    
                    msg = f"""✅ <b>UPI ID Saved!</b>

📱 Your UPI: <code>{upi_id}</code>

You can now request withdrawals."""
                    
                    buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
                    keyboard = self.create_keyboard(buttons, 2)
                    self.bot.send_message(chat_id, msg, keyboard)
                else:
                    self.bot.send_message(chat_id, "❌ Invalid UPI ID. Format: <code>name@upi</code>")
                    return
                
                del self.user_states[user_id]
            
            elif state_type == "awaiting_channel":
                lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
                
                if len(lines) >= 2:
                    name = lines[0]
                    second = lines[1]
                    
                    # Check if private channel
                    is_private = "t.me/+" in second or second.startswith("-100")
                    
                    if is_private:
                        # Private channel
                        link = second if "t.me" in second else None
                        chat_id_num = lines[2] if len(lines) >= 3 else (second if second.startswith("-100") else None)
                        
                        if not chat_id_num or not str(chat_id_num).startswith("-100"):
                            self.bot.send_message(chat_id, """❌ For private channels, provide chat_id (-100XXX)

Format:
<code>Channel Name
https://t.me/+XXXXX
-100XXXXXXXXX</code>

Get chat_id by forwarding a message to @userinfobot""")
                            return
                        
                        channel_id = f"private_{int(time.time())}"
                        channel_data = {
                            "id": channel_id,
                            "name": name,
                            "link": link or f"Private Channel",
                            "chat_id": str(chat_id_num),
                            "is_private": True,
                            "added_at": datetime.now().isoformat()
                        }
                    else:
                        # Public channel
                        username = second.replace("@", "").replace("https://t.me/", "").replace(" ", "").lower()
                        
                        channel_id = f"channel_{username}_{int(time.time())}"
                        channel_data = {
                            "id": channel_id,
                            "name": name,
                            "username": username,
                            "link": f"https://t.me/{username}",
                            "is_private": False,
                            "added_at": datetime.now().isoformat()
                        }
                    
                    result = self.db.add_channel(channel_data)
                    
                    if result is not None:
                        private_text = " (Private)" if is_private else ""
                        msg = f"""✅ <b>Channel Added{private_text}!</b>

📢 Name: {name}
🔗 Link: {channel_data.get('link', 'N/A')}

Bot must be admin in this channel!"""
                    else:
                        msg = "❌ Failed to add channel. Try again."
                    
                    buttons = [
                        ("📢 View Channels", "admin_view_channels"),
                        ("➕ Add More", "admin_add_channel"),
                        ("🔙 Back", "admin_channels")
                    ]
                    keyboard = self.create_keyboard(buttons, 2)
                    self.bot.send_message(chat_id, msg, keyboard)
                else:
                    self.bot.send_message(chat_id, "❌ Invalid format. Send at least 2 lines.")
                    return
                
                del self.user_states[user_id]
            
            elif state_type == "awaiting_rejection_reason":
                reason = text.strip()
                wd_id = state["withdrawal_id"]
                wd_user_id = state["user_id"]
                amount = state["amount"]
                
                # Reject and refund
                self.db.update_withdrawal(wd_id, "rejected", reason)
                
                user = self.db.get_user(wd_user_id)
                if user:
                    self.db.update_user(wd_user_id, {
                        "pending_balance": user.get("pending_balance", 0) + amount
                    })
                
                # Notify user
                self.bot.send_message(wd_user_id, f"""❌ <b>Withdrawal Rejected</b>

💰 Amount: ₹{amount}
📋 ID: {wd_id}
📝 Reason: {reason}

Amount has been returned to your balance.""")
                
                msg = f"❌ Withdrawal {wd_id} rejected. User notified. ₹{amount} refunded."
                buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
                keyboard = self.create_keyboard(buttons, 1)
                self.bot.send_message(chat_id, msg, keyboard)
                
                del self.user_states[user_id]
            
            elif state_type == "awaiting_web_url":
                url = text.strip()
                
                if url.startswith("http://") or url.startswith("https://"):
                    self.db.set_setting("web_url", url)
                    msg = f"✅ Web URL updated to:\n<code>{url}</code>"
                else:
                    msg = "❌ Invalid URL. Must start with http:// or https://"
                
                buttons = [("🔙 Back", "admin_web_url")]
                keyboard = self.create_keyboard(buttons, 1)
                self.bot.send_message(chat_id, msg, keyboard)
                del self.user_states[user_id]
            
            elif state_type == "awaiting_ai_button_name":
                name = text.strip()
                
                if 0 < len(name) <= 20:
                    self.db.set_setting("ai_button_name", name)
                    msg = f"✅ AI Button name updated to:\n<code>{name}</code>"
                else:
                    msg = "❌ Name must be 1-20 characters."
                
                buttons = [("🔙 Back", "admin_ai_button")]
                keyboard = self.create_keyboard(buttons, 1)
                self.bot.send_message(chat_id, msg, keyboard)
                del self.user_states[user_id]
        
        # Handle broadcast command
        elif text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                message = parts[1]
                users = self.db.get_all_users()
                
                if not users:
                    self.bot.send_message(chat_id, "❌ No users to broadcast.")
                    return
                
                total = len(users)
                self.bot.send_message(chat_id, f"📢 Broadcasting to {total} users...")
                
                success = 0
                for uid in users.keys():
                    try:
                        result = self.bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{message}")
                        if result:
                            success += 1
                        time.sleep(0.1)
                    except:
                        pass
                
                self.bot.send_message(chat_id, f"✅ Broadcast complete!\nSent: {success}/{total}")
    
    def run(self):
        """Run the bot"""
        print("=" * 50)
        print("🤖 Trade Genius Bot Starting...")
        print(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        
        # Disable webhook
        print("🔄 Disabling webhook...")
        self.bot.api_request("deleteWebhook", {"drop_pending_updates": True})
        time.sleep(2)
        
        print(f"💰 Reward: ₹{Config.REWARD_PER_REFERRAL}/referral")
        print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        print("✅ Private channel support enabled")
        print("✅ All users support enabled")
        print("=" * 50)
        print("🟢 Bot is running!")
        
        error_count = 0
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset)
                
                if updates is None:
                    error_count += 1
                    if error_count > 5:
                        print("🔄 Re-initializing...")
                        self.bot.api_request("deleteWebhook", {"drop_pending_updates": True})
                        error_count = 0
                        time.sleep(5)
                    else:
                        time.sleep(2)
                    continue
                
                error_count = 0
                
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
                                    self.handle_start(chat_id, user_id, username, first_name, last_name, args)
                                
                                elif text.startswith("/admin") and str(user_id) == Config.ADMIN_USER_ID:
                                    self.show_admin_panel(chat_id, msg["message_id"], user_id)
                                
                                else:
                                    self.handle_message(chat_id, user_id, text)
                        
                        elif "callback_query" in update:
                            cb = update["callback_query"]
                            chat_id = cb["message"]["chat"]["id"]
                            message_id = cb["message"]["message_id"]
                            user_id = cb["from"]["id"]
                            
                            self.handle_callback(chat_id, message_id, user_id, cb)
                    
                    except Exception as e:
                        print(f"❌ Error processing update: {e}")
                
                time.sleep(0.5)
            
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.running = False
            
            except Exception as e:
                print(f"❌ Error: {e}")
                error_count += 1
                if error_count > 10:
                    print("🔄 Too many errors, restarting...")
                    time.sleep(10)
                    self.offset = 0
                    error_count = 0
                else:
                    time.sleep(5)

# ==================== MAIN ====================
if __name__ == "__main__":
    print("🔥 Trade Genius Bot - Complete Fixed Version")
    print("=" * 50)
    
    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask server started")
    
    # Start bot
    bot = TradeGeniusBot()
    bot.run()