import os
import logging
import json
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Setup basic configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_DATA = {}
MAIN_MENU = [
    [KeyboardButton("📤 Upload File"), KeyboardButton("🔍 Check Files")],
    [KeyboardButton("🚀 Start Bot"), KeyboardButton("🔄 Restart Bot")],
    [KeyboardButton("🗑️ Delete Bot")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

# Define your secure application instance
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8842248531:AAFLjUKst9mYf2IJgP2j4sSK4p_B5tymkik")
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    profile_photos = await context.bot.get_user_profile_photos(user_id=user.id, limit=1)
    profile_text = (
        f"👋 *Welcome to the Automated Vercel Hosting System!*\n\n"
        f"👤 *Your Profile Metadata:*\n"
        f"┣ 📛 *Name:* {user.first_name}\n"
        f"┣ 🆔 *Chat ID:* `{chat_id}`\n"
        f"┗ 🏷️ *Username:* @{user.username or 'None'}\n\n"
        f"Slot Allocations available: *{3 - len(USER_DATA[chat_id]['files'])} / 3 remaining*"
    )
    if profile_photos.total_count > 0:
        await context.bot.send_photo(chat_id=chat_id, photo=profile_photos.photos[0][-1].file_id, caption=profile_text, parse_mode="Markdown", reply_markup=REPLY_MARKUP)
    else:
        await update.message.reply_text(text=profile_text, parse_mode="Markdown", reply_markup=REPLY_MARKUP)

async def handle_menu_options(update: Update, context) -> None:
    text = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in USER_DATA: USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    if text == "📤 Upload File":
        if len(USER_DATA[chat_id]["files"]) >= 3:
            await update.message.reply_text("❌ All slots filled.")
            return
        USER_DATA[chat_id]["status"] = "awaiting_file"
        await update.message.reply_text("📝 Send your `.py` or `.js` document text attachment:")
    elif text == "🔍 Check Files":
        files = USER_DATA[chat_id]["files"]
        await update.message.reply_text(f"📂 Current Hosted Cache Slots: {len(files)}/3")
    elif text == "🗑️ Delete Bot":
        USER_DATA[chat_id]["files"] = {}
        await update.message.reply_text("🗑️ All structures cleared.")

async def handle_document(update: Update, context) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in USER_DATA or USER_DATA[chat_id]["status"] != "awaiting_file": return
    doc = update.message.document
    filename = doc.file_name
    
    file_obj = await context.bot.get_file(doc.file_id)
    file_bytes = await file_obj.download_as_bytearray()
    USER_DATA[chat_id]["files"][filename] = file_bytes.decode('utf-8')
    USER_DATA[chat_id]["status"] = "idle"
    await update.message.reply_text(f"✅ Loaded file: `{filename}`", parse_mode="Markdown")

# Register logic execution blocks
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options))
application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

# 🌟 CRITICAL FIX: The top-level application interface entry point Vercel was missing
async def handler(request):
    """Exposes the required serverless function entryway Vercel expects."""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            await application.initialize()
            update = Update.de_json(data, application.bot)
            await application.process_update(update)
            return {"statusCode": 200, "body": "OK"}
        except Exception as e:
            logger.error(f"Error executing event cycle: {e}")
            return {"statusCode": 500, "body": str(e)}
    return {"statusCode": 200, "body": "Bot backend interface active."}
