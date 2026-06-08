from flask import Flask, request, jsonify, render_template_string
import threading
import requests
import json
import time
import os
from datetime import datetime

app = Flask(__name__)

# Store running bots
running_bots = {}

# ============================================================
# SIMPLE HTML FRONTEND
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FT-OSINT Bot Hosting</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; padding: 30px 0; }
        .header h1 { font-size: 28px; color: #333; }
        .header p { color: #666; margin-top: 10px; }
        .card {
            background: white; border-radius: 12px; padding: 20px;
            margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 { font-size: 18px; color: #333; margin-bottom: 15px; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; font-size: 14px; color: #555; margin-bottom: 5px; font-weight: bold; }
        .input-group input {
            width: 100%; padding: 12px; border: 2px solid #ddd;
            border-radius: 8px; font-size: 14px;
        }
        .input-group input:focus { outline: none; border-color: #667eea; }
        .tools-grid {
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
        }
        .tool-btn {
            padding: 12px; border: 2px solid #ddd; border-radius: 8px;
            cursor: pointer; text-align: center; background: #f8f9fa;
            transition: all 0.3s;
        }
        .tool-btn:hover { border-color: #667eea; }
        .tool-btn.selected {
            border-color: #667eea; background: #667eea; color: white;
        }
        .tool-btn .icon { font-size: 24px; display: block; margin-bottom: 5px; }
        .tool-btn .name { font-size: 12px; font-weight: bold; }
        .toggle-all {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; padding: 12px; margin-bottom: 15px;
            background: #e9ecef; border-radius: 8px; cursor: pointer;
        }
        .toggle-all.active { background: #667eea; color: white; }
        .btn {
            width: 100%; padding: 15px; border: none; border-radius: 8px;
            font-size: 16px; font-weight: bold; cursor: pointer;
            background: #667eea; color: white;
        }
        .btn:hover { background: #5a6fd6; }
        .status { margin-top: 10px; padding: 10px; border-radius: 8px; text-align: center; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .status.loading { background: #fff3cd; color: #856404; }
        .bot-list { margin-top: 15px; }
        .bot-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px; border-bottom: 1px solid #eee;
        }
        .bot-item:last-child { border-bottom: none; }
        .bot-info { flex: 1; }
        .bot-token { font-size: 12px; font-weight: bold; color: #333; }
        .bot-meta { font-size: 11px; color: #666; }
        .bot-actions { display: flex; gap: 5px; }
        .btn-small {
            padding: 6px 12px; border: none; border-radius: 6px;
            font-size: 12px; cursor: pointer;
        }
        .btn-stop { background: #dc3545; color: white; }
        .btn-start { background: #28a745; color: white; }
        .btn-delete { background: #6c757d; color: white; }
        .badge {
            padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;
        }
        .badge.running { background: #d4edda; color: #155724; }
        .badge.stopped { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 FT-OSINT Bot Hosting</h1>
            <p>Host Telegram bots on this server</p>
        </div>

        <div class="card">
            <h2>⚙️ Bot Configuration</h2>
            <div class="input-group">
                <label>Telegram Bot Token</label>
                <input type="text" id="token" placeholder="Enter bot token">
            </div>
            <div class="input-group">
                <label>Chat ID (Admin)</label>
                <input type="text" id="chatId" placeholder="Enter chat ID">
            </div>
        </div>

        <div class="card">
            <h2>🛠️ Select Tools</h2>
            <div class="toggle-all" id="toggleAll" onclick="toggleAll()">
                <span>☐</span> <b>Enable ALL Tools</b>
            </div>
            <div class="tools-grid" id="toolsGrid">
                <div class="tool-btn" data-tool="phone" onclick="toggleTool(this)">
                    <span class="icon">📱</span>
                    <span class="name">Phone</span>
                </div>
                <div class="tool-btn" data-tool="aadhaar" onclick="toggleTool(this)">
                    <span class="icon">🆔</span>
                    <span class="name">Aadhaar</span>
                </div>
                <div class="tool-btn" data-tool="aadhaar_family" onclick="toggleTool(this)">
                    <span class="icon">👨‍👩‍👧</span>
                    <span class="name">Aadhaar Family</span>
                </div>
                <div class="tool-btn" data-tool="email" onclick="toggleTool(this)">
                    <span class="icon">📧</span>
                    <span class="name">Email</span>
                </div>
                <div class="tool-btn" data-tool="vehicle" onclick="toggleTool(this)">
                    <span class="icon">🚗</span>
                    <span class="name">Vehicle</span>
                </div>
                <div class="tool-btn" data-tool="github" onclick="toggleTool(this)">
                    <span class="icon">🐙</span>
                    <span class="name">GitHub</span>
                </div>
                <div class="tool-btn" data-tool="instagram" onclick="toggleTool(this)">
                    <span class="icon">📸</span>
                    <span class="name">Instagram</span>
                </div>
                <div class="tool-btn" data-tool="tg_user" onclick="toggleTool(this)">
                    <span class="icon">✈️</span>
                    <span class="name">Telegram Info</span>
                </div>
                <div class="tool-btn" data-tool="pan" onclick="toggleTool(this)">
                    <span class="icon">🪪</span>
                    <span class="name">PAN → GST</span>
                </div>
                <div class="tool-btn" data-tool="tg_id" onclick="toggleTool(this)">
                    <span class="icon">🆔</span>
                    <span class="name">Telegram ID</span>
                </div>
                <div class="tool-btn" data-tool="sms_bomber" onclick="toggleTool(this)">
                    <span class="icon">💥</span>
                    <span class="name">SMS Bomber</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>⏰ Expiry</h2>
            <div class="input-group">
                <label>Expiry Date (leave blank for lifetime)</label>
                <input type="date" id="expiry">
            </div>
        </div>

        <div class="card">
            <button class="btn" onclick="deployBot()">🚀 START BOT ON SERVER</button>
            <div id="status"></div>
        </div>

        <div class="card">
            <h2>📜 Running Bots</h2>
            <div class="bot-list" id="botList">
                <p style="text-align:center;color:#666;">No bots running</p>
            </div>
        </div>
    </div>

    <script>
        var selectedTools = new Set();
        var allTools = false;

        function toggleTool(el) {
            if (allTools) return;
            var t = el.getAttribute('data-tool');
            if (selectedTools.has(t)) {
                selectedTools.delete(t);
                el.classList.remove('selected');
            } else {
                selectedTools.add(t);
                el.classList.add('selected');
            }
        }

        function toggleAll() {
            allTools = !allTools;
            var toggle = document.getElementById('toggleAll');
            var btns = document.querySelectorAll('.tool-btn');
            if (allTools) {
                toggle.classList.add('active');
                toggle.innerHTML = '<span>☑</span> <b>ALL TOOLS ENABLED</b>';
                btns.forEach(function(b) { b.classList.add('selected'); });
                selectedTools = new Set(['phone','aadhaar','aadhaar_family','email','vehicle','github','instagram','tg_user','pan','tg_id','sms_bomber']);
            } else {
                toggle.classList.remove('active');
                toggle.innerHTML = '<span>☐</span> <b>Enable ALL Tools</b>';
                btns.forEach(function(b) { b.classList.remove('selected'); });
                selectedTools.clear();
            }
        }

        function showStatus(msg, type) {
            var s = document.getElementById('status');
            s.className = 'status ' + type;
            s.textContent = msg;
        }

        function deployBot() {
            var token = document.getElementById('token').value.trim();
            var chatId = document.getElementById('chatId').value.trim();
            var expiry = document.getElementById('expiry').value;
            var tools = allTools ? ['phone','aadhaar','aadhaar_family','email','vehicle','github','instagram','tg_user','pan','tg_id','sms_bomber'] : Array.from(selectedTools);

            if (!token) { showStatus('Enter Bot Token!', 'error'); return; }
            if (!chatId) { showStatus('Enter Chat ID!', 'error'); return; }
            if (tools.length === 0) { showStatus('Select at least one tool!', 'error'); return; }

            showStatus('Starting bot...', 'loading');

            fetch('/api/deploy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token, chat_id: chatId, tools: tools, expiry: expiry })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    showStatus('✅ Bot started successfully!', 'success');
                    loadBots();
                } else {
                    showStatus('❌ ' + (data.error || 'Failed'), 'error');
                }
            })
            .catch(function(e) {
                showStatus('❌ Server error: ' + e, 'error');
            });
        }

        function loadBots() {
            fetch('/api/bots')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var list = document.getElementById('botList');
                if (data.bots.length === 0) {
                    list.innerHTML = '<p style="text-align:center;color:#666;">No bots running</p>';
                    return;
                }
                list.innerHTML = data.bots.map(function(bot) {
                    return '<div class="bot-item">' +
                        '<div class="bot-info">' +
                        '<div class="bot-token">' + bot.token_preview + '</div>' +
                        '<div class="bot-meta">' + bot.tools.length + ' tools | ' + bot.expiry + '</div>' +
                        '</div>' +
                        '<div class="bot-actions">' +
                        '<span class="badge ' + (bot.running ? 'running' : 'stopped') + '">' + (bot.running ? '● Running' : '○ Stopped') + '</span>' +
                        '<button class="btn-small ' + (bot.running ? 'btn-stop' : 'btn-start') + '" onclick="toggleBot('' + bot.id + '')">' + (bot.running ? 'Stop' : 'Start') + '</button>' +
                        '<button class="btn-small btn-delete" onclick="deleteBot('' + bot.id + '')">Delete</button>' +
                        '</div>' +
                        '</div>';
                }).join('');
            })
            .catch(function(e) {
                console.log('Error loading bots:', e);
            });
        }

        function toggleBot(id) {
            fetch('/api/toggle/' + id, { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                showStatus(data.message, data.success ? 'success' : 'error');
                loadBots();
            });
        }

        function deleteBot(id) {
            if (!confirm('Delete this bot?')) return;
            fetch('/api/delete/' + id, { method: 'DELETE' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                showStatus(data.message, data.success ? 'success' : 'error');
                loadBots();
            });
        }

        setInterval(loadBots, 3000);
        loadBots();
    </script>
</body>
</html>
"""

# ============================================================
# BOT CLASS
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
        self.base_url = "https://api.telegram.org/bot" + token
        self.api_key = "ftgamer2"

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

        self.prompts = {
            'phone': ('📱 Phone Lookup', 'Send 10 digit mobile number:'),
            'aadhaar': ('🆔 Aadhaar Lookup', 'Send 12 digit Aadhaar number:'),
            'aadhaar_family': ('👨‍👩‍👧 Aadhaar Family', 'Send 12 digit Aadhaar number:'),
            'email': ('📧 Email Info', 'Send email address:'),
            'vehicle': ('🚗 Vehicle Lookup', 'Send vehicle number:'),
            'github': ('🐙 GitHub Lookup', 'Send GitHub username:'),
            'instagram': ('📸 Instagram Info', 'Send Instagram username:'),
            'tg_user': ('✈️ Telegram Info', 'Send Telegram username:'),
            'pan': ('🪪 PAN to GST', 'Send 10 character PAN number:'),
            'tg_id': ('🆔 Telegram ID', 'Send Telegram numeric ID:'),
            'sms_bomber': ('💥 SMS Bomber', 'Send 10 digit phone number:'),
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
            requests.post(self.base_url + "/sendMessage", json=payload, timeout=10)
        except Exception as e:
            print("[Bot " + self.bot_id + "] Send error: " + str(e))

    def get_updates(self):
        try:
            params = {"limit": 100, "timeout": 30}
            if self.offset:
                params["offset"] = self.offset
            resp = requests.get(self.base_url + "/getUpdates", params=params, timeout=35)
            return resp.json()
        except Exception as e:
            print("[Bot " + self.bot_id + "] Get updates error: " + str(e))
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
        return "<pre>" + json.dumps(data, indent=2, ensure_ascii=False) + "</pre>"

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
        print("[Bot " + self.bot_id + "] Started")
        self.send_message(self.chat_id, "Bot started!\nTools: " + str(len(self.tools)))

        while self.running:
            try:
                if not self.check_expiry():
                    self.send_message(self.chat_id, "Bot expired! Contact admin.")
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

                    if text == "/start":
                        welcome = "Welcome to FT-OSINT Bot!\n\nSelect a tool below!"
                        self.send_message(chat_id, welcome, self.create_keyboard())
                        self.waiting_for.pop(chat_id, None)
                        continue

                    for tool_key in self.tools:
                        if tool_key in self.prompts and text == self.prompts[tool_key][0]:
                            self.send_message(chat_id, self.prompts[tool_key][1])
                            self.waiting_for[chat_id] = tool_key
                            break
                    else:
                        if chat_id in self.waiting_for:
                            state = self.waiting_for[chat_id]
                            if state in self.validators and self.validators[state](text):
                                self.send_message(chat_id, "Processing...")
                                url, param = self.apis[state]
                                params = {"key": self.api_key, param: text}
                                if state == 'sms_bomber':
                                    params["counter"] = 100
                                result = self.call_api(url, params)
                                self.send_message(chat_id, self.format_response(result))
                                self.waiting_for.pop(chat_id, None)
                            else:
                                self.send_message(chat_id, "Invalid input! Try again.")
                            continue

                        self.send_message(chat_id, "I didn't understand. Use /start or select a tool.")

                if not updates.get("result"):
                    time.sleep(1)

            except Exception as e:
                print("[Bot " + self.bot_id + "] Loop error: " + str(e))
                time.sleep(3)

        self.running = False
        print("[Bot " + self.bot_id + "] Stopped")

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
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/deploy', methods=['POST'])
def deploy():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"})

        token = data.get('token', '').strip()
        chat_id = data.get('chat_id', '').strip()
        tools = data.get('tools', [])
        expiry = data.get('expiry', '')

        if not token:
            return jsonify({"success": False, "error": "Bot token is required"})
        if not chat_id:
            return jsonify({"success": False, "error": "Chat ID is required"})
        if not tools:
            return jsonify({"success": False, "error": "Select at least one tool"})

        bot_id = str(int(time.time()))

        for bid, bot in list(running_bots.items()):
            if bot.token == token:
                bot.stop()
                del running_bots[bid]

        bot = TelegramBot(bot_id, token, chat_id, tools, expiry)
        running_bots[bot_id] = bot
        bot.start()

        return jsonify({"success": True, "bot_id": bot_id, "message": "Bot started!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bots', methods=['GET'])
def list_bots():
    try:
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
    except Exception as e:
        return jsonify({"bots": [], "error": str(e)})

@app.route('/api/toggle/<bot_id>', methods=['POST'])
def toggle_bot(bot_id):
    try:
        if bot_id not in running_bots:
            return jsonify({"success": False, "error": "Bot not found"})

        bot = running_bots[bot_id]
        if bot.running:
            bot.stop()
            return jsonify({"success": True, "message": "Bot stopped"})
        else:
            bot.start()
            return jsonify({"success": True, "message": "Bot restarted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/delete/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    try:
        if bot_id not in running_bots:
            return jsonify({"success": False, "error": "Bot not found"})

        running_bots[bot_id].stop()
        del running_bots[bot_id]
        return jsonify({"success": True, "message": "Bot deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
