# main.py - Complete Bot with Fixed Requirements
"""
🔥 Trade Genius Bot - Final Version
✅ Channel Verification Only for Users | ✅ Admin No Verification
✅ 20₹ Minimum Withdrawal | ✅ No Channels = No Verification
✅ 2₹ Per Referral | ✅ UPI Only Withdrawal
✅ Flask Server for Render | ✅ Terms & Conditions Button
"""

import os
import json
import logging
import hashlib
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
    """Run Flask server for Render hosting"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== CONFIGURATION ====================
class Config:
    # 🔧 YOUR BOT CREDENTIALS
    BOT_TOKEN = "8285080906:AAHEfKnYLeW_ygtgtqgzbbLfbaMJGRuSEgM"
    BOT_USERNAME = "TradeGenius07Pro_bot"
    
    # 🔥 FIREBASE CONFIGURATION
    FIREBASE_URL = "https://colortraderpro-panel-default-rtdb.firebaseio.com/"
    
    # Reward Settings - 2₹ PER REFERRAL
    REWARD_PER_REFERRAL = 2
    MINIMUM_WITHDRAWAL = 20  # Changed to 20₹
    BONUS_AT_10_REFERRALS = 5
    
    # 🔐 ADMIN SETTINGS
    ADMIN_USER_ID = "6608445090"  # Your Telegram ID
    SUPPORT_CHANNEL = "@TradeGenius07_HelpCenter_bot"
    
    # Bot Settings
    LOG_FILE = "bot_logs.txt"
    DATA_FILE = "local_backup.json"

# ==================== HTTP HELPER ====================
import urllib.request
import urllib.error

class HTTPHelper:
    @staticmethod
    def make_request(url, method="GET", data=None, headers=None, timeout=30):
        """Universal HTTP request method"""
        try:
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            if data and isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            response = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(response.read().decode('utf-8'))
            
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
                "minimum_withdrawal": Config.MINIMUM_WITHDRAWAL
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
    
    # User Management
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
            "is_verified": False,  # Default not verified
            "channels_joined": {},
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "is_admin": (user_id == Config.ADMIN_USER_ID)
        }
        
        # If user is admin, auto-verify
        if user_id == Config.ADMIN_USER_ID:
            user_data["is_verified"] = True
        
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
        """Mark user as verified"""
        return self.update_user(user_id, {"is_verified": True})
    
    def mark_channel_joined(self, user_id, channel_id):
        """Mark a channel as joined by user"""
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
        """Check if user has joined all required channels"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        channels = self.get_channels()
        if not channels:
            return True  # No channels required
        
        user_channels = user.get("channels_joined", {})
        
        for channel_id in channels.keys():
            if channel_id not in user_channels or not user_channels[channel_id].get("verified", False):
                return False
        
        return True
    
    # Channel Management
    def add_channel(self, channel_data):
        """Add a new channel for verification"""
        channel_id = channel_data.get("id")
        if not channel_id:
            return False
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        return result
    
    def get_channels(self):
        """Get all channels"""
        data = self._firebase_request("GET", "channels") or {}
        return data
    
    def delete_channel(self, channel_id):
        """Delete a channel"""
        result = self._firebase_request("DELETE", f"channels/{channel_id}")
        return result
    
    # Withdrawal Management
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
    
    # Other methods
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
        """Fixed API request method"""
        try:
            url = self.base_url + method
            
            if data:
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('result') if result.get('ok') else None
                
        except Exception as e:
            self.logger.error(f"API Error ({method}): {e}")
            return None
    
    def get_chat_member(self, chat_id, user_id):
        """Check if user is member of a channel"""
        data = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        return self._api_request("getChatMember", data)
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=True):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        return self._api_request("sendMessage", data)
    
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        return self._api_request("editMessageText", data)
    
    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        
        if text:
            data["text"] = text
        
        return self._api_request("answerCallbackQuery", data)
    
    def get_updates(self, offset=None, timeout=30):
        data = {"timeout": timeout}
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
            ("📜 Terms & Conditions", "terms_conditions"),  # NEW: Terms button
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support"),
        ]
        
        if is_admin:
            buttons.append(("👑 Admin Panel", "admin_panel"))
        
        return buttons
    
    # NEW: Terms & Conditions Function
    def show_terms_conditions(self, chat_id, message_id, user_id):
        """Show Terms & Conditions"""
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
        """Handle /start command"""
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username)
        
        # Check if admin - no verification needed
        if str(user_id) == Config.ADMIN_USER_ID:
            user["is_verified"] = True
            self.db.update_user(user_id, {"is_verified": True})
        
        # Check if user needs verification
        if not user.get("is_verified", False):
            channels = self.db.get_channels()
            
            if channels:
                # Show verification screen
                self.show_verification_screen(chat_id, user_id, username)
                return
            else:
                # No channels required, auto verify
                self.db.mark_user_verified(user_id)
                user["is_verified"] = True
        
        # User is verified, show welcome screen
        self.show_welcome_screen(chat_id, user_id, username, user, args)
    
    def show_verification_screen(self, chat_id, user_id, username):
    """Show channel verification screen ONLY if channels exist"""
    channels = self.db.get_channels()
    
    if not channels:
        # No channels, auto verify
        self.db.mark_user_verified(user_id)
        self.show_welcome_screen(chat_id, user_id, username, None, [])
        return
    
    # Debug: Print channels
    print(f"📢 Available channels: {channels}")
    
    msg = """🔐 <b>Channel Verification Required</b>

To use this bot and earn money, you must join our official channels first.

👇 <b>Join these channels:</b>\n"""
    
    buttons = []
    
    for channel_id, channel in channels.items():
        if not channel:
            continue
            
        channel_name = channel.get("name", "Channel")
        channel_link = channel.get("link", "")
        
        print(f"📢 Processing channel: {channel_name} | Link: {channel_link}")
        
        if not channel_link:
            continue
        
        # Fix channel link format
        if channel_link.startswith("@"):
            channel_url = f"https://t.me/{channel_link[1:]}"
        elif "t.me/" in channel_link:
            if not channel_link.startswith("https://"):
                channel_url = f"https://{channel_link}"
            else:
                channel_url = channel_link
        elif channel_link.startswith("https://t.me/"):
            channel_url = channel_link
        else:
            channel_url = f"https://t.me/{channel_link}"
        
        msg += f"\n📢 {channel_name}"
        buttons.append({"text": f"📢 {channel_name}", "url": channel_url})
    
    if not buttons:
        msg = """⚠️ <b>No Channels Available</b>

Currently, no verification channels are set up.
You can proceed directly to the bot."""
        
        self.db.mark_user_verified(user_id)
        self.show_welcome_screen(chat_id, user_id, username, None, [])
        return
    
    msg += "\n\n✅ After joining all channels, click <b>Verify Join</b>"
    
    buttons.append(("✅ Verify Join", "check_verification"))
    buttons.append(("🔄 Refresh", "refresh_verification"))
    
    keyboard = self.generate_keyboard(buttons, 2)
    self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id, message_id, user_id):
    """Check if user has joined all channels"""
    channels = self.db.get_channels()
    
    print(f"🔍 Checking verification for user {user_id}")
    print(f"📢 Total channels to check: {len(channels) if channels else 0}")
    
    if not channels:
        # No channels required, auto verify
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
        if not channel:
            continue
            
        channel_link = channel.get("link", "")
        channel_name = channel.get("name", "Channel")
        
        if not channel_link:
            continue
        
        print(f"🔍 Checking channel: {channel_name} ({channel_link})")
        
        try:
            # Fix channel link format for API
            if channel_link.startswith("https://t.me/"):
                chat_username = channel_link.replace("https://t.me/", "")
            elif channel_link.startswith("@"):
                chat_username = channel_link[1:]
            elif "t.me/" in channel_link:
                chat_username = channel_link.split("t.me/")[-1]
            else:
                chat_username = channel_link
            
            # Remove any query parameters
            chat_username = chat_username.split('?')[0]
            
            print(f"🔍 API Check: chat_id={chat_username}, user_id={user_id}")
            
            member_info = self.bot.get_chat_member(chat_username, user_id)
            
            if member_info:
                status = member_info.get("status", "")
                print(f"✅ Status: {status}")
                
                if status in ["member", "administrator", "creator"]:
                    self.db.mark_channel_joined(user_id, channel_id)
                    print(f"✅ User is member of {channel_name}")
                else:
                    all_joined = False
                    not_joined_channels.append(channel_name)
                    print(f"❌ User NOT member of {channel_name}")
            else:
                all_joined = False
                not_joined_channels.append(channel_name)
                print(f"❌ No member info for {channel_name}")
        
        except Exception as e:
            print(f"⚠️ Error checking channel {channel_name}: {e}")
            all_joined = False
            not_joined_channels.append(channel_name)
    
    print(f"📊 Verification result: {'PASS' if all_joined else 'FAIL'}")
    print(f"📋 Missing channels: {not_joined_channels}")
    
    if all_joined:
        self.db.mark_user_verified(user_id)
        self.show_verification_success(chat_id, message_id, user_id)
    else:
        self.show_verification_failed(chat_id, message_id, user_id, not_joined_channels)
    
    def show_verification_success(self, chat_id, message_id, user_id):
        """Show verification success"""
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
        """Show verification failed"""
        msg = """❌ <b>Verification Failed</b>

You haven't joined all required channels.

<b>Missing Channels:</b>\n"""
        
        for channel in missing_channels:
            msg += f"• {channel}\n"
        
        msg += "\n⚠️ Please join all channels and try again."
        
        channels = self.db.get_channels()
        buttons = []
        
        for channel_id, channel in channels.items():
            if channel.get("name") in missing_channels:
                channel_link = channel.get("link", "")
                if channel_link.startswith("@"):
                    channel_url = f"https://t.me/{channel_link[1:]}"
                else:
                    channel_url = channel_link
                
                buttons.append({"text": f"📢 {channel.get('name')}", "url": channel_url})
        
        buttons.append(("✅ Verify Again", "check_verification"))
        buttons.append(("🔄 Refresh", "refresh_verification"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_welcome_screen(self, chat_id, user_id, username, user, args):
        """Show welcome screen after verification"""
        if not user:
            user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username)
        
        # Process referral if provided - ONLY if user is verified
        if args and len(args) > 0 and user.get("is_verified", False):
            referral_code = args[0]
            
            if not user.get("referral_claimed", False):
                # Find referrer by code
                all_users = self.db.get_all_users()
                referrer_id = None
                
                for uid, user_data in all_users.items():
                    if user_data and user_data.get("referral_code") == referral_code:
                        referrer_id = uid
                        break
                
                if referrer_id and referrer_id != str(user_id):
                    # Update referrer stats
                    referrer = self.db.get_user(referrer_id)
                    if referrer and referrer.get("is_verified", False):
                        new_refs = referrer.get("referrals", 0) + 1
                        reward = Config.REWARD_PER_REFERRAL  # 2₹
                        
                        if new_refs == 10:
                            reward += Config.BONUS_AT_10_REFERRALS
                        
                        self.db.update_user(referrer_id, {
                            "referrals": new_refs,
                            "pending_balance": referrer.get("pending_balance", 0) + reward,
                            "total_earnings": referrer.get("total_earnings", 0) + reward
                        })
                        
                        # Notify referrer
                        self.bot.send_message(
                            referrer_id,
                            f"""🎉 <b>New Referral!</b>

✅ @{username} joined using your link!
💰 You earned: <b>₹{reward}</b>
👥 Total referrals: <b>{new_refs}</b>

Keep sharing to earn more!"""
                        )
                        
                        # Mark user as referred
                        self.db.update_user(user_id, {
                            "referrer": referrer_id,
                            "referral_claimed": True
                        })
        
        # Welcome message
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
        
        # Check admin access
        if callback == "admin_panel" and str(user_id) != Config.ADMIN_USER_ID:
            msg = "⛔ <b>Access Denied</b>"
            keyboard = self.generate_keyboard([("🏠 Main Menu", "main_menu")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
        # Admin has no verification check
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
            if callback not in ["check_verification", "refresh_verification"]:
                msg = "❌ <b>Verification Required</b>\n\nPlease complete verification first."
                keyboard = self.generate_keyboard([("✅ Verify", "check_verification")], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        # Handle Terms & Conditions callback
        if callback == "terms_conditions":
            self.show_terms_conditions(chat_id, message_id, user_id)
            return
        
        if callback == "check_verification":
            self.check_verification(chat_id, message_id, user_id)
        
        elif callback == "refresh_verification":
            self.show_verification_screen(chat_id, user_id, user.get("username", "User"))
        
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
            ("📜 Withdrawal History", "withdraw_history"),  # ✅ ADDED HERE
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
    
    elif pending >= Config.MINIMUM_WITHDRAWAL:
        msg = f"""💳 <b>Withdraw Funds</b>

💰 Available: <b>₹{pending}</b>
💰 Minimum: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>
📱 Your UPI: <code>{upi_id}</code>

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
            ("🔗 Get Link", "my_referral"),
            ("📜 Withdrawal History", "withdraw_history"),  # ✅ ADDED HERE
            ("📊 Dashboard", "dashboard"),
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
        admin_msg = f"""🆕 <b>WITHDRAWAL REQUEST</b>

👤 User: @{user.get('username', 'N/A')}
💰 Amount: <b>₹{pending}</b>
📱 UPI: <code>{upi_id}</code>
📋 ID: {withdrawal_id}
⏰ Time: {datetime.now().strftime('%H:%M %d/%m')}

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
        
        buttons = [("💳 Withdraw", "withdraw"), ("🏠 Main Menu", "main_menu")]
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
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
💳 Pending WD: {pending_withdrawals}
📢 Channels: {total_channels}

👇 <b>Select:</b>"""
        
        buttons = [
            ("📊 Statistics", "admin_stats"),
            ("💳 Withdrawals", "admin_withdrawals"),
            ("📢 Channels", "admin_channels"),
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
    
    def show_admin_stats(self, chat_id, message_id, user_id):
        """Show admin statistics"""
        users = self.db.get_all_users()
        
        total_users = len(users) if users else 0
        verified = sum(1 for u in users.values() if u and u.get("is_verified", False))
        total_earnings = sum(u.get("total_earnings", 0) for u in users.values() if u)
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
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
• Verification: {'Required' if total_channels > 0 else 'Not Required'}"""
        
        buttons = [("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdrawal_management(self, chat_id, message_id, user_id):
        """Show pending withdrawals for admin"""
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
                    msg += f"   📱 {upi_id}\n"
                    msg += f"   📅 {date}\n\n"
                    
                    buttons.append((f"✅ Approve {i}", f"admin_approve_{wd_id}"))
                    buttons.append((f"❌ Reject {i}", f"admin_reject_{wd_id}"))
            
            buttons.append(("🔄 Refresh", "admin_withdrawals"))
            buttons.append(("🔙 Back", "admin_panel"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_channel_management(self, chat_id, message_id, user_id):
        """Show channel management menu"""
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
    """Show add channel interface"""
    msg = """➕ <b>Add New Channel</b>

Send channel details in this format:

<b>Channel Name
Channel Username/Link</b>

<b>Examples:</b>
<code>Trade Genius Official
@TradeGenius07</code>

<code>Cryptocurrency News
https://t.me/CryptoNews</code>

<code>Tech Updates
TechUpdatesOfficial</code>

<b>Important:</b>
• Bot must be ADMIN in the channel
• Channel link should be public
• Users must join ALL channels to use bot"""
    
    self.user_states[user_id] = {
        "state": "awaiting_channel",
        "chat_id": chat_id,
        "message_id": message_id
    }
    
    buttons = [("❌ Cancel", "admin_channels")]
    keyboard = self.generate_keyboard(buttons, 1)
    self.bot.edit_message_text(chat_id, message_id, msg, keyboard)

def handle_user_message(self, chat_id, user_id, text):
    """Handle user text messages"""
    if user_id in self.user_states:
        state = self.user_states[user_id]
        
        elif state.get("state") == "awaiting_channel":
            lines = text.strip().split('\n')
            if len(lines) >= 2:
                channel_name = lines[0].strip()
                channel_link = lines[1].strip()
                
                # Generate channel ID
                channel_id = hashlib.md5(channel_link.encode()).hexdigest()[:10]
                
                channel_data = {
                    "name": channel_name,
                    "link": channel_link,
                    "id": channel_id,
                    "added_by": str(user_id),
                    "added_at": datetime.now().isoformat()
                }
                
                result = self.db.add_channel(channel_data)
                
                if result:
                    msg = f"""✅ <b>Channel Added Successfully!</b>

📢 <b>Channel Name:</b> {channel_name}
🔗 <b>Channel Link:</b> {channel_link}
🆔 <b>Channel ID:</b> {channel_id}

Users will now need to join this channel to use the bot."""
                else:
                    msg = "❌ Failed to add channel. Please try again."
            else:
                msg = "❌ Invalid format. Please send:\n\nChannel Name\nChannel Link"
            
            buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
            keyboard = self.generate_keyboard(buttons, 2)
            self.bot.send_message(chat_id, msg, keyboard)
            del self.user_states[user_id]
    
    def show_channel_list(self, chat_id, message_id, user_id):
    """Show list of channels"""
    channels = self.db.get_channels()
    
    if not channels:
        msg = "📢 <b>No Channels</b>\n\nNo channels added yet.\nUsers will NOT see verification screen."
        buttons = [("➕ Add Channel", "admin_add_channel"), ("🔙 Back", "admin_channels")]
    else:
        msg = "📢 <b>Current Channels</b>\n\nUsers must join ALL these channels:\n"
        buttons = []
        
        for i, (channel_id, channel) in enumerate(channels.items(), 1):
            if not channel:
                continue
                
            name = channel.get("name", "Unknown")
            link = channel.get("link", "No link")
            msg += f"{i}. <b>{name}</b>\n   🔗 {link}\n\n"
            
            buttons.append((f"❌ Delete {i}", f"admin_delete_channel_{channel_id}"))
        
        buttons.append(("➕ Add More", "admin_add_channel"))
        buttons.append(("🔙 Back", "admin_channels"))
    
    keyboard = self.generate_keyboard(buttons, 2)
    self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def delete_channel(self, chat_id, message_id, user_id, channel_id):
        """Delete a channel"""
        result = self.db.delete_channel(channel_id)
        
        if result is not None:
            msg = "✅ Channel deleted successfully."
        else:
            msg = "❌ Failed to delete channel."
        
        buttons = [("📢 View Channels", "admin_view_channels"), ("🔙 Back", "admin_channels")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def approve_withdrawal(self, chat_id, message_id, user_id, withdrawal_id):
        """Admin approves a withdrawal"""
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

Payment processed successfully!"""
            
            self.bot.send_message(wd_data["user_id"], user_msg)
            msg = f"✅ Withdrawal {withdrawal_id} approved."
        
        buttons = [("💳 Back to Withdrawals", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def reject_withdrawal(self, chat_id, message_id, user_id, withdrawal_id):
        """Admin rejects a withdrawal"""
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

Send rejection reason:"""
        
        buttons = [("❌ Cancel", "admin_withdrawals")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def process_rejection_reason(self, admin_id, reason):
        """Process rejection reason from admin"""
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

Amount returned to balance."""
        
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
        """Show user management interface"""
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
        """Show broadcast menu"""
        msg = """📢 <b>Broadcast Message</b>

Use /broadcast command:

<code>/broadcast Your message here</code>

Example:
<code>/broadcast New update available!</code>"""
        
        buttons = [("🔙 Back", "admin_panel")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def handle_info_callback(self, chat_id, message_id, user_id, callback):
        """Handle info callbacks"""
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
        """Handle user text messages"""
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
    
    def run_bot(self):
        """Run the Telegram bot"""
        print("🤖 Trade Genius Bot Started!")
        print(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        print(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
        print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        print("📱 Running on Render with Flask Server")
        print("="*50)
        
        self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset)
                
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
                
                time.sleep(0.3)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped")
                self.running = False
                
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

# ==================== START BOTH SERVERS ====================
def run_both():
    """Run both Flask server and Telegram bot"""
    bot = TradeGeniusBot()
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Flask server started on port 5000")
    print("🤖 Starting Telegram bot...")
    
    # Start Telegram bot in main thread
    bot.run_bot()

# ==================== START BOT ====================
if __name__ == "__main__":
    print("🔥 Trade Genius Bot Starting...")
    print(f"👑 Admin: {Config.ADMIN_USER_ID}")
    print(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
    print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
    print("✅ Added: Flask Server for Render")
    print("✅ Added: Terms & Conditions Button")
    print("="*50)
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure bot token first!")
    else:
        run_both()