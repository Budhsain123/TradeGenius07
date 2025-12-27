import os
import logging
import random
import string
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from pymongo import MongoClient
import certifi
from flask import Flask
from threading import Thread

# ================= FLASK SERVER =================
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

# ================= ENV =================
load_dotenv()

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL")

ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
ADMINS = [int(i.strip()) for i in ADMIN_IDS_STR.split(",") if i.strip()]

# ================= MONGODB (SSL FIX) =================
try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000
    )
    client.admin.command("ping")
    db = client["file_link_bot"]
    files_collection = db["files"]
    settings_collection = db["settings"]
    logging.info("✅ MongoDB Connected Successfully")
except Exception as e:
    logging.error(f"❌ MongoDB Connection Failed: {e}")
    raise SystemExit(1)

# ================= PYROGRAM =================
app = Client(
    "FileLinkBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= HELPERS =================
def generate_random_string(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def is_user_member(client: Client, user_id: int) -> bool:
    try:
        await client.get_chat_member(f"@{UPDATE_CHANNEL}", user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Join check error: {e}")
        return False

def get_bot_mode():
    setting = settings_collection.find_one({"_id": "bot_mode"})
    if setting:
        return setting.get("mode", "public")
    settings_collection.update_one(
        {"_id": "bot_mode"},
        {"$set": {"mode": "public"}},
        upsert=True
    )
    return "public"

# ================= COMMANDS =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if len(message.command) > 1:
        file_id = message.command[1]

        if not await is_user_member(client, message.from_user.id):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{UPDATE_CHANNEL}")],
                [InlineKeyboardButton("✅ I Have Joined", callback_data=f"check_join_{file_id}")]
            ])
            await message.reply(
                "👋 **File access ke liye channel join karo**",
                reply_markup=keyboard
            )
            return

        data = files_collection.find_one({"_id": file_id})
        if data:
            await client.copy_message(
                message.chat.id,
                LOG_CHANNEL,
                data["message_id"]
            )
        else:
            await message.reply("❌ File not found")
    else:
        await message.reply(
            "**File to Link Bot**\n\nKoi bhi file bhejo aur link pao ✅"
        )

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def file_handler(client: Client, message: Message):
    if get_bot_mode() == "private" and message.from_user.id not in ADMINS:
        await message.reply("❌ Sirf admins upload kar sakte hain")
        return

    status = await message.reply("⏳ Uploading...")

    try:
        fwd = await message.forward(LOG_CHANNEL)
        code = generate_random_string()
        files_collection.insert_one({
            "_id": code,
            "message_id": fwd.id
        })
        bot = await client.get_me()
        link = f"https://t.me/{bot.username}?start={code}"
        await status.edit_text(f"✅ **Link Ready**\n\n`{link}`")
    except Exception as e:
        logging.error(e)
        await status.edit_text("❌ Error occurred")

@app.on_message(filters.command("settings") & filters.private)
async def settings_handler(client: Client, message: Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ Permission denied")

    mode = get_bot_mode()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Public", callback_data="set_mode_public")],
        [InlineKeyboardButton("🔒 Private", callback_data="set_mode_private")]
    ])
    await message.reply(
        f"⚙️ Current Mode: **{mode.upper()}**",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^set_mode_"))
async def set_mode(client: Client, cq: CallbackQuery):
    if cq.from_user.id not in ADMINS:
        return await cq.answer("❌ Not allowed", show_alert=True)

    mode = cq.data.split("_")[2]
    settings_collection.update_one(
        {"_id": "bot_mode"},
        {"$set": {"mode": mode}},
        upsert=True
    )
    await cq.answer(f"Mode set to {mode.upper()}", show_alert=True)

@app.on_callback_query(filters.regex("^check_join_"))
async def check_join(client: Client, cq: CallbackQuery):
    file_id = cq.data.split("_", 2)[2]

    if not await is_user_member(client, cq.from_user.id):
        return await cq.answer("❌ Join channel first", show_alert=True)

    data = files_collection.find_one({"_id": file_id})
    if data:
        await client.copy_message(
            cq.from_user.id,
            LOG_CHANNEL,
            data["message_id"]
        )
        await cq.message.delete()
    else:
        await cq.answer("❌ File not found", show_alert=True)

# ================= START =================
if __name__ == "__main__":
    if not ADMINS:
        logging.warning("ADMIN_IDS not set")

    Thread(target=run_flask).start()
    logging.info("🤖 Bot Started")
    app.run()