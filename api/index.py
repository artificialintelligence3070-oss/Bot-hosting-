from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import razorpay
import hmac
import hashlib
import json

app = Flask(__name__)

# SECURITY PROTOCOL: Secure cookie encryption key
app.secret_key = "crimson_vex_secure_vault_key_hash"

# GATEWAY CONFIG: Configured with your live credentials
RAZORPAY_KEY_ID = "rzp_live_TCZPUI3LDHONP8"
RAZORPAY_KEY_SECRET = "t1elWq3O1G1j9x93GHBdfMQP"

try:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception:
    razorpay_client = None

# Temporary In-Memory Database (Resets on Vercel spin-downs)
USERS_DB = {}

# Production Pricing Data Matrix
API_PRODUCTS = {
    "demo_test": {"name": "₹1 Platform System Demo Test", "monthly": 1, "quarterly": 1, "desc": "1 Rupee Live Gateway Connectivity Testing Asset"},
    "number_api": {"name": "Number API Suite", "monthly": 100, "quarterly": 250, "desc": "Includes: Paytm Validator, Call Tracer, and Advance ICMR"},
    "hiteck_leak": {"name": "HiTeckGroop.in Leak Portal", "monthly": 400, "quarterly": 1100, "desc": "Includes: Advanced Targeted Deep Lookup & Email Search"},
    "aadhaar_family": {"name": "Identity Core Gateway Suite", "monthly": 200, "quarterly": 550, "desc": "Standard Identity verification pipeline and lookup modules"},
    "upi_full": {"name": "UPI Full + Num to UPI Module", "monthly": 150, "quarterly": 400, "desc": "Complete payment handle lookups & financial addressing maps"},
    "ifsc_lookup": {"name": "IFSC Routing Lookup Validator", "monthly": 50, "quarterly": 120, "desc": "Instant branch network locator & routing resolution data"},
    "pan_gst": {"name": "PAN to GST Compliance Bridge", "monthly": 100, "quarterly": 250, "desc": "Direct correlation mapping protocols to tax registry frameworks"},
    "pincode": {"name": "Pincode Postal Geolocation Matrix", "monthly": 30, "quarterly": 80, "desc": "Regional geo-fencing maps and area code classification"},
    "ip_lookup": {"name": "IP Address Lookup Intelligence", "monthly": 30, "quarterly": 80, "desc": "Network routing profiles, ISP logs, and target geo-metadata"},
    "vehicle_owner": {"name": "Vehicle to Owner Enterprise Registry", "monthly": 400, "quarterly": 1000, "desc": "Automotive ledger validation and ownership analysis infrastructure"},
    "ff_bgmi": {"name": "Free Fire + BGMI Stats Engine", "monthly": 80, "quarterly": 200, "desc": "Real-time game profile synchronization metrics and user statistics"},
    "snapchat": {"name": "Snapchat Platform Analytic Engine", "monthly": 80, "quarterly": 200, "desc": "Handles secure target network cross-platform validation maps"},
    "sms_bomber": {"name": "SMS Bomber Network Load Simulator", "monthly": 150, "quarterly": 400, "desc": "High-volume notification stress-testing deployment environment"},
    "pak_num": {"name": "Pakistan Number Core Routing API", "monthly": 100, "quarterly": 250, "desc": "International regional dataset structure validation capabilities"},
    "bundle_starter": {"name": "Starter Operations Pack Bundle", "monthly": 500, "quarterly": 1300, "desc": "Includes: Number + Identity Core + UPI + PAN + IFSC + Pincode + IP + Gaming"},
    "bundle_pro": {"name": "Pro Development Suite Bundle", "monthly": 1200, "quarterly": 3000, "desc": "Unrestricted programmatic execution access across all interfaces excluding Vehicle tools"},
    "bundle_ultimate": {"name": "Ultimate Full-Stack Enterprise Bundle", "monthly": 1600, "quarterly": 4200, "desc": "Total operational capacity profiles across 100% of all standard modules and bundles"}
}

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRIMSON VEX API STOREFRONT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght=300;400;700&display=swap');
        body { background-color: #030303; color: #f3f4f6; font-family: 'Space Grotesk', sans-serif; }
        .neon-glow-red { box-shadow: 0 0 30px rgba(239, 68, 68, 0.2); }
        .neon-border-red { border: 1px solid #3a0808; }
        .premium-dark-gradient { background: linear-gradient(135deg, #0f0202 0%, #030000 100%); }
        .card-transform { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        .card-transform:hover { transform: translateY(-6px); border-color: #ef4444; box-shadow: 0 15px 35px rgba(239, 68, 68, 0.25); }
    </style>
</head>
<body class="min-h-screen relative overflow-x-hidden selection:bg-red-600 selection:text-white">

    <!-- TOP CONTROL HEADER WITH AUTHENTICATION MANAGEMENT & MAILBOX -->
    <nav class="max-w-7xl mx-auto px-4 py-6 flex flex-col sm:flex-row justify-between items-center border-b border-red-950/40 gap-4">
        <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full bg-red-600 animate-ping"></div>
            <span class="text-xl font-bold tracking-widest text-white uppercase font-mono">VEX<span class="text-red-500 font-light">_NET</span></span>
        </div>
        
        <!-- DYNAMIC ACCOUNT MANAGER CONTROLLER (SAFE ELEMENT TOGGLING) -->
        <div class="flex items-center gap-4 flex-wrap justify-center">
            <div id="auth-state-area" class="text-xs font-mono">
                <div id="auth-logged-in" class="hidden items-center gap-3">
                    <span class="text-gray-400 font-mono">NODE: <span id="user-node-name" class="text-red-500 font-bold"></span></span>
                    <button onclick="triggerLogout()" class="px-2.5 py-1 bg-red-950/40 border border-red-900/60 hover:bg-red-600 hover:text-white rounded text-[10px] uppercase transition-all font-mono">Disconnect</button>
                </div>
                <div id="auth-logged-out" class="hidden">
                    <button onclick="openAuthModal('login')" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl text-[10px] uppercase tracking-wider transition-all font-mono">Initialize Identity Link</button>
                </div>
            </div>

            <!-- AUTOMATED DELIVERY MAILBOX WIDGET -->
            <div onclick="openMailboxModal()" class="relative bg-neutral-950 border border-red-900/30 rounded-xl px-4 py-2 flex items-center gap-3 cursor-pointer hover:border-red-600 transition-all">
                <div class="p-1.5 bg-red-950/40 border border-red-800/40 rounded-lg text-red-500">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 19v-8.93a2 2 0 01.89-1.664l8-5.333a2 2 0 012.22 0l8 5.333A2 2 0 0121 10.07V19a2 2 0 01-2 2H5a2 2 0 01-2-2zM14 14h-4v-4h4v4z"></path></svg>
                </div>
                <div class="text-xs font-mono">
                    <div class="text-gray-400 font-bold uppercase tracking-wider text-[10px]">Deployment Mailbox</div>
                    <div id="mailbox-status" class="text-[9px] text-gray-500 mt-0.5 truncate max-w-[160px]">0 Keys Allocated</div>
                </div>
            </div>
        </div>
    </nav>

    <!-- HERO DISPLAY SECTION -->
    <header class="max-w-4xl mx-auto text-center px-4 py-12">
        <h1 class="text-4xl sm:text-6xl font-black tracking-tighter text-white uppercase">HIGH SPEED CORE <span class="text-red-600">APIS</span></h1>
        <p class="text-gray-400 mt-2 text-xs sm:text-sm max-w-xl mx-auto font-light">Authenticate your dashboard terminal node, initialize runtime tokens, and configure webhook delivery metrics.</p>
    </header>

    <!-- MAIN PRODUCT ECOSYSTEM CONTAINER -->
    <main class="max-w-7xl mx-auto px-4 pb-24">
        <h2 class="text-sm font-bold tracking-widest text-red-500 uppercase mb-6 flex items-center gap-2 font-mono">
            <span>[00]</span> QUICK ENDPOINT VERIFICATION ASSETS
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12" id="demo-grid"></div>

        <h2 class="text-sm font-bold tracking-widest text-red-500 uppercase mb-6 flex items-center gap-2 font-mono">
            <span>[01]</span> PIPELINE INFRASTRUCTURE ARCHITECTURE
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16" id="products-grid"></div>

        <h2 class="text-sm font-bold tracking-widest text-red-500 uppercase mb-6 flex items-center gap-2 font-mono">
            <span>[02]</span> HIGH ALLOCATION COMPREHENSIVE BUNDLES
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16" id="bundles-grid"></div>
    </main>

    <!-- MANDATORY IDENTITY PROTOCOL MODAL (LOGIN / REGISTER) -->
    <div id="auth-modal" class="fixed inset-0 bg-black/95 backdrop-blur-md hidden items-center justify-center p-4 z-50">
        <div class="w-full max-w-sm bg-[#090202] neon-border-red p-6 rounded-2xl shadow-2xl">
            <h3 id="auth-modal-title" class="text-lg font-bold text-white uppercase tracking-tight mb-1 font-mono">Terminal Authentication</h3>
            <p id="auth-modal-desc" class="text-[11px] text-gray-400 mb-6 font-mono">Access your central API developer keys configuration platform</p>
            
            <form id="auth-form" onsubmit="handleAuthTransaction(event)" class="space-y-4 font-mono text-xs">
                <div>
                    <label class="block text-gray-400 uppercase tracking-widest mb-1 text-[10px]">User Account Name</label>
                    <input type="text" id="auth-username" required class="w-full bg-black border border-neutral-800 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-red-600 font-mono">
                </div>
                <div>
                    <label class="block text-gray-400 uppercase tracking-widest mb-1 text-[10px]">Security Phrase Access Key</label>
                    <input type="password" id="auth-password" required class="w-full bg-black border border-neutral-800 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-red-600 font-mono">
                </div>
                <button type="submit" class="w-full py-3.5 bg-red-600 hover:bg-red-700 transition-colors text-white font-bold tracking-widest text-xs rounded-xl uppercase mt-2">
                    CONFIRM ROUTE
                </button>
            </form>
            <div class="mt-4 text-center">
                <button onclick="toggleAuthMode()" id="auth-toggle-btn" class="text-[10px] text-red-400 hover:underline uppercase font-mono tracking-wider">Create a new access node account</button>
            </div>
        </div>
    </div>

    <!-- REVOLUTIONARY DATA INPUT & CHECKOUT PROCESSING MODAL -->
    <div id="checkout-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md hidden items-center justify-center p-4 z-50">
        <div class="w-full max-w-md bg-[#0a0202] neon-border-red p-6 rounded-2xl shadow-2xl relative">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h3 class="text-lg font-bold text-white uppercase tracking-tight" id="modal-product-name">System Deployment Initialization</h3>
                    <p class="text-[10px] text-red-500 uppercase font-mono tracking-wider mt-0.5" id="modal-product-tier">Allocating Subscription Parameter Block</p>
                </div>
                <button onclick="closeModal()" class="text-gray-500 hover:text-white transition-colors text-2xl font-light">&times;</button>
            </div>

            <div class="space-y-4 mb-6 font-mono text-xs">
                <div>
                    <label class="block text-gray-400 uppercase tracking-widest mb-1.5 text-[10px]">1. Custom Identifier Token Name</label>
                    <input type="text" id="config-key-name" placeholder="e.g., Production_Core_Node" class="w-full bg-black border border-neutral-800 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-red-600 font-mono transition-colors">
                </div>
                <div>
                    <label class="block text-gray-400 uppercase tracking-widest mb-1.5 text-[10px]">2. Custom Access Secret Token String</label>
                    <input type="text" id="config-key-secret" placeholder="e.g., custom_secret_passphrase_x" class="w-full bg-black border border-neutral-800 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-red-600 font-mono transition-colors">
                </div>
                <div>
                    <label class="block text-gray-400 uppercase tracking-widest mb-1.5 text-[10px]">3. Desired Rate/Execution Limitations Block</label>
                    <select id="config-limits" class="w-full bg-black border border-neutral-800 rounded-xl px-3 py-3 text-white focus:outline-none focus:border-red-600 font-mono transition-colors">
                        <option value="10k">10,000 requests capacity block</option>
                        <option value="50k">50,000 requests capacity block</option>
                        <option value="unlimited">Unrestricted execution model pipeline</option>
                    </select>
                </div>
            </div>

            <div class="bg-black border border-red-950/60 rounded-xl p-4 space-y-2.5 mb-6 font-mono text-[11px]">
                <div class="flex justify-between text-gray-500">
                    <span>Base Framework Rate Cost:</span>
                    <span class="text-gray-300" id="cost-base">₹0.00</span>
                </div>
                <div class="flex justify-between text-gray-500">
                    <span>Platform Transaction Fee (2%):</span>
                    <span class="text-gray-300" id="cost-platform">₹0.00</span>
                </div>
                <div class="flex justify-between text-gray-500">
                    <span>Regulatory GST Framework (18%):</span>
                    <span class="text-gray-300" id="cost-gst">₹0.00</span>
                </div>
                <div class="h-px bg-red-950/40 my-1"></div>
                <div class="flex justify-between text-white font-bold text-xs uppercase tracking-wider">
                    <span>Aggregate Settlement Sum:</span>
                    <span class="text-red-500 text-sm" id="cost-aggregate">₹0.00</span>
                </div>
            </div>

            <button onclick="executeOrderPipeline()" class="w-full py-4 bg-red-600 hover:bg-red-700 active:scale-[0.99] transition-all text-white font-bold tracking-widest text-xs rounded-xl uppercase font-mono">
                EXECUTE TRANSACTION ROUTE
            </button>
        </div>
    </div>

    <!-- LIVE MAILBOX INVENTORY MODAL -->
    <div id="mailbox-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md hidden items-center justify-center p-4 z-50">
        <div class="w-full max-w-md bg-[#0a0202] neon-border-red p-6 rounded-2xl shadow-2xl relative">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-base font-bold text-white uppercase tracking-tight font-mono">DEPLOYED KEY VAULT</h3>
                    <p class="text-[10px] text-gray-400 font-mono">Automated delivery system database verification</p>
                </div>
                <button onclick="closeMailboxModal()" class="text-gray-500 hover:text-white transition-colors text-2xl font-light">&times;</button>
            </div>
            <div id="mailbox-keys-container" class="space-y-3 max-h-60 overflow-y-auto pr-1 font-mono text-xs">
                <!-- Dynamically filled with active valid items -->
            </div>
        </div>
    </div>

    <!-- SAFE INTERACTION CODE ASSETS (NO ESCAPE CONFLICTS) -->
    <script>
        const products_schema = JSON_PRODUCTS_PLACEHOLDER;
        let active_session_username = SESSION_USER_PLACEHOLDER;
        let current_checkout = { id: '', duration: '', total: 0 };
        let current_auth_mode = 'login'; 
        let user_purchased_keys = [];

        const RAW_CARD_LAYOUT = `
            <div class="premium-dark-gradient border border-neutral-900 p-6 rounded-2xl card-transform flex flex-col justify-between relative overflow-hidden">
                <div>
                    <h3 class="text-white font-bold text-base tracking-tight uppercase font-mono text-ellipsis overflow-hidden whitespace-nowrap">##NAME##</h3>
                    <p class="text-gray-400 text-[11px] mt-2 min-h-[32px] font-light leading-relaxed">##DESC##</p>
                </div>
                <div class="mt-6 pt-4 border-t border-red-950/20">
                    <div class="grid grid-cols-2 gap-2.5">
                        <button onclick="openCheckout('##ID##', 'monthly')" class="p-2 bg-black hover:bg-neutral-950 border border-neutral-800 rounded-xl text-left transition-colors">
                            <span class="block text-[8px] text-gray-500 font-mono tracking-widest uppercase">1 MONTH ACCESS</span>
                            <span class="text-white font-mono font-bold text-xs">₹##MONTHLY##</span>
                        </button>
                        <button onclick="openCheckout('##ID##', 'quarterly')" class="p-2 bg-black hover:bg-neutral-950 border border-neutral-800 rounded-xl text-left transition-colors">
                            <span class="block text-[8px] text-gray-500 font-mono tracking-widest uppercase">3 MONTH ACCESS</span>
                            <span class="text-white font-mono font-bold text-xs">₹##QUARTERLY##</span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        function evaluateSessionUIRender() {
            const loggedInDiv = document.getElementById('auth-logged-in');
            const loggedOutDiv = document.getElementById('auth-logged-out');
            const nodeNameSpan = document.getElementById('user-node-name');
            
            if (active_session_username) {
                nodeNameSpan.innerText = active_session_username;
                loggedInDiv.classList.remove('hidden');
                loggedInDiv.classList.add('flex');
                loggedOutDiv.classList.add('hidden');
            } else {
                loggedInDiv.classList.add('hidden');
                loggedInDiv.classList.remove('flex');
                loggedOutDiv.classList.remove('hidden');
            }
        }

        function openAuthModal(mode) {
            current_auth_mode = mode;
            document.getElementById('auth-modal-title').innerText = mode === 'login' ? 'Terminal Authentication' : 'Establish Client Account';
            document.getElementById('auth-modal-desc').innerText = mode === 'login' ? 'Access your central API developer keys configuration platform' : 'Register a new stateless development block identity';
            document.getElementById('auth-toggle-btn').innerText = mode === 'login' ? 'Create a new access node account' : 'Return to system login profile';
            document.getElementById('auth-modal').classList.remove('hidden');
            document.getElementById('auth-modal').classList.add('flex');
        }

        function toggleAuthMode() {
            openAuthModal(current_auth_mode === 'login' ? 'register' : 'login');
        }

        function handleAuthTransaction(e) {
            e.preventDefault();
            const u = document.getElementById('auth-username').value.trim();
            const p = document.getElementById('auth-password').value.trim();
            const endpoint = current_auth_mode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/register';

            fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: u, password: p })
            })
            .then(res => res.json())
            .then(data => {
                if(data.error) { alert(data.error); }
                else {
                    active_session_username = data.username;
                    evaluateSessionUIRender();
                    document.getElementById('auth-modal').classList.add('hidden');
                    document.getElementById('auth-modal').classList.remove('flex');
                    document.getElementById('auth-form').reset();
                }
            });
        }

        function triggerLogout() {
            fetch('/api/v1/auth/logout', { method: 'POST' })
            .then(() => {
                active_session_username = null;
                user_purchased_keys = [];
                evaluateSessionUIRender();
                updateMailboxStatusUI();
            });
        }

        function mountPlatformGrid() {
            const dGrid = document.getElementById('demo-grid');
            const pGrid = document.getElementById('products-grid');
            const bGrid = document.getElementById('bundles-grid');

            dGrid.innerHTML = '';
            pGrid.innerHTML = '';
            bGrid.innerHTML = '';

            Object.entries(products_schema).forEach(([id, obj]) => {
                let cardHtml = RAW_CARD_LAYOUT
                    .replaceAll('##ID##', id)
                    .replaceAll('##NAME##', obj.name)
                    .replaceAll('##DESC##', obj.desc)
                    .replaceAll('##MONTHLY##', obj.monthly)
                    .replaceAll('##QUARTERLY##', obj.quarterly);

                if(id === "demo_test") { 
                    dGrid.innerHTML += cardHtml; 
                } else if(id.startsWith('bundle_')) { 
                    cardHtml = cardHtml.replace("premium-dark-gradient border border-neutral-900", "bg-gradient-to-b from-[#160404] to-[#030000] border border-red-900/40 neon-glow-red");
                    bGrid.innerHTML += cardHtml; 
                } else { 
                    pGrid.innerHTML += cardHtml; 
                }
            });
        }

        function openCheckout(productId, tier) {
            if(!active_session_username) {
                openAuthModal('login');
                return;
            }
            const dataObj = products_schema[productId];
            const baseAmount = dataObj[tier];

            const platformFee = Math.round((baseAmount * 0.02) * 100) / 100;
            const gstFee = Math.round(((baseAmount + platformFee) * 0.18) * 100) / 100;
            const absoluteTotal = Math.round((baseAmount + platformFee + gstFee) * 100) / 100;

            current_checkout = { id: productId, duration: tier, total: absoluteTotal };

            document.getElementById('modal-product-name').innerText = dataObj.name;
            document.getElementById('modal-product-tier').innerText = tier + " license tracking configuration block";
            document.getElementById('cost-base').innerText = "₹" + baseAmount.toFixed(2);
            document.getElementById('cost-platform').innerText = "₹" + platformFee.toFixed(2);
            document.getElementById('cost-gst').innerText = "₹" + gstFee.toFixed(2);
            document.getElementById('cost-aggregate').innerText = "₹" + absoluteTotal.toFixed(2);

            document.getElementById('config-key-name').value = "";
            document.getElementById('config-key-secret').value = "";

            const modal = document.getElementById('checkout-modal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function closeModal() {
            const modal = document.getElementById('checkout-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        function updateMailboxStatusUI() {
            const statusDiv = document.getElementById('mailbox-status');
            if(user_purchased_keys.length === 0) {
                statusDiv.innerText = "0 Keys Allocated";
                statusDiv.className = "text-[9px] text-gray-500 mt-0.5";
            } else {
                statusDiv.innerText = user_purchased_keys.length + " Active Deployed Keys";
                statusDiv.className = "text-[9px] text-green-400 font-bold mt-0.5";
            }
        }

        function openMailboxModal() {
            if(!active_session_username) {
                openAuthModal('login');
                return;
            }
            const container = document.getElementById('mailbox-keys-container');
            container.innerHTML = '';
            
            if(user_purchased_keys.length === 0) {
                container.innerHTML = '<div class="text-gray-500 text-center py-4">No active API keys found in this node instance. Please make a purchase first.</div>';
            } else {
                user_purchased_keys.forEach(k => {
                    container.innerHTML += '<div class="bg-black border border-red-950 p-3 rounded-xl space-y-1">' +
                        '<div class="flex justify-between font-bold text-white"><span class="text-red-500">' + k.api_name + '</span><span>' + k.limits + '</span></div>' +
                        '<div class="text-[10px] text-gray-400 select-all">Key Name: ' + k.key_name + '</div>' +
                        '<div class="text-[10px] text-gray-400 select-all">Secret: ' + k.key_secret + '</div>' +
                        '<div class="flex justify-between text-[9px] text-gray-500 mt-1 pt-1 border-t border-neutral-900"><span>Status: ACTIVE</span><span>Expires in: ' + k.expires_in + '</span></div>' +
                    '</div>';
                });
            }
            
            const modal = document.getElementById('mailbox-modal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function closeMailboxModal() {
            const modal = document.getElementById('mailbox-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        function executeOrderPipeline() {
            const customName = document.getElementById('config-key-name').value.trim();
            const customSecret = document.getElementById('config-key-secret').value.trim();
            const selectedLimits = document.getElementById('config-limits').value;

            if(!customName || !customSecret) {
                alert("Validation Exception: Custom Identity Parameters Cannot Remain Empty.");
                return;
            }

            fetch('/api/v1/payment/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: current_checkout.id,
                    duration_tier: current_checkout.duration,
                    total_calculated: current_checkout.total
                })
            })
            .then(res => res.json())
            .then(order => {
                if(order.error) { alert('Downstream Disruption: ' + order.error); return; }

                const options = {
                    "key": order.razorpay_key_id,
                    "amount": order.amount,
                    "currency": "INR",
                    "name": "VEX_CORE GATEWAYS",
                    "description": "System Allocation: " + order.product_name,
                    "order_id": order.id,
                    "handler": function (response){
                        fetch('/api/v1/payment/verify', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                                custom_config: { key_name: customName, key_secret: customSecret, limits: selectedLimits, duration: current_checkout.duration }
                            })
                        })
                        .then(vRes => vRes.json())
                        .then(vData => {
                            if(vData.status === 'verified') {
                                user_purchased_keys.push({
                                    api_name: products_schema[current_checkout.id].name,
                                    key_name: customName,
                                    key_secret: customSecret,
                                    limits: selectedLimits === 'unlimited' ? 'UNLIMITED' : selectedLimits.toUpperCase(),
                                    expires_in: current_checkout.duration === 'monthly' ? '30 Days' : '90 Days'
                                });
                                
                                updateMailboxStatusUI();
                                alert("Handshake Complete! API Token deployed. Click on the top-right deployment mailbox to view your active credentials.");
                                closeModal();
                            } else { alert('Cryptographic Handshake Verification Failure.'); }
                        });
                    },
                    "theme": { "color": "#ef4444" }
                };
                const rzp1 = new Razorpay(options);
                rzp1.open();
            })
            .catch(() => alert('Gateway pipeline communications interruption.'));
        }

        window.onload = () => {
            mountPlatformGrid();
            evaluateSessionUIRender();
            updateMailboxStatusUI();
        };
    </script>
</body>
</html>'''

@app.route('/', methods=['GET'])
def render_storefront_portal():
    session_user = session.get("user")
    session_user_js = f'"{session_user}"' if session_user else "null"
    
    rendered_page = HTML_TEMPLATE.replace("JSON_PRODUCTS_PLACEHOLDER", json.dumps(API_PRODUCTS)).replace("SESSION_USER_PLACEHOLDER", session_user_js)
    return rendered_page, 200, {'Content-Type': 'text/html'}

@app.route('/api/v1/auth/register', methods=['POST'])
def run_registration_pipeline():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Parameters fields mismatch syntax verification"}), 400
    if username in USERS_DB:
        return jsonify({"error": "Identifier node mapping already claimed"}), 409
        
    USERS_DB[username] = generate_password_hash(password)
    session["user"] = username
    return jsonify({"success": True, "username": username}), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def run_login_pipeline():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if username not in USERS_DB or not check_password_hash(USERS_DB[username], password):
        return jsonify({"error": "Invalid Identity Node Verification Checksum Key"}), 401
        
    session["user"] = username
    return jsonify({"success": True, "username": username}), 200

@app.route('/api/v1/auth/logout', methods=['POST'])
def terminate_session_route():
    session.pop("user", None)
    return jsonify({"success": True}), 200

@app.route('/api/v1/payment/order', methods=['POST'])
def provision_razorpay_order():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized endpoint access state"}), 401
    if not razorpay_client:
        return jsonify({"error": "Downstream Gateway Instance Token is unconfigured or broken."}), 500
        
    data = request.json or {}
    product_id = data.get("product_id")
    duration_tier = data.get("duration_tier")
    
    if product_id not in API_PRODUCTS or duration_tier not in ['monthly', 'quarterly']:
        return jsonify({"error": "Malformed Selection Input parameters."}), 400
        
    product_profile = API_PRODUCTS[product_id]
    base_cost = product_profile[duration_tier]
    
    platform_fee = round((base_cost * 0.02), 2)
    gst_fee = round(((base_cost + platform_fee) * 0.18), 2)
    aggregate_total = round((base_cost + platform_fee + gst_fee), 2)
    
    paise_amount = int(aggregate_total * 100)
    
    try:
        order_payload = {'amount': paise_amount, 'currency': 'INR', 'payment_capture': 1}
        razorpay_order = razorpay_client.order.create(data=order_payload)
        return jsonify({
            "id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "razorpay_key_id": RAZORPAY_KEY_ID,
            "product_name": product_profile['name']
        }), 200
    except Exception as e:
        return jsonify({"error": "Razorpay Instance Disruption", "details": str(e)}), 502

@app.route('/api/v1/payment/verify', methods=['POST'])
def clear_signature_token():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized verification handshake"}), 401
        
    data = request.json or {}
    order_id = data.get("razorpay_order_id", "")
    payment_id = data.get("razorpay_payment_id", "")
    client_signature = data.get("razorpay_signature", "")
    custom_config = data.get("custom_config", {})
    
    signature_data = f"{order_id}|{payment_id}"
    generated_signature = hmac.new(
        bytes(RAZORPAY_KEY_SECRET, 'utf-8'),
        msg=bytes(signature_data, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if hmac.compare_digest(generated_signature, client_signature):
        expiration_duration = "30 Days" if custom_config.get("duration") == "monthly" else "90 Days"
        return jsonify({
            "status": "verified",
            "delivery": {
                "name": custom_config.get("key_name", "Default_Node"),
                "expires_in": expiration_duration,
                "limit_status": custom_config.get("limits", "10k")
            }
        }), 200
    else:
        return jsonify({"status": "failed", "message": "Cryptographic Token Handshake Mismatch."}), 400

if __name__ == '__main__':
    app.run(port=3000, debug=True)
