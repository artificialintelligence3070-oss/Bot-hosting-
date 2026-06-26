import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Setup basic system logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask environment
app = Flask(__name__)

# Virtual database tracking user files/deployments (Max 3 slots per user)
USER_DATA = {}

# Persistent Menu Layout
MAIN_MENU = [
    [KeyboardButton("📤 Upload File"), KeyboardButton("🔍 Check Files")],
    [KeyboardButton("🚀 Start Bot"), KeyboardButton("🔄 Restart Bot")],
    [KeyboardButton("🗑️ Delete Bot")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

# Fetch system configurations securely
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8842248531:AAFLjUKst9mYf2IJgP2j4sSK4p_B5tymkik")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN")

# Build Telegram Application backend instance (Webhook mode - no run_polling)
tg_app = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context) -> None:
    """Triggered on /start. Tracks slots and outputs user profile metrics."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    # Fetch User Avatar
    profile_photos = await context.bot.get_user_profile_photos(user_id=user.id, limit=1)
    
    profile_text = (
        f"👋 *Welcome to the Automated Vercel Hosting System!*\n\n"
        f"👤 *Your Profile Metadata:*\n"
        f"┣ 📛 *Name:* {user.first_name} {user.last_name or ''}\n"
        f"┣ 🆔 *Chat ID:* `{chat_id}`\n"
        f"┗ 🏷️ *Username:* @{user.username or 'None'}\n\n"
        f"📊 *Slot Allocations:* {len(USER_DATA[chat_id]['files'])}/3 used."
    )

    if profile_photos.total_count > 0:
        await context.bot.send_photo(
            chat_id=chat_id, photo=profile_photos.photos[0][-1].file_id, 
            caption=profile_text, parse_mode="Markdown", reply_markup=REPLY_MARKUP
        )
    else:
        await update.message.reply_text(text=profile_text, parse_mode="Markdown", reply_markup=REPLY_MARKUP)

async def handle_menu_options(update: Update, context) -> None:
    """Evaluates text strings sent from bottom application panel."""
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    if text == "📤 Upload File":
        if len(USER_DATA[chat_id]["files"]) >= 3:
            await update.message.reply_text("❌ All 3 hosting slots are full! Delete active instances to free space.")
            return
        USER_DATA[chat_id]["status"] = "awaiting_file"
        await update.message.reply_text("📝 Drop your code script attachment file (`.py` or `.js`). Max 3 files:")

    elif text == "🔍 Check Files":
        files = USER_DATA[chat_id]["files"]
        url = USER_DATA[chat_id]["deployment_url"]
        if not files:
            await update.message.reply_text("📭 Your configuration profile slot allocations are clear.")
        else:
            file_list = "\n".join([f"📄 `{name}`" for name in files.keys()])
            status_url = f"\n\n🔗 *Live Deploy URL:* {url}" if url else "\n\n⚠️ *Status:* Ready. Tap 🚀 Start Bot."
            await update.message.reply_text(f"📂 *Your Files on Server:*\n{file_list}{status_url}", parse_mode="Markdown")

    elif text == "🚀 Start Bot":
        if not USER_DATA[chat_id]["files"]:
            await update.message.reply_text("❌ There are zero source files found to register. Upload software first.")
            return
        
        await update.message.reply_text("⚡ *Initiating server deployment context with Vercel API structures...*")
        url = deploy_to_vercel(chat_id)
        if url:
            USER_DATA[chat_id]["deployment_url"] = url
            await update.message.reply_text(f"🎉 *Success! Your script is deployed live to Vercel:*\n\n🌐 {url}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Deployment execution failed. Confirm your Vercel Token settings configuration.")

    elif text == "🔄 Restart Bot":
        if not USER_DATA[chat_id]["deployment_url"]:
            await update.message.reply_text("❌ There is no active container found running to reboot.")
        else:
            await update.message.reply_text("🔄 *Re-triggering deployment hook instances...*")
            url = deploy_to_vercel(chat_id)
            await update.message.reply_text(f"✅ Reboot completed successfully!\n🌐 {url}")

    elif text == "🗑️ Delete Bot":
        USER_DATA[chat_id]["files"] = {}
        USER_DATA[chat_id]["deployment_url"] = None
        await update.message.reply_text("🗑️ Active host structures completely removed. Slots reset to 0/3.")

async def handle_document(update: Update, context) -> None:
    """Intercerts files, extracts contents, and assigns them to internal storage memory."""
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA or USER_DATA[chat_id]["status"] != "awaiting_file":
        return

    doc = update.message.document
    filename = doc.file_name
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.py', '.js']:
        await update.message.reply_text("❌ Rejected! Only `.py` and `.js` formats are accepted.")
        return

    file_obj = await context.bot.get_file(doc.file_id)
    file_bytes = await file_obj.download_as_bytearray()
    
    USER_DATA[chat_id]["files"][filename] = file_bytes.decode('utf-8')
    USER_DATA[chat_id]["status"] = "idle"

    await update.message.reply_text(
        f"✅ *File successfully uploaded!*\n📦 Name: `{filename}`\n📊 Total slots filled: {len(USER_DATA[chat_id]['files'])}/3",
        parse_mode="Markdown", reply_markup=REPLY_MARKUP
    )

def deploy_to_vercel(chat_id: int) -> str:
    """Programmatically pushes the user's uploaded scripts straight into Vercel's Engine via API."""
    if not VERCEL_TOKEN:
        logger.error("Missing VERCEL_TOKEN Environment Setting")
        return None

    user_files = USER_DATA[chat_id]["files"]
    payload_files = []
    main_file = None

    for fname, content in user_files.items():
        payload_files.append({"file": fname, "data": content})
        if main_file is None:
            main_file = fname

    if not main_file:
        return None

    ext = os.path.splitext(main_file)[1].lower()
    runtime = "@vercel/python" if ext == ".py" else "@vercel/node"
    
    vercel_config = {
        "version": 2,
        "builds": [{"src": main_file, "use": runtime}],
        "routes": [{"src": "/(.*)", "dest": main_file}]
    }
    
    payload_files.append({"file": "vercel.json", "data": json.dumps(vercel_config)})
    if ext == ".py":
        payload_files.append({"file": "requirements.txt", "data": "requests==2.32.3\npython-telegram-bot==21.3\n"})

    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    body = {"name": f"user-bot-{chat_id}", "files": payload_files}

    try:
        res = requests.post("https://api.vercel.com/v13/deployments", headers=headers, json=body)
        if res.status_code in [200, 201]:
            return f"https://{res.json()['url']}"
    except Exception as e:
        logger.error(f"Network compilation exception: {e}")
    return None

# Attach command logic processors
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options))
tg_app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

@app.route("/", methods=["GET"])
def index():
    return "Master System Online"

@app.route("/", methods=["POST"])
def webhook():
    """Vercel execution route entry point."""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, tg_app.bot)
        tg_app.initialize()
        tg_app.process_update(update)
        return jsonify({"status": "processed"}), 200
    except Exception as e:
        logger.error(f"Error lifecycle processing webhook: {e}")
        return jsonify({"error": str(e)}), 500
