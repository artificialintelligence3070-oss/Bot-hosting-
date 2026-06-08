from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import requests
import json
import time
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store running bots in memory
running_bots = {}

# ============================================================
# Bot Runner Class
# ============================================================

class TelegramBot:
    def __init__(self, bot_id, token, chat_id, tools, expiry=None):
        self.bot_id = bot_id
        self.token = token
        self.chat_id = chat_id
        self.tools = tools
        self.expiry = expiry
        self.running = False
        self.thread = None
        self.offset = None
        self.waiting_for = {}
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.api_key = "ftgamer2"

        # API Endpoints
        self.apis = {
            'phone': ('https://ft-osint-api.duckdns.org/api/number', 'num'),
            'aadhaar': ('https://ft-osint-api.duckdns.org/api/aadhar', 'num'),
            'aadhaar_family': ('https://ft-osint-api.duckdns.org/api/adharfamily', 'num'),
            'email': ('https://ft-osint-api.duckdns.org/api/email', 'email'),
            'vehicle': ('https://ft-osint-api.duckdns.org/api/vehicle', 'vehicle'),
            'github': ('https://ft-osint-api.duckdns.org/api/git', 'username'),
            'instagram': ('https://ft-osint-api.duckdns.org/api/insta', 'username'),
            'tg_user': ('https://ft-osint-api.duckdns.org/api/tg', 'info'),
            'pan': ('https://ft-osint-api.duckdns.org/api/pan', 'pan'),
            'tg_id': ('https://ft-osint-api.duckdns.org/api/tgidinfo', 'id'),
            'sms_bomber': ('https://ft-osint-api.duckdns.org/api/bomber', 'number'),
        }

        # Validation functions
        self.validators = {
            'phone': lambda t: t and t.isdigit() and len(t) == 10,
            'aadhaar': lambda t: t and t.isdigit() and len(t) == 12,
            'aadhaar_family': lambda t: t and t.isdigit() and len(t) == 12,
            'email': lambda t: t and "@" in t and "." in t.split("@")[-1],
            'vehicle': lambda t: t and len(t) >= 5,
            'github': lambda t: t and len(t) >= 1 and " " not in t,
            'instagram': lambda t: t and len(t) >= 1 and " " not in t,
            'tg_user': lambda t: t and len(t) >= 1,
            'pan': lambda t: t and len(t) == 10,
            'tg_id': lambda t: t and t.isdigit(),
            'sms_bomber': lambda t: t and t.isdigit() and len(t) == 10,
        }

        # Tool prompts
        self.prompts = {
            'phone': ('📱 Phone Lookup', '📞 Send 10 digit mobile number:\nExample: <code>9876543210</code>'),
            'aadhaar': ('🆔 Aadhaar Lookup', '🆔 Send 12 digit Aadhaar number:\nExample: <code>393933081942</code>'),
            'aadhaar_family': ('👨‍👩‍👧 Aadhaar Family', '👨‍👩‍👧 Send 12 digit Aadhaar number:\nExample: <code>984154610245</code>'),
            'email': ('📧 Email Info', '📧 Send email address:\nExample: <code>airtel123@gmail.com</code>'),
            'vehicle': ('🚗 Vehicle Lookup', '🚗 Send vehicle number:\nExample: <code>MH02FZ0555</code>'),
            'github': ('🐙 GitHub Lookup', '🐙 Send GitHub username:\nExample: <code>ftgamer2</code>'),
            'instagram': ('📸 Instagram Info', '📸 Send Instagram username:\nExample: <code>cristiano</code>'),
            'tg_user': ('✈️ Telegram Info', '✈️ Send Telegram username (without @):\nExample: <code>username</code>'),
            'pan': ('🪪 PAN → GST', '🪪 Send 10 character PAN number:\nExample: <code>ANXPV7978A</code>'),
            'tg_id': ('🆔 Telegram ID', '🆔 Send Telegram numeric ID:\nExample: <code>7530266953</code>'),
            'sms_bomber': ('💥 SMS Bomber', '💥 Send 10 digit phone number:\nExample: <code>9876543210</code>'),
        }

    def check_expiry(self):
        if not self.expiry:
            return True
        try:
            return datetime.now() <= datetime.strptime(self.expiry, "%Y-%m-%d")
        except:
            return True

    def send_message(self, chat_id, text, reply_markup=None):
        try:
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            requests.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
        except Exception as e:
            print(f"[Bot {self.bot_id}] Send error: {e}")

    def get_updates(self):
        try:
            params = {"limit": 100, "timeout": 30}
            if self.offset:
                params["offset"] = self.offset
            resp = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=35)
            return resp.json()
        except Exception as e:
            print(f"[Bot {self.bot_id}] Get updates error: {e}")
            return {"ok": False, "result": []}

    def call_api(self, url, params):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            try:
                return resp.json()
            except:
                return {"response": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def format_response(self, data):
        return f"<pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>"

    def create_keyboard(self):
        keyboard = []
        row = []
        for tool_key in self.tools:
            if tool_key in self.prompts:
                row.append({"text": self.prompts[tool_key][0]})
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        if row:
            keyboard.append(row)
        return {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": False}

    def run(self):
        self.running = True
        print(f"[Bot {self.bot_id}] Started")
        self.send_message(self.chat_id, f"✅ Bot started!\nTools: {len(self.tools)}")

        while self.running:
            try:
                if not self.check_expiry():
                    self.send_message(self.chat_id, "❌ Bot expired! Contact admin.")
                    break

                updates = self.get_updates()
                if not updates.get("ok"):
                    time.sleep(2)
                    continue

                for update in updates.get("result", []):
                    self.offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")

                    if not chat_id or text is None:
                        continue

                    # /start
                    if text == "/start":
                        welcome = "👋 <b>Welcome to FT-OSINT Bot!</b>\n\n🔍 Select a tool below!"
                        self.send_message(chat_id, welcome, self.create_keyboard())
                        self.waiting_for.pop(chat_id, None)
                        continue

                    # Tool buttons
                    for tool_key in self.tools:
                        if tool_key in self.prompts and text == self.prompts[tool_key][0]:
                            self.send_message(chat_id, self.prompts[tool_key][1])
                            self.waiting_for[chat_id] = tool_key
                            break
                    else:
                        # Handle input
                        if chat_id in self.waiting_for:
                            state = self.waiting_for[chat_id]
                            if state in self.validators and self.validators[state](text):
                                self.send_message(chat_id, f"🔍 Processing...")
                                url, param = self.apis[state]
                                params = {"key": self.api_key, param: text}
                                if state == 'sms_bomber':
                                    params["counter"] = 100
                                result = self.call_api(url, params)
                                self.send_message(chat_id, self.format_response(result))
                                self.waiting_for.pop(chat_id, None)
                            else:
                                error_msg = {
                                    'phone': '❌ Invalid! Send 10-digit number.',
                                    'aadhaar': '❌ Invalid! Send 12-digit number.',
                                    'aadhaar_family': '❌ Invalid! Send 12-digit number.',
                                    'email': '❌ Invalid email!',
                                    'vehicle': '❌ Invalid vehicle number!',
                                    'github': '❌ Invalid username!',
                                    'instagram': '❌ Invalid username!',
                                    'tg_user': '❌ Invalid username!',
                                    'pan': '❌ Invalid PAN! 10 chars required.',
                                    'tg_id': '❌ Invalid ID! Numbers only.',
                                    'sms_bomber': '❌ Invalid! Send 10-digit number.',
                                }
                                self.send_message(chat_id, error_msg.get(state, '❌ Invalid input!'))
                            continue

                        # Fallback
                        self.send_message(chat_id, "I didn't understand. Use /start or select a tool.")

                if not updates.get("result"):
                    time.sleep(1)

            except Exception as e:
                print(f"[Bot {self.bot_id}] Loop error: {e}")
                time.sleep(3)

        self.running = False
        print(f"[Bot {self.bot_id}] Stopped")

    def start(self):
        if not self.running:
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        self.running = False
        return True

# ============================================================
# Flask Routes
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>FT-OSINT Bot Hosting Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        .bg-3d {
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 0; pointer-events: none;
        }
        .cube {
            position: absolute; width: 60px; height: 60px;
            border: 2px solid rgba(102, 126, 234, 0.12);
            animation: float 8s infinite ease-in-out;
            transform-style: preserve-3d;
        }
        .cube:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
        .cube:nth-child(2) { top: 20%; left: 80%; animation-delay: 1s; }
        .cube:nth-child(3) { top: 60%; left: 15%; animation-delay: 2s; }
        .cube:nth-child(4) { top: 70%; left: 70%; animation-delay: 3s; }
        .cube:nth-child(5) { top: 40%; left: 50%; animation-delay: 4s; }
        .cube:nth-child(6) { top: 85%; left: 30%; animation-delay: 5s; }
        .cube:nth-child(7) { top: 15%; left: 45%; animation-delay: 1.5s; }
        .cube:nth-child(8) { top: 50%; left: 85%; animation-delay: 2.5s; }
        @keyframes float {
            0%, 100% { transform: translateY(0) rotateX(0deg) rotateY(0deg); }
            25% { transform: translateY(-20px) rotateX(90deg) rotateY(45deg); }
            50% { transform: translateY(0) rotateX(180deg) rotateY(90deg); }
            75% { transform: translateY(20px) rotateX(270deg) rotateY(135deg); }
        }
        .container {
            position: relative; z-index: 1;
            max-width: 500px; margin: 0 auto; padding: 20px;
        }
        .header {
            text-align: center; padding: 30px 0 20px;
        }
        .logo {
            width: 80px; height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 15px; font-size: 36px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .header h1 { font-size: 24px; color: #2d3748; font-weight: 700; }
        .header p { color: #718096; font-size: 14px; margin-top: 5px; }
        .section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px; padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.05);
            animation: slideUp 0.5s ease-out;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .section-title {
            font-size: 16px; font-weight: 700; color: #2d3748;
            margin-bottom: 15px;
            display: flex; align-items: center; gap: 8px;
        }
        .section-title .icon { font-size: 20px; }
        .input-group { margin-bottom: 15px; }
        .input-group label {
            display: block; font-size: 13px; font-weight: 600;
            color: #4a5568; margin-bottom: 6px;
        }
        .input-group input {
            width: 100%; padding: 14px 16px;
            border: 2px solid #e2e8f0; border-radius: 12px;
            font-size: 14px; transition: all 0.3s; background: #f7fafc;
        }
        .input-group input:focus {
            outline: none; border-color: #667eea; background: #fff;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .input-group .hint {
            font-size: 11px; color: #a0aec0; margin-top: 4px;
        }
        .tools-grid {
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
        }
        .tool-card {
            padding: 14px; border: 2px solid #e2e8f0;
            border-radius: 12px; cursor: pointer;
            text-align: center; transition: all 0.3s;
            background: #f7fafc; position: relative; overflow: hidden;
            user-select: none;
        }
        .tool-card:hover {
            border-color: #667eea; transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }
        .tool-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .tool-card .tool-icon { font-size: 28px; margin-bottom: 6px; display: block; }
        .tool-card .tool-name { font-size: 12px; font-weight: 600; }
        .all-tools-toggle {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; padding: 12px; margin-bottom: 15px;
            background: #edf2f7; border-radius: 10px;
            cursor: pointer; transition: all 0.3s;
        }
        .all-tools-toggle.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .toggle-switch {
            width: 44px; height: 24px; background: #cbd5e0;
            border-radius: 12px; position: relative; transition: all 0.3s;
        }
        .toggle-switch::after {
            content: ''; position: absolute;
            width: 20px; height: 20px; background: white;
            border-radius: 50%; top: 2px; left: 2px;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .all-tools-toggle.active .toggle-switch { background: rgba(255,255,255,0.3); }
        .all-tools-toggle.active .toggle-switch::after { left: 22px; }
        .expiry-options {
            display: flex; gap: 10px; margin-bottom: 15px;
        }
        .expiry-btn {
            flex: 1; padding: 12px; border: 2px solid #e2e8f0;
            border-radius: 10px; background: #f7fafc;
            cursor: pointer; text-align: center;
            font-size: 13px; font-weight: 600; transition: all 0.3s;
        }
        .expiry-btn.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .expiry-input { display: none; }
        .expiry-input.show { display: block; animation: fadeIn 0.3s; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .btn {
            width: 100%; padding: 16px; border: none;
            border-radius: 12px; font-size: 15px; font-weight: 700;
            cursor: pointer; transition: all 0.3s;
            display: flex; align-items: center; justify-content: center;
            gap: 8px; margin-bottom: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white; box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
        }
        .btn-danger {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white; box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);
        }
        .btn:disabled {
            opacity: 0.6; cursor: not-allowed;
            transform: none !important;
        }
        .status-badge {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 12px; border-radius: 20px;
            font-size: 12px; font-weight: 700;
        }
        .status-running { background: #c6f6d5; color: #22543d; }
        .status-stopped { background: #fed7d7; color: #742a2a; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; animation: blink 1.5s infinite; }
        .status-running .status-dot { background: #48bb78; }
        .status-stopped .status-dot { background: #f56565; animation: none; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .history-list { max-height: 300px; overflow-y: auto; }
        .history-item {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px; border-bottom: 1px solid #edf2f7;
            transition: all 0.2s;
        }
        .history-item:hover { background: #f7fafc; border-radius: 8px; }
        .history-item:last-child { border-bottom: none; }
        .history-info { flex: 1; }
        .history-token { font-size: 12px; font-weight: 700; color: #2d3748; font-family: monospace; }
        .history-meta { font-size: 11px; color: #a0aec0; margin-top: 2px; }
        .history-actions { display: flex; gap: 6px; }
        .history-btn {
            padding: 6px 10px; border: none; border-radius: 6px;
            font-size: 11px; font-weight: 700; cursor: pointer;
            transition: all 0.2s;
        }
        .history-btn-start { background: #c6f6d5; color: #22543d; }
        .history-btn-stop { background: #fed7d7; color: #742a2a; }
        .history-btn-delete { background: #e2e8f0; color: #4a5568; }
        .history-btn:hover { transform: scale(1.05); }
        .empty-history { text-align: center; padding: 30px; color: #a0aec0; font-size: 14px; }
        .toast-container {
            position: fixed; top: 20px; right: 20px; z-index: 2000;
            display: flex; flex-direction: column; gap: 10px;
        }
        .toast {
            padding: 14px 20px; border-radius: 10px; color: white;
            font-size: 14px; font-weight: 600;
            animation: toastSlide 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            display: flex; align-items: center; gap: 8px;
        }
        @keyframes toastSlide {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .toast-success { background: linear-gradient(135deg, #48bb78, #38a169); }
        .toast-error { background: linear-gradient(135deg, #f56565, #e53e3e); }
        .toast-info { background: linear-gradient(135deg, #667eea, #764ba2); }
        @media (max-width: 480px) {
            .container { padding: 12px; }
            .section { padding: 15px; border-radius: 12px; }
            .tools-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
            .tool-card { padding: 10px; }
            .tool-card .tool-icon { font-size: 24px; }
            .header h1 { font-size: 20px; }
        }
    </style>
</head>
<body>
    <div class="bg-3d">
        <div class="cube"></div><div class="cube"></div><div class="cube"></div><div class="cube"></div>
        <div class="cube"></div><div class="cube"></div><div class="cube"></div><div class="cube"></div>
    </div>
    <div class="toast-container" id="toastContainer"></div>
    <div class="container">
        <div class="header">
            <div class="logo">🤖</div>
            <h1>FT-OSINT Bot Hosting</h1>
            <p>⚡ Host bots directly on this server - No download needed!</p>
        </div>

        <div class="section">
            <div class="section-title"><span class="icon">⚙️</span>Bot Configuration</div>
            <div class="input-group">
                <label>Telegram Bot Token</label>
                <input type="text" id="botToken" placeholder="Enter bot token from @BotFather">
                <div class="hint">Example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz</div>
            </div>
            <div class="input-group">
                <label>Chat ID (Admin)</label>
                <input type="text" id="chatId" placeholder="Enter your Telegram chat ID">
                <div class="hint">Your personal chat ID for notifications</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title"><span class="icon">🛠️</span>Select Tools</div>
            <div class="all-tools-toggle" id="allToolsToggle" onclick="toggleAllTools()">
                <div class="toggle-switch"></div>
                <span><b>Enable ALL Tools</b> (Lifetime)</span>
            </div>
            <div class="tools-grid" id="toolsGrid">
                <div class="tool-card" data-tool="phone" onclick="toggleTool(this)"><span class="tool-icon">📱</span><span class="tool-name">Phone</span></div>
                <div class="tool-card" data-tool="aadhaar" onclick="toggleTool(this)"><span class="tool-icon">🆔</span><span class="tool-name">Aadhaar</span></div>
                <div class="tool-card" data-tool="aadhaar_family" onclick="toggleTool(this)"><span class="tool-icon">👨‍👩‍👧</span><span class="tool-name">Aadhaar Family</span></div>
                <div class="tool-card" data-tool="email" onclick="toggleTool(this)"><span class="tool-icon">📧</span><span class="tool-name">Email</span></div>
                <div class="tool-card" data-tool="vehicle" onclick="toggleTool(this)"><span class="tool-icon">🚗</span><span class="tool-name">Vehicle</span></div>
                <div class="tool-card" data-tool="github" onclick="toggleTool(this)"><span class="tool-icon">🐙</span><span class="tool-name">GitHub</span></div>
                <div class="tool-card" data-tool="instagram" onclick="toggleTool(this)"><span class="tool-icon">📸</span><span class="tool-name">Instagram</span></div>
                <div class="tool-card" data-tool="tg_user" onclick="toggleTool(this)"><span class="tool-icon">✈️</span><span class="tool-name">Telegram Info</span></div>
                <div class="tool-card" data-tool="pan" onclick="toggleTool(this)"><span class="tool-icon">🪪</span><span class="tool-name">PAN → GST</span></div>
                <div class="tool-card" data-tool="tg_id" onclick="toggleTool(this)"><span class="tool-icon">🆔</span><span class="tool-name">Telegram ID</span></div>
                <div class="tool-card" data-tool="sms_bomber" onclick="toggleTool(this)"><span class="tool-icon">💥</span><span class="tool-name">SMS Bomber</span></div>
            </div>
        </div>

        <div class="section">
            <div class="section-title"><span class="icon">⏰</span>Expiry Settings</div>
            <div class="expiry-options">
                <div class="expiry-btn active" onclick="setExpiry('lifetime')" id="expLifetime">♾️ Lifetime</div>
                <div class="expiry-btn" onclick="setExpiry('custom')" id="expCustom">📅 Custom Date</div>
            </div>
            <div class="input-group expiry-input" id="customExpiryInput">
                <label>Expiry Date</label>
                <input type="date" id="expiryDate">
                <div class="hint">Bot will stop after this date</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title"><span class="icon">🚀</span>Deploy Bot</div>
            <button class="btn btn-primary" id="deployBtn" onclick="deployBot()">
                <span>🚀</span> START BOT ON SERVER
            </button>
            <div id="deployStatus" style="margin-top:10px;font-size:13px;color:#718096;text-align:center;"></div>
        </div>

        <div class="section">
            <div class="section-title"><span class="icon">📜</span>Running Bots</div>
            <div class="history-list" id="botList">
                <div class="empty-history">No bots running. Deploy one above!</div>
            </div>
        </div>
    </div>

    <script>
        let selectedTools = new Set();
        let allToolsEnabled = false;
        let expiryType = 'lifetime';

        const TOOLS = {
            phone: 'Phone', aadhaar: 'Aadhaar', aadhaar_family: 'Aadhaar Family',
            email: 'Email', vehicle: 'Vehicle', github: 'GitHub',
            instagram: 'Instagram', tg_user: 'Telegram Info', pan: 'PAN',
            tg_id: 'Telegram ID', sms_bomber: 'SMS Bomber'
        };

        function toggleTool(el) {
            if (allToolsEnabled) return;
            const t = el.dataset.tool;
            if (selectedTools.has(t)) { selectedTools.delete(t); el.classList.remove('selected'); }
            else { selectedTools.add(t); el.classList.add('selected'); }
        }

        function toggleAllTools() {
            allToolsEnabled = !allToolsEnabled;
            const toggle = document.getElementById('allToolsToggle');
            const cards = document.querySelectorAll('.tool-card');
            if (allToolsEnabled) {
                toggle.classList.add('active');
                selectedTools = new Set(Object.keys(TOOLS));
                cards.forEach(c => c.classList.add('selected'));
            } else {
                toggle.classList.remove('active');
                selectedTools.clear();
                cards.forEach(c => c.classList.remove('selected'));
            }
        }

        function setExpiry(type) {
            expiryType = type;
            document.getElementById('expLifetime').classList.toggle('active', type === 'lifetime');
            document.getElementById('expCustom').classList.toggle('active', type === 'custom');
            document.getElementById('customExpiryInput').classList.toggle('show', type === 'custom');
        }

        function showToast(msg, type) {
            const c = document.getElementById('toastContainer');
            const t = document.createElement('div');
            t.className = 'toast toast-' + type;
            const icons = { success: '✅', error: '❌', info: 'ℹ️' };
            t.innerHTML = '<span>' + icons[type] + '</span> ' + msg;
            c.appendChild(t);
            setTimeout(() => { t.style.animation = 'toastSlide 0.3s reverse'; setTimeout(() => t.remove(), 300); }, 3000);
        }

        function deployBot() {
            const token = document.getElementById('botToken').value.trim();
            const chatId = document.getElementById('chatId').value.trim();
            const tools = allToolsEnabled ? Object.keys(TOOLS) : Array.from(selectedTools);

            if (!token) { showToast('Enter Bot Token!', 'error'); return; }
            if (!chatId) { showToast('Enter Chat ID!', 'error'); return; }
            if (tools.length === 0) { showToast('Select at least one tool!', 'error'); return; }

            const expiry = expiryType === 'custom' ? document.getElementById('expiryDate').value : '';

            document.getElementById('deployStatus').innerHTML = '<span style="color:#667eea;">⏳ Starting bot on server...</span>';

            fetch('/api/deploy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, chat_id: chatId, tools, expiry })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showToast('Bot started on server!', 'success');
                    document.getElementById('deployStatus').innerHTML = '<span style="color:#48bb78;">✅ Bot is running on server!</span>';
                    loadBots();
                } else {
                    showToast(data.error || 'Failed to start bot', 'error');
                    document.getElementById('deployStatus').innerHTML = '<span style="color:#f56565;">❌ ' + (data.error || 'Failed') + '</span>';
                }
            })
            .catch(e => {
                showToast('Server error: ' + e, 'error');
                document.getElementById('deployStatus').innerHTML = '<span style="color:#f56565;">❌ Server not connected</span>';
            });
        }

        function loadBots() {
            fetch('/api/bots')
            .then(r => r.json())
            .then(data => {
                const list = document.getElementById('botList');
                if (data.bots.length === 0) {
                    list.innerHTML = '<div class="empty-history">No bots running. Deploy one above!</div>';
                    return;
                }
                list.innerHTML = data.bots.map(bot => {
                    return '<div class="history-item">' +
                        '<div class="history-info">' +
                        '<div class="history-token">' + bot.token_preview + '</div>' +
                        '<div class="history-meta">' + bot.tools.length + ' tools • ' + bot.expiry + ' • Started: ' + bot.started + '</div>' +
                        '</div>' +
                        '<div class="history-actions">' +
                        '<span class="status-badge ' + (bot.running ? 'status-running' : 'status-stopped') + '">' +
                        '<span class="status-dot"></span>' + (bot.running ? 'Running' : 'Stopped') + '</span>' +
                        '<button class="history-btn ' + (bot.running ? 'history-btn-stop' : 'history-btn-start') + '" onclick="toggleBot('' + bot.id + '')">' +
                        (bot.running ? '⏹️ Stop' : '▶️ Start') + '</button>' +
                        '<button class="history-btn history-btn-delete" onclick="deleteBot('' + bot.id + '')">🗑️</button>' +
                        '</div></div>';
                }).join('');
            });
        }

        function toggleBot(id) {
            fetch('/api/toggle/' + id, { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                showToast(data.message, data.success ? 'info' : 'error');
                loadBots();
            });
        }

        function deleteBot(id) {
            if (!confirm('Delete this bot?')) return;
            fetch('/api/delete/' + id, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                showToast(data.message, data.success ? 'info' : 'error');
                loadBots();
            });
        }

        setInterval(loadBots, 5000);
        loadBots();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    token = data.get('token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    tools = data.get('tools', [])
    expiry = data.get('expiry', '')

    if not token or not chat_id or not tools:
        return jsonify({"success": False, "error": "Missing required fields"})

    bot_id = str(int(time.time()))

    # Stop existing bot with same token
    for bid, bot in list(running_bots.items()):
        if bot.token == token:
            bot.stop()
            del running_bots[bid]

    # Create and start new bot
    bot = TelegramBot(bot_id, token, chat_id, tools, expiry)
    running_bots[bot_id] = bot
    bot.start()

    return jsonify({"success": True, "bot_id": bot_id, "message": "Bot started on server!"})

@app.route('/api/bots', methods=['GET'])
def list_bots():
    bots = []
    for bid, bot in running_bots.items():
        bots.append({
            "id": bid,
            "token_preview": bot.token[:15] + "..." if len(bot.token) > 15 else bot.token,
            "chat_id": bot.chat_id,
            "tools": bot.tools,
            "expiry": bot.expiry or "Lifetime",
            "running": bot.running,
            "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"bots": bots})

@app.route('/api/toggle/<bot_id>', methods=['POST'])
def toggle_bot(bot_id):
    if bot_id not in running_bots:
        return jsonify({"success": False, "error": "Bot not found"})

    bot = running_bots[bot_id]
    if bot.running:
        bot.stop()
        return jsonify({"success": True, "message": "Bot stopped"})
    else:
        bot.start()
        return jsonify({"success": True, "message": "Bot restarted"})

@app.route('/api/delete/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    if bot_id not in running_bots:
        return jsonify({"success": False, "error": "Bot not found"})

    running_bots[bot_id].stop()
    del running_bots[bot_id]
    return jsonify({"success": True, "message": "Bot deleted"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
