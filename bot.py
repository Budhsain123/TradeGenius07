import os
import logging
import random
import string
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import firebase_admin
from firebase_admin import credentials, db

# ---------------- BASIC ----------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL")

ADMINS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# ---------------- FLASK (Render ke liye mandatory) ----------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot Alive ✅", 200

def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------------- FIREBASE RTDB INIT ----------------
if not os.path.exists("firebase.json"):
    raise RuntimeError("❌ firebase.json file missing")

cred = credentials.Certificate("firebase.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://colortraderpro-panel-default-rtdb.firebaseio.com"
        }
    )

files_ref = db.reference("files")
settings_ref = db.reference("settings")

# ---------------- PYROGRAM ----------------
bot = Client(
    "FileLinkBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- HELPERS ----------------
def gen_code(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

async def is_member(client, user_id):
    try:
        await client.get_chat_member(f"@{UPDATE_CHANNEL}", user_id)
        return True
    except UserNotParticipant:
        return False
    except:
        return False

def get_mode():
    mode = settings_ref.child("bot_mode").get()
    if mode:
        return mode
    settings_ref.child("bot_mode").set("public")
    return "public"

# ---------------- START COMMAND ----------------
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, msg):
    if len(msg.command) > 1:
        code = msg.command[1]

        if not await is_member(client, msg.from_user.id):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{UPDATE_CHANNEL}")],
                [InlineKeyboardButton("✅ Joined", callback_data=f"check_{code}")]
            ])
            return await msg.reply(
                "📢 File access ke liye pehle channel join karo",
                reply_markup=kb
            )

        data = files_ref.child(code).get()
        if data:
            await client.copy_message(
                msg.chat.id,
                LOG_CHANNEL,
                data["message_id"]
            )
        else:
            await msg.reply("❌ File not found / expired")
    else:
        await msg.reply("📁 Koi bhi file bhejo, main uska link bana dunga")

# ---------------- FILE UPLOAD ----------------
@bot.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def upload_handler(client, msg):
    if get_mode() == "private" and msg.from_user.id not in ADMINS:
        return await msg.reply("❌ Sirf admins file upload kar sakte hain")

    wait = await msg.reply("⏳ Uploading...")
    fwd = await msg.forward(LOG_CHANNEL)

    code = gen_code()
    files_ref.child(code).set({
        "message_id": fwd.id
    })

    me = await client.get_me()
    link = f"https://t.me/{me.username}?start={code}"

    await wait.edit_text(
        f"✅ **Link Generated**\n\n`{link}`",
        disable_web_page_preview=True
    )

# ---------------- SETTINGS ----------------
@bot.on_message(filters.command("settings") & filters.private)
async def settings_handler(client, msg):
    if msg.from_user.id not in ADMINS:
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Public", callback_data="mode_public")],
        [InlineKeyboardButton("🔒 Private", callback_data="mode_private")]
    ])

    await msg.reply(
        f"⚙ **Current Mode:** `{get_mode()}`",
        reply_markup=kb
    )

@bot.on_callback_query(filters.regex("^mode_"))
async def set_mode(client, cq):
    if cq.from_user.id not in ADMINS:
        return

    mode = cq.data.split("_")[1]
    settings_ref.child("bot_mode").set(mode)

    await cq.answer(
        f"✅ Mode set to {mode.upper()}",
        show_alert=True
    )

@bot.on_callback_query(filters.regex("^check_"))
async def check_join(client, cq):
    code = cq.data.split("_")[1]

    if not await is_member(client, cq.from_user.id):
        return await cq.answer(
            "❌ Pehle channel join karo",
            show_alert=True
        )

    data = files_ref.child(code).get()
    if data:
        await client.copy_message(
            cq.from_user.id,
            LOG_CHANNEL,
            data["message_id"]
        )
        await cq.message.delete()
    else:
        await cq.answer("❌ File not found", show_alert=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    Thread(target=run_flask).start()
    logging.info("🤖 Bot starting...")
    bot.run()