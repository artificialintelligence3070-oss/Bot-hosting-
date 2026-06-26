import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Virtual database tracking user files/deployments
USER_DATA = {}

# Menu buttons
MAIN_MENU = [
    [KeyboardButton("📤 Upload File"), KeyboardButton("🔍 Check Files")],
    [KeyboardButton("🚀 Start Bot"), KeyboardButton("🔄 Restart Bot")],
    [KeyboardButton("🗑️ Delete Bot")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered on /start. Displays profile data & avatar layout."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    profile_photos = await context.bot.get_user_profile_photos(user_id=user.id, limit=1)
    
    profile_text = (
        f"👋 *Welcome to the Automated Vercel Hosting System!*\n\n"
        f"👤 *Your Profile Metadata:*\n"
        f"┣ 📛 *Name:* {user.first_name} {user.last_name or ''}\n"
        f"┣ 🆔 *Chat ID:* `{chat_id}`\n"
        f"┗ 🏷️ *Username:* @{user.username or 'None'}\n\n"
        f"Slot Allocations available: *{3 - len(USER_DATA[chat_id]['files'])} / 3 remaining*"
    )

    if profile_photos.total_count > 0:
        photo_file_id = profile_photos.photos[0][-1].file_id
        await context.bot.send_photo(
            chat_id=chat_id, photo=photo_file_id, caption=profile_text,
            parse_mode="Markdown", reply_markup=REPLY_MARKUP
        )
    else:
        await update.message.reply_text(text=profile_text, parse_mode="Markdown", reply_markup=REPLY_MARKUP)

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes persistent layout buttons."""
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": {}, "status": "idle", "deployment_url": None}

    if text == "📤 Upload File":
        if len(USER_DATA[chat_id]["files"]) >= 3:
            await update.message.reply_text("❌ All 3 hosting slots are full! Delete active instances to free space.")
            return
        USER_DATA[chat_id]["status"] = "awaiting_file"
        await update.message.reply_text("📝 Drop your text/code attachment file (`.py` or `.js`). Only 3 allowed:")

    elif text == "🔍 Check Files":
        files = USER_DATA[chat_id]["files"]
        url = USER_DATA[chat_id]["deployment_url"]
        if not files:
            await update.message.reply_text("📭 Your instance cache is completely clean.")
        else:
            file_list = "\n".join([f"📄 `{name}`" for name in files.keys()])
            status_url = f"\n\n🔗 *Live URL:* {url}" if url else "\n\n⚠️ *Status:* Not deployed yet. Press 🚀 Start Bot."
            await update.message.reply_text(f"📂 *Your Files on Server:*\n{file_list}{status_url}", parse_mode="Markdown")

    elif text == "🚀 Start Bot":
        if not USER_DATA[chat_id]["files"]:
            await update.message.reply_text("❌ There are zero source files found to register. Upload software first.")
            return
        
        await update.message.reply_text("⚡ *Initiating deployment protocol with Vercel APIs... Please stand by.*")
        
        # Trigger remote Vercel Deployment compilation
        url = deploy_to_vercel(chat_id)
        if url:
            USER_DATA[chat_id]["deployment_url"] = url
            await update.message.reply_text(f"🎉 *Success! Your bot code has been compiled and deployed live to Vercel:*\n\n🌐 {url}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Vercel deployment error. Check configuration tokens or syntax properties.")

    elif text == "🔄 Restart Bot":
        if not USER_DATA[chat_id]["deployment_url"]:
            await update.message.reply_text("❌ There is no active live container found to restart.")
        else:
            await update.message.reply_text("🔄 *Re-triggering deployment hook to clear server caching modules...*")
            url = deploy_to_vercel(chat_id)
            await update.message.reply_text(f"✅ Instance reboot complete! App is live: \n {url}")

    elif text == "🗑️ Delete Bot":
        USER_DATA[chat_id]["files"] = {}
        USER_DATA[chat_id]["deployment_url"] = None
        await update.message.reply_text("🗑️ Active host structures completely removed. Slots reset to 0/3.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intercerts files, reads structure, and adds it to the user storage space dynamically."""
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA or USER_DATA[chat_id]["status"] != "awaiting_file":
        return

    document = update.message.document
    filename = document.file_name
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.py', '.js']:
        await update.message.reply_text("❌ Target runtime architecture mismatch! Only `.py` and `.js` servers are handled right now.")
        return

    # In-memory download sequence to extract the file text data
    file_obj = await context.bot.get_file(document.file_id)
    file_bytes = await file_obj.download_as_bytearray()
    file_content = file_bytes.decode('utf-8')

    # Save to dynamic storage mapping
    USER_DATA[chat_id]["files"][filename] = file_content
    USER_DATA[chat_id]["status"] = "idle"

    await update.message.reply_text(
        f"✅ *File received & validated!*\n📦 Name: `{filename}`\n📊 Used capacity: {len(USER_DATA[chat_id]['files'])}/3 slots.",
        parse_mode="Markdown", reply_markup=REPLY_MARKUP
    )

def deploy_to_vercel(chat_id: int) -> str:
    """Uses the Vercel REST Deployment Engine to dynamically compile code structures."""
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        logger.error("VERCEL_TOKEN environment variable is missing!")
        return None

    user_files = USER_DATA[chat_id]["files"]
    
    # 1. Structure the file tree payload required by the Vercel Manifest specification
    payload_files = []
    
    # Inject user-uploaded scripts into payload
    main_file = None
    for fname, content in user_files.items():
        payload_files.append({"file": fname, "data": content})
        if main_file is None:
            main_file = fname  # Set first uploaded file as the default routing point

    if not main_file:
        return None

    # 2. Build explicit vercel.json configurations matching their precise execution target
    ext = os.path.splitext(main_file)[1].lower()
    runtime = "@vercel/python" if ext == ".py" else "@vercel/node"
    
    vercel_config = {
        "version": 2,
        "builds": [{"src": main_file, "use": runtime}],
        "routes": [{"src": "/(.*)", "dest": main_file}]
    }
    
    import json
    payload_files.append({"file": "vercel.json", "data": json.dumps(vercel_config)})

    # Add minimum default requirements.txt if runtime is python
    if ext == ".py":
        payload_files.append({"file": "requirements.txt", "data": "requests==2.32.3\npython-telegram-bot==21.3\n"})

    # 3. Deliver requests payload into Vercel Deployment Matrix
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    body = {
        "name": f"user-bot-{chat_id}",
        "files": payload_files,
        "projectSettings": {"framework": None}
    }

    try:
        response = requests.post("https://api.vercel.com/v13/deployments", headers=headers, json=body)
        res_data = response.json()
        if response.status_code in [200, 201]:
            return f"https://{res_data['url']}"
        else:
            logger.error(f"Vercel Error Output: {res_data}")
            return None
    except Exception as e:
        logger.error(f"Failed handling deployment network stack: {e}")
        return None

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "8842248531:AAFLjUKst9mYf2IJgP2j4sSK4p_B5tymkik")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🚀 Auto-Hosting SaaS System Active...")
    application.run_polling()

if __name__ == "__main__":
    main()
