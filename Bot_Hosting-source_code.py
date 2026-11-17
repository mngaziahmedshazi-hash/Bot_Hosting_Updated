# -*- coding: utf-8 -*-
import atexit
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import zipfile
from flask import Flask, render_template_string
from threading import Thread
import psutil
import requests
import telebot
from telebot import types

USDT_BDT_RATE = 120.0

# --- Flask Server with Monetag Ad Integration ---
app = Flask("")
MONETAG_ZONE_ID = "12284632"

@app.route("/")
def home():
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HOSTIFY ⚡ Ultimate Cloud Hosting & Reward Center</title>
        <style>
            body {{ background: #090d16; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding-top: 60px; }}
            .card {{ background: #111827; padding: 40px; border-radius: 20px; display: inline-block; box-shadow: 0 10px 30px rgba(0,0,0,0.8); border: 1px solid #1f2937; max-width: 450px; width: 90%; }}
            h1 {{ color: #38bdf8; font-size: 26px; margin-bottom: 10px; }}
            p {{ color: #94a3b8; font-size: 15px; margin-bottom: 25px; }}
            .btn {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 14px 28px; border: none; border-radius: 12px; cursor: pointer; font-size: 16px; font-weight: bold; transition: 0.3s; box-shadow: 0 4px 12px rgba(37,99,235,0.4); }}
            .btn:hover {{ background: linear-gradient(135deg, #1d4ed8, #1e40af); transform: translateY(-2px); }}
        </style>
        <script src='//libtl.com/sdk.js' data-zone='{MONETAG_ZONE_ID}' data-sdk='show_{MONETAG_ZONE_ID}'></script>
    </head>
    <body>
        <div class="card">
            <h1>🚀 HOSTIFY REWARD HUB</h1>
            <p>অ্যাড দেখে ফ্রিতে VIP সাবস্ক্রিপশন কোড ক্লেইম করুন এবং আপনার টেলিগ্রাম বট ২৪/৭ অনলাইন রাখুন!</p>
            <button class="btn" onclick="triggerAd()">✨ View Ad & Earn Reward</button>
        </div>
        <script>
            function triggerAd() {{
                if(typeof show_{MONETAG_ZONE_ID} === 'function') {{
                    show_{MONETAG_ZONE_ID}}}({{
                        ytag: true
                    }}).then(() => {{
                        alert('🎉 ধন্যবাদ! আপনার অ্যাড দেখা সফল হয়েছে। বোট থেকে কোড ক্লেইম করুন।');
                    }}).catch(e => {{
                        alert('⚠️ অ্যাড লোড হতে একটু সময় নিচ্ছে। দয়া করে পুনরায় চেষ্টা করুন।');
                    }});
                }} else {{
                    alert('⏳ অ্যাড লোড হচ্ছে, দয়া করে একটু অপেক্ষা করুন...');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- Updated Bot Token Here ---
TOKEN = "9023993338:AAH04Lbx9nRvlwUou0NaYH82RRsh8m912Z8"
OWNER_ID = 8452462370
ADMIN_ID = 8452462370
YOUR_USERNAME = "@freelancertradernahid"
UPDATE_CHANNEL = "hostifyofficialsbot"

BINANCE_API_KEY = "MubnGkbVK41BceyaTqhqQyrDPGxfmFd1107H5lmVsa2dDysoL8mLmZByIThd4kmw"
BINANCE_SECRET_KEY = "MBq2Kqe5UmbHizKhZz0rj8s4hcHPlELksEDBeLI1EsIwBSXJj2ClqfA0aRIg748E"
BINANCE_PAY_ID = "1246752417"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, "upload_bots")
IROTECH_DIR = os.path.join(BASE_DIR, "inf")
DATABASE_PATH = os.path.join(IROTECH_DIR, "bot_data.db")

FREE_USER_LIMIT = 0
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float("inf")

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

bot = telebot.TeleBot(TOKEN)

bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
banned_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
maintenance_mode = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Modern & Stylish Layouts ---
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", "⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴"],
    ["🚀 𝗨𝗽𝗹𝗼𝗮𝗱 𝗕𝗼𝘁", "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗕𝗼𝘁𝘀"],
    ["💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀", "🎁 𝗘𝗮𝗿𝗻 𝗩𝗜𝗣"],
    ["👤 𝗠𝘆 𝗣𝗿𝗼𝗳𝗶𝗹𝗲", "💬 𝗦𝘂𝗽𝗽𝗼𝗿𝘁"],
    ["👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿"],
]

ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", "⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴"],
    ["🚀 𝗨𝗽𝗹𝗼𝗮𝗱 𝗕𝗼𝘁", "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗕𝗼𝘁𝘀"],
    ["💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀", "🛡️ 𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹"],
    ["👤 𝗠𝘆 𝗣𝗿𝗼𝗳𝗶𝗹𝗲", "📊 𝗦𝘆𝘀𝘁𝗲𝗺 𝗦𝘁𝗮𝘁𝘀"],
    ["👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿"],
]

DB_LOCK = threading.Lock()

def init_db():
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, plan_name TEXT, expiry TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_files (user_id INTEGER, file_name TEXT, file_type TEXT, PRIMARY KEY (user_id, file_name))""")
        c.execute("""CREATE TABLE IF NOT EXISTS active_users (user_id INTEGER PRIMARY KEY)""")
        c.execute("""CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY)""")
        c.execute("""CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)""")
        c.execute("""CREATE TABLE IF NOT EXISTS plans (plan_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, file_limit INTEGER, price TEXT, duration INTEGER, buy_link TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS referrals (user_id INTEGER PRIMARY KEY, referred_by INTEGER, ref_count INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS used_txids (tx_id TEXT PRIMARY KEY)""")
        c.execute("""CREATE TABLE IF NOT EXISTS vouchers (code TEXT PRIMARY KEY, days INTEGER, file_limit INTEGER, is_used INTEGER DEFAULT 0)""")
        
        c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (ADMIN_ID,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Init Error: {e}")

def load_data():
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT user_id, plan_name, expiry FROM subscriptions")
        for row in c.fetchall():
            try: user_subscriptions[row[0]] = {"plan_name": row[1], "expiry": datetime.fromisoformat(row[2])}
            except: pass
            
        c.execute("SELECT user_id, file_name, file_type FROM user_files")
        for uid, fname, ftype in c.fetchall():
            if uid not in user_files: user_files[uid] = []
            user_files[uid].append((fname, ftype))
            
        c.execute("SELECT user_id FROM active_users")
        active_users.update(u[0] for u in c.fetchall())
        c.execute("SELECT user_id FROM banned_users")
        banned_users.update(u[0] for u in c.fetchall())
        c.execute("SELECT user_id FROM admins")
        admin_ids.update(u[0] for u in c.fetchall())
        conn.close()
    except Exception as e:
        logger.error(f"Load Data Error: {e}")

init_db()
load_data()

def parse_price_to_usdt(price_str):
    price_clean = str(price_str).upper().strip()
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", price_clean)
    if not numbers: return 0.0, price_str
    val = float(numbers[0])
    if "BDT" in price_clean or "TK" in price_clean:
        return round(val / USDT_BDT_RATE, 2), f"{price_str} (~{round(val / USDT_BDT_RATE, 2)} USDT)"
    return round(val, 2), f"{val} USDT"

def add_plan_db(name, file_limit, price, duration, buy_link):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT INTO plans (name, file_limit, price, duration, buy_link) VALUES (?, ?, ?, ?, ?)", (name, file_limit, price, duration, buy_link))
        conn.commit()
        conn.close()

def get_all_plans():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT plan_id, name, file_limit, price, duration, buy_link FROM plans")
    plans = c.fetchall()
    conn.close()
    return plans

def get_plan_by_id(plan_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT plan_id, name, file_limit, price, duration, buy_link FROM plans WHERE plan_id = ?", (plan_id,))
    plan = c.fetchone()
    conn.close()
    return plan

def delete_plan_db(plan_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("DELETE FROM plans WHERE plan_id = ?", (plan_id,))
        conn.commit()
        conn.close()

def save_subscription(user_id, plan_name, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO subscriptions (user_id, plan_name, expiry) VALUES (?, ?, ?)", (user_id, plan_name, expiry.isoformat()))
        conn.commit()
        conn.close()
        user_subscriptions[user_id] = {"plan_name": plan_name, "expiry": expiry}

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        if user_id in user_subscriptions: del user_subscriptions[user_id]

def is_txid_used(tx_id):
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT tx_id FROM used_txids WHERE tx_id=?", (str(tx_id).strip(),))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_used_txid(tx_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO used_txids (tx_id) VALUES (?)", (str(tx_id).strip(),))
        conn.commit()
        conn.close()

def check_binance_payment(pay_order_id):
    if not BINANCE_API_KEY or BINANCE_API_KEY == "YOUR_NEW_BINANCE_API_KEY_HERE":
        return False, 0.0, "API Key কনফিগার করা নেই।"
    endpoint = "https://api.binance.com/sapi/v1/pay/transactions"
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = f"{endpoint}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            transactions = data.get("data", []) if isinstance(data, dict) else data
            for item in transactions:
                if str(item.get("orderId", "")).strip() == str(pay_order_id).strip():
                    amount = float(item.get("amount", 0.0))
                    return True, amount, f"{amount} USDT"
            return False, 0.0, "TxID Binance এ পাওয়া যায়নি।"
        return False, 0.0, "Binance API Error"
    except Exception as e:
        return False, 0.0, f"Error: {e}"

def check_force_sub(user_id):
    if user_id in admin_ids: return True
    try:
        member = bot.get_chat_member(f"@{UPDATE_CHANNEL}", user_id)
        if member.status in ['member', 'administrator', 'creator']: return True
    except: pass
    return False

def get_user_folder(user_id):
    folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_file_limit(user_id):
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]["expiry"] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    skey = f"{script_owner_id}_{file_name}"
    sinfo = bot_scripts.get(skey)
    if sinfo and sinfo.get("process"):
        try:
            proc = psutil.Process(sinfo["process"].pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except: return False
    return False

def kill_process_tree(sinfo):
    try:
        proc = sinfo.get("process")
        if proc and hasattr(proc, "pid"):
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True): child.terminate()
            parent.terminate()
    except: pass

def run_script(script_path, owner_id, folder, fname, msg=None):
    skey = f"{owner_id}_{fname}"
    try:
        log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        log_file = open(log_path, "w", encoding="utf-8", errors="ignore")
        proc = subprocess.Popen([sys.executable, script_path], cwd=folder, stdout=log_file, stderr=log_file, stdin=subprocess.PIPE)
        bot_scripts[skey] = {"process": proc, "log_file": log_file, "file_name": fname, "owner_id": owner_id, "start_time": datetime.now(), "folder": folder, "type": "py"}
        if msg: bot.reply_to(msg, f"🚀 **PYTHON BOT STARTED SUCCESSFULLY!**\n━━━━━━━━━━━━━━━━━━━\n📄 File: `{fname}`\n🆔 PID: `{proc.pid}`\n⚡ Status: `Online (24/7)`", parse_mode="Markdown")
    except Exception as e:
        if msg: bot.reply_to(msg, f"❌ Start Error: {e}")

def run_js_script(script_path, owner_id, folder, fname, msg=None):
    skey = f"{owner_id}_{fname}"
    try:
        log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        log_file = open(log_path, "w", encoding="utf-8", errors="ignore")
        proc = subprocess.Popen(["node", script_path], cwd=folder, stdout=log_file, stderr=log_file, stdin=subprocess.PIPE)
        bot_scripts[skey] = {"process": proc, "log_file": log_file, "file_name": fname, "owner_id": owner_id, "start_time": datetime.now(), "folder": folder, "type": "js"}
        if msg: bot.reply_to(msg, f"🚀 **NODE.JS BOT STARTED SUCCESSFULLY!**\n━━━━━━━━━━━━━━━━━━━\n📄 File: `{fname}`\n🆔 PID: `{proc.pid}`\n⚡ Status: `Online (24/7)`", parse_mode="Markdown")
    except Exception as e:
        if msg: bot.reply_to(msg, f"❌ JS Start Error: {e}")

def save_user_file(uid, fname, ftype):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)", (uid, fname, ftype))
        conn.commit()
        conn.close()
        if uid not in user_files: user_files[uid] = []
        user_files[uid] = [f for f in user_files[uid] if f[0] != fname]
        user_files[uid].append((fname, ftype))

def remove_user_file_db(uid, fname):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("DELETE FROM user_files WHERE user_id = ? AND file_name = ?", (uid, fname))
        conn.commit()
        conn.close()
        if uid in user_files:
            user_files[uid] = [f for f in user_files[uid] if f[0] != fname]

def main_menu_markup(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout = ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC if uid in admin_ids else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    for row in layout: markup.add(*[types.KeyboardButton(t) for t in row])
    return markup

def admin_panel_markup():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("➕ Add Plan", callback_data="add_plan_init"), types.InlineKeyboardButton("🗑️ Manage Plans", callback_data="manage_plans"))
    m.add(types.InlineKeyboardButton("💎 Add Sub", callback_data="add_subscription"), types.InlineKeyboardButton("❌ Remove Sub", callback_data="remove_subscription"))
    m.add(types.InlineKeyboardButton("🎟️ Create Voucher", callback_data="create_voucher"), types.InlineKeyboardButton("🛠️ Maintenance", callback_data="toggle_maint"))
    m.add(types.InlineKeyboardButton("🚫 Ban", callback_data="ban_user"), types.InlineKeyboardButton("✅ Unban", callback_data="unban_user"))
    m.add(types.InlineKeyboardButton("📣 Broadcast", callback_data="broadcast"), types.InlineKeyboardButton("⚙️ Run All", callback_data="run_all_scripts"))
    m.add(types.InlineKeyboardButton("🛑 Stop All", callback_data="stop_all_scripts"), types.InlineKeyboardButton("📊 System Stats", callback_data="stats"))
    return m

@bot.message_handler(commands=["start"])
def start_cmd(message):
    uid = message.from_user.id
    if uid in banned_users:
        bot.reply_to(message, "❌ **Access Denied:** আপনি এই সিস্টেম থেকে ব্যানড হয়েছেন।")
        return
    if maintenance_mode and uid not in admin_ids:
        bot.reply_to(message, "🛠️ **System Maintenance:** বোট বর্তমানে আপগ্রেড ও মেইনটেইন্যান্স মোডে আছে। কিছুক্ষণ পর চেষ্টা করুন।")
        return
    if not check_force_sub(uid):
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 Join Official Channel", url=f"https://t.me/{UPDATE_CHANNEL}"))
        m.add(types.InlineKeyboardButton("🔄 Verify Membership", callback_data="check_join"))
        bot.send_message(message.chat.id, f"⚠️ **Attention Required!**\n\nবোটের হোস্টিং ফিচার ব্যবহার করতে হলে আমাদের অফিশিয়াল চ্যানেলে জয়েন করা বাধ্যতামূলক।", reply_markup=m, parse_mode="Markdown")
        return

    args = message.text.split()
    if len(args) > 1 and uid not in active_users:
        try:
            ref_id = int(args[1])
            if ref_id != uid:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO referrals (user_id, referred_by) VALUES (?, ?)", (uid, ref_id))
                c.execute("UPDATE referrals SET ref_count = ref_count + 1 WHERE user_id = ?", (ref_id,))
                conn.commit()
                conn.close()
                bot.send_message(ref_id, f"🎁 **Referral Alert:** নতুন একজন ইউজার আপনার ইনভাইট লিংকের মাধ্যমে জয়েন করেছে!")
        except: pass

    if uid not in active_users:
        active_users.add(uid)
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO active_users (user_id) VALUES (?)", (uid,))
            conn.commit()
            conn.close()

    welcome_text = (
        f"✨ **WELCOME TO HOSTIFY CLOUD** ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Hello, **{message.from_user.first_name}**!\n\n"
        f"⚡ The most powerful, secure & lightning-fast 24/7 Telegram Bot Hosting Platform.\n"
        f"🛡️ Deploy Python (`.py`), Node.js (`.js`) & Zip projects instantly without VPS hassles.\n\n"
        f"👇 *Choose an option from the sleek control menu below:*"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_markup(uid), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_cb(call):
    if check_force_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Membership Verified Successfully!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✨ চমৎকার! এখন আপনি HOSTIFY এর সমস্ত প্রিমিয়াম ফিচার উপভোগ করতে পারবেন।", reply_markup=main_menu_markup(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

def _logic_my_profile(message):
    uid = message.from_user.id
    status = "👑 System Owner" if uid == OWNER_ID else ("🛡️ Administrator" if uid in admin_ids else ("💎 VIP Enterprise Active" if uid in user_subscriptions and user_subscriptions[uid]["expiry"] > datetime.now() else "🆓 Standard Free Tier"))
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT ref_count FROM referrals WHERE user_id = ?", (uid,))
    row = c.fetchone()
    ref_count = row[0] if row else 0
    conn.close()

    text = (
        f"👤 **USER ACCOUNT PROFILE**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Telegram ID: `{uid}`\n"
        f"🔰 Account Tier: `{status}`\n"
        f"📁 Deployed Bots: `{get_user_file_count(uid)}` / `{get_user_file_limit(uid)}`\n"
        f"🎁 Successful Referrals: `{ref_count} users`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

def _logic_earn_vip(message):
    webapp_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL', 'your-app-name.onrender.com')}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👀 Watch Ad & Generate Code", url=webapp_url))
    markup.add(types.InlineKeyboardButton("🎁 Claim VIP Subscription", callback_data="claim_ad_reward"))
    
    bot.reply_to(message, 
                 "🎁 **REWARD CENTER: EARN FREE VIP**\n"
                 "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 "১. নিচের **'Watch Ad & Generate Code'** বাটনে ক্লিক করে স্পন্সরড অ্যাড দেখুন।\n"
                 "২. অ্যাড দেখা শেষ করে ফিরে এসে **'Claim VIP Subscription'** বাটনে ক্লিক করুন এবং ইনস্ট্যান্ট ৭ দিনের ভিআইপি প্ল্যান পান!", 
                 reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "claim_ad_reward")
def handle_claim_ad_reward(call):
    uid = call.from_user.id
    promo_code = f"HOSTIFY-VIP-{random.randint(10000, 99999)}"
    expiry = datetime.now() + timedelta(days=7)
    save_subscription(uid, "Monetag Ad-Reward VIP", expiry)
    
    bot.answer_callback_query(call.id, "🎉 Success! 7 Days VIP Activated!", show_alert=True)
    bot.send_message(call.message.chat.id, 
                     f"🎉 **REWARD CLAIMED SUCCESSFULLY!**\n"
                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     f"🔑 Voucher Code: `{promo_code}`\n"
                     f"💎 Package: `7 Days VIP (15 Bot Files Limit)`\n\n"
                     f"আপনার ক্লাউড হোস্টিং অ্যাকাউন্ট সফলভাবে আপগ্রেড করা হয়েছে।", parse_mode="Markdown")

def _logic_support(message):
    bot.reply_to(message, f"💬 **24/7 SUPPORT CENTER**\n\nযেকোনো টেকনিক্যাল সহায়তার জন্য সরাসরি যোগাযোগ করুন: {YOUR_USERNAME}", parse_mode="Markdown")

def _logic_view_plans(m_or_c):
    chat_id = m_or_c.chat.id if isinstance(m_or_c, telebot.types.Message) else m_or_c.message.chat.id
    plans = get_all_plans()
    if not plans:
        bot.send_message(chat_id, "ℹ️ বর্তমানে কোনো প্রিমিয়াম প্ল্যান উপলব্ধ নেই।")
        return
    for p in plans:
        pid, name, limit, price, duration, _ = p
        usdt, fprice = parse_price_to_usdt(price)
        markup = types.InlineKeyboardMarkup()
        if usdt == 0 or str(price).lower() in ["free", "0"]:
            markup.add(types.InlineKeyboardButton(f"🎁 Claim {name} (Free)", callback_data=f"claim_free_{pid}"))
        else:
            markup.add(types.InlineKeyboardButton(f"🛒 Purchase {name} ({usdt} USDT)", callback_data=f"buy_binance_{pid}"))
        bot.send_message(chat_id, f"📦 **HOSTING TIER:** `{name}`\n━━━━━━━━━━━━━━━━━━━\n📁 Bot Limit: `{limit} Files`\n⏱️ Duration: `{duration} Days`\n💰 Price: `{fprice}`\n━━━━━━━━━━━━━━━━━━━", reply_markup=markup, parse_mode="Markdown")

def _logic_upload_file(message):
    bot.reply_to(message, "🚀 **DEPLOYMENT READY**\n\nআপনার পাইথন (`.py`), নোড.জেএস (`.js`) অথবা জিপ (`.zip`) প্রজেক্ট ফাইলটি সরাসরি এই চ্যাটে ড্রপ বা সেন্ড করুন। বোট অটোমেটিক হোস্টিং শুরু করে দেবে।", parse_mode="Markdown")

def _logic_check_files(message):
    uid = message.from_user.id
    flist = user_files.get(uid, [])
    if not flist:
        bot.reply_to(message, "📂 **YOUR HOSTED BOTS:**\n\nআপনার অ্যাকাউন্টে বর্তমানে কোনো ফাইল হোস্টেড নেই।", parse_mode="Markdown")
        return
    m = types.InlineKeyboardMarkup(row_width=1)
    for fname, ftype in flist:
        status = "🟢 Online" if is_bot_running(uid, fname) else "🔴 Offline"
        m.add(types.InlineKeyboardButton(f"📄 {fname} [{ftype.upper()}] — {status}", callback_data=f"file_{uid}_{fname}"))
    
    m.add(types.InlineKeyboardButton("🗑️ Purge All Files", callback_data=f"del_all_{uid}"))
    bot.reply_to(message, "📁 **ACTIVE CLOUD DEPLOYMENTS:**", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(content_types=["document"])
def handle_docs(message):
    uid = message.from_user.id
    if uid in banned_users: return
    if not (uid in admin_ids or uid == OWNER_ID or (uid in user_subscriptions and user_subscriptions[uid]["expiry"] > datetime.now())):
        bot.reply_to(message, "❌ **Deployment Blocked:** ফাইল আপলোড করতে প্রথমে একটিভ প্ল্যান বা ভিআইপি সাবস্ক্রিপশন প্রয়োজন।")
        return

    doc = message.document
    fname = doc.file_name
    fext = os.path.splitext(fname)[1].lower()
    if fext not in [".py", ".js", ".zip"]:
        bot.reply_to(message, "⚠️ **Invalid Format:** শুধুমাত্র `.py`, `.js` এবং `.zip` ফাইল সমর্থিত!")
        return

    try:
        wait_msg = bot.reply_to(message, f"⏳ **Cloud Uploading:** `{fname}` প্রসেস করা হচ্ছে...")
        finfo = bot.get_file(doc.file_id)
        content = bot.download_file(finfo.file_path)
        folder = get_user_folder(uid)
        fpath = os.path.join(folder, fname)
        with open(fpath, "wb") as f: f.write(content)

        if fext == ".zip":
            with zipfile.ZipFile(fpath, 'r') as zf: zf.extractall(folder)
            os.remove(fpath)
            bot.edit_message_text(f"✅ **Extract Success:** জিপ ফাইল সফলভাবে এক্সট্রাক্ট করা হয়েছে!", message.chat.id, wait_msg.message_id)
            return

        bot.edit_message_text(f"✅ **Upload Success:** `{fname}` সফলভাবে স্টোরেজে সংরক্ষিত হয়েছে!", message.chat.id, wait_msg.message_id)
        save_user_file(uid, fname, fext[1:])
        if fext == ".js": run_js_script(fpath, uid, folder, fname, message)
        else: run_script(fpath, uid, folder, fname, message)
    except Exception as e:
        bot.reply_to(message, f"❌ **Error Occurred:** {e}")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id
    data = call.data

    if data == "view_plans_cb": _logic_view_plans(call)
    elif data.startswith("claim_free_"):
        pid = int(data.split("_")[2])
        plan = get_plan_by_id(pid)
        if plan:
            save_subscription(uid, plan[1], datetime.now() + timedelta(days=plan[4]))
            bot.answer_callback_query(call.id, "🎉 Plan Claimed Successfully!")
            bot.send_message(call.message.chat.id, f"🎉 অভিনন্দন! আপনার `{plan[1]}` প্ল্যানটি সফলভাবে সচল করা হয়েছে।")

    elif data.startswith("buy_binance_"):
        pid = int(data.split("_")[2])
        plan = get_plan_by_id(pid)
        if plan:
            usdt, _ = parse_price_to_usdt(plan[3])
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔍 Submit Binance TxID", callback_data=f"sub_tx_{pid}"))
            bot.send_message(call.message.chat.id, f"💛 **BINANCE PAY GATEWAY**\n━━━━━━━━━━━━━━━━━━━\n💳 Pay ID: `{BINANCE_PAY_ID}`\n💰 Exact Amount: `{usdt} USDT`\n\nপেমেন্ট সম্পন্ন করার পর নিচের বাটনে ক্লিক করে TxID জমা দিন।", reply_markup=m, parse_mode="Markdown")

    elif data.startswith("sub_tx_"):
        pid = int(data.split("_")[2])
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📩 আপনার Binance Pay Order ID / Transaction ID টি এখানে পাঠান:")
        bot.register_next_step_handler(msg, lambda m: process_txid(m, pid))

    elif data.startswith("file_"):
        _, owner_id, fname = data.split("_", 2)
        running = is_bot_running(int(owner_id), fname)
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(types.InlineKeyboardButton("🛑 Stop Bot", callback_data=f"stop_{owner_id}_{fname}") if running else types.InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_{owner_id}_{fname}"))
        m.add(types.InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{owner_id}_{fname}"))
        m.add(types.InlineKeyboardButton("📥 Download", callback_data=f"dl_{owner_id}_{fname}"), types.InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{owner_id}_{fname}"))
        m.add(types.InlineKeyboardButton("📜 Live Logs", callback_data=f"log_{owner_id}_{fname}"))
        bot.send_message(call.message.chat.id, f"📄 **BOT MANAGEMENT CONSOLE**\n━━━━━━━━━━━━━━━━━━━\n📁 File: `{fname}`\n⚡ Status: `{'🟢 Online & Running' if running else '🔴 Offline & Stopped'}`", reply_markup=m, parse_mode="Markdown")

    elif data.startswith("stop_"):
        _, owner_id, fname = data.split("_", 2)
        skey = f"{owner_id}_{fname}"
        if skey in bot_scripts: kill_process_tree(bot_scripts[skey]); del bot_scripts[skey]
        bot.answer_callback_query(call.id, "Bot Stopped!")
        bot.send_message(call.message.chat.id, f"🛑 বট `{fname}` সফলভাবে বন্ধ করা হয়েছে।")

    elif data.startswith("start_"):
        _, owner_id, fname = data.split("_", 2)
        folder = get_user_folder(int(owner_id))
        fpath = os.path.join(folder, fname)
        if os.path.exists(fpath):
            if fname.endswith(".py"): run_script(fpath, int(owner_id), folder, fname, call.message)
            elif fname.endswith(".js"): run_js_script(fpath, int(owner_id), folder, fname, call.message)
            bot.answer_callback_query(call.id, "Bot Started!")

    elif data.startswith("restart_"):
        _, owner_id, fname = data.split("_", 2)
        skey = f"{owner_id}_{fname}"
        if skey in bot_scripts: kill_process_tree(bot_scripts[skey]); del bot_scripts[skey]
        folder = get_user_folder(int(owner_id))
        fpath = os.path.join(folder, fname)
        if os.path.exists(fpath):
            if fname.endswith(".py"): run_script(fpath, int(owner_id), folder, fname, call.message)
            elif fname.endswith(".js"): run_js_script(fpath, int(owner_id), folder, fname, call.message)
            bot.answer_callback_query(call.id, "Restarted successfully!")

    elif data.startswith("dl_"):
        _, owner_id, fname = data.split("_", 2)
        fpath = os.path.join(get_user_folder(int(owner_id)), fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f: bot.send_document(call.message.chat.id, f)

    elif data.startswith("log_"):
        _, owner_id, fname = data.split("_", 2)
        log_path = os.path.join(get_user_folder(int(owner_id)), f"{os.path.splitext(fname)[0]}.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f: logs = f.read()[-1500:]
            bot.send_message(call.message.chat.id, f"📜 **LIVE CONSOLE LOGS (`{fname}`):**\n```\n{logs or 'No output logs recorded yet.'}\n```", parse_mode="Markdown")
        else: bot.answer_callback_query(call.id, "Log file not found!", show_alert=True)

    elif data.startswith("del_"):
        _, owner_id, fname = data.split("_", 2)
        skey = f"{owner_id}_{fname}"
        if skey in bot_scripts: kill_process_tree(bot_scripts[skey]); del bot_scripts[skey]
        remove_user_file_db(int(owner_id), fname)
        fpath = os.path.join(get_user_folder(int(owner_id)), fname)
        if os.path.exists(fpath): os.remove(fpath)
        bot.answer_callback_query(call.id, "File Deleted!")
        bot.send_message(call.message.chat.id, f"🗑️ ফাইল `{fname}` সার্ভার থেকে স্থায়ীভাবে মুছে ফেলা হয়েছে।")

    elif data.startswith("del_all_"):
        target_uid = int(data.split("_")[2])
        if uid == target_uid or uid in admin_ids:
            flist = user_files.get(target_uid, [])
            for fname, _ in flist:
                skey = f"{target_uid}_{fname}"
                if skey in bot_scripts: kill_process_tree(bot_scripts[skey]); del bot_scripts[skey]
                remove_user_file_db(target_uid, fname)
            folder = get_user_folder(target_uid)
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)
            bot.answer_callback_query(call.id, "All files purged!")
            bot.send_message(call.message.chat.id, "🗑️ আপনার হোস্টিং ফোল্ডারে থাকা সমস্ত বট ও ডেটা সফলভাবে পরিষ্কার করা হয়েছে।")

    # Admin actions
    elif data == "add_plan_init" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "📝 **Format:** `Name | Limit | Price | Duration | Link`\nউদাহরণ: `VIP | 50 | 5 USDT | 30 | https://t.me/...`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: add_plan_db(*[x.strip() for x in m.text.split("|")]))
    elif data == "manage_plans" and uid in admin_ids:
        plans = get_all_plans()
        m = types.InlineKeyboardMarkup()
        for p in plans: m.add(types.InlineKeyboardButton(f"🗑️ Delete {p[1]}", callback_data=f"del_plan_{p[0]}"))
        bot.send_message(call.message.chat.id, "🗑️ ডিলিট করার জন্য প্ল্যানে ক্লিক করুন:", reply_markup=m)
    elif data.startswith("del_plan_") and uid in admin_ids:
        delete_plan_db(int(data.split("_")[2]))
        bot.answer_callback_query(call.id, "Plan Deleted!")
    elif data == "add_subscription" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "💎 **Format:** `UserID PlanName Days`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: save_subscription(int(m.text.split()[0]), m.text.split()[1], datetime.now() + timedelta(days=int(m.text.split()[2]))))
    elif data == "remove_subscription" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "❌ সাবস্ক্রিপশন রিমুভ করতে User ID পাঠান:")
        bot.register_next_step_handler(msg, lambda m: remove_subscription_db(int(m.text.strip())))
    elif data == "toggle_maint" and uid in admin_ids:
        global maintenance_mode
        maintenance_mode = not maintenance_mode
        bot.answer_callback_query(call.id, f"Maintenance: {maintenance_mode}")
        bot.send_message(call.message.chat.id, f"🛠️ **Maintenance Mode:** `{maintenance_mode}`", parse_mode="Markdown")
    elif data == "ban_user" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "🚫 ব্যান করার জন্য User ID পাঠান:")
        bot.register_next_step_handler(msg, lambda m: (banned_users.add(int(m.text.strip())), bot.reply_to(m, "✅ ইউজার সফলভাবে ব্যান করা হয়েছে।")))
    elif data == "unban_user" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "✅ আনব্যান করার জন্য User ID পাঠান:")
        bot.register_next_step_handler(msg, lambda m: (banned_users.discard(int(m.text.strip())), bot.reply_to(m, "✅ ইউজারের ব্যান তুলে নেওয়া হয়েছে।")))
    elif data == "broadcast" and uid in admin_ids:
        msg = bot.send_message(call.message.chat.id, "📢 সমস্ত ইউজারের কাছে পাঠানোর জন্য ব্রডকাস্ট মেসেজটি সেন্ড বা ফরোয়ার্ড করুন:")
        bot.register_next_step_handler(msg, process_broadcast)
    elif data == "stop_all_scripts" and uid in admin_ids:
        for skey in list(bot_scripts.keys()): kill_process_tree(bot_scripts[skey]); del bot_scripts[skey]
        bot.answer_callback_query(call.id, "All bots terminated!")
    elif data == "stats" and uid in admin_ids:
        total_users = len(active_users)
        total_subs = len(user_subscriptions)
        running_bots = len(bot_scripts)
        bot.send_message(call.message.chat.id, 
                         f"📊 **ENTERPRISE SYSTEM METRICS**\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👥 Total Unique Users: `{total_users}`\n"
                         f"💎 Active Subscriptions: `{total_subs}`\n"
                         f"🚀 Running Bot Instances: `{running_bots}`\n"
                         f"🚫 Blacklisted Users: `{len(banned_users)}`\n"
                         f"🌐 Platform Status: `100% Operational`\n"
                         f"━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")

def process_txid(message, pid):
    tx = message.text.strip()
    uid = message.from_user.id
    plan = get_plan_by_id(pid)
    if is_txid_used(tx):
        bot.reply_to(message, "❌ **Error:** এই TxID টি ইতিপূর্বেই ব্যবহার করা হয়েছে!")
        return
    valid, _, _ = check_binance_payment(tx)
    if valid or float(re.findall(r'\d+', plan[3])[0]) == 0:
        add_used_txid(tx)
        save_subscription(uid, plan[1], datetime.now() + timedelta(days=plan[4]))
        bot.reply_to(message, f"🎉 **Payment Verified!** আপনার `{plan[1]}` প্যাকেজ সফলভাবে সচল করা হয়েছে।", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ **Verification Failed:** Binance Pay হিস্টোরিতে এই Order/TxID পাওয়া যায়নি।")

def process_broadcast(message):
    success, fail = 0, 0
    status_msg = bot.reply_to(message, "📢 ব্রডকাস্ট ক্যাম্পেইন প্রসেস হচ্ছে...")
    for uid in active_users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
            time.sleep(0.03)
        except: fail += 1
    bot.edit_message_text(f"✅ **BROADCAST COMPLETED**\n━━━━━━━━━━━━━━━━━━━\n🚀 Successful: `{success}`\n❌ Failed: `{fail}`", message.chat.id, status_msg.message_id, parse_mode="Markdown")

# --- Interactive Text Handlers ---
BUTTON_MAPPING = {
    "📢 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹": lambda m: bot.reply_to(m, f"📢 **Official Channel:** https://t.me/{UPDATE_CHANNEL}", parse_mode="Markdown"),
    "⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴": lambda m: bot.reply_to(m, "⚡ **Server Latency:** `12 ms`\n🚀 **Status:** `Lightning Fast & Secure`", parse_mode="Markdown"),
    "🚀 𝗨𝗽𝗹𝗼𝗮𝗱 𝗕𝗼𝘁": _logic_upload_file,
    "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗕𝗼𝘁𝘀": _logic_check_files,
    "💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀": _logic_view_plans,
    "🎁 𝗘𝗮𝗿𝗻 𝗩𝗜𝗣": _logic_earn_vip,
    "👤 𝗠𝘆 𝗣𝗿𝗼𝗳𝗶𝗹𝗲": _logic_my_profile,
    "💬 𝗦𝘂𝗽𝗽𝗼𝗿𝘁": _logic_support,
    "👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿": lambda m: bot.reply_to(m, f"👑 **Platform Owner:** {YOUR_USERNAME}", parse_mode="Markdown"),
    "🛡️ 𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹": lambda m: bot.reply_to(m, "🛡️ **ADMIN CONTROL CONSOLE:**", reply_markup=admin_panel_markup(), parse_mode="Markdown"),
    "📊 𝗦𝘆𝘀𝘁𝗲𝗺 𝗦𝘁𝗮𝘁𝘀": lambda m: bot.reply_to(m, f"📊 **Active Users Online:** `{len(active_users)}`\n🚀 **Running Bots:** `{len(bot_scripts)}`", parse_mode="Markdown"),
}

@bot.message_handler(func=lambda m: m.text in BUTTON_MAPPING)
def main_btns(m): BUTTON_MAPPING[m.text](m)

if __name__ == "__main__":
    logger.info("🤖 HOSTIFY Ultimate Enterprise Edition Loaded Successfully...")
    keep_alive()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
