import requests
import json
import time
import os
from datetime import datetime

# ============================================================
# Configuration - Read from environment variables
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
API_KEY = os.environ.get("API_KEY", "ftgamer2")

# Tool toggles from environment (true/false)
TOOL_PHONE = os.environ.get("TOOL_PHONE", "false").lower() == "true"
TOOL_AADHAAR = os.environ.get("TOOL_AADHAAR", "false").lower() == "true"
TOOL_AADHAAR_FAMILY = os.environ.get("TOOL_AADHAAR_FAMILY", "false").lower() == "true"
TOOL_EMAIL = os.environ.get("TOOL_EMAIL", "false").lower() == "true"
TOOL_VEHICLE = os.environ.get("TOOL_VEHICLE", "false").lower() == "true"
TOOL_GITHUB = os.environ.get("TOOL_GITHUB", "false").lower() == "true"
TOOL_INSTAGRAM = os.environ.get("TOOL_INSTAGRAM", "false").lower() == "true"
TOOL_TG_USER = os.environ.get("TOOL_TG_USER", "false").lower() == "true"
TOOL_PAN = os.environ.get("TOOL_PAN", "false").lower() == "true"
TOOL_TG_ID = os.environ.get("TOOL_TG_ID", "false").lower() == "true"
TOOL_SMS_BOMBER = os.environ.get("TOOL_SMS_BOMBER", "false").lower() == "true"

EXPIRY_DATE_STR = os.environ.get("EXPIRY_DATE", "")

# API Endpoints
PHONE_API = "https://ft-osint-api.duckdns.org/api/number"
AADHAR_API = "https://ft-osint-api.duckdns.org/api/aadhar"
AADHAR_FAMILY_API = "https://ft-osint-api.duckdns.org/api/adharfamily"
EMAIL_API = "https://ft-osint-api.duckdns.org/api/email"
VEHICLE_API = "https://ft-osint-api.duckdns.org/api/vehicle"
GITHUB_API = "https://ft-osint-api.duckdns.org/api/git"
INSTA_API = "https://ft-osint-api.duckdns.org/api/insta"
TG_USER_API = "https://ft-osint-api.duckdns.org/api/tg"
TG_ID_API = "https://ft-osint-api.duckdns.org/api/tgidinfo"
PAN_API = "https://ft-osint-api.duckdns.org/api/pan"
SMS_BOMBER_API = "https://ft-osint-api.duckdns.org/api/bomber"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ============================================================
# Expiry Check
# ============================================================

def check_expiry():
    if not EXPIRY_DATE_STR:
        return True
    try:
        expiry = datetime.strptime(EXPIRY_DATE_STR, "%Y-%m-%d")
        return datetime.now() <= expiry
    except:
        return True

# ============================================================
# Helper Functions
# ============================================================

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"limit": 100, "timeout": 30}
    if offset is not None:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] get_updates: {e}")
        return {"ok": False, "result": []}

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] send_message: {e}")
        return {"ok": False}

def format_api_response(data):
    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    return f"<pre>{formatted_json}</pre>"

def call_api(url, params):
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# Validation Functions
# ============================================================

def is_valid_phone(text):
    return text and text.isdigit() and len(text) == 10

def is_valid_aadhar(text):
    return text and text.isdigit() and len(text) == 12

def is_valid_email(text):
    return text and "@" in text and "." in text.split("@")[-1]

def is_valid_vehicle(text):
    return text and len(text) >= 5

def is_valid_username(text):
    return text and len(text) >= 1 and " " not in text

def is_valid_pan(text):
    return text and len(text) == 10

def is_valid_tg_id(text):
    return text and text.isdigit()

# ============================================================
# Build Keyboard Dynamically
# ============================================================

def create_keyboard():
    keyboard = []
    row = []

    tools_list = [
        (TOOL_PHONE, "📱 Phone Lookup"),
        (TOOL_AADHAAR, "🆔 Aadhaar Lookup"),
        (TOOL_AADHAAR_FAMILY, "👨‍👩‍👧 Aadhaar Family"),
        (TOOL_EMAIL, "📧 Email Info"),
        (TOOL_VEHICLE, "🚗 Vehicle Lookup"),
        (TOOL_GITHUB, "🐙 GitHub Lookup"),
        (TOOL_INSTAGRAM, "📸 Instagram Info"),
        (TOOL_TG_USER, "✈️ Telegram Info"),
        (TOOL_PAN, "🪪 PAN → GST"),
        (TOOL_TG_ID, "🆔 Telegram ID"),
        (TOOL_SMS_BOMBER, "💥 SMS Bomber"),
    ]

    for enabled, label in tools_list:
        if enabled:
            row.append({"text": label})
            if len(row) == 2:
                keyboard.append(row)
                row = []

    if row:
        keyboard.append(row)

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ============================================================
# Main Bot Logic
# ============================================================

def main():
    print("=" * 60)
    print("FT-OSINT Bot Started on Render")
    print(f"Token: {BOT_TOKEN[:20]}...")
    print(f"Admin: {ADMIN_CHAT_ID}")
    print("=" * 60)

    if not BOT_TOKEN:
        print("[FATAL] BOT_TOKEN not set!")
        return

    offset = None
    waiting_for = {}

    while True:
        try:
            # Check expiry
            if not check_expiry():
                print("[EXPIRED] Bot expired! Stopping...")
                try:
                    send_message(ADMIN_CHAT_ID, "❌ Bot expired! Please renew.")
                except:
                    pass
                break

            updates = get_updates(offset)

            if not updates.get("ok"):
                time.sleep(2)
                continue

            result = updates.get("result", [])

            for update in result:
                update_id = update.get("update_id")
                offset = update_id + 1

                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")

                if not chat_id or text is None:
                    continue

                # Admin notification
                if text == "/start" and ADMIN_CHAT_ID:
                    try:
                        send_message(ADMIN_CHAT_ID, f"👤 New user started bot: {chat_id}")
                    except:
                        pass

                # /start command
                if text == "/start":
                    welcome = (
                        "👋 <b>Welcome to FT-OSINT Bot!</b>

"
                        "🔍 Select a tool below to begin!"
                    )
                    keyboard = create_keyboard()
                    send_message(chat_id, welcome, keyboard)
                    waiting_for.pop(chat_id, None)
                    continue

                # Tool Buttons
                if TOOL_PHONE and text == "📱 Phone Lookup":
                    send_message(chat_id, "📞 Send 10 digit mobile number:
Example: <code>9876543210</code>")
                    waiting_for[chat_id] = "phone"
                    continue

                if TOOL_AADHAAR and text == "🆔 Aadhaar Lookup":
                    send_message(chat_id, "🆔 Send 12 digit Aadhaar number:
Example: <code>393933081942</code>")
                    waiting_for[chat_id] = "aadhaar"
                    continue

                if TOOL_AADHAAR_FAMILY and text == "👨‍👩‍👧 Aadhaar Family":
                    send_message(chat_id, "👨‍👩‍👧 Send 12 digit Aadhaar number for family lookup:
Example: <code>984154610245</code>")
                    waiting_for[chat_id] = "aadhaar_family"
                    continue

                if TOOL_EMAIL and text == "📧 Email Info":
                    send_message(chat_id, "📧 Send email address:
Example: <code>airtel123@gmail.com</code>")
                    waiting_for[chat_id] = "email"
                    continue

                if TOOL_VEHICLE and text == "🚗 Vehicle Lookup":
                    send_message(chat_id, "🚗 Send vehicle number:
Example: <code>MH02FZ0555</code>")
                    waiting_for[chat_id] = "vehicle"
                    continue

                if TOOL_GITHUB and text == "🐙 GitHub Lookup":
                    send_message(chat_id, "🐙 Send GitHub username:
Example: <code>ftgamer2</code>")
                    waiting_for[chat_id] = "github"
                    continue

                if TOOL_INSTAGRAM and text == "📸 Instagram Info":
                    send_message(chat_id, "📸 Send Instagram username:
Example: <code>cristiano</code>")
                    waiting_for[chat_id] = "instagram"
                    continue

                if TOOL_TG_USER and text == "✈️ Telegram Info":
                    send_message(chat_id, "✈️ Send Telegram username (without @):
Example: <code>username</code>")
                    waiting_for[chat_id] = "tg_user"
                    continue

                if TOOL_PAN and text == "🪪 PAN → GST":
                    send_message(chat_id, "🪪 Send 10 character PAN number:
Example: <code>ANXPV7978A</code>")
                    waiting_for[chat_id] = "pan"
                    continue

                if TOOL_TG_ID and text == "🆔 Telegram ID":
                    send_message(chat_id, "🆔 Send Telegram numeric ID:
Example: <code>7530266953</code>")
                    waiting_for[chat_id] = "tg_id"
                    continue

                if TOOL_SMS_BOMBER and text == "💥 SMS Bomber":
                    send_message(chat_id, "💥 Send 10 digit phone number for SMS bombing:
Example: <code>9876543210</code>")
                    waiting_for[chat_id] = "sms_bomber"
                    continue

                # Handle Input
                if chat_id in waiting_for:
                    state = waiting_for[chat_id]

                    if state == "phone" and TOOL_PHONE:
                        if is_valid_phone(text):
                            send_message(chat_id, "🔍 Looking up phone number...")
                            result = call_api(PHONE_API, {"key": API_KEY, "num": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid! Send 10-digit number.
Example: <code>9876543210</code>")

                    elif state == "aadhaar" and TOOL_AADHAAR:
                        if is_valid_aadhar(text):
                            send_message(chat_id, "🔍 Looking up Aadhaar...")
                            result = call_api(AADHAR_API, {"key": API_KEY, "num": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid! Send 12-digit number.
Example: <code>393933081942</code>")

                    elif state == "aadhaar_family" and TOOL_AADHAAR_FAMILY:
                        if is_valid_aadhar(text):
                            send_message(chat_id, "🔍 Looking up Aadhaar family...")
                            result = call_api(AADHAR_FAMILY_API, {"key": API_KEY, "num": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid! Send 12-digit number.
Example: <code>984154610245</code>")

                    elif state == "email" and TOOL_EMAIL:
                        if is_valid_email(text):
                            send_message(chat_id, "🔍 Looking up email...")
                            result = call_api(EMAIL_API, {"key": API_KEY, "email": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid email!
Example: <code>airtel123@gmail.com</code>")

                    elif state == "vehicle" and TOOL_VEHICLE:
                        if is_valid_vehicle(text):
                            send_message(chat_id, "🔍 Looking up vehicle...")
                            result = call_api(VEHICLE_API, {"key": API_KEY, "vehicle": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid vehicle number!
Example: <code>MH02FZ0555</code>")

                    elif state == "github" and TOOL_GITHUB:
                        if is_valid_username(text):
                            send_message(chat_id, "🔍 Looking up GitHub...")
                            result = call_api(GITHUB_API, {"key": API_KEY, "username": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid username!
Example: <code>ftgamer2</code>")

                    elif state == "instagram" and TOOL_INSTAGRAM:
                        if is_valid_username(text):
                            send_message(chat_id, "🔍 Looking up Instagram...")
                            result = call_api(INSTA_API, {"key": API_KEY, "username": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid username!
Example: <code>cristiano</code>")

                    elif state == "tg_user" and TOOL_TG_USER:
                        if is_valid_username(text):
                            send_message(chat_id, "🔍 Looking up Telegram info...")
                            result = call_api(TG_USER_API, {"key": API_KEY, "info": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid username!
Example: <code>username</code>")

                    elif state == "pan" and TOOL_PAN:
                        if is_valid_pan(text):
                            send_message(chat_id, "🔍 Looking up PAN → GST...")
                            result = call_api(PAN_API, {"key": API_KEY, "pan": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid PAN! 10 chars required.
Example: <code>ANXPV7978A</code>")

                    elif state == "tg_id" and TOOL_TG_ID:
                        if is_valid_tg_id(text):
                            send_message(chat_id, "🔍 Looking up Telegram ID...")
                            result = call_api(TG_ID_API, {"key": API_KEY, "id": text})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid ID! Numbers only.
Example: <code>7530266953</code>")

                    elif state == "sms_bomber" and TOOL_SMS_BOMBER:
                        if is_valid_phone(text):
                            send_message(chat_id, "💥 Starting SMS bomber (100 messages)...")
                            result = call_api(SMS_BOMBER_API, {"key": API_KEY, "number": text, "counter": 100})
                            send_message(chat_id, format_api_response(result))
                            waiting_for.pop(chat_id, None)
                        else:
                            send_message(chat_id, "❌ Invalid! Send 10-digit number.
Example: <code>9876543210</code>")

                    continue

                # Fallback
                fallback = "I didn't understand. Use /start or select a tool from the keyboard."
                send_message(chat_id, fallback)

            if not result:
                time.sleep(1)

        except KeyboardInterrupt:
            print("
[STOP] Bot stopped by user.")
            break
        except Exception as e:
            print(f"[ERROR] Main loop: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
