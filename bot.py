import os
import logging
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

# In-memory database to track user files (In production, use a real database like MongoDB or SQLite)
# Structure: { chat_id: { "files": [filename1, filename2, ...], "status": "idle" } }
USER_DATA = {}

# Keyboard Menu Layout
MAIN_MENU = [
    [KeyboardButton("📤 Upload File"), KeyboardButton("🔍 Check Files")],
    [KeyboardButton("🚀 Start Bot"), KeyboardButton("🔄 Restart Bot")],
    [KeyboardButton("🗑️ Delete Bot")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and displays user profile info."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Initialize user slot data if not exists
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": [], "status": "idle"}

    # Fetch User Profile Photo
    profile_photos = await context.bot.get_user_profile_photos(user_id=user.id, limit=1)
    
    profile_text = (
        f"👋 *Welcome to the VERNEX HOSTING BOT!*\n\n"
        f"👤 *Your Profile Info:*\n"
        f"┣ 📛 *Name:* {user.first_name} {user.last_name or ''}\n"
        f"┣ 🆔 *Chat ID:* `{chat_id}`\n"
        f"┗ 🏷️ *Username:* @{user.username or 'None'}\n\n"
        f"Use the menu below to manage your bot deployments. (Max 3 files allowed)"
    )

    if profile_photos.total_count > 0:
        # Send profile info alongside their profile photo
        photo_file_id = profile_photos.photos[0][-1].file_id
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo_file_id,
            caption=profile_text,
            parse_mode="Markdown",
            reply_markup=REPLY_MARKUP
        )
    else:
        # Fallback if user has no profile picture
        await update.message.reply_text(
            text=profile_text,
            parse_mode="Markdown",
            reply_markup=REPLY_MARKUP
        )

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles menu button clicks."""
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {"files": [], "status": "idle"}

    if text == "📤 Upload File":
        slots_left = 3 - len(USER_DATA[chat_id]["files"])
        if slots_left <= 0:
            await update.message.reply_text("❌ You have reached your limit of 3 files! Please delete a bot first.")
            return
        
        USER_DATA[chat_id]["status"] = "awaiting_file"
        await update.message.reply_text(f"📝 Please send your file (`.py`, `.php`, `.js`). You have *{slots_left}* slots remaining.", parse_mode="Markdown")

    elif text == "🔍 Check Files":
        files = USER_DATA[chat_id]["files"]
        if not files:
            await update.message.reply_text("📭 You haven't uploaded any files yet.")
        else:
            file_list = "\n".join([f"🔹 {idx+1}. {name}" for idx, name in enumerate(files)])
            await update.message.reply_text(f"📂 *Your Uploaded Files (Active Slots):*\n{file_list}", parse_mode="Markdown")

    elif text == "🚀 Start Bot":
        if not USER_DATA[chat_id]["files"]:
            await update.message.reply_text("❌ No files uploaded to host. Please upload a file first.")
        else:
            await update.message.reply_text("⚡ *Deploying to Vercel...* Please wait.", parse_mode="Markdown")
            # Triggering actual Vercel deployment would happen here via API call

    elif text == "🔄 Restart Bot":
        await update.message.reply_text("🔄 Restarting your Vercel deployment context...")

    elif text == "🗑️ Delete Bot":
        USER_DATA[chat_id]["files"] = []
        await update.message.reply_text("🗑️ All deployed bot configurations cleared! Your 3 slots are now reset.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes uploaded files (.py, .php, .js) if the user is in the uploading state."""
    chat_id = update.effective_chat.id
    
    if chat_id not in USER_DATA or USER_DATA[chat_id]["status"] != "awaiting_file":
        return

    document = update.message.document
    filename = document.file_name
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ['.py', '.php', '.js']:
        await update.message.reply_text("❌ Invalid format! Only `.py`, `.php`, and `.js` code files are accepted.")
        return

    if len(USER_DATA[chat_id]["files"]) >= 3:
        await update.message.reply_text("❌ Upload failed. Max limit of 3 files reached.")
        USER_DATA[chat_id]["status"] = "idle"
        return

    # Download file (Optional: save to disk or push direct to Vercel project context)
    file = await context.bot.get_file(document.file_id)
    # await file.download_to_drive(filename) 

    # Save to user's virtual slots
    USER_DATA[chat_id]["files"].append(filename)
    USER_DATA[chat_id]["status"] = "idle"

    await update.message.reply_text(
        f"✅ *File uploaded successfully!*\n📦 Name: `{filename}`\n Slots filled: {len(USER_DATA[chat_id]['files'])}/3",
        parse_mode="Markdown",
        reply_markup=REPLY_MARKUP
    )

def main():
    # Replace with your actual Master Bot token from @BotFather
    TOKEN = "YOUR_MASTER_BOT_TOKEN"
    
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Run the bot
    print("Master Host Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
