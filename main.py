# main.py - Optimized Trade Genius Bot

import os, json, logging, time, random, string, threading, urllib.request, urllib.error
from datetime import datetime
from urllib.parse import quote
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home(): return jsonify({"status": "online", "bot": "TradeGeniusBot"})

@app.route('/health')
def health(): return jsonify({"status": "healthy"})

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False)

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

class HTTPHelper:
    @staticmethod
    def request(url, method="GET", data=None, timeout=30):
        try:
            headers = {'Content-Type': 'application/json'}
            if data and isinstance(data, dict): data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code != 409: print(f"HTTP Error {e.code}: {e}")
            return None
        except Exception as e:
            print(f"HTTP Error: {e}")
            return None

class FirebaseDB:
    def __init__(self):
        self.base_url = Config.FIREBASE_URL.rstrip('/') + '/'
        self.local = self._load_backup()
    
    def _load_backup(self):
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
        return {"users": {}, "withdrawals": {}, "referrals": {}, "channels": {}, 
                "settings": {"reward_per_referral": Config.REWARD_PER_REFERRAL, "minimum_withdrawal": Config.MINIMUM_WITHDRAWAL, 
                            "web_url": Config.WEB_URL, "ai_button_name": Config.AI_BUTTON_NAME}}
    
    def _save(self):
        try:
            with open(Config.DATA_FILE, 'w', encoding='utf-8') as f: json.dump(self.local, f, indent=2, ensure_ascii=False)
        except: pass
    
    def _req(self, method, path, data=None):
        try: return HTTPHelper.request(self.base_url + path.lstrip('/') + ".json", method, data)
        except: return None
    
    def get_setting(self, key, default=None):
        settings = self._req("GET", "settings") or {}
        return settings.get(key, default)
    
    def set_setting(self, key, value):
        result = self._req("PATCH", "settings", {key: value})
        if result: self.local.setdefault("settings", {})[key] = value; self._save()
        return result
    
    def get_user(self, uid):
        uid = str(uid)
        return self._req("GET", f"users/{uid}") or self.local.get('users', {}).get(uid)
    
    def create_user(self, uid, username="", first_name="", last_name=""):
        uid = str(uid)
        if not username: username = f"{first_name} {last_name}".strip() or f"User_{uid[-6:]}"
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        is_admin = uid == Config.ADMIN_USER_ID
        data = {"user_id": uid, "username": username, "first_name": first_name or "", "last_name": last_name or "",
                "referral_code": code, "referrals": 0, "total_earnings": 0, "pending_balance": 0, "withdrawn": 0,
                "referrer": None, "referral_claimed": False, "upi_id": "", "is_verified": is_admin,
                "channels_joined": {}, "created_at": datetime.now().isoformat(), "is_admin": is_admin}
        self._req("PUT", f"users/{uid}", data)
        self.local.setdefault("users", {})[uid] = data; self._save()
        return data
    
    def update_user(self, uid, updates):
        uid = str(uid)
        current = self.get_user(uid)
        if not current: return False
        current.update(updates); current["last_active"] = datetime.now().isoformat()
        self._req("PATCH", f"users/{uid}", updates)
        self.local.setdefault("users", {})[uid] = current; self._save()
        return True
    
    def find_by_code(self, code):
        users = self._req("GET", "users") or {}
        for uid, data in users.items():
            if data and data.get("referral_code") == code: return uid, data
        return None, None
    
    def add_channel(self, data):
        cid = data.get("id")
        if not cid: return False
        result = self._req("PUT", f"channels/{cid}", data)
        if result is not None: self.local.setdefault("channels", {})[cid] = data; self._save()
        return result
    
    def get_channels(self): return self._req("GET", "channels") or {}
    def delete_channel(self, cid):
        result = self._req("DELETE", f"channels/{cid}")
        if result is not None and cid in self.local.get("channels", {}): del self.local["channels"][cid]; self._save()
        return result
    
    def create_withdrawal(self, wid, data): return self._req("PUT", f"withdrawals/{wid}", data)
    def get_withdrawals(self, status=None):
        wds = self._req("GET", "withdrawals") or {}
        return {k: v for k, v in wds.items() if v and (not status or v.get("status") == status)} if status else wds
    
    def update_withdrawal(self, wid, status, note=""):
        return self._req("PATCH", f"withdrawals/{wid}", {"status": status, "processed_at": datetime.now().isoformat(), "admin_note": note})
    
    def get_all_users(self): return self._req("GET", "users") or {}

class TelegramBot:
    def __init__(self, token):
        self.base = f"https://api.telegram.org/bot{token}/"
        self.db = FirebaseDB()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    def api(self, method, data=None):
        try:
            if data: data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(self.base + method, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            result = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
            return result.get('result') if result.get('ok') else None
        except: return None
    
    def get_member(self, chat_id, user_id):
        result = self.api("getChatMember", {"chat_id": chat_id, "user_id": user_id})
        if not result and str(chat_id).startswith("@"):
            result = self.api("getChatMember", {"chat_id": chat_id[1:], "user_id": user_id})
        return result
    
    def send(self, chat_id, text, kb=None, parse="HTML"):
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse, "disable_web_page_preview": True}
        if kb: data["reply_markup"] = kb
        return self.api("sendMessage", data)
    
    def edit(self, chat_id, msg_id, text, kb=None, parse="HTML"):
        data = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": parse}
        if kb: data["reply_markup"] = kb
        return self.api("editMessageText", data)
    
    def answer(self, cb_id, text=None, alert=False):
        return self.api("answerCallbackQuery", {"callback_query_id": cb_id, "text": text, "show_alert": alert})
    
    def updates(self, offset=None):
        data = {"timeout": 60, "allowed_updates": ["message", "callback_query"]}
        if offset: data["offset"] = offset
        return self.api("getUpdates", data) or []

class TradeGeniusBot:
    def __init__(self):
        self.bot = TelegramBot(Config.BOT_TOKEN)
        self.db = self.bot.db
        self.running = True
        self.offset = 0
        self.states = {}
        self.pending_refs = {}
    
    def kb(self, buttons, cols=2):
        keyboard, row = [], []
        for i, btn in enumerate(buttons):
            if isinstance(btn, tuple): row.append({"text": btn[0], "callback_data": btn[1]})
            elif isinstance(btn, dict): row.append(btn)
            if len(row) == cols or i == len(buttons) - 1: keyboard.append(row); row = []
        return {"inline_keyboard": keyboard}
    
    def menu_btns(self, uid):
        btns = [("🔗 Get Referral Link", "my_referral"), ("📊 My Dashboard", "dashboard"), ("💳 Withdraw", "withdraw"),
                (self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME), "open_web"),
                ("📜 Terms & Conditions", "terms"), ("📢 How It Works", "how"), ("🎁 Rewards", "rewards"), ("📞 Support", "support")]
        if str(uid) == Config.ADMIN_USER_ID: btns.append(("👑 Admin Panel", "admin"))
        return btns
    
    def check_channels(self, uid):
        channels = self.db.get_channels()
        if not channels: return True
        for cid, ch in channels.items():
            chat_id = ch.get("chat_id") or ch.get("username")
            if not chat_id: continue
            # For private channels with chat_id
            if ch.get("is_private") and ch.get("chat_id"):
                chat_id = ch.get("chat_id")
            elif ch.get("username"):
                chat_id = "@" + ch["username"] if not ch["username"].startswith("@") else ch["username"]
            else:
                continue
            try:
                member = self.bot.get_member(chat_id, uid)
                if not member or member.get("status") not in ["member", "administrator", "creator"]: return False
                self.db.update_user(uid, {"channels_joined": {cid: {"verified": True, "at": datetime.now().isoformat()}}})
            except: return False
        return True
    
    def process_referral(self, uid, username, code):
        user = self.db.get_user(uid)
        if not user or user.get("referral_claimed"): return True
        ref_id, referrer = self.db.find_by_code(code)
        if not referrer or ref_id == str(uid) or not referrer.get("is_verified"): return False
        new_refs = referrer.get("referrals", 0) + 1
        reward = Config.REWARD_PER_REFERRAL + (Config.BONUS_AT_10_REFERRALS if new_refs == 10 else 0)
        self.db.update_user(ref_id, {"referrals": new_refs, "pending_balance": referrer.get("pending_balance", 0) + reward,
                                     "total_earnings": referrer.get("total_earnings", 0) + reward})
        self.db.update_user(uid, {"referrer": ref_id, "referral_claimed": True})
        self.bot.send(ref_id, f"🎉 <b>New Referral!</b>\n\n✅ @{username} joined!\n💰 Earned: <b>₹{reward}</b>\n👥 Total: <b>{new_refs}</b>")
        return True
    
    def start(self, chat_id, uid, username, fname, lname, args):
        user = self.db.get_user(uid) or self.db.create_user(uid, username, fname, lname)
        is_admin = str(uid) == Config.ADMIN_USER_ID
        if is_admin and not user.get("is_verified"): self.db.update_user(uid, {"is_verified": True}); user["is_verified"] = True
        
        ref_code = args[0] if args else None
        if ref_code: self.pending_refs[str(uid)] = ref_code
        
        channels = self.db.get_channels()
        if not channels or is_admin or self.check_channels(uid):
            if not user.get("is_verified"): self.db.update_user(uid, {"is_verified": True}); user["is_verified"] = True
            if str(uid) in self.pending_refs: self.process_referral(uid, username, self.pending_refs.pop(str(uid)))
            self.welcome(chat_id, uid, user)
        else:
            self.verify_screen(chat_id, uid)
    
    def verify_screen(self, chat_id, uid):
        channels = self.db.get_channels()
        if not channels: self.db.update_user(uid, {"is_verified": True}); self.welcome(chat_id, uid, self.db.get_user(uid)); return
        btns = []
        for cid, ch in channels.items():
            name = ch.get("name", "Channel")
            link = ch.get("link") or (f"https://t.me/{ch['username']}" if ch.get("username") else "")
            if link: btns.append({"text": f"📢 {name}", "url": link})
        btns.append(("✅ VERIFY NOW", "verify"))
        self.bot.send(chat_id, "🔐 <b>Join channels to continue</b>\n\nJoin ALL channels:", self.kb(btns, 1))
    
    def verify(self, chat_id, msg_id, uid):
        user = self.db.get_user(uid)
        if self.check_channels(uid):
            self.db.update_user(uid, {"is_verified": True})
            if str(uid) in self.pending_refs: self.process_referral(uid, user.get("username", "User"), self.pending_refs.pop(str(uid)))
            self.bot.edit(chat_id, msg_id, "✅ <b>Verified!</b>\n\nWelcome! Start earning now.", self.kb([("🔗 Referral", "my_referral"), ("📊 Dashboard", "dashboard"), ("🏠 Menu", "menu")]))
        else:
            self.bot.edit(chat_id, msg_id, "❌ <b>Failed</b>\n\nJoin ALL channels, wait 10s, try again.", self.kb([("🔄 Retry", "verify"), ("📋 Channels", "channels")]))
    
    def welcome(self, chat_id, uid, user):
        if not user: user = self.db.get_user(uid)
        if not user: return
        admin = "\n👑 <b>Admin</b>" if str(uid) == Config.ADMIN_USER_ID else ""
        msg = f"👋 <b>Welcome!</b> 💸{admin}\n\n💰 Earn <b>₹{Config.REWARD_PER_REFERRAL}</b>/referral\n🔗 Code: <code>{user.get('referral_code', 'N/A')}</code>\n👥 Referrals: {user.get('referrals', 0)}\n💸 Balance: ₹{user.get('pending_balance', 0)}"
        self.bot.send(chat_id, msg, self.kb(self.menu_btns(uid)))
    
    def callback(self, chat_id, msg_id, uid, cb):
        self.bot.answer(cb["id"])
        user = self.db.get_user(uid) or {}
        data = cb.get("data", "")
        is_admin = str(uid) == Config.ADMIN_USER_ID
        
        if not is_admin and not user.get("is_verified") and data not in ["verify", "channels", "menu"]:
            self.bot.edit(chat_id, msg_id, "❌ Verify first!", self.kb([("✅ VERIFY", "verify")]))
            return
        
        handlers = {
            "verify": lambda: self.verify(chat_id, msg_id, uid),
            "channels": lambda: self.verify_screen(chat_id, uid),
            "menu": lambda: self.show_menu(chat_id, msg_id, uid, user),
            "my_referral": lambda: self.show_referral(chat_id, msg_id, uid, user),
            "dashboard": lambda: self.show_dash(chat_id, msg_id, uid, user),
            "withdraw": lambda: self.show_withdraw(chat_id, msg_id, uid, user),
            "setup_upi": lambda: self.setup_upi(chat_id, msg_id, uid),
            "request_wd": lambda: self.request_wd(chat_id, msg_id, uid, user),
            "wd_history": lambda: self.show_history(chat_id, msg_id, uid),
            "terms": lambda: self.bot.edit(chat_id, msg_id, f"📜 <b>Terms</b>\n\n1. Join channels to earn\n2. One referrer per user\n3. No self-referral\n4. Min withdraw: ₹{Config.MINIMUM_WITHDRAWAL}\n5. Fraud = Ban", self.kb([("🏠 Menu", "menu")])),
            "how": lambda: self.bot.edit(chat_id, msg_id, f"📢 <b>How It Works</b>\n\n1️⃣ Join Channels\n2️⃣ Get Referral Link\n3️⃣ Earn ₹{Config.REWARD_PER_REFERRAL}/referral\n4️⃣ Withdraw (Min ₹{Config.MINIMUM_WITHDRAWAL})", self.kb([("🏠 Menu", "menu")])),
            "rewards": lambda: self.bot.edit(chat_id, msg_id, f"🎁 <b>Rewards</b>\n\n💰 Per Referral: ₹{Config.REWARD_PER_REFERRAL}\n🔥 10 Referrals: +₹{Config.BONUS_AT_10_REFERRALS}", self.kb([("🏠 Menu", "menu")])),
            "support": lambda: self.bot.edit(chat_id, msg_id, f"📞 <b>Support</b>\n\n{Config.SUPPORT_CHANNEL}", self.kb([("🏠 Menu", "menu")])),
            "open_web": lambda: self.bot.edit(chat_id, msg_id, "🤖 <b>AI Assistant</b>\n\nTap below:", self.kb([{"text": self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME), "url": self.db.get_setting("web_url", Config.WEB_URL)}, ("🏠 Menu", "menu")])),
            "admin": lambda: self.admin_panel(chat_id, msg_id, uid) if is_admin else None,
        }
        
        if data in handlers: handlers[data]()
        elif data.startswith("admin_") and is_admin: self.admin_cb(chat_id, msg_id, uid, data)
    
    def show_menu(self, chat_id, msg_id, uid, user):
        self.bot.edit(chat_id, msg_id, f"🏠 <b>Menu</b>\n\n💰 ₹{user.get('pending_balance', 0)} | 👥 {user.get('referrals', 0)}", self.kb(self.menu_btns(uid)))
    
    def show_referral(self, chat_id, msg_id, uid, user):
        code = user.get("referral_code") or ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        link = f"https://t.me/{Config.BOT_USERNAME}?start={code}"
        msg = f"🔗 <b>Your Link</b>\n\n<code>{link}</code>\n\n💰 ₹{Config.REWARD_PER_REFERRAL}/referral\n👥 {user.get('referrals', 0)} referrals"
        self.bot.edit(chat_id, msg_id, msg, self.kb([{"text": "📤 Share", "url": f"https://t.me/share/url?url={quote(link)}"}, ("📊 Dashboard", "dashboard"), ("🏠 Menu", "menu")]))
    
    def show_dash(self, chat_id, msg_id, uid, user):
        msg = f"📊 <b>Dashboard</b>\n\n🔗 <code>{user.get('referral_code', 'N/A')}</code>\n📱 UPI: <code>{user.get('upi_id', 'Not set')}</code>\n\n👥 {user.get('referrals', 0)} | 💰 ₹{user.get('pending_balance', 0)} | 💸 ₹{user.get('total_earnings', 0)}"
        self.bot.edit(chat_id, msg_id, msg, self.kb([("💳 Withdraw", "withdraw"), ("🔗 Link", "my_referral"), ("🏠 Menu", "menu")]))
    
    def show_withdraw(self, chat_id, msg_id, uid, user):
        bal, upi = user.get("pending_balance", 0), user.get("upi_id", "")
        if not upi:
            msg = f"❌ <b>Setup UPI first</b>\n\nBalance: ₹{bal} | Min: ₹{Config.MINIMUM_WITHDRAWAL}"
            btns = [("📱 Setup UPI", "setup_upi"), ("🏠 Menu", "menu")]
        elif bal >= Config.MINIMUM_WITHDRAWAL:
            msg = f"💳 <b>Withdraw</b>\n\n💰 ₹{bal} | UPI: <code>{upi}</code>"
            btns = [("✅ Request", "request_wd"), ("✏️ Change UPI", "setup_upi"), ("📜 History", "wd_history"), ("🏠 Menu", "menu")]
        else:
            need = Config.MINIMUM_WITHDRAWAL - bal
            msg = f"❌ <b>Need ₹{need} more</b>\n\nBalance: ₹{bal} | Min: ₹{Config.MINIMUM_WITHDRAWAL}"
            btns = [("🔗 Referral", "my_referral"), ("📜 History", "wd_history"), ("🏠 Menu", "menu")]
        self.bot.edit(chat_id, msg_id, msg, self.kb(btns))
    
    def setup_upi(self, chat_id, msg_id, uid):
        self.states[uid] = {"state": "upi", "chat": chat_id, "msg": msg_id}
        self.bot.edit(chat_id, msg_id, "📱 <b>Send UPI ID</b>\n\nFormat: <code>name@upi</code>", self.kb([("❌ Cancel", "withdraw")]))
    
    def request_wd(self, chat_id, msg_id, uid, user):
        bal, upi = user.get("pending_balance", 0), user.get("upi_id", "")
        if bal < Config.MINIMUM_WITHDRAWAL or not upi: self.show_withdraw(chat_id, msg_id, uid, user); return
        wid = f"WD{random.randint(100000, 999999)}"
        self.db.create_withdrawal(wid, {"user_id": str(uid), "username": user.get("username", ""), "amount": bal, "upi_id": upi, "status": "pending", "requested_at": datetime.now().isoformat()})
        self.db.update_user(uid, {"pending_balance": 0, "withdrawn": user.get("withdrawn", 0) + bal})
        self.bot.send(Config.ADMIN_USER_ID, f"🆕 <b>WITHDRAWAL</b>\n\n@{user.get('username', 'N/A')} | ₹{bal}\nUPI: <code>{upi}</code>\nID: {wid}")
        self.bot.edit(chat_id, msg_id, f"✅ <b>Submitted</b>\n\nID: <code>{wid}</code> | ₹{bal}\nProcessed in 24-72hrs", self.kb([("📜 Status", "wd_history"), ("🏠 Menu", "menu")]))
    
    def show_history(self, chat_id, msg_id, uid):
        wds = self.db.get_withdrawals()
        user_wds = [(k, v) for k, v in wds.items() if v and v.get("user_id") == str(uid)]
        if not user_wds: msg = "📜 <b>No withdrawals</b>"
        else:
            msg = "📜 <b>History</b>\n\n"
            for wid, w in sorted(user_wds, key=lambda x: x[1].get("requested_at", ""), reverse=True)[:10]:
                s = {"completed": "✅", "rejected": "❌"}.get(w.get("status"), "⏳")
                msg += f"{s} ₹{w.get('amount', 0)} - {w.get('status', 'pending')}\n"
        self.bot.edit(chat_id, msg_id, msg, self.kb([("💳 Withdraw", "withdraw"), ("🏠 Menu", "menu")]))
    
    def admin_panel(self, chat_id, msg_id, uid):
        users, wds, chs = len(self.db.get_all_users()), len(self.db.get_withdrawals("pending")), len(self.db.get_channels())
        msg = f"👑 <b>Admin</b>\n\n👥 {users} | 💳 {wds} pending | 📢 {chs} channels"
        btns = [("📊 Stats", "admin_stats"), ("💳 Withdrawals", "admin_wds"), ("📢 Channels", "admin_chs"), ("🌐 Web URL", "admin_url"), ("🤖 AI Button", "admin_ai"), ("👥 Users", "admin_users"), ("📢 Broadcast", "admin_bc"), ("🏠 Menu", "menu")]
        self.bot.edit(chat_id, msg_id, msg, self.kb(btns))
    
    def admin_cb(self, chat_id, msg_id, uid, data):
        if data == "admin_stats":
            users = self.db.get_all_users()
            total = len(users); verified = sum(1 for u in users.values() if u and u.get("is_verified"))
            earnings = sum(u.get("total_earnings", 0) for u in users.values() if u)
            msg = f"📊 <b>Stats</b>\n\n👥 {total} users ({verified} verified)\n💰 ₹{earnings} earnings\n📢 {len(self.db.get_channels())} channels"
            self.bot.edit(chat_id, msg_id, msg, self.kb([("🔄 Refresh", "admin_stats"), ("🔙 Back", "admin")]))
        
        elif data == "admin_wds":
            wds = self.db.get_withdrawals("pending")
            if not wds: msg, btns = "💳 <b>No pending</b>", [("🔄 Refresh", "admin_wds"), ("🔙 Back", "admin")]
            else:
                msg, btns = "💳 <b>Pending</b>\n\n", []
                for i, (wid, w) in enumerate(wds.items(), 1):
                    msg += f"{i}. ₹{w.get('amount', 0)} - @{w.get('username', 'N/A')}\n   UPI: {w.get('upi_id', 'N/A')}\n\n"
                    btns.extend([(f"✅ {i}", f"admin_approve_{wid}"), (f"❌ {i}", f"admin_reject_{wid}")])
                btns.extend([("🔄 Refresh", "admin_wds"), ("🔙 Back", "admin")])
            self.bot.edit(chat_id, msg_id, msg, self.kb(btns))
        
        elif data == "admin_chs":
            msg = f"📢 <b>Channels</b>\n\n{len(self.db.get_channels())} added"
            btns = [("➕ Add", "admin_add_ch"), ("👁 View", "admin_view_ch"), ("🔙 Back", "admin")]
            self.bot.edit(chat_id, msg_id, msg, self.kb(btns))
        
        elif data == "admin_add_ch":
            msg = """➕ <b>Add Channel</b>

<b>PUBLIC:</b> Send 2 lines:
Channel Name
username

<b>PRIVATE:</b> Send 3 lines:
Channel Name
https://t.me/+XXXXX
-100XXXXXXXXX

⚠️ For private: add chat_id (get from @userinfobot when forwarding from channel)"""
            self.states[uid] = {"state": "channel", "chat": chat_id, "msg": msg_id}
            self.bot.edit(chat_id, msg_id, msg, self.kb([("❌ Cancel", "admin_chs")]))
        
        elif data == "admin_view_ch":
            channels = self.db.get_channels()
            if not channels: msg, btns = "📢 <b>No channels</b>", [("➕ Add", "admin_add_ch"), ("🔙 Back", "admin_chs")]
            else:
                msg, btns = "📢 <b>Channels</b>\n\n", []
                for i, (cid, ch) in enumerate(channels.items(), 1):
                    link = ch.get("link") or f"@{ch.get('username', 'N/A')}"
                    priv = " 🔒" if ch.get("is_private") else ""
                    msg += f"{i}. <b>{ch.get('name', 'Unknown')}</b>{priv}\n   {link}\n\n"
                    btns.append((f"❌ Del {i}", f"admin_del_ch_{cid}"))
                btns.extend([("➕ Add", "admin_add_ch"), ("🔙 Back", "admin_chs")])
            self.bot.edit(chat_id, msg_id, msg, self.kb(btns))
        
        elif data.startswith("admin_del_ch_"):
            cid = data.replace("admin_del_ch_", "")
            self.db.delete_channel(cid)
            self.bot.edit(chat_id, msg_id, "✅ Deleted", self.kb([("📢 View", "admin_view_ch"), ("🔙 Back", "admin_chs")]))
        
        elif data.startswith("admin_approve_"):
            wid = data.replace("admin_approve_", "")
            wds = self.db.get_withdrawals()
            if w := wds.get(wid):
                self.db.update_withdrawal(wid, "completed", f"Approved by {uid}")
                self.bot.send(w["user_id"], f"✅ <b>Approved!</b>\n\n₹{w['amount']} | ID: {wid}")
                self.bot.edit(chat_id, msg_id, f"✅ Approved {wid}", self.kb([("💳 Back", "admin_wds")]))
        
        elif data.startswith("admin_reject_"):
            wid = data.replace("admin_reject_", "")
            wds = self.db.get_withdrawals()
            if w := wds.get(wid):
                self.states[uid] = {"state": "reject", "wid": wid, "chat": chat_id, "msg": msg_id, "user_id": w["user_id"], "amount": w["amount"]}
                self.bot.edit(chat_id, msg_id, f"❌ <b>Reject</b>\n\n₹{w['amount']} | @{w.get('username')}\n\nSend reason:", self.kb([("❌ Cancel", "admin_wds")]))
        
        elif data == "admin_url":
            url = self.db.get_setting("web_url", Config.WEB_URL)
            self.bot.edit(chat_id, msg_id, f"🌐 <b>Web URL</b>\n\n<code>{url}</code>", self.kb([("✏️ Update", "admin_set_url"), ("🔙 Back", "admin")]))
        
        elif data == "admin_set_url":
            self.states[uid] = {"state": "url", "chat": chat_id, "msg": msg_id}
            self.bot.edit(chat_id, msg_id, "🌐 Send new URL (https://...):", self.kb([("❌ Cancel", "admin_url")]))
        
        elif data == "admin_ai":
            name = self.db.get_setting("ai_button_name", Config.AI_BUTTON_NAME)
            self.bot.edit(chat_id, msg_id, f"🤖 <b>AI Button</b>\n\n<code>{name}</code>", self.kb([("✏️ Update", "admin_set_ai"), ("🔙 Back", "admin")]))
        
        elif data == "admin_set_ai":
            self.states[uid] = {"state": "ai_name", "chat": chat_id, "msg": msg_id}
            self.bot.edit(chat_id, msg_id, "🤖 Send new name (max 20 chars):", self.kb([("❌ Cancel", "admin_ai")]))
        
        elif data == "admin_users":
            users = self.db.get_all_users()
            sorted_u = sorted([(k, v) for k, v in users.items() if v], key=lambda x: x[1].get("referrals", 0), reverse=True)[:10]
            msg = "👥 <b>Top Users</b>\n\n"
            for i, (uid, u) in enumerate(sorted_u, 1):
                v = "✅" if u.get("is_verified") else "❌"
                msg += f"{i}. {v} {u.get('username', 'User')} | ₹{u.get('total_earnings', 0)} | 👥{u.get('referrals', 0)}\n"
            self.bot.edit(chat_id, msg_id, msg, self.kb([("🔄 Refresh", "admin_users"), ("🔙 Back", "admin")]))
        
        elif data == "admin_bc":
            self.bot.edit(chat_id, msg_id, "📢 <b>Broadcast</b>\n\nUse: <code>/broadcast message</code>", self.kb([("🔙 Back", "admin")]))
    
    def handle_msg(self, chat_id, uid, text):
        if uid in self.states:
            state = self.states[uid]
            
            if state["state"] == "upi":
                if '@' in text and len(text) > 5:
                    self.db.update_user(uid, {"upi_id": text.strip()})
                    self.bot.send(chat_id, f"✅ UPI saved: <code>{text}</code>", self.kb([("💳 Withdraw", "withdraw"), ("🏠 Menu", "menu")]))
                else:
                    self.bot.send(chat_id, "❌ Invalid. Use: name@upi")
                    return
                del self.states[uid]
            
            elif state["state"] == "channel":
                lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
                if len(lines) >= 2:
                    name, second = lines[0], lines[1]
                    is_private = "t.me/+" in second or second.startswith("-100")
                    
                    if is_private:
                        # Private channel
                        link = second if "t.me" in second else None
                        chat_id_num = lines[2] if len(lines) >= 3 else (second if second.startswith("-100") else None)
                        
                        if not chat_id_num or not chat_id_num.startswith("-100"):
                            self.bot.send(chat_id, "❌ For private channels, provide chat_id (-100XXX)\n\nFormat:\nName\nhttps://t.me/+XXX\n-100XXXXXXXXX")
                            return
                        
                        cid = f"private_{int(time.time())}"
                        ch_data = {"name": name, "link": link or f"Private ({chat_id_num})", "chat_id": chat_id_num, 
                                   "is_private": True, "id": cid, "added_at": datetime.now().isoformat()}
                    else:
                        # Public channel
                        username = second.replace("@", "").replace("https://t.me/", "").replace(" ", "").lower()
                        cid = f"channel_{username}_{int(time.time())}"
                        ch_data = {"name": name, "username": username, "link": f"https://t.me/{username}",
                                   "is_private": False, "id": cid, "added_at": datetime.now().isoformat()}
                    
                    if self.db.add_channel(ch_data) is not None:
                        priv_text = " (Private)" if is_private else ""
                        self.bot.send(chat_id, f"✅ <b>Added{priv_text}!</b>\n\n{name}", self.kb([("📢 View", "admin_view_ch"), ("➕ Add More", "admin_add_ch"), ("🔙 Back", "admin_chs")]))
                    else:
                        self.bot.send(chat_id, "❌ Failed")
                else:
                    self.bot.send(chat_id, "❌ Invalid format")
                del self.states[uid]
            
            elif state["state"] == "reject":
                wid, user_id, amount = state["wid"], state["user_id"], state["amount"]
                self.db.update_withdrawal(wid, "rejected", text)
                user = self.db.get_user(user_id)
                if user: self.db.update_user(user_id, {"pending_balance": user.get("pending_balance", 0) + amount})
                self.bot.send(user_id, f"❌ <b>Rejected</b>\n\n₹{amount} returned\nReason: {text}")
                self.bot.send(chat_id, f"❌ Rejected {wid}", self.kb([("💳 Back", "admin_wds")]))
                del self.states[uid]
            
            elif state["state"] == "url":
                if text.startswith("http"):
                    self.db.set_setting("web_url", text.strip())
                    self.bot.send(chat_id, f"✅ URL updated", self.kb([("🔙 Back", "admin_url")]))
                else:
                    self.bot.send(chat_id, "❌ Invalid URL")
                del self.states[uid]
            
            elif state["state"] == "ai_name":
                if 0 < len(text) <= 20:
                    self.db.set_setting("ai_button_name", text.strip())
                    self.bot.send(chat_id, f"✅ Updated: {text}", self.kb([("🔙 Back", "admin_ai")]))
                else:
                    self.bot.send(chat_id, "❌ 1-20 chars only")
                del self.states[uid]
        
        elif text.startswith("/broadcast") and str(uid) == Config.ADMIN_USER_ID:
            msg = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
            if msg:
                users = self.db.get_all_users()
                self.bot.send(chat_id, f"📢 Sending to {len(users)}...")
                success = sum(1 for u in users if self.bot.send(u, f"📢 <b>Announcement</b>\n\n{msg}") and not time.sleep(0.1))
                self.bot.send(chat_id, f"✅ Sent: {success}/{len(users)}")
    
    def run(self):
        print("🤖 Bot Started!")
        self.bot.api("deleteWebhook", {"drop_pending_updates": True})
        time.sleep(2)
        print(f"💰 ₹{Config.REWARD_PER_REFERRAL}/referral | Min: ₹{Config.MINIMUM_WITHDRAWAL}")
        print("✅ Private channel support added")
        print("=" * 40)
        
        errors = 0
        while self.running:
            try:
                updates = self.bot.updates(self.offset)
                if updates is None: errors += 1; time.sleep(2 if errors <= 5 else 5); continue
                errors = 0
                
                for upd in updates:
                    self.offset = upd["update_id"] + 1
                    if "message" in upd:
                        m = upd["message"]
                        cid, uid = m["chat"]["id"], m["from"]["id"]
                        if "text" in m:
                            txt = m["text"]
                            if txt.startswith("/start"):
                                args = txt.split()[1:] if len(txt.split()) > 1 else []
                                self.start(cid, uid, m["from"].get("username", ""), m["from"].get("first_name", ""), m["from"].get("last_name", ""), args)
                            elif txt.startswith("/admin") and str(uid) == Config.ADMIN_USER_ID:
                                self.admin_panel(cid, m["message_id"], uid)
                            else:
                                self.handle_msg(cid, uid, txt)
                    elif "callback_query" in upd:
                        cb = upd["callback_query"]
                        self.callback(cb["message"]["chat"]["id"], cb["message"]["message_id"], cb["from"]["id"], cb)
                
                time.sleep(0.5)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"❌ Error: {e}")
                errors += 1
                if errors > 10: time.sleep(10); self.offset = 0; errors = 0
                else: time.sleep(5)

if __name__ == "__main__":
    print("🔥 Trade Genius Bot - Optimized")
    print("=" * 40)
    threading.Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask started")
    TradeGeniusBot().run()