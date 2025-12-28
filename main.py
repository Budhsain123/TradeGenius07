# main.py - Complete Bot with Flask Server and Terms & Conditions

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
from flask import Flask, request, jsonify  # Added Flask

# ==================== FLASK SERVER SETUP ====================
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

@app.route('/webhook', methods=['POST'])
def webhook():
    # Optional: Add webhook support
    return jsonify({"status": "webhook_received"})

def run_flask():
    """Run Flask server for Render"""
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
    ADMIN_USER_ID = "1882237415"  # Your Telegram ID
    SUPPORT_CHANNEL = "@TradeGenius07_HelpCenter_bot"
    
    # Bot Settings
    LOG_FILE = "bot_logs.txt"
    DATA_FILE = "local_backup.json"
    
    # Terms & Conditions
    TERMS_TEXT = """📜 <b>Terms & Conditions</b>

✅ <b>By using this bot, you agree to:</b>

1. <b>Join all channels</b> to earn points
2. Each user can earn points from <b>ONLY ONE referrer</b>
3. <b>No self-referrals</b> allowed
4. Points and coupons are <b>non-transferable</b>
5. <b>Fraudulent activity</b> will result in permanent ban
6. Admin reserves the right to modify terms
7. Minimum withdrawal amount: ₹20
8. Payments processed within 24 hours
9. UPI is the only withdrawal method

📝 <b>Important Notes:</b>
• We don't ask for passwords or OTPs
• Keep your UPI ID updated
• Report suspicious activity immediately
• Terms may change without notice

<i>Last Updated: {}</i>""".format(datetime.now().strftime("%d %B %Y"))

# ==================== HTTP HELPER ====================
import urllib.request
import urllib.error
import threading  # Added for multi-threading

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
            "is_admin": (user_id == Config.ADMIN_USER_ID),
            "agreed_to_terms": False  # New field for T&C
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
    
    def mark_terms_accepted(self, user_id):
        """Mark user as accepted terms"""
        return self.update_user(user_id, {"agreed_to_terms": True})
    
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
            ("📜 Terms & Conditions", "terms_conditions"),  # Added T&C button
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards", "rewards"),
            ("📞 Support", "support"),
        ]
        
        if is_admin:
            buttons.append(("👑 Admin Panel", "admin_panel"))
        
        return buttons
    
    def show_terms_conditions(self, chat_id, message_id, user_id):
        """Show Terms & Conditions"""
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, "User")
        
        terms_accepted = user.get("agreed_to_terms", False)
        
        msg = Config.TERMS_TEXT
        
        if not terms_accepted:
            msg += "\n\n⚠️ <b>You must accept terms to continue</b>"
            buttons = [
                ("✅ I Agree", "accept_terms"),
                ("❌ Cancel", "main_menu")
            ]
        else:
            buttons = [
                ("✅ Accepted", "show_acceptance"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def accept_terms(self, chat_id, message_id, user_id):
        """User accepts terms"""
        self.db.mark_terms_accepted(user_id)
        
        msg = """✅ <b>Terms Accepted</b>

Thank you for agreeing to our Terms & Conditions.

You can now use all features of Trade Genius Bot.

👇 <b>Get started:</b>"""
        
        buttons = [
            ("🔗 Get Referral Link", "my_referral"),
            ("📊 Dashboard", "dashboard"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_terms_acceptance(self, chat_id, message_id, user_id):
        """Show acceptance status"""
        user = self.db.get_user(user_id)
        accepted_date = user.get("agreed_to_terms", False)
        
        if accepted_date:
            msg = """✅ <b>Terms Accepted</b>

You have already accepted our Terms & Conditions.

You can review them anytime from the main menu."""
        else:
            msg = """❌ <b>Terms Not Accepted</b>

You must accept Terms & Conditions to use this bot.

Please review and accept them from the main menu."""
        
        buttons = [("📜 View Terms", "terms_conditions"), ("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def start_command(self, chat_id, user_id, username, args):
        """Handle /start command"""
        user = self.db.get_user(user_id)
        
        if not user:
            user = self.db.create_user(user_id, username)
        
        # Check if admin - no verification needed
        if str(user_id) == Config.ADMIN_USER_ID:
            user["is_verified"] = True
            self.db.update_user(user_id, {"is_verified": True})
        
        # Check terms acceptance for non-admin users
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("agreed_to_terms", False):
            self.show_terms_welcome(chat_id, user_id, username)
            return
        
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
    
    def show_terms_welcome(self, chat_id, user_id, username):
        """Show welcome screen with terms first"""
        msg = f"""👋 <b>Welcome to Trade Genius Bot!</b> 💸

👤 Hello, @{username}!

📜 <b>Before you start,</b> please read and accept our Terms & Conditions.

This is required to ensure fair usage for all users."""

        buttons = [
            ("📜 Read Terms", "terms_conditions"),
            ("❌ Skip for Now", "skip_terms")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def skip_terms(self, chat_id, message_id, user_id):
        """Handle terms skipping"""
        msg = """⚠️ <b>Limited Access</b>

You can browse but <b>cannot earn or withdraw</b> without accepting Terms & Conditions.

Accept terms to unlock full features."""
        
        buttons = [
            ("📜 Accept Terms", "terms_conditions"),
            ("👀 Browse Features", "main_menu_limited")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_main_menu_limited(self, chat_id, message_id, user_id):
        """Show limited menu for users who haven't accepted terms"""
        msg = """🏠 <b>Main Menu (Limited Access)</b>

⚠️ <b>Accept Terms to unlock:</b>
• Earn money from referrals
• Withdraw funds
• Full dashboard access

📜 <b>Available Features:</b>"""
        
        buttons = [
            ("📜 Terms & Conditions", "terms_conditions"),
            ("📢 How It Works", "how_it_works"),
            ("🎁 Rewards Info", "rewards"),
            ("📞 Support", "support")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_verification_screen(self, chat_id, user_id, username):
        """Show channel verification screen ONLY if channels exist"""
        channels = self.db.get_channels()
        
        if not channels:
            # No channels, auto verify
            self.db.mark_user_verified(user_id)
            self.show_welcome_screen(chat_id, user_id, username, None, [])
            return
        
        msg = """🔐 <b>Channel Verification Required</b>

To use this bot and earn money, you must join our official channels first.

👇 <b>Join these channels:</b>\n"""
        
        buttons = []
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            channel_link = channel.get("link", "")
            
            if channel_link.startswith("@"):
                channel_url = f"https://t.me/{channel_link[1:]}"
            elif "t.me/" in channel_link:
                channel_url = channel_link
            else:
                channel_url = f"https://t.me/{channel_link}"
            
            msg += f"\n📢 {channel_name}"
            buttons.append({"text": f"📢 {channel_name}", "url": channel_url})
        
        msg += "\n\n✅ After joining all channels, click <b>Verify Join</b>"
        
        buttons.append(("✅ Verify Join", "check_verification"))
        buttons.append(("🔄 Refresh", "refresh_verification"))
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id, message_id, user_id):
        """Check if user has joined all channels"""
        channels = self.db.get_channels()
        
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
            channel_link = channel.get("link", "")
            
            if not channel_link:
                continue
            
            try:
                member_info = self.bot.get_chat_member(channel_link, user_id)
                
                if member_info and member_info.get("status") in ["member", "administrator", "creator"]:
                    self.db.mark_channel_joined(user_id, channel_id)
                else:
                    all_joined = False
                    not_joined_channels.append(channel.get("name", "Channel"))
            
            except Exception as e:
                print(f"⚠️ Error checking channel: {e}")
                all_joined = False
                not_joined_channels.append(channel.get("name", "Channel"))
        
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
        
        # Check terms acceptance
        if not user.get("agreed_to_terms", False) and str(user_id) != Config.ADMIN_USER_ID:
            self.show_terms_welcome(chat_id, user_id, username)
            return
        
        # Process referral if provided - ONLY if user is verified and accepted terms
        if args and len(args) > 0 and user.get("is_verified", False) and user.get("agreed_to_terms", False):
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
                    if referrer and referrer.get("is_verified", False) and referrer.get("agreed_to_terms", False):
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
        terms_text = "\n📜 <b>Terms: Accepted</b>" if user.get("agreed_to_terms", False) else "\n⚠️ <b>Terms: Not Accepted</b>"
        
        welcome_msg = f"""👋 <b>Welcome to Trade Genius Bot!</b> 💸

👤 Hello, @{username}!{admin_text}{verified_text}{terms_text}

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
        
        # Handle terms-related callbacks
        if callback in ["terms_conditions", "accept_terms", "show_acceptance", "skip_terms", "main_menu_limited"]:
            if callback == "terms_conditions":
                self.show_terms_conditions(chat_id, message_id, user_id)
            elif callback == "accept_terms":
                self.accept_terms(chat_id, message_id, user_id)
            elif callback == "show_acceptance":
                self.show_terms_acceptance(chat_id, message_id, user_id)
            elif callback == "skip_terms":
                self.skip_terms(chat_id, message_id, user_id)
            elif callback == "main_menu_limited":
                self.show_main_menu_limited(chat_id, message_id, user_id)
            return
        
        # Check terms for non-admin users
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("agreed_to_terms", False):
            if callback not in ["check_verification", "refresh_verification", "terms_conditions", "accept_terms"]:
                msg = "📜 <b>Terms & Conditions Required</b>\n\nPlease accept Terms & Conditions first to use this feature."
                keyboard = self.generate_keyboard([("📜 Accept Terms", "terms_conditions")], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                return
        
        # Admin has no verification check
        if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
            if callback not in ["check_verification", "refresh_verification"]:
                msg = "❌ <b>Verification Required</b>\n\nPlease complete verification first."
                keyboard = self.generate_keyboard([("✅ Verify", "check_verification")], 1)
                self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
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
        terms_status = "✅ Accepted" if user.get("agreed_to_terms", False) else "❌ Not Accepted"
        
        msg = f"""📊 <b>Dashboard</b>

👤 @{user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
🔄 Status: <b>{verified_status}</b>
📜 Terms: <b>{terms_status}</b>

📈 <b>Statistics:</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
💰 Pending: <b>₹{user.get('pending_balance', 0)}</b>
💸 Total Earned: <b>₹{user.get('total_earnings', 0)}</b>
✅ Withdrawn: <b>₹{user.get('withdrawn', 0)}</b>"""
        
        buttons = [
            ("💳 Withdraw", "withdraw"),
            ("🔗 Get Link", "my_referral"),
            ("📜 Terms", "terms_conditions"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_withdraw_menu(self, chat_id, message_id, user_id, user):
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if not user.get("agreed_to_terms", False):
            msg = """❌ <b>Terms Not Accepted</b>

You must accept Terms & Conditions before withdrawing.

Please review and accept the terms first."""
            
            buttons = [
                ("📜 Accept Terms", "terms_conditions"),
                ("🏠 Main Menu", "main_menu")
            ]
        
        elif not upi_id:
            msg = f"""❌ <b>UPI ID Required</b>

You need to set up your UPI ID first.
UPI ID format: <code>username@upi</code>

Current balance: <b>₹{pending}</b>
Minimum withdrawal: <b>₹{Config.MINIMUM_WITHDRAWAL}</b>"""
            
            buttons = [
                ("📱 Setup UPI ID", "setup_upi"),
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
        if not user.get("agreed_to_terms", False):
            msg = "❌ You must accept Terms & Conditions first."
            keyboard = self.generate_keyboard([("📜 Accept Terms", "terms_conditions")], 1)
            self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            return
        
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
        terms_text = "\n📜 <b>Terms Accepted</b>" if user.get("agreed_to_terms", False) else "\n⚠️ <b>Terms Not Accepted</b>"
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}{verified_text}{terms_text}

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
        
        # Count users who accepted terms
        accepted_terms = sum(1 for u in users.values() if u and u.get("agreed_to_terms", False))
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
📜 Terms Accepted: {accepted_terms}/{total_users}
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
        users = self.db.get_all_users()
        
        total_users = len(users) if users else 0
        verified = sum(1 for u in users.values() if u and u.get("is_verified", False))
        accepted_terms = sum(1 for u in users.values() if u and u.get("agreed_to_terms", False))
        total_earnings = sum(u.get("total_earnings", 0) for u in users.values() if u)
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        msg = f"""📊 <b>Admin Statistics</b>

👥 <b>Users:</b>
• Total: {total_users}
• Verified: {verified}
• Accepted Terms: {accepted_terms}
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
    
    def handle_info_callback(self, chat_id, message_id, user_id, callback):
        if callback == "how_it_works":
            msg = f"""📢 <b>How It Works</b>

1️⃣ <b>Accept Terms & Conditions</b>
   Must agree to continue

2️⃣ <b>Join Channels</b> (If Required)
   Complete verification first

3️⃣ <b>Get Referral Link</b>
   Share with friends

4️⃣ <b>Earn Money</b>
   Get ₹{Config.REWARD_PER_REFERRAL} per referral

5️⃣ <b>Setup UPI & Withdraw</b>
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
Admin: @AdminUsername

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
    
    # ... (rest of the methods remain the same as before)

    def run_bot(self):
        """Run the Telegram bot (separate thread)"""
        print("🤖 Trade Genius Bot Started!")
        print(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        print(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
        print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        print("📱 Running with Flask Server")
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
    
    # Start Telegram bot in main thread
    bot.run_bot()

if __name__ == "__main__":
    print("🔥 Trade Genius Bot Starting...")
    print(f"👑 Admin: {Config.ADMIN_USER_ID}")
    print(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
    print(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Configure bot token first!")
    else:
        run_both()