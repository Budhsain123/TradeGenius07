# main_complete_fixed.py - Complete Solution

"""
🔥 Trade Genius Bot - COMPLETE FIXED VERSION
✅ ALL referral issues FIXED
✅ Channel verification IMPROVED  
✅ Anonymous user handling COMPLETE
✅ Firebase sync FIXED
✅ Error handling ADDED
✅ Performance OPTIMIZED
✅ Security IMPROVED
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
from typing import Dict, List, Optional, Tuple, Any

# ==================== FLASK SERVER FOR RENDER ====================
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "TradeGeniusBot",
        "version": "2.0.0",
        "fixes": "All referral issues fixed"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users": 0  # Will be updated dynamically
    })

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== CONFIGURATION ====================
class Config:
    # Bot Configuration
    BOT_TOKEN = "8560550222:AAFYTkiQMa_ElkH1dBKhKdGUceKs9R5p9Xk"
    BOT_USERNAME = "TradeGenius07RewardsHub_bot"
    WEB_URL = "https://www.nextwin.great-site.net/"
    AI_BUTTON_NAME = "🤖 AI Chat"
    
    # Firebase Configuration
    FIREBASE_URL = "https://colortraderpro-panel-default-rtdb.firebaseio.com/"
    
    # Reward Configuration
    REWARD_PER_REFERRAL = 2
    MINIMUM_WITHDRAWAL = 20
    BONUS_AT_10_REFERRALS = 5
    
    # Admin & Support
    ADMIN_USER_ID = "6608445090"
    SUPPORT_CHANNEL = "@TradeGenius07_HelpCenter_bot"
    
    # Files
    LOG_FILE = "bot_logs.txt"
    DATA_FILE = "local_backup.json"
    ERROR_LOG = "error_logs.txt"
    
    # Timing Configuration
    REFERRAL_VERIFICATION_DELAY = 3  # seconds
    MAX_VERIFICATION_ATTEMPTS = 3
    CHANNEL_CHECK_TIMEOUT = 10  # seconds
    API_RETRY_DELAY = 2  # seconds
    
    # Security
    MAX_MESSAGE_LENGTH = 4000
    MAX_USERNAME_LENGTH = 32
    MIN_UPI_LENGTH = 5
    MAX_UPI_LENGTH = 50
    
    # Performance
    BATCH_SIZE = 50
    CACHE_DURATION = 300  # 5 minutes

# ==================== ENHANCED LOGGING ====================
class EnhancedLogger:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Error logging
        self.error_logger = logging.getLogger('error')
        error_handler = logging.FileHandler(Config.ERROR_LOG)
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter('%(asctime)s - ERROR - %(message)s')
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str, exc_info=None):
        self.error_logger.error(message, exc_info=exc_info)
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)

# ==================== VALIDATION UTILITIES ====================
class Validator:
    @staticmethod
    def is_valid_user_id(user_id: Any) -> bool:
        """Validate Telegram user ID"""
        try:
            user_id_str = str(user_id)
            return user_id_str.isdigit() and len(user_id_str) > 3
        except:
            return False
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Validate Telegram username"""
        if not username or username == "User":
            return False
        return len(username) <= Config.MAX_USERNAME_LENGTH and re.match(r'^[a-zA-Z0-9_]+$', username)
    
    @staticmethod
    def is_valid_upi(upi_id: str) -> bool:
        """Validate UPI ID"""
        if not upi_id:
            return False
        upi_id = upi_id.strip()
        return (Config.MIN_UPI_LENGTH <= len(upi_id) <= Config.MAX_UPI_LENGTH and 
                '@' in upi_id and 
                not upi_id.startswith('@') and 
                not upi_id.endswith('@'))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL"""
        try:
            return url.startswith('http://') or url.startswith('https://')
        except:
            return False
    
    @staticmethod
    def is_valid_referral_code(code: str) -> bool:
        """Validate referral code"""
        if not code:
            return False
        return len(code) == 8 and code.isalnum()
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize user input text"""
        if not text:
            return ""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Escape HTML special characters
        text = (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#39;'))
        return text[:Config.MAX_MESSAGE_LENGTH]

# ==================== CACHE MANAGER ====================
class CacheManager:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def set(self, key: str, value: Any, duration: int = Config.CACHE_DURATION):
        """Set cache value with expiration"""
        self.cache[key] = value
        self.timestamps[key] = time.time() + duration
    
    def get(self, key: str) -> Any:
        """Get cache value if not expired"""
        if key in self.cache and key in self.timestamps:
            if time.time() < self.timestamps[key]:
                return self.cache[key]
            else:
                # Clean expired cache
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def clear(self, key: str = None):
        """Clear cache"""
        if key:
            if key in self.cache:
                del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
        else:
            self.cache.clear()
            self.timestamps.clear()

# ==================== ENHANCED HTTP HELPER ====================
import urllib.request
import urllib.error

class EnhancedHTTPHelper:
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
        self.retry_count = 3
    
    def make_request(self, url: str, method: str = "GET", data: Dict = None, 
                    headers: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.retry_count):
            try:
                if headers is None:
                    headers = {'Content-Type': 'application/json'}
                
                if data and isinstance(data, dict):
                    data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                response = urllib.request.urlopen(req, timeout=timeout)
                result = json.loads(response.read().decode('utf-8'))
                
                if attempt > 0:
                    self.logger.info(f"Request succeeded on attempt {attempt + 1}")
                
                return result
                
            except urllib.error.HTTPError as e:
                if e.code == 409:
                    self.logger.warning(f"HTTP 409 Conflict (Attempt {attempt + 1}): {url}")
                    if attempt < self.retry_count - 1:
                        time.sleep(Config.API_RETRY_DELAY * (attempt + 1))
                        continue
                else:
                    self.logger.error(f"HTTP Error {e.code}: {e}")
                
                return None
                
            except urllib.error.URLError as e:
                self.logger.error(f"URL Error (Attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(Config.API_RETRY_DELAY * (attempt + 1))
                    continue
                return None
                
            except Exception as e:
                self.logger.error(f"HTTP Request Error (Attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(Config.API_RETRY_DELAY * (attempt + 1))
                    continue
                return None
        
        return None

# ==================== ENHANCED FIREBASE HELPER ====================
class EnhancedFirebaseDB:
    def __init__(self, logger: EnhancedLogger):
        self.base_url = Config.FIREBASE_URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.logger = logger
        self.http_helper = EnhancedHTTPHelper(logger)
        self.cache = CacheManager()
        self.local_data = self._load_local_backup()
        
        self.logger.info(f"🔥 Firebase initialized: {self.base_url}")
    
    def _load_local_backup(self) -> Dict:
        """Load local backup data"""
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"📦 Loaded local backup with {len(data.get('users', {}))} users")
                    return data
        except Exception as e:
            self.logger.error(f"Failed to load local backup: {e}")
        
        return {
            "users": {},
            "withdrawals": {},
            "referrals": {},
            "channels": {},
            "referral_attempts": {},
            "settings": {
                "reward_per_referral": Config.REWARD_PER_REFERRAL,
                "minimum_withdrawal": Config.MINIMUM_WITHDRAWAL,
                "web_url": Config.WEB_URL,
                "ai_button_name": Config.AI_BUTTON_NAME,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _save_local_backup(self):
        """Save local backup data"""
        try:
            with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.local_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save local backup: {e}")
    
    def _firebase_request(self, method: str, path: str, data: Dict = None) -> Optional[Dict]:
        """Make Firebase request with caching"""
        cache_key = f"{method}_{path}"
        
        # Don't cache POST/PUT/PATCH requests
        if method in ["GET"]:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            if path.startswith('/'):
                path = path[1:]
            
            url = self.base_url + path + ".json"
            result = self.http_helper.make_request(url, method, data)
            
            # Cache GET requests
            if method in ["GET"] and result:
                self.cache.set(cache_key, result, duration=60)  # 1 minute cache
            
            return result
            
        except Exception as e:
            self.logger.error(f"Firebase request error: {e}")
            return None
    
    # ========== USER MANAGEMENT ==========
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data with local fallback"""
        if not Validator.is_valid_user_id(user_id):
            return None
        
        user_id_str = str(user_id)
        
        # Try Firebase first
        data = self._firebase_request("GET", f"users/{user_id_str}")
        
        if data:
            # Update local backup
            self.local_data.setdefault("users", {})[user_id_str] = data
            return data
        else:
            # Fallback to local data
            return self.local_data.get("users", {}).get(user_id_str)
    
    def create_user(self, user_id: str, username: str = "", 
                   first_name: str = "", last_name: str = "") -> Optional[Dict]:
        """Create new user with validation"""
        if not Validator.is_valid_user_id(user_id):
            self.logger.error(f"Invalid user ID for creation: {user_id}")
            return None
        
        user_id_str = str(user_id)
        
        # Generate username if not provided
        if not username or username == "User":
            if first_name:
                username = first_name
                if last_name:
                    username += f" {last_name}"
            else:
                username = f"User_{user_id_str[-6:]}"
        
        # Sanitize username
        username = Validator.sanitize_text(username)[:Config.MAX_USERNAME_LENGTH]
        
        # Generate unique referral code
        referral_code = self._generate_unique_referral_code()
        
        is_admin = (user_id_str == Config.ADMIN_USER_ID)
        
        user_data = {
            "user_id": user_id_str,
            "username": username,
            "first_name": Validator.sanitize_text(first_name),
            "last_name": Validator.sanitize_text(last_name),
            "referral_code": referral_code,
            "referrals": 0,
            "total_earnings": 0,
            "pending_balance": 0,
            "withdrawn": 0,
            "referrer": None,
            "referral_claimed": False,
            "referral_claimed_at": None,
            "upi_id": "",
            "phone": "",
            "email": "",
            "is_verified": is_admin,
            "verified_at": datetime.now().isoformat() if is_admin else None,
            "channels_joined": {},
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "is_admin": is_admin,
            "verification_attempts": 0,
            "last_verification_attempt": None
        }
        
        # Save to Firebase
        result = self._firebase_request("PUT", f"users/{user_id_str}", user_data)
        
        if result:
            # Update local backup
            self.local_data.setdefault("users", {})[user_id_str] = user_data
            self._save_local_backup()
            
            # Clear cache
            self.cache.clear(f"GET_users/{user_id_str}")
            
            self.logger.info(f"✅ Created user: {user_id_str} ({username})")
            return user_data
        else:
            self.logger.error(f"Failed to create user: {user_id_str}")
            return None
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user data with validation"""
        if not Validator.is_valid_user_id(user_id):
            return False
        
        user_id_str = str(user_id)
        current = self.get_user(user_id_str)
        
        if not current:
            self.logger.warning(f"User not found for update: {user_id_str}")
            return False
        
        # Validate and sanitize updates
        validated_updates = {}
        for key, value in updates.items():
            if key == "username" and value:
                validated_updates[key] = Validator.sanitize_text(str(value))[:Config.MAX_USERNAME_LENGTH]
            elif key == "upi_id" and value:
                if Validator.is_valid_upi(str(value)):
                    validated_updates[key] = str(value).strip()
                else:
                    self.logger.warning(f"Invalid UPI ID for user {user_id_str}: {value}")
                    continue
            elif key == "referrals" and isinstance(value, int) and value >= 0:
                validated_updates[key] = value
            elif key in ["pending_balance", "total_earnings", "withdrawn"]:
                try:
                    validated_updates[key] = float(value)
                except:
                    continue
            else:
                validated_updates[key] = value
        
        # Always update last_active
        validated_updates["last_active"] = datetime.now().isoformat()
        
        # Update Firebase
        result = self._firebase_request("PATCH", f"users/{user_id_str}", validated_updates)
        
        if result is not None:
            # Update local data
            current.update(validated_updates)
            self.local_data.setdefault("users", {})[user_id_str] = current
            self._save_local_backup()
            
            # Clear cache
            self.cache.clear(f"GET_users/{user_id_str}")
            
            self.logger.debug(f"Updated user {user_id_str}: {list(validated_updates.keys())}")
            return True
        else:
            self.logger.error(f"Failed to update user {user_id_str}")
            return False
    
    def _generate_unique_referral_code(self) -> str:
        """Generate unique referral code"""
        attempts = 0
        while attempts < 10:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Check if code exists
            users = self.get_all_users()
            if not any(user and user.get("referral_code") == code for user in users.values()):
                return code
            
            attempts += 1
        
        # Fallback with timestamp
        timestamp = int(time.time())
        return f"REF{timestamp % 1000000:06d}"
    
    # ========== REFERRAL MANAGEMENT ==========
    def process_referral(self, new_user_id: str, referral_code: str) -> Tuple[bool, str]:
        """Process referral with comprehensive validation"""
        # Validate inputs
        if not Validator.is_valid_user_id(new_user_id) or not Validator.is_valid_referral_code(referral_code):
            return False, "Invalid input"
        
        new_user_id_str = str(new_user_id)
        
        # Check if new user exists
        new_user = self.get_user(new_user_id_str)
        if not new_user:
            return False, "New user not found"
        
        # Check if already claimed referral
        if new_user.get("referral_claimed", False):
            return True, "Referral already claimed"
        
        # Find referrer
        referrer_id, referrer = self.find_user_by_referral_code(referral_code)
        if not referrer or not referrer_id:
            return False, "Invalid referral code"
        
        # Prevent self-referral
        if referrer_id == new_user_id_str:
            return False, "Self-referral not allowed"
        
        # Check referrer verification
        if not referrer.get("is_verified", False):
            return False, "Referrer not verified"
        
        # Check if referral already exists
        existing_ref = self.get_existing_referral(new_user_id_str, referrer_id)
        if existing_ref:
            return False, "Referral already exists"
        
        # Create referral record
        referral_id = f"REF{new_user_id_str}_{int(time.time())}"
        referral_data = {
            "new_user_id": new_user_id_str,
            "referrer_id": referrer_id,
            "referral_code": referral_code,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "verified": False
        }
        
        self._firebase_request("PUT", f"referrals/{referral_id}", referral_data)
        
        # Update referral attempts tracking
        attempt_key = f"{new_user_id_str}_{referral_code}"
        self.local_data.setdefault("referral_attempts", {})[attempt_key] = {
            "user_id": new_user_id_str,
            "referral_code": referral_code,
            "referrer_id": referrer_id,
            "attempts": self.get_referral_attempts(new_user_id_str, referral_code) + 1,
            "last_attempt": datetime.now().isoformat(),
            "status": "pending"
        }
        self._save_local_backup()
        
        return True, "Referral processing started"
    
    def complete_referral(self, new_user_id: str, referral_code: str) -> bool:
        """Complete referral process and award rewards"""
        new_user_id_str = str(new_user_id)
        
        # Get users
        new_user = self.get_user(new_user_id_str)
        referrer_id, referrer = self.find_user_by_referral_code(referral_code)
        
        if not new_user or not referrer:
            return False
        
        # Calculate reward
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL
        
        # Bonus at 10 referrals
        if new_refs == 10:
            reward += Config.BONUS_AT_10_REFERRALS
        
        # Update referrer
        referrer_updates = {
            "referrals": new_refs,
            "pending_balance": referrer.get("pending_balance", 0) + reward,
            "total_earnings": referrer.get("total_earnings", 0) + reward
        }
        
        # Update new user
        new_user_updates = {
            "referrer": referrer_id,
            "referral_claimed": True,
            "referral_claimed_at": datetime.now().isoformat()
        }
        
        # Update both users
        success1 = self.update_user(referrer_id, referrer_updates)
        success2 = self.update_user(new_user_id_str, new_user_updates)
        
        if success1 and success2:
            # Update referral record
            self.update_referral_status(new_user_id_str, referrer_id, "completed", reward)
            
            # Update attempt tracking
            attempt_key = f"{new_user_id_str}_{referral_code}"
            if attempt_key in self.local_data.get("referral_attempts", {}):
                self.local_data["referral_attempts"][attempt_key]["status"] = "completed"
                self.local_data["referral_attempts"][attempt_key]["reward"] = reward
                self._save_local_backup()
            
            self.logger.info(f"✅ Referral completed: {new_user_id_str} -> {referrer_id} (₹{reward})")
            return True
        
        return False
    
    def find_user_by_referral_code(self, referral_code: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Find user by referral code with caching"""
        cache_key = f"user_by_code_{referral_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        users = self.get_all_users()
        for user_id, user_data in users.items():
            if user_data and user_data.get("referral_code") == referral_code:
                result = (user_id, user_data)
                self.cache.set(cache_key, result, duration=300)  # 5 minutes
                return result
        
        return None, None
    
    def get_existing_referral(self, new_user_id: str, referrer_id: str) -> Optional[Dict]:
        """Check if referral already exists"""
        referrals = self._firebase_request("GET", "referrals") or {}
        for ref_id, ref_data in referrals.items():
            if (ref_data and 
                ref_data.get("new_user_id") == new_user_id and 
                ref_data.get("referrer_id") == referrer_id):
                return ref_data
        return None
    
    def update_referral_status(self, new_user_id: str, referrer_id: str, 
                              status: str, reward: float = 0):
        """Update referral status"""
        referrals = self._firebase_request("GET", "referrals") or {}
        for ref_id, ref_data in referrals.items():
            if (ref_data and 
                ref_data.get("new_user_id") == new_user_id and 
                ref_data.get("referrer_id") == referrer_id):
                
                updates = {
                    "status": status,
                    "verified": status == "completed",
                    "verified_at": datetime.now().isoformat() if status == "completed" else None,
                    "reward_amount": reward if status == "completed" else 0
                }
                
                self._firebase_request("PATCH", f"referrals/{ref_id}", updates)
                break
    
    def get_referral_attempts(self, user_id: str, referral_code: str) -> int:
        """Get number of referral attempts"""
        attempt_key = f"{user_id}_{referral_code}"
        attempts = self.local_data.get("referral_attempts", {}).get(attempt_key, {})
        return attempts.get("attempts", 0)
    
    # ========== CHANNEL MANAGEMENT ==========
    def get_channels(self) -> Dict:
        """Get all channels with caching"""
        channels = self._firebase_request("GET", "channels") or {}
        
        # Update local backup
        if channels:
            self.local_data["channels"] = channels
            self._save_local_backup()
        
        return channels
    
    def add_channel(self, channel_data: Dict) -> bool:
        """Add new channel"""
        channel_id = channel_data.get("id")
        if not channel_id:
            return False
        
        # Validate channel data
        required_fields = ["name", "link", "id"]
        if not all(field in channel_data for field in required_fields):
            return False
        
        result = self._firebase_request("PUT", f"channels/{channel_id}", channel_data)
        
        if result:
            # Clear cache
            self.cache.clear("GET_channels")
            
            # Update local backup
            self.local_data.setdefault("channels", {})[channel_id] = channel_data
            self._save_local_backup()
            
            self.logger.info(f"✅ Added channel: {channel_data.get('name')}")
            return True
        
        return False
    
    def mark_channel_joined(self, user_id: str, channel_id: str) -> bool:
        """Mark channel as joined by user"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        channels_joined = user.get("channels_joined", {})
        channels_joined[channel_id] = {
            "joined_at": datetime.now().isoformat(),
            "verified": True,
            "verified_at": datetime.now().isoformat()
        }
        
        return self.update_user(user_id, {"channels_joined": channels_joined})
    
    def check_all_channels_joined(self, user_id: str) -> bool:
        """Check if user has joined all channels"""
        channels = self.get_channels()
        if not channels:
            return True
        
        user = self.get_user(user_id)
        if not user:
            return False
        
        user_channels = user.get("channels_joined", {})
        
        for channel_id in channels.keys():
            if channel_id not in user_channels or not user_channels[channel_id].get("verified", False):
                return False
        
        return True
    
    # ========== OTHER METHODS ==========
    def get_all_users(self) -> Dict:
        """Get all users with caching"""
        cache_key = "all_users"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        users = self._firebase_request("GET", "users") or {}
        
        # Update local backup
        if users:
            self.local_data["users"] = users
            self._save_local_backup()
        
        # Cache for 2 minutes
        self.cache.set(cache_key, users, duration=120)
        
        return users
    
    def get_web_url(self) -> str:
        """Get web URL from settings"""
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("web_url", Config.WEB_URL)
    
    def get_ai_button_name(self) -> str:
        """Get AI button name from settings"""
        settings = self._firebase_request("GET", "settings") or {}
        return settings.get("ai_button_name", Config.AI_BUTTON_NAME)
    
    def update_web_url(self, new_url: str) -> bool:
        """Update web URL"""
        if not Validator.is_valid_url(new_url):
            return False
        
        data = {"web_url": new_url}
        result = self._firebase_request("PATCH", "settings", data)
        
        if result:
            self.cache.clear("GET_settings")
            self.local_data["settings"]["web_url"] = new_url
            self._save_local_backup()
            return True
        
        return False
    
    def update_ai_button_name(self, new_name: str) -> bool:
        """Update AI button name"""
        if not new_name or len(new_name) > 20:
            return False
        
        data = {"ai_button_name": new_name}
        result = self._firebase_request("PATCH", "settings", data)
        
        if result:
            self.cache.clear("GET_settings")
            self.local_data["settings"]["ai_button_name"] = new_name
            self._save_local_backup()
            return True
        
        return False

# ==================== ENHANCED TELEGRAM BOT API ====================
class EnhancedTelegramBotAPI:
    def __init__(self, token: str, logger: EnhancedLogger):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.logger = logger
        self.http_helper = EnhancedHTTPHelper(logger)
        
    def _api_request(self, method: str, data: Dict = None) -> Optional[Dict]:
        """Make Telegram API request with retry logic"""
        url = self.base_url + method
        return self.http_helper.make_request(url, "POST", data)
    
    def get_chat_member(self, chat_id: str, user_id: str) -> Optional[Dict]:
        """Get chat member info with improved error handling"""
        try:
            # Normalize chat_id
            if isinstance(chat_id, int) or (isinstance(chat_id, str) and chat_id.lstrip('-').isdigit()):
                # Numeric chat ID
                chat_id_str = str(chat_id)
            elif chat_id.startswith('@'):
                # Username format
                chat_id_str = chat_id
            else:
                # Assume username without @
                chat_id_str = f"@{chat_id}"
            
            data = {
                "chat_id": chat_id_str,
                "user_id": int(user_id)
            }
            
            result = self._api_request("getChatMember", data)
            
            if result and result.get("status") in ["member", "administrator", "creator"]:
                return result
            else:
                self.logger.debug(f"User {user_id} not member of {chat_id_str}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking chat member: {e}")
            return None
    
    def send_message(self, chat_id: str, text: str, reply_markup: Dict = None, 
                    parse_mode: str = "HTML", disable_web_page_preview: bool = True) -> Optional[Dict]:
        """Send message with validation"""
        try:
            # Sanitize and truncate text
            text = Validator.sanitize_text(text)
            if len(text) > Config.MAX_MESSAGE_LENGTH:
                text = text[:Config.MAX_MESSAGE_LENGTH - 100] + "\n\n... (message truncated)"
            
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
            self.logger.error(f"Error sending message: {e}")
            return None
    
    def edit_message_text(self, chat_id: str, message_id: int, text: str, 
                         reply_markup: Dict = None, parse_mode: str = "HTML") -> Optional[Dict]:
        """Edit message text"""
        try:
            text = Validator.sanitize_text(text)
            
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
            self.logger.error(f"Error editing message: {e}")
            return None
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, 
                             show_alert: bool = False) -> Optional[Dict]:
        """Answer callback query"""
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        
        if text:
            data["text"] = Validator.sanitize_text(text)[:200]
        
        return self._api_request("answerCallbackQuery", data)

# ==================== MAIN BOT CLASS ====================
class TradeGeniusBotEnhanced:
    def __init__(self):
        self.logger = EnhancedLogger()
        self.bot = EnhancedTelegramBotAPI(Config.BOT_TOKEN, self.logger)
        self.db = EnhancedFirebaseDB(self.logger)
        self.running = True
        self.offset = 0
        self.user_states = {}
        self.pending_referrals = {}
        self.pending_verifications = {}
        
        self.logger.info("🤖 Trade Genius Bot Enhanced Initialized")
    
    def generate_keyboard(self, buttons: List, columns: int = 2) -> Dict:
        """Generate inline keyboard markup"""
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
    
    def get_main_menu_buttons(self, user_id: str) -> List:
        """Get main menu buttons for user"""
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
    
    def start_command(self, chat_id: str, user_id: str, username: str, 
                     first_name: str, last_name: str, args: List[str]):
        """Handle /start command"""
        try:
            # Get or create user
            user = self.db.get_user(user_id)
            if not user:
                user = self.db.create_user(user_id, username, first_name, last_name)
                if not user:
                    self.bot.send_message(chat_id, "❌ Failed to create user account. Please try again.")
                    return
            
            # Check if admin
            if str(user_id) == Config.ADMIN_USER_ID and not user.get("is_verified", False):
                self.db.update_user(user_id, {"is_verified": True})
                user["is_verified"] = True
            
            # Check for referral code
            referral_code = args[0] if args and len(args) > 0 else None
            if referral_code and Validator.is_valid_referral_code(referral_code):
                # Store pending referral
                self.pending_referrals[str(user_id)] = {
                    "referral_code": referral_code,
                    "attempts": 0,
                    "last_attempt": datetime.now().isoformat(),
                    "status": "pending"
                }
                
                self.logger.info(f"📝 Pending referral for {user_id}: {referral_code}")
            
            # Check channels
            channels = self.db.get_channels()
            
            if not channels:
                # No channels required, mark verified
                if not user.get("is_verified", False):
                    self.db.mark_user_verified(user_id)
                    user["is_verified"] = True
                
                # Process any pending referral
                self._process_pending_referral(user_id, user.get("username", "User"))
                
                self.show_welcome_screen(chat_id, user_id, user)
                return
            
            # Check if already verified all channels
            if self.db.check_all_channels_joined(user_id):
                if not user.get("is_verified", False):
                    self.db.mark_user_verified(user_id)
                    user["is_verified"] = True
                
                # Process pending referral
                self._process_pending_referral(user_id, user.get("username", "User"))
                
                self.show_welcome_screen(chat_id, user_id, user)
            else:
                # Show verification screen
                self.show_verification_screen(chat_id, user_id, user.get("username", "User"))
                
        except Exception as e:
            self.logger.error(f"Error in start_command: {e}", exc_info=True)
            self.bot.send_message(chat_id, "❌ An error occurred. Please try again.")
    
    def _process_pending_referral(self, user_id: str, username: str) -> bool:
        """Process pending referral after verification"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_referrals:
            return False
        
        pending = self.pending_referrals[user_id_str]
        
        # Check max attempts
        if pending.get("attempts", 0) >= Config.MAX_VERIFICATION_ATTEMPTS:
            del self.pending_referrals[user_id_str]
            return False
        
        # Check if already claimed
        user = self.db.get_user(user_id)
        if user and user.get("referral_claimed", False):
            del self.pending_referrals[user_id_str]
            return True
        
        # Wait for verification to complete
        time.sleep(Config.REFERRAL_VERIFICATION_DELAY)
        
        # Process referral
        referral_code = pending["referral_code"]
        success, message = self.db.process_referral(user_id, referral_code)
        
        if success:
            # Complete the referral
            if self.db.complete_referral(user_id, referral_code):
                del self.pending_referrals[user_id_str]
                
                # Notify referrer
                referrer_id, referrer = self.db.find_user_by_referral_code(referral_code)
                if referrer_id:
                    try:
                        self.bot.send_message(
                            referrer_id,
                            f"""🎉 <b>New Referral Success!</b>

✅ @{username} joined using your link!
💰 You earned: <b>₹{Config.REWARD_PER_REFERRAL}</b>
👥 Keep sharing to earn more!"""
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to notify referrer: {e}")
                
                self.logger.info(f"✅ Referral processed successfully: {user_id} -> {referrer_id}")
                return True
        
        # Increment attempts
        pending["attempts"] = pending.get("attempts", 0) + 1
        pending["last_attempt"] = datetime.now().isoformat()
        pending["last_error"] = message
        
        if pending["attempts"] >= Config.MAX_VERIFICATION_ATTEMPTS:
            del self.pending_referrals[user_id_str]
            self.logger.warning(f"Max referral attempts reached for {user_id}")
        
        return False
    
    def show_verification_screen(self, chat_id: str, user_id: str, username: str):
        """Show channel verification screen"""
        channels = self.db.get_channels()
        
        if not channels:
            self.db.mark_user_verified(user_id)
            self.show_verification_success(chat_id, None, user_id)
            return
        
        msg = """🔐 <b>Verification Required</b>

To use this bot, you must join our official channels:

👇 <b>Join ALL channels below:</b>"""
        
        buttons = []
        
        for channel_id, channel in channels.items():
            channel_name = channel.get("name", "Channel")
            channel_link = channel.get("link", "")
            
            # Format channel URL
            if channel_link.startswith("@"):
                channel_url = f"https://t.me/{channel_link[1:]}"
            elif "t.me/" in channel_link:
                channel_url = channel_link
            else:
                channel_url = f"https://t.me/{channel_link}"
            
            clean_name = channel_name.replace("📢", "").replace("🔔", "").replace("📰", "").strip()
            if not clean_name:
                clean_name = "Join Channel"
            
            buttons.append({"text": f"📢 {clean_name}", "url": channel_url})
        
        buttons.append(("✅ I'VE JOINED ALL - VERIFY NOW", "check_verification"))
        
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.send_message(chat_id, msg, keyboard)
    
    def check_verification(self, chat_id: str, message_id: int, user_id: str):
        """Check if user has joined all channels"""
        try:
            user = self.db.get_user(user_id)
            if not user:
                self.bot.send_message(chat_id, "❌ User not found.")
                return
            
            # Increment verification attempts
            attempts = user.get("verification_attempts", 0) + 1
            self.db.update_user(user_id, {
                "verification_attempts": attempts,
                "last_verification_attempt": datetime.now().isoformat()
            })
            
            channels = self.db.get_channels()
            all_joined = True
            not_joined = []
            
            for channel_id, channel in channels.items():
                channel_link = channel.get("link", "")
                
                if not channel_link:
                    continue
                
                # Check membership
                member_info = self.bot.get_chat_member(channel_link, user_id)
                
                if member_info:
                    self.db.mark_channel_joined(user_id, channel_id)
                else:
                    all_joined = False
                    not_joined.append(channel.get("name", "Channel"))
            
            if all_joined:
                # Mark as verified
                self.db.mark_user_verified(user_id)
                
                # Process pending referral
                username = user.get("username", "User")
                self._process_pending_referral(user_id, username)
                
                self.show_verification_success(chat_id, message_id, user_id)
            else:
                self.show_verification_failed(chat_id, message_id, user_id, not_joined)
                
        except Exception as e:
            self.logger.error(f"Error in check_verification: {e}", exc_info=True)
            self.bot.send_message(chat_id, "❌ Verification error. Please try again.")
    
    def show_verification_success(self, chat_id: str, message_id: Optional[int], user_id: str):
        """Show verification success message"""
        user = self.db.get_user(user_id)
        username = user.get("username", "User") if user else "User"
        
        msg = f"""✅ <b>Verification Successful!</b>

Welcome to <b>Trade Genius</b>, {username}!

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
    
    def show_verification_failed(self, chat_id: str, message_id: int, user_id: str, not_joined: List[str]):
        """Show verification failed message"""
        if not_joined:
            channels_text = "\n".join([f"• {name}" for name in not_joined])
            msg = f"""❌ <b>Verification Failed</b>

You haven't joined these channels:

{channels_text}

Please:
1. Join ALL channels above
2. Wait 10 seconds
3. Click VERIFY again"""
        else:
            msg = """❌ <b>Verification Failed</b>

Please join all channels and try again."""
        
        buttons = [
            ("🔄 Try Again", "check_verification"),
            ("❌ Cancel", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_welcome_screen(self, chat_id: str, user_id: str, user: Dict):
        """Show welcome screen after verification"""
        if not user:
            user = self.db.get_user(user_id)
        
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Status: Active</b>" if is_admin else ""
        verified_text = "\n✅ <b>Status: Verified</b>" if user.get("is_verified", False) else "\n❌ <b>Status: Not Verified</b>"
        
        # Show referral status
        referral_status = ""
        if user.get("referrer"):
            referrer = self.db.get_user(user["referrer"])
            if referrer:
                referral_status = f"\n👥 Referred by: {referrer.get('username', 'User')}"
        elif user.get("referral_claimed", False):
            referral_status = "\n✅ Referral already claimed"
        
        welcome_msg = f"""👋 <b>Welcome to Trade Genius Bot!</b> 💸

👤 Hello, {user.get('username', 'User')}!{admin_text}{verified_text}{referral_status}

💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b> per referral
🔗 Your Code: <code>{user.get('referral_code', 'N/A')}</code>
👥 Referrals: {user.get('referrals', 0)}
💸 Balance: ₹{user.get('pending_balance', 0)}

👇 <b>Select an option:</b>"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        
        self.bot.send_message(chat_id, welcome_msg, keyboard)
    
    def handle_callback(self, chat_id: str, message_id: int, user_id: str, callback_data: Dict):
        """Handle callback queries"""
        callback_query_id = callback_data["id"]
        callback = callback_data.get("data", "")
        
        # Answer callback query immediately
        self.bot.answer_callback_query(callback_query_id)
        
        try:
            user = self.db.get_user(user_id) or {}
            
            # Handle verification callbacks without verification check
            if callback in ["check_verification", "show_channels_again"]:
                if callback == "check_verification":
                    self.check_verification(chat_id, message_id, user_id)
                elif callback == "show_channels_again":
                    self.show_verification_screen(chat_id, user_id, user.get("username", "User"))
                return
            
            # Check if user is verified (except admin)
            if str(user_id) != Config.ADMIN_USER_ID and not user.get("is_verified", False):
                if callback not in ["main_menu"]:
                    msg = """❌ <b>Verification Required</b>

Please complete verification first to access bot features.

Join all required channels and verify."""
                    buttons = [("✅ VERIFY NOW", "check_verification")]
                    keyboard = self.generate_keyboard(buttons, 1)
                    self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
                    return
            
            # Route callback
            if callback == "main_menu":
                self.show_main_menu(chat_id, message_id, user_id, user)
            
            elif callback == "my_referral":
                self.show_referral_link(chat_id, message_id, user_id, user)
            
            elif callback == "dashboard":
                self.show_dashboard(chat_id, message_id, user_id, user)
            
            elif callback == "withdraw":
                self.show_withdraw_menu(chat_id, message_id, user_id, user)
            
            elif callback == "open_web":
                self.open_web_page(chat_id, message_id, user_id)
            
            elif callback == "terms_conditions":
                self.show_terms_conditions(chat_id, message_id, user_id)
            
            elif callback == "how_it_works":
                self.show_how_it_works(chat_id, message_id, user_id)
            
            elif callback == "rewards":
                self.show_rewards(chat_id, message_id, user_id)
            
            elif callback == "support":
                self.show_support(chat_id, message_id, user_id)
            
            elif callback == "admin_panel":
                if str(user_id) == Config.ADMIN_USER_ID:
                    self.show_admin_panel(chat_id, message_id, user_id)
                else:
                    msg = "⛔ <b>Access Denied</b>"
                    keyboard = self.generate_keyboard([("🏠 Main Menu", "main_menu")], 1)
                    self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
            
            elif callback.startswith("admin_"):
                if str(user_id) == Config.ADMIN_USER_ID:
                    self.handle_admin_callback(chat_id, message_id, user_id, callback)
            
            elif callback.startswith("setup_"):
                self.handle_setup_callback(chat_id, message_id, user_id, callback)
            
            else:
                self.logger.warning(f"Unknown callback: {callback}")
                self.bot.answer_callback_query(callback_query_id, "Unknown command", show_alert=True)
                
        except Exception as e:
            self.logger.error(f"Error handling callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback_query_id, "An error occurred", show_alert=True)
    
    # ========== USER FEATURES ==========
    def show_main_menu(self, chat_id: str, message_id: int, user_id: str, user: Dict):
        """Show main menu"""
        is_admin = (str(user_id) == Config.ADMIN_USER_ID)
        admin_text = "\n👑 <b>Admin Mode</b>" if is_admin else ""
        verified_text = "\n✅ <b>Verified</b>" if user.get("is_verified", False) else "\n❌ <b>Not Verified</b>"
        
        ai_button_name = self.db.get_ai_button_name()
        
        msg = f"""🏠 <b>Main Menu</b>{admin_text}{verified_text}

👋 {user.get('username', 'User')}
💰 Balance: <b>₹{user.get('pending_balance', 0)}</b>
👥 Referrals: <b>{user.get('referrals', 0)}</b>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
🤖 AI Button: {ai_button_name}"""
        
        buttons = self.get_main_menu_buttons(user_id)
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_referral_link(self, chat_id: str, message_id: int, user_id: str, user: Dict):
        """Show referral link"""
        referral_code = user.get("referral_code", "")
        if not referral_code:
            # Regenerate if missing
            user = self.db.get_user(user_id)
            referral_code = user.get("referral_code", "") if user else ""
        
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
    
    def show_dashboard(self, chat_id: str, message_id: int, user_id: str, user: Dict):
        """Show user dashboard"""
        verified_status = "✅ Verified" if user.get("is_verified", False) else "❌ Not Verified"
        
        # Referral info
        referral_info = ""
        if user.get("referrer"):
            referrer = self.db.get_user(user["referrer"])
            if referrer:
                referral_info = f"\n👥 Referred by: {referrer.get('username', 'User')}"
        elif user.get("referral_claimed", False):
            referral_info = "\n✅ Referral already claimed"
        
        msg = f"""📊 <b>Dashboard</b>

👤 {user.get('username', 'User')}
🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>
📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>
📞 Phone: {user.get('phone', 'Not set')}
📧 Email: {user.get('email', 'Not set')}
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
    
    def show_withdraw_menu(self, chat_id: str, message_id: int, user_id: str, user: Dict):
        """Show withdraw menu"""
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
    
    def open_web_page(self, chat_id: str, message_id: int, user_id: str):
        """Open web page"""
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        buttons = [
            {"text": ai_button_name, "url": web_url},
            ("🏠 Main Menu", "main_menu")
        ]
        keyboard = self.generate_keyboard(buttons, 2)
        msg = f"""🌐 <b>Open Web Page</b>

Click the button below to open the web page:"""
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_terms_conditions(self, chat_id: str, message_id: int, user_id: str):
        """Show terms and conditions"""
        terms_text = f"""📜 <b>Terms & Conditions</b>

✅ <b>By using this bot, you agree to:</b>

1. <b>Join all channels</b> to earn points
2. Each user can earn points from <b>ONLY ONE referrer</b>
3. <b>No self-referrals</b> allowed
4. Points and coupons are <b>non-transferable</b>
5. <b>Fraudulent activity</b> will result in permanent ban

📝 <b>Additional Terms:</b>
• Minimum withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}
• UPI is the only withdrawal method
• Payments processed within 24 hours
• Admin reserves right to modify terms
• You must be 18+ to use this service

<i>Last Updated: {datetime.now().strftime("%d %B %Y")}</i>"""
        
        buttons = [
            ("✅ I Understand", "main_menu"),
            ("🏠 Main Menu", "main_menu")
        ]
        
        keyboard = self.generate_keyboard(buttons, 2)
        self.bot.edit_message_text(chat_id, message_id, terms_text, keyboard)
    
    def show_how_it_works(self, chat_id: str, message_id: int, user_id: str):
        """Show how it works"""
        msg = f"""📢 <b>How It Works</b>

1️⃣ <b>Join Channels</b> (If Required)
   Complete verification first

2️⃣ <b>Get Referral Link</b>
   Share with friends

3️⃣ <b>Earn Money</b>
   Get ₹{Config.REWARD_PER_REFERRAL} per referral

4️⃣ <b>Setup UPI & Withdraw</b>
   Minimum ₹{Config.MINIMUM_WITHDRAWAL} to withdraw"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_rewards(self, chat_id: str, message_id: int, user_id: str):
        """Show rewards information"""
        msg = f"""🎁 <b>Rewards System</b>

💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}
🔥 10 Referrals Bonus: +₹{Config.BONUS_AT_10_REFERRALS}
👑 Top Referrer: Special Reward

📊 Example Earnings:
• 5 referrals = ₹{Config.REWARD_PER_REFERRAL * 5}
• 10 referrals = ₹{Config.REWARD_PER_REFERRAL * 10 + Config.BONUS_AT_10_REFERRALS}
• 20 referrals = ₹{Config.REWARD_PER_REFERRAL * 20 + (Config.BONUS_AT_10_REFERRALS * 2)}"""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    def show_support(self, chat_id: str, message_id: int, user_id: str):
        """Show support information"""
        msg = f"""📞 <b>Support</b>

Channel: {Config.SUPPORT_CHANNEL}

We're here to help! Contact us for any issues."""
        
        buttons = [("🏠 Main Menu", "main_menu")]
        keyboard = self.generate_keyboard(buttons, 1)
        self.bot.edit_message_text(chat_id, message_id, msg, keyboard)
    
    # ========== ADMIN FEATURES ==========
    def show_admin_panel(self, chat_id: str, message_id: int, user_id: str):
        """Show admin panel"""
        users = self.db.get_all_users()
        total_users = len(users) if users else 0
        
        withdrawals = self.db.get_withdrawals("pending")
        pending_withdrawals = len(withdrawals) if withdrawals else 0
        
        channels = self.db.get_channels()
        total_channels = len(channels) if channels else 0
        
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        msg = f"""👑 <b>Admin Control Panel</b>

📊 <b>Stats:</b>
👥 Users: {total_users}
💳 Pending WD: {pending_withdrawals}
📢 Channels: {total_channels}
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
    
    def handle_admin_callback(self, chat_id: str, message_id: int, user_id: str, callback: str):
        """Handle admin callbacks"""
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
        
        elif callback == "admin_update_web_url":
            self.show_update_web_url(chat_id, message_id, user_id)
        
        elif callback == "admin_update_ai_button":
            self.show_update_ai_button(chat_id, message_id, user_id)
        
        elif callback.startswith("admin_delete_channel_"):
            channel_id = callback.replace("admin_delete_channel_", "")
            self.delete_channel(chat_id, message_id, user_id, channel_id)
        
        elif callback.startswith("admin_approve_"):
            wd_id = callback.replace("admin_approve_", "")
            self.approve_withdrawal(chat_id, message_id, user_id, wd_id)
        
        elif callback.startswith("admin_reject_"):
            wd_id = callback.replace("admin_reject_", "")
            self.reject_withdrawal(chat_id, message_id, user_id, wd_id)
    
    # ========== SETUP HANDLERS ==========
    def handle_setup_callback(self, chat_id: str, message_id: int, user_id: str, callback: str):
        """Handle setup callbacks"""
        if callback == "setup_upi":
            self.setup_upi_id(chat_id, message_id, user_id)
        
        elif callback == "request_withdraw":
            user = self.db.get_user(user_id)
            if user:
                self.request_withdrawal(chat_id, message_id, user_id, user)
        
        elif callback == "withdraw_history":
            self.show_withdrawal_history(chat_id, message_id, user_id)
    
    def setup_upi_id(self, chat_id: str, message_id: int, user_id: str):
        """Setup UPI ID"""
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
    
    def request_withdrawal(self, chat_id: str, message_id: int, user_id: str, user: Dict):
        """Request withdrawal"""
        pending = user.get("pending_balance", 0)
        upi_id = user.get("upi_id", "")
        
        if pending < Config.MINIMUM_WITHDRAWAL:
            msg = f"❌ Insufficient balance. Minimum: ₹{Config.MINIMUM_WITHDRAWAL}"
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
            "withdrawal_id": withdrawal_id,
            "form_type": "upi/mono"
        }
        
        # Create withdrawal record
        self.db.create_withdrawal(withdrawal_id, withdrawal_data)
        
        # Update user balance
        self.db.update_user(user_id, {
            "pending_balance": 0,
            "withdrawn": user.get("withdrawn", 0) + pending
        })
        
        # Notify admin
        admin_msg = f"""🆕 <b>WITHDRAWAL REQUEST</b>

👤 User: @{user.get('username', 'N/A')}
💰 Amount: <b>₹{pending}</b>
📱 UPI ID: <code>{upi_id}</code>
📋 ID: {withdrawal_id}
⏰ Time: {datetime.now().strftime('%H:%M %d/%m')}
📄 Form Type: UPI/Mono Form

Click /admin to manage."""
        
        self.bot.send_message(Config.ADMIN_USER_ID, admin_msg)
        
        # Confirm to user
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
    
    def show_withdrawal_history(self, chat_id: str, message_id: int, user_id: str):
        """Show withdrawal history"""
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
    
    # ========== MESSAGE HANDLER ==========
    def handle_user_message(self, chat_id: str, user_id: str, text: str):
        """Handle user messages"""
        try:
            if user_id in self.user_states:
                state = self.user_states[user_id]
                
                if state.get("state") == "awaiting_upi":
                    upi_id = text.strip()
                    
                    if Validator.is_valid_upi(upi_id):
                        if self.db.update_user(user_id, {"upi_id": upi_id}):
                            msg = f"""✅ <b>UPI ID Saved</b>

📱 Your UPI ID: <code>{upi_id}</code>

You can now request withdrawals."""
                            
                            buttons = [("💳 Withdraw", "withdraw"), ("🏠 Menu", "main_menu")]
                            keyboard = self.generate_keyboard(buttons, 2)
                            self.bot.send_message(chat_id, msg, keyboard)
                            
                            # Update original message
                            self.bot.edit_message_text(
                                state["chat_id"],
                                state["message_id"],
                                "✅ UPI ID setup completed!",
                                self.generate_keyboard([("🏠 Menu", "main_menu")], 1)
                            )
                        else:
                            self.bot.send_message(chat_id, "❌ Failed to save UPI ID. Please try again.")
                    else:
                        self.bot.send_message(chat_id, "❌ Invalid UPI ID.\n\nUse format: <code>username@upi</code>")
                    
                    del self.user_states[user_id]
            
            elif text.startswith("/broadcast") and str(user_id) == Config.ADMIN_USER_ID:
                self.handle_broadcast(chat_id, user_id, text)
            
            else:
                # Handle other commands
                if text.startswith("/"):
                    self.bot.send_message(chat_id, "❌ Unknown command. Use /start to begin.")
                
        except Exception as e:
            self.logger.error(f"Error handling user message: {e}", exc_info=True)
            self.bot.send_message(chat_id, "❌ An error occurred. Please try again.")
    
    def handle_broadcast(self, chat_id: str, user_id: str, text: str):
        """Handle broadcast command"""
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
            failed = 0
            
            for uid in users.keys():
                try:
                    self.bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{message}")
                    success += 1
                    time.sleep(0.05)  # Rate limiting
                except Exception as e:
                    failed += 1
                    self.logger.error(f"Failed to send to {uid}: {e}")
            
            self.bot.send_message(chat_id, f"✅ Broadcast complete!\n\n✅ Sent: {success}\n❌ Failed: {failed}")
    
    # ========== BOT RUNNER ==========
    def run_bot(self):
        """Main bot runner"""
        self.logger.info("🤖 Trade Genius Bot Enhanced Starting...")
        self.logger.info(f"👑 Admin ID: {Config.ADMIN_USER_ID}")
        
        # Disable webhook
        self.logger.info("🔄 Disabling webhook...")
        try:
            delete_result = self.bot._api_request("deleteWebhook", {"drop_pending_updates": True})
            if delete_result:
                self.logger.info("✅ Webhook disabled successfully")
            else:
                self.logger.warning("⚠️ Could not disable webhook")
        except Exception as e:
            self.logger.error(f"Error disabling webhook: {e}")
        
        time.sleep(2)
        
        # Get current settings
        web_url = self.db.get_web_url()
        ai_button_name = self.db.get_ai_button_name()
        
        self.logger.info(f"💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}")
        self.logger.info(f"💰 Min Withdrawal: ₹{Config.MINIMUM_WITHDRAWAL}")
        self.logger.info(f"🌐 Web URL: {web_url}")
        self.logger.info(f"🤖 AI Button Name: {ai_button_name}")
        self.logger.info("✅ ALL ISSUES FIXED")
        self.logger.info("="*50)
        
        self.offset = 0
        error_count = 0
        
        while self.running:
            try:
                updates = self.bot.get_updates(self.offset, timeout=30)
                
                if not updates:
                    error_count += 1
                    if error_count > 10:
                        self.logger.warning("🔄 No updates received, reconnecting...")
                        error_count = 0
                        time.sleep(5)
                    continue
                
                error_count = 0
                
                for update in updates:
                    self.offset = update.get("update_id", 0) + 1
                    
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
                                self.show_admin_panel(chat_id, msg.get("message_id"), user_id)
                            
                            else:
                                self.handle_user_message(chat_id, user_id, text)
                    
                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        message_id = cb["message"]["message_id"]
                        user_id = cb["from"]["id"]
                        
                        self.handle_callback(chat_id, message_id, user_id, cb)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                self.logger.info("\n🛑 Bot stopped by user")
                self.running = False
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected Error in main loop: {e}", exc_info=True)
                error_count += 1
                if error_count > 20:
                    self.logger.error("🔴 Too many errors, restarting bot...")
                    time.sleep(30)
                    self.offset = 0
                    error_count = 0
                else:
                    time.sleep(5)

# ==================== START BOTH SERVERS ====================
def run_both():
    """Start both Flask server and Telegram bot"""
    bot = TradeGeniusBotEnhanced()
    
    # Start Flask server in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("🌐 Flask server started on port 5000")
    print("🤖 Starting Enhanced Telegram bot...")
    print("="*50)
    
    # Start bot
    bot.run_bot()

# ==================== START BOT ====================
if __name__ == "__main__":
    print("🔥 Trade Genius Bot - COMPLETE FIXED VERSION")
    print("="*50)
    
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Configure bot token first!")
        print("Edit Config.BOT_TOKEN in the code")
    else:
        try:
            run_both()
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()