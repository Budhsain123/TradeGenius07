import os
import json
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
from firebase_admin import credentials, firestore

# ---------------- BASIC ----------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL")

ADMINS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# ---------------- FLASK ----------------
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot Alive", 200

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app_flask.run("0.0.0.0", port)

# ---------------- FIREBASE (SECURE INIT) ----------------
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
if not firebase_json:
    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env missing")

cred = credentials.Certificate(json.loads(firebase_json))
firebase_admin.initialize_app(cred)
db = firestore.client()

files_col = db.collection("files")
settings_col = db.collection("settings")

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
    doc = settings_col.document("bot_mode").get()
    if doc.exists:
        return doc.to_dict().get("mode", "public")
    settings_col.document("bot_mode").set({"mode": "public"})
    return "public"

# ---------------- START ----------------
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, msg):
    if len(msg.command) > 1:
        code = msg.command[1]

        if not await is_member(client, msg.from_user.id):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{UPDATE_CHANNEL}")],
                [InlineKeyboardButton("✅ Joined", callback_data=f"check_{code}")]
            ])
            return await msg.reply("📢 Pehle channel join karo", reply_markup=kb)

        doc = files_col.document(code).get()
        if doc.exists:
            await client.copy_message(msg.chat.id, LOG_CHANNEL, doc.to_dict()["message_id"])
        else:
            await msg.reply("❌ File not found")
    else:
        await msg.reply("📁 File bhejo, link pao")

# ---------------- FILE UPLOAD ----------------
@bot.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def upload(client, msg):
    if get_mode() == "private" and msg.from_user.id not in ADMINS:
        return await msg.reply("❌ Sirf admins upload kar sakte hain")

    wait = await msg.reply("⏳ Uploading...")
    fwd = await msg.forward(LOG_CHANNEL)

    code = gen_code()
    files_col.document(code).set({"message_id": fwd.id})

    me = await client.get_me()
    link = f"https://t.me/{me.username}?start={code}"

    await wait.edit_text(f"✅ Link Generated\n\n`{link}`")

# ---------------- SETTINGS ----------------
@bot.on_message(filters.command("settings") & filters.private)
async def settings(client, msg):
    if msg.from_user.id not in ADMINS:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Public", callback_data="mode_public")],
        [InlineKeyboardButton("🔒 Private", callback_data="mode_private")]
    ])
    await msg.reply(f"⚙ Mode: {get_mode()}", reply_markup=kb)

@bot.on_callback_query(filters.regex("^mode_"))
async def set_mode(client, cq):
    if cq.from_user.id not in ADMINS:
        return
    mode = cq.data.split("_")[1]
    settings_col.document("bot_mode").set({"mode": mode})
    await cq.answer(f"Mode set to {mode.upper()}", show_alert=True)

@bot.on_callback_query(filters.regex("^check_"))
async def check_join(client, cq):
    code = cq.data.split("_")[1]
    if not await is_member(client, cq.from_user.id):
        return await cq.answer("❌ Join first", show_alert=True)

    doc = files_col.document(code).get()
    if doc.exists:
        await client.copy_message(cq.from_user.id, LOG_CHANNEL, doc.to_dict()["message_id"])
        await cq.message.delete()
    else:
        await cq.answer("❌ File not found", show_alert=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run()