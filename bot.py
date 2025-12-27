import os
import logging
import random
import string
from dotenv import load_dotenv
from pyrogram import Client, filters, enums
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from pymongo import MongoClient
from flask import Flask # <-- Yahan add kiya hai
from threading import Thread # <-- Yahan add kiya hai

# --- Flask Web Server (Render ko busy rakhne ke liye) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is alive!", 200

def run_flask():
    # Render port ko environment variable se leta hai
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)
# --- Web Server ka code yahan khatam ---


# --- Basic Logging ---
logging.basicConfig(level=logging.INFO)

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL")) 
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL") 

# Admin configuration
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
ADMINS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id]

# --- Database Setup ---
try:
    client = MongoClient(MONGO_URI)
    db = client['file_link_bot']
    files_collection = db['files']
    settings_collection = db['settings']
    logging.info("MongoDB Connected Successfully!")
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    exit()

# --- Pyrogram Client ---
app = Client("FileLinkBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Helper Functions ---
def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def is_user_member(client: Client, user_id: int) -> bool:
    try:
        await client.get_chat_member(chat_id=f"@{UPDATE_CHANNEL}", user_id=user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Error checking membership for {user_id}: {e}")
        return False

async def get_bot_mode() -> str:
    setting = settings_collection.find_one({"_id": "bot_mode"})
    if setting:
        return setting.get("mode", "public")
    settings_collection.update_one({"_id": "bot_mode"}, {"$set": {"mode": "public"}}, upsert=True)
    return "public"

# --- Bot Command Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if len(message.command) > 1:
        file_id_str = message.command[1]
        
        if not await is_user_member(client, message.from_user.id):
            join_button = InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{UPDATE_CHANNEL}")
            joined_button = InlineKeyboardButton("✅ I Have Joined", callback_data=f"check_join_{file_id_str}")
            keyboard = InlineKeyboardMarkup([[join_button], [joined_button]])
            
            await message.reply(
                f"👋 **Hello, {message.from_user.first_name}!**\n\nYe file access karne ke liye, aapko hamara update channel join karna hoga.",
                reply_markup=keyboard
            )
            return

        file_record = files_collection.find_one({"_id": file_id_str})
        if file_record:
            try:
                await client.copy_message(chat_id=message.from_user.id, from_chat_id=LOG_CHANNEL, message_id=file_record['message_id'])
            except Exception as e:
                await message.reply(f"❌ Sorry, file bhejte waqt ek error aa gaya.\n`Error: {e}`")
        else:
            await message.reply("🤔 File not found! Ho sakta hai link galat ya expire ho gaya ho.")
    else:
        await message.reply("**Hello! Mai ek File-to-Link bot hu.**\n\nMujhe koi bhi file bhejo, aur mai aapko uska ek shareable link dunga.")

@app.on_message(filters.private & (filters.document | filters.video | filters.photo | filters.audio))
async def file_handler(client: Client, message: Message):
    bot_mode = await get_bot_mode()
    if bot_mode == "private" and message.from_user.id not in ADMINS:
        await message.reply("😔 **Sorry!** Abhi sirf Admins hi files upload kar sakte hain.")
        return

    status_msg = await message.reply("⏳ Please wait, file upload kar raha hu...", quote=True)
    
    try:
        forwarded_message = await message.forward(LOG_CHANNEL)
        file_id_str = generate_random_string()
        files_collection.insert_one({'_id': file_id_str, 'message_id': forwarded_message.id})
        bot_username = (await client.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={file_id_str}"
        await status_msg.edit_text(
            f"✅ **Link Generated Successfully!**\n\n🔗 Your Link: `{share_link}`",
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"File handling error: {e}")
        await status_msg.edit_text(f"❌ **Error!**\n\nKuch galat ho gaya. Please try again.\n`Details: {e}`")

@app.on_message(filters.command("settings") & filters.private)
async def settings_handler(client: Client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply("❌ Aapke paas is command ko use karne ki permission nahi hai.")
        return
    
    current_mode = await get_bot_mode()
    
    public_button = InlineKeyboardButton("🌍 Public (Anyone)", callback_data="set_mode_public")
    private_button = InlineKeyboardButton("🔒 Private (Admins Only)", callback_data="set_mode_private")
    keyboard = InlineKeyboardMarkup([[public_button], [private_button]])
    
    await message.reply(
        f"⚙️ **Bot Settings**\n\n"
        f"Abhi bot ka file upload mode **{current_mode.upper()}** hai.\n\n"
        f"**Public:** Koi bhi file bhej kar link bana sakta hai.\n"
        f"**Private:** Sirf admins hi file bhej sakte hain.\n\n"
        f"Naya mode select karein:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^set_mode_"))
async def set_mode_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Permission Denied!", show_alert=True)
        return
        
    new_mode = callback_query.data.split("_")[2]
    
    settings_collection.update_one(
        {"_id": "bot_mode"},
        {"$set": {"mode": new_mode}},
        upsert=True
    )
    
    await callback_query.answer(f"Mode successfully {new_mode.upper()} par set ho gaya hai!", show_alert=True)
    
    public_button = InlineKeyboardButton("🌍 Public (Anyone)", callback_data="set_mode_public")
    private_button = InlineKeyboardButton("🔒 Private (Admins Only)", callback_data="set_mode_private")
    keyboard = InlineKeyboardMarkup([[public_button], [private_button]])
    
    await callback_query.message.edit_text(
        f"⚙️ **Bot Settings**\n\n"
        f"✅ Bot ka file upload mode ab **{new_mode.upper()}** hai.\n\n"
        f"Naya mode select karein:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^check_join_"))
async def check_join_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    file_id_str = callback_query.data.split("_", 2)[2]

    if await is_user_member(client, user_id):
        await callback_query.answer("Thanks for joining! File bhej raha hu...", show_alert=True)
        file_record = files_collection.find_one({"_id": file_id_str})
        if file_record:
            try:
                await client.copy_message(chat_id=user_id, from_chat_id=LOG_CHANNEL, message_id=file_record['message_id'])
                await callback_query.message.delete()
            except Exception as e:
                await callback_query.message.edit_text(f"❌ File bhejte waqt error aa gaya.\n`Error: {e}`")
        else:
            await callback_query.message.edit_text("🤔 File not found!")
    else:
        await callback_query.answer("Aapne abhi tak channel join nahi kiya hai. Please join karke dobara try karein.", show_alert=True)

# --- Bot ko Start Karo ---
if __name__ == "__main__":
    if not ADMINS:
        logging.warning("WARNING: ADMIN_IDS is not set. Settings command kaam nahi karega.")
    
    # Flask server ko ek alag thread me start karo
    logging.info("Starting Flask web server...")
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    logging.info("Bot is starting...")
    app.run()
    logging.info("Bot has stopped.")
