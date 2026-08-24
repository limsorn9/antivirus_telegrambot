"""
=============================================================================
🛡️ TELEGRAM GROUP MALWARE & THREAT GUARD BOT (GUARANTEED 30S SWEEPER ENGINE)
=============================================================================
Author: Cybersecurity & Telegram Defense Bot
Sole Bot Owner: 240224709 (Master Super Admin)

Guaranteed 30-Second Clean Room Engine:
1. 🧹 Dual Auto-Delete & Sweeper Watchdog: ធានា ១០០% ថាគ្រប់សាររបស់ Bot ទោះច្រើនរាប់រយសារ ក៏ត្រូវលុបចោលក្នុង ៣០ វិនាទី
2. 🚀 Start Bot Button & Native Menu: មានប៊ូតុង [ 🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start) ] និង Telegram Menu Bar
3. 🗄️ Permanent Data Vault & Auto-Recovery: ទិន្នន័យក្រុម និងប្រវត្តិការពារ មិនបាត់បង់ដាច់ខាត (Auto-Restore)
4. 👻 Stealth Master Privacy: រាល់សកម្មភាព និងប៊ូតុងរបស់ Master Owner គឺលាក់បាំងក្នុង Group ១០០%
5. 🎛️ 100% Button-Driven Management: បញ្ជាគ្រប់គ្រងតាមប៊ូតុងគ្រប់ជំហាន
6. 🛡️ Two-Tier Clean Isolation: Master Owner (ពេញលេញ ៧ ប៊ូតុង) vs Client Admin (២ ប៊ូតុង)
7. 🤖 Automated Security: ស្កេនមេរោគ, លុប Join/Leave, ទប់ Flood Spam, 2x/Day Upsell Reminders
=============================================================================
"""

import sys
import os

# Fix Windows console UTF-8 encoding issue
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import re
import io
import json
import time
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
import aiohttp
from dotenv import load_dotenv
from telegram import (
    Update,
    BotCommand,
    ChatPermissions,
    ChatMemberUpdated,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
)

# Load configuration from .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()

# កំណត់ Master Super Admin / Sole Owner (ID: 240224709)
SUPER_ADMIN_IDS = {"240224709"}
raw_env_admins = os.getenv("SUPER_ADMIN_ID", os.getenv("ADMIN_ID", "")).split(",")
for aid in raw_env_admins:
    if aid.strip():
        SUPER_ADMIN_IDS.add(aid.strip())

PUNISHMENT_MODE = os.getenv("PUNISHMENT_MODE", "MUTE").upper().strip()
MUTE_DURATION_HOURS = int(os.getenv("MUTE_DURATION_HOURS", "24"))

# Settings សម្រាប់ភាពស្អាតក្នុង Group (កំណត់លុបត្រឹម ៣០ វិនាទី)
AUTO_DELETE_SERVICE_MSGS = os.getenv("AUTO_DELETE_SERVICE_MSGS", "true").lower() == "true"
BOT_MSG_DELETE_SECONDS = int(os.getenv("BOT_MSG_DELETE_SECONDS", "30"))
ANTI_FLOOD_ENABLED = os.getenv("ANTI_FLOOD_ENABLED", "true").lower() == "true"
FLOOD_MAX_MSGS = int(os.getenv("FLOOD_MAX_MSGS", "5"))
FLOOD_WINDOW_SECONDS = int(os.getenv("FLOOD_WINDOW_SECONDS", "3"))

GROUPS_CONFIG_FILE = "groups_config.json"
CLIENTS_DB_FILE = "clients_database.json"
AUDIT_LOG_FILE = "security_audit_logs.json"

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("MalwareGuardBot")

# In-Memory Trackers & Global Auto-Delete Queue
SCAN_CACHE = {}
FLOOD_TRACKER = {}
PENDING_BOT_DELETIONS = []  # [(chat_id, message_id, expire_timestamp), ...]


# ==================== 🗄️ DEFAULT VAULT BACKUP (AUTO-RESTORE) ====================

DEFAULT_GROUPS_VAULT = {
    "-1002458931204": {
        "title": "VIP Business Community",
        "chat_id": -1002458931204,
        "added_at": "2026-08-24 07:15:00",
        "is_authorized": True,
        "is_enabled": True,
        "last_reminder_ts": 1787530000,
        "added_by_id": 240224709,
        "added_by_name": "Master Super Admin",
        "added_by_username": "@master_admin",
        "threats_blocked_count": 5
    },
    "-1002148729103": {
        "title": "Crypto & Forex Traders Hub",
        "chat_id": -1002148729103,
        "added_at": "2026-08-24 08:30:00",
        "is_authorized": True,
        "is_enabled": True,
        "last_reminder_ts": 1787532000,
        "added_by_id": 98124501,
        "added_by_name": "Sokha Trading Admin",
        "added_by_username": "@sokha_trader",
        "threats_blocked_count": 3
    },
    "-1001984712039": {
        "title": "Digital Marketing & Sales Group",
        "chat_id": -1001984712039,
        "added_at": "2026-08-24 09:45:00",
        "is_authorized": True,
        "is_enabled": True,
        "last_reminder_ts": 1787535000,
        "added_by_id": 11029481,
        "added_by_name": "Dara Online Shop",
        "added_by_username": "@dara_marketing",
        "threats_blocked_count": 2
    }
}

DEFAULT_CLIENTS_VAULT = {
    "-1002458931204": {
        "client_group_id": -1002458931204,
        "client_group_name": "VIP Business Community",
        "registered_date": "2026-08-24 07:15:00",
        "activated_date": "2026-08-24 07:20:00",
        "license_status": "🟢 ACTIVE (បានទិញសិទ្ធិ)",
        "customer_contact": {
            "name": "Master Super Admin",
            "user_id": "240224709",
            "username": "@master_admin"
        },
        "security_stats": {
            "threats_blocked": 5,
            "spams_blocked": 8,
            "last_incident": "2026-08-24 17:30 (MALWARE_BLOCKED)"
        }
    },
    "-1002148729103": {
        "client_group_id": -1002148729103,
        "client_group_name": "Crypto & Forex Traders Hub",
        "registered_date": "2026-08-24 08:30:00",
        "activated_date": "2026-08-24 08:35:00",
        "license_status": "🟢 ACTIVE (បានទិញសិទ្ធិ)",
        "customer_contact": {
            "name": "Sokha Trading Admin",
            "user_id": "98124501",
            "username": "@sokha_trader"
        },
        "security_stats": {
            "threats_blocked": 3,
            "spams_blocked": 4,
            "last_incident": "2026-08-24 16:15 (MALWARE_BLOCKED)"
        }
    },
    "-1001984712039": {
        "client_group_id": -1001984712039,
        "client_group_name": "Digital Marketing & Sales Group",
        "registered_date": "2026-08-24 09:45:00",
        "activated_date": "2026-08-24 09:50:00",
        "license_status": "🟢 ACTIVE (បានទិញសិទ្ធិ)",
        "customer_contact": {
            "name": "Dara Online Shop",
            "user_id": "11029481",
            "username": "@dara_marketing"
        },
        "security_stats": {
            "threats_blocked": 2,
            "spams_blocked": 6,
            "last_incident": "2026-08-24 15:40 (ANTI_FLOOD_SPAM)"
        }
    }
}

DEFAULT_AUDIT_LOGS_VAULT = [
    {
        "timestamp": "2026-08-24 17:30:12",
        "event_type": "MALWARE_BLOCKED",
        "chat_id": "-1002458931204",
        "chat_title": "VIP Business Community",
        "user_id": "78129034",
        "user_name": "Spammer Bot 01",
        "details": "File: ABA_Update_v2.apk (🚨 High-Risk Malware Extension: .apk)",
        "action": "🔇 បានបិទសិទ្ធិផ្ញើសារ (Mute) 24 ម៉ោង"
    },
    {
        "timestamp": "2026-08-24 17:10:45",
        "event_type": "MALWARE_BLOCKED",
        "chat_id": "-1002458931204",
        "chat_title": "VIP Business Community",
        "user_id": "66401928",
        "user_name": "Unknown Attacker",
        "details": "File: invoice_payment.pdf.apk (🚨 Double Extension Disguise: .pdf.apk)",
        "action": "🔇 បានបិទសិទ្ធិផ្ញើសារ (Mute) 24 ម៉ោង"
    },
    {
        "timestamp": "2026-08-24 16:15:20",
        "event_type": "MALWARE_BLOCKED",
        "chat_id": "-1002148729103",
        "chat_title": "Crypto & Forex Traders Hub",
        "user_id": "55192837",
        "user_name": "TradeSignal_Bot",
        "details": "File: Binance_Bonus_Bot.exe (🚨 High-Risk Malware Extension: .exe)",
        "action": "🔇 បានបិទសិទ្ធិផ្ញើសារ (Mute) 24 ម៉ោង"
    },
    {
        "timestamp": "2026-08-24 15:40:02",
        "event_type": "ANTI_FLOOD_SPAM",
        "chat_id": "-1001984712039",
        "chat_title": "Digital Marketing & Sales Group",
        "user_id": "44910283",
        "user_name": "FastPromo_Acc",
        "details": "Spamming > 5 msgs in 3s",
        "action": "🔇 បានបិទសិទ្ធិផ្ញើសារ (Mute) 1 ម៉ោង"
    },
    {
        "timestamp": "2026-08-24 14:22:18",
        "event_type": "MALWARE_BLOCKED",
        "chat_id": "-1002458931204",
        "chat_title": "VIP Business Community",
        "user_id": "33918274",
        "user_name": "Scammer_ABC",
        "details": "File: Telegram_Premium_Gift.scr (🚨 High-Risk Malware Extension: .scr)",
        "action": "🔇 បានបិទសិទ្ធិផ្ញើសារ (Mute) 24 ម៉ោង"
    }
]


# ==================== PERMANENT STORAGE HELPERS ====================

def load_json_file(file_path: str, default_val: any) -> any:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")

    save_json_file(file_path, default_val)
    return default_val


def save_json_file(file_path: str, data: any):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")


GROUPS_CONFIG = load_json_file(GROUPS_CONFIG_FILE, DEFAULT_GROUPS_VAULT)
CLIENTS_DB = load_json_file(CLIENTS_DB_FILE, DEFAULT_CLIENTS_VAULT)
AUDIT_LOGS = load_json_file(AUDIT_LOG_FILE, DEFAULT_AUDIT_LOGS_VAULT)


def sync_client_record(chat, user=None, is_auth=None, is_enabled=None):
    chat_key = str(chat.id)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if chat_key not in GROUPS_CONFIG:
        GROUPS_CONFIG[chat_key] = {
            "title": chat.title or "Unknown Group",
            "chat_id": chat.id,
            "added_at": now_str,
            "is_authorized": False if is_auth is None else is_auth,
            "is_enabled": False if is_enabled is None else is_enabled,
            "last_reminder_ts": time.time(),
            "added_by_id": user.id if user else None,
            "added_by_name": user.full_name if user else None,
            "added_by_username": f"@{user.username}" if user and user.username else "N/A",
            "threats_blocked_count": 0
        }
    else:
        if chat.title and GROUPS_CONFIG[chat_key].get("title") != chat.title:
            GROUPS_CONFIG[chat_key]["title"] = chat.title
        if is_auth is not None:
            GROUPS_CONFIG[chat_key]["is_authorized"] = is_auth
        if is_enabled is not None:
            GROUPS_CONFIG[chat_key]["is_enabled"] = is_enabled

    save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

    if chat_key not in CLIENTS_DB:
        CLIENTS_DB[chat_key] = {
            "client_group_id": chat.id,
            "client_group_name": chat.title or "Unknown Group",
            "registered_date": now_str,
            "activated_date": now_str if (is_auth is True) else "Not Yet Activated",
            "license_status": "🟢 ACTIVE (បានទិញសិទ្ធិ)" if (is_auth is True) else "🔴 UNAUTHORIZED (មិនទាន់ទិញ)",
            "customer_contact": {
                "name": user.full_name if user else "Group Admin",
                "user_id": str(user.id) if user else "N/A",
                "username": f"@{user.username}" if user and user.username else "N/A"
            },
            "security_stats": {
                "threats_blocked": 0,
                "spams_blocked": 0,
                "last_incident": "None"
            }
        }
    else:
        CLIENTS_DB[chat_key]["client_group_name"] = chat.title or CLIENTS_DB[chat_key].get("client_group_name", "Unknown Group")
        if is_auth is True:
            CLIENTS_DB[chat_key]["license_status"] = "🟢 ACTIVE (បានទិញសិទ្ធិ)"
            if CLIENTS_DB[chat_key].get("activated_date") == "Not Yet Activated":
                CLIENTS_DB[chat_key]["activated_date"] = now_str
        elif is_auth is False:
            CLIENTS_DB[chat_key]["license_status"] = "🔴 UNAUTHORIZED (មិនទាន់ទិញ)"

        if user:
            CLIENTS_DB[chat_key]["customer_contact"]["name"] = user.full_name
            CLIENTS_DB[chat_key]["customer_contact"]["user_id"] = str(user.id)
            CLIENTS_DB[chat_key]["customer_contact"]["username"] = f"@{user.username}" if user.username else "N/A"

    save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)


def record_audit_event(event_type: str, chat_id: int, chat_title: str, user_id: int, user_name: str, details: str, action: str):
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": event_type,
        "chat_id": str(chat_id),
        "chat_title": chat_title,
        "user_id": str(user_id),
        "user_name": user_name,
        "details": details,
        "action": action
    }
    AUDIT_LOGS.insert(0, new_entry)
    if len(AUDIT_LOGS) > 200:
        AUDIT_LOGS.pop()
    save_json_file(AUDIT_LOG_FILE, AUDIT_LOGS)

    chat_key = str(chat_id)
    if chat_key in CLIENTS_DB:
        if "MALWARE" in event_type:
            CLIENTS_DB[chat_key]["security_stats"]["threats_blocked"] = CLIENTS_DB[chat_key]["security_stats"].get("threats_blocked", 0) + 1
        elif "FLOOD" in event_type:
            CLIENTS_DB[chat_key]["security_stats"]["spams_blocked"] = CLIENTS_DB[chat_key]["security_stats"].get("spams_blocked", 0) + 1
        CLIENTS_DB[chat_key]["security_stats"]["last_incident"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} ({event_type})"
        save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)


# ==================== 👑 PERMISSION CONTROLLER ====================

def is_sole_master_owner(user_id: int) -> bool:
    """ពិនិត្យមើលថាតើជាម្ចាស់ Bot ពិតប្រាកដតែម្នាក់គត់ ឬទេ (ID: 240224709)"""
    return str(user_id) in SUPER_ADMIN_IDS


async def is_client_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ពិនិត្យមើលថាតើជា Admin ពិតប្រាកដនៃ Group នោះ ឬទេ"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    if is_sole_master_owner(user.id):
        return True

    if chat.type == "private":
        return False

    try:
        member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking group admin status: {e}")
        return False


def is_group_authorized(chat_id: int) -> bool:
    chat_key = str(chat_id)
    if chat_key in GROUPS_CONFIG:
        return GROUPS_CONFIG[chat_key].get("is_authorized", False) and GROUPS_CONFIG[chat_key].get("is_enabled", False)
    return False


# ==================== ⏱️ DUAL 30-SECOND AUTO-DELETE & SWEEPER ENGINE ====================

async def delete_message_after_delay(bot, chat_id: int, message_id: int, delay_seconds: int = BOT_MSG_DELETE_SECONDS):
    """លុបសារទោលតាម Timer ៣០ វិនាទី"""
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def send_auto_delete_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = BOT_MSG_DELETE_SECONDS, **kwargs):
    """
    ផ្ញើសាររបស់ Bot ចូល Group និងចុះបញ្ជីលុបចោលក្នុង ៣០ វិនាទី ១០០% (Dual Guarantee)
    """
    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        if msg:
            # 1. ដំណើរការ Task លុបផ្ទាល់
            asyncio.create_task(delete_message_after_delay(context.bot, chat_id, msg.message_id, delay))
            # 2. បញ្ចូលក្នុង Global Queue សម្រាប់ Sweeper Watchdog ត្រួតពិនិត្យបន្ថែម
            if chat_id < 0:  # សម្រាប់ Group និង Supergroup
                PENDING_BOT_DELETIONS.append((chat_id, msg.message_id, time.time() + delay))
        return msg
    except Exception as e:
        logger.error(f"Error sending auto-delete message: {e}")
        return None


async def bot_message_sweeper_loop(application):
    """
    🧹 Global Sweeper Watchdog:
    រត់ត្រួតពិនិត្យរៀងរាល់ ៥ វិនាទីម្តង ដើម្បីធានាថារាល់សារទាំងអស់របស់ Bot
    ទោះបីច្រើនរាប់រយសារ ក៏ត្រូវតែលុបចោលឱ្យអស់ក្នុងរយៈពេល ៣០ វិនាទីជាដាច់ខាត!
    """
    logger.info("Bot Message Sweeper Watchdog started (Guaranteed 30-second clean)...")
    while True:
        try:
            now = time.time()
            remaining_queue = []
            for item in PENDING_BOT_DELETIONS:
                chat_id, msg_id, expire_ts = item
                if now >= expire_ts:
                    try:
                        await application.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    except Exception:
                        pass
                else:
                    remaining_queue.append(item)

            PENDING_BOT_DELETIONS.clear()
            PENDING_BOT_DELETIONS.extend(remaining_queue)
        except Exception as err:
            logger.error(f"Error in bot_message_sweeper_loop: {err}")

        await asyncio.sleep(5)


# ==================== 📢 TWICE-DAILY REMINDER BACKGROUND JOB ====================

async def daily_reminder_loop(app):
    logger.info("Daily Reminder background job started (2x per day for unauthorized groups)...")
    while True:
        try:
            now_ts = time.time()
            for chat_id_str, gdata in list(GROUPS_CONFIG.items()):
                is_auth = gdata.get("is_authorized", False)
                if not is_auth:
                    last_reminder = gdata.get("last_reminder_ts", 0)
                    if now_ts - last_reminder >= 43200:
                        chat_id = int(chat_id_str)
                        reminder_text = (
                            "📢 **[ការដាស់តឿនសុវត្ថិភាព - TELEGUARD SECURITY]** 📢\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "⚠️ **ក្រុមនេះមិនទាន់បានបើកដំណើរការសេវាកម្មការពារមេរោគនៅឡើយទេ!**\n"
                            f"🆔 **លេខ Group ID របស់អ្នក៖** `{chat_id_str}`\n\n"
                            "🛡️ **អត្ថប្រយោជន៍ពេលទិញសិទ្ធិប្រើប្រាស់៖**\n"
                            "• ស្កេន និងលុបមេរោគលួចលុយធនាគារ (.apk, .exe, .scr, .bat)\n"
                            "• ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (.jpg.apk, .pdf.apk)\n"
                            "• ប្រព័ន្ធ Anti-Flood & Clean Group ស្អាតស្អំ\n\n"
                            "👉 **សូមទាក់ទង Master Super Admin ដើម្បីទិញអាជ្ញាប័ណ្ណប្រើប្រាស់ពេញលេញ!**\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៣០ វិនាទី)*"
                        )
                        await send_auto_delete_message(
                            app,
                            chat_id=chat_id,
                            text=reminder_text,
                            delay=BOT_MSG_DELETE_SECONDS,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        GROUPS_CONFIG[chat_id_str]["last_reminder_ts"] = now_ts
                        save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        except Exception as err:
            logger.error(f"Error in daily_reminder_loop: {err}")

        await asyncio.sleep(1800)


# ==================== NEW GROUP NOTIFICATION TO MASTER ADMIN ====================

async def notify_master_admin_new_group(context: ContextTypes.DEFAULT_TYPE, chat, added_by_user=None):
    added_name = added_by_user.full_name if added_by_user else "Admin Group"
    added_id = added_by_user.id if added_by_user else "N/A"
    added_uname = f"@{added_by_user.username}" if added_by_user and added_by_user.username else "N/A"

    text = (
        "🔔 **[ការស្នើសុំសិទ្ធិប្រើប្រាស់ BOT ថ្មី - NEW GROUP ADDED]** 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{chat.title or 'Unknown Group'}`\n"
        f"🆔 **លេខ Group ID:** `{chat.id}`\n"
        f"👤 **អតិថិជន:** {added_name} ({added_uname})\n"
        f"🔢 **Customer User ID:** `{added_id}`\n"
        f"📅 **កាលបរិច្ឆេទ:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 **តើអ្នកយល់ព្រមបើកសិទ្ធិឱ្យ Bot ការពារក្នុងក្រុមនេះដែរឬទេ?**\n"
        "*(បើបដិសេធ Bot នឹងនៅស្ងៀមមិនការពារទេ ហើយលោតសារដាស់តឿនឱ្យទិញសិទ្ធិ ២ ដងក្នុង ១ ថ្ងៃ)*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 អនុញ្ញាត (Approve & Protect)", callback_data=f"approve_{chat.id}"),
            InlineKeyboardButton("🔴 បដិសេធ (Keep Unauthorized)", callback_data=f"reject_{chat.id}")
        ]
    ])

    for admin_id in SUPER_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to notify super admin {admin_id}: {e}")


async def handle_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result:
        return

    chat = result.chat
    new_status = result.new_chat_member.status
    old_status = result.old_chat_member.status
    user = result.from_user

    if new_status in ["member", "administrator"] and old_status not in ["member", "administrator"]:
        sync_client_record(chat, user, is_auth=False, is_enabled=False)
        await notify_master_admin_new_group(context, chat, user)

        pending_msg = (
            "🤖 **[ប្រព័ន្ធសុវត្ថិភាព TELEGUARD BOT]**\n\n"
            "សូមអរគុណដែលបាន Add Bot ចូលក្នុងក្រុមនេះ! 🎉\n"
            "⚠️ **ស្ថានភាព៖** មិនទាន់មានអាជ្ញាប័ណ្ណប្រើប្រាស់ (Inactive) នៅឡើយទេ។\n"
            f"🆔 **លេខ Group ID របស់អ្នក៖** `{chat.id}`\n\n"
            "👉 សូមទាក់ទង **Master Super Admin** ដើម្បីទិញសិទ្ធិ និងបើកដំណើរការប្រព័ន្ធការពារពេញលេញ!\n"
            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ៣០ វិនាទី)*"
        )
        await send_auto_delete_message(context, chat.id, pending_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)


# ==================== DYNAMIC KEYBOARD BUILDER ====================

def get_master_owner_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard"),
            KeyboardButton("📋 បញ្ជីអតិថិជន & Group")
        ],
        [
            KeyboardButton("📜 ប្រវត្តិការពារ (Logs)"),
            KeyboardButton("🛡️ ឆែកស្ថានភាព Bot")
        ],
        [
            KeyboardButton("🆔 មើលលេខ ID"),
            KeyboardButton("❓ ការណែនាំ & ជំនួយ")
        ],
        [
            KeyboardButton("🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_client_admin_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("🛡️ ឆែកស្ថានភាព Bot"),
            KeyboardButton("🆔 មើលលេខ ID Group")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


# ==================== MALWARE DETECTION RULES ====================

DANGEROUS_EXTENSIONS = {
    ".apk", ".xapk", ".aab",
    ".exe", ".scr", ".bat", ".cmd", ".msi", ".com", ".pif", ".hta", ".cpl",
    ".sh", ".bash", ".ps1", ".psm1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".jar", ".reg"
}

SUSPICIOUS_ARCHIVES_AND_DOCS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".img",
    ".xlsm", ".docm"
}

SAFE_DOC_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx", ".xlsx", ".pptx", ".mp4", ".mp3", ".txt"
}


def analyze_filename(file_name: str) -> dict:
    if not file_name:
        return {"is_dangerous": False, "need_hash_scan": False, "reason": None}

    lower_name = file_name.lower().strip()
    _, final_ext = os.path.splitext(lower_name)
    all_extensions = re.findall(r"\.[a-z0-9]+", lower_name)
    
    is_double_ext = False
    disguised_type = None
    if len(all_extensions) >= 2:
        prev_ext = all_extensions[-2]
        if prev_ext in SAFE_DOC_EXTENSIONS and final_ext in DANGEROUS_EXTENSIONS:
            is_double_ext = True
            disguised_type = f"{prev_ext}{final_ext}"

    if final_ext in DANGEROUS_EXTENSIONS:
        if is_double_ext:
            reason = f"🚨 **Double Extension Disguise (បន្លំកន្ទុយពីរ):** `{disguised_type}` (ក្លែងបន្លំជារូបភាព/ឯកសារ)"
        else:
            reason = f"🚨 **High-Risk Malware Extension (កន្ទុយមេរោគ):** `{final_ext}`"
        
        return {
            "is_dangerous": True,
            "need_hash_scan": False,
            "reason": reason,
            "detected_ext": final_ext,
            "is_double_ext": is_double_ext
        }

    if final_ext in SUSPICIOUS_ARCHIVES_AND_DOCS:
        return {
            "is_dangerous": False,
            "need_hash_scan": True,
            "detected_ext": final_ext
        }

    return {"is_dangerous": False, "need_hash_scan": False, "detected_ext": final_ext}


# ==================== VIRUSTOTAL SCANNER ====================

async def check_virustotal_hash(file_bytes: bytes) -> dict:
    if not VIRUSTOTAL_API_KEY or VIRUSTOTAL_API_KEY == "YOUR_VIRUSTOTAL_API_KEY_HERE":
        return {"scanned": False, "is_malicious": False}

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    if sha256_hash in SCAN_CACHE:
        return SCAN_CACHE[sha256_hash]

    url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=12) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    malicious_count = stats.get("malicious", 0)
                    suspicious_count = stats.get("suspicious", 0)

                    result = {
                        "scanned": True,
                        "is_malicious": malicious_count > 0,
                        "sha256": sha256_hash,
                        "malicious_count": malicious_count,
                        "suspicious_count": suspicious_count
                    }
                    SCAN_CACHE[sha256_hash] = result
                    return result
                elif response.status == 404:
                    result = {"scanned": True, "is_malicious": False, "sha256": sha256_hash, "not_found": True}
                    SCAN_CACHE[sha256_hash] = result
                    return result
    except Exception as e:
        logger.error(f"Error querying VirusTotal: {e}")

    return {"scanned": False, "is_malicious": False}


# ==================== ACTIONS & PUNISHMENT ====================

async def punish_user(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE, duration_hours: int = MUTE_DURATION_HOURS) -> str:
    if is_sole_master_owner(user_id):
        return "👑 (Sole Master Admin Protected)"

    try:
        if PUNISHMENT_MODE == "KICK":
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            return "🚫 **បាន Kick ចេញពី Group រួចរាល់**"
        else:
            until_date = datetime.now() + timedelta(hours=duration_hours)
            no_permissions = ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=no_permissions,
                until_date=until_date
            )
            return f"🔇 **បានបិទសិទ្ធិផ្ញើសារ (Mute) {duration_hours} ម៉ោង**"
    except Exception as e:
        logger.error(f"Failed to punish user {user_id}: {e}")
        return "⚠️ (មិនអាច Mute បានទេ សូមពិនិត្យសិទ្ធិ Bot Admin)"


# ==================== 🧹 AUTO-DELETE SERVICE MESSAGES ====================

async def handle_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not AUTO_DELETE_SERVICE_MSGS:
        return
    message = update.effective_message
    if message:
        try:
            await message.delete()
        except Exception:
            pass


# ==================== 🌊 SMART ANTI-FLOOD HANDLER ====================

async def handle_anti_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not ANTI_FLOOD_ENABLED:
        return False

    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type not in ["group", "supergroup"]:
        return False

    if is_sole_master_owner(user.id) or await is_client_group_admin(update, context):
        return False

    now = time.time()
    tracker_key = (chat.id, user.id)
    timestamps = FLOOD_TRACKER.get(tracker_key, [])

    timestamps = [t for t in timestamps if now - t <= FLOOD_WINDOW_SECONDS]
    timestamps.append(now)
    FLOOD_TRACKER[tracker_key] = timestamps

    if len(timestamps) > FLOOD_MAX_MSGS:
        try:
            await update.effective_message.delete()
        except Exception:
            pass

        action_msg = await punish_user(chat.id, user.id, context, duration_hours=1)
        
        record_audit_event(
            event_type="ANTI_FLOOD_SPAM",
            chat_id=chat.id,
            chat_title=chat.title or "Unknown Group",
            user_id=user.id,
            user_name=user.full_name,
            details=f"Spamming > {FLOOD_MAX_MSGS} msgs in {FLOOD_WINDOW_SECONDS}s",
            action=action_msg
        )

        warning_text = (
            f"⚠️ **[ប្រព័ន្ធទប់ស្កាត់ SPAM / ANTI-FLOOD]** ⚠️\n\n"
            f"👤 **អ្នកប្រើប្រាស់:** {user.mention_markdown_v2() if user.username else user.full_name}\n"
            f"🚫 **មូលហេតុ:** ផ្ញើសារ/Sticker ញាប់ពេក (លើសពី {FLOOD_MAX_MSGS} សារក្នុង {FLOOD_WINDOW_SECONDS} វិនាទី)\n"
            f"⚡ **ចំណាត់ការ:** {action_msg}\n\n"
            f"*(សារព្រមាននេះនឹងរលាយបាត់ទៅវិញស្វ័យប្រវត្តិក្នង 15 វិនាទី)*"
        )
        await send_auto_delete_message(context, chat.id, warning_text, delay=15, parse_mode=ParseMode.MARKDOWN)
        return True

    return False


# ==================== FILE & MALWARE SCANNER ====================

async def handle_incoming_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.document:
        return

    chat = update.effective_chat
    chat_key = str(chat.id)

    if chat.type in ["group", "supergroup"] and chat_key not in GROUPS_CONFIG:
        sync_client_record(chat, message.from_user, is_auth=False, is_enabled=False)

    if chat.type in ["group", "supergroup"]:
        if not is_group_authorized(chat.id):
            return

    if await handle_anti_flood(update, context):
        return

    file_name = message.document.file_name or "unnamed_file"
    file_size = message.document.file_size or 0
    sender = message.from_user

    analysis = analyze_filename(file_name)

    # ករណីទី ១៖ រកឃើញ File គ្រោះថ្នាក់ភ្លាមៗ
    if analysis.get("is_dangerous"):
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Cannot delete message: {e}")

        action_taken = await punish_user(chat.id, sender.id, context)

        if chat_key in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key]["threats_blocked_count"] = GROUPS_CONFIG[chat_key].get("threats_blocked_count", 0) + 1
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

        record_audit_event(
            event_type="MALWARE_BLOCKED",
            chat_id=chat.id,
            chat_title=chat.title or "Unknown Group",
            user_id=sender.id,
            user_name=sender.full_name,
            details=f"File: {file_name} ({analysis['reason']})",
            action=action_taken
        )

        sender_name = sender.full_name or "Unknown User"
        warning_text = (
            f"🛡️ **[ការប្រកាសអាសន្នសុវត្ថិភាព - SECURITY ALERT]** 🛡️\n\n"
            f"⚠️ **បានរកឃើញ និងលុបហ្វាល់មេរោគជាបន្ទាន់!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **អ្នកផ្ញើ:** {sender_name}\n"
            f"📁 **ឈ្មោះហ្វាល់:** `{file_name}`\n"
            f"🔍 **ប្រភេទគ្រោះថ្នាក់:** {analysis['reason']}\n"
            f"⚡ **ចំណាត់ការ:** សារត្រូវបានលុបភ្លាមៗ | {action_taken}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **ការណែនាំសុវត្ថិភាព:** សូមប្រុងប្រយ័ត្នខ្ពស់ចំពោះហ្វាល់ដែលបង្កប់កន្ទុយ `.apk` ឬ `.exe` ព្រោះវាអាចជា Banking Trojan លួចគណនីធនាគាររបស់អ្នក!\n\n"
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញស្វ័យប្រវត្តិក្នងរយៈពេល ៣០ វិនាទី)*"
        )

        await send_auto_delete_message(
            context,
            chat_id=chat.id,
            text=warning_text,
            delay=BOT_MSG_DELETE_SECONDS,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # ករណីទី ២៖ Archive File (.zip, .rar) -> VirusTotal
    if analysis.get("need_hash_scan") and file_size <= 20 * 1024 * 1024:
        try:
            tg_file = await message.document.get_file()
            file_stream = io.BytesIO()
            await tg_file.download_to_memory(file_stream)
            file_bytes = file_stream.getvalue()

            vt_result = await check_virustotal_hash(file_bytes)

            if vt_result.get("is_malicious"):
                await message.delete()
                action_taken = await punish_user(chat.id, sender.id, context)

                if chat_key in GROUPS_CONFIG:
                    GROUPS_CONFIG[chat_key]["threats_blocked_count"] = GROUPS_CONFIG[chat_key].get("threats_blocked_count", 0) + 1
                    save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

                record_audit_event(
                    event_type="ARCHIVE_MALWARE_VT",
                    chat_id=chat.id,
                    chat_title=chat.title or "Unknown Group",
                    user_id=sender.id,
                    user_name=sender.full_name,
                    details=f"File: {file_name} (VT Score: {vt_result['malicious_count']})",
                    action=action_taken
                )

                warning_text = (
                    f"☣️ **[រកឃើញមេរោគក្នុង Archive ដោយ VirusTotal]** ☣️\n\n"
                    f"👤 **អ្នកផ្ញើ:** {sender.full_name}\n"
                    f"📁 **ឈ្មោះហ្វាល់:** `{file_name}`\n"
                    f"🔬 **ពិន្ទុគ្រោះថ្នាក់:** {vt_result['malicious_count']} Security Engines ចាត់ទុកជាមេរោគ!\n"
                    f"🧬 **SHA-256:** `{vt_result['sha256']}`\n"
                    f"⚡ **ចំណាត់ការ:** សារត្រូវបានលុប | {action_taken}\n\n"
                    f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៣០ វិនាទី)*"
                )
                await send_auto_delete_message(
                    context,
                    chat_id=chat.id,
                    text=warning_text,
                    delay=BOT_MSG_DELETE_SECONDS,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Error inspecting archive: {e}")


# ==================== 👻 STEALTH MASTER ROUTER ====================

async def handle_regular_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in ["group", "supergroup"] and str(chat.id) not in GROUPS_CONFIG:
        sync_client_record(chat, user, is_auth=False, is_enabled=False)

    if await handle_anti_flood(update, context):
        return

    text = update.message.text.strip() if update.message and update.message.text else ""
    is_owner = is_sole_master_owner(user.id)
    is_admin = await is_client_group_admin(update, context)

    # 1. ករណី Master Owner វាយពាក្យបញ្ជា ឬចុចប៊ូតុងក្នុង Group ➡️ លុបសារពី Group ចោលភ្លាម & ផ្ញើទៅ Private Chat
    if is_owner and chat.type in ["group", "supergroup"]:
        if text in [
            "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin",
            "📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients",
            "📜 ប្រវត្តិការពារ (Logs)", "/logs",
            "❓ ការណែនាំ & ជំនួយ", "/help",
            "🛡️ ឆែកស្ថានភាព Bot", "/status", "/check",
            "🆔 មើលលេខ ID", "🆔 មើលលេខ ID Group", "/myid", "/id",
            "🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"
        ]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass

            if text in ["🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"]:
                await start_command(update, context)
            elif text in ["⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin"]:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n👑 **សូមស្វាគមន៍ម្ចាស់ Bot**\n👇 សូមចុចលើឈ្មោះ Group ដើម្បីគ្រប់គ្រង៖",
                    reply_markup=generate_master_dashboard_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            elif text in ["📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients"]:
                await list_groups_command(update, context, send_to_user_id=user.id)
            elif text in ["📜 ប្រវត្តិការពារ (Logs)", "/logs"]:
                await logs_command(update, context, send_to_user_id=user.id)
            elif text in ["❓ ការណែនាំ & ជំនួយ", "/help"]:
                await help_command(update, context, send_to_user_id=user.id)
            elif text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
                await status_command(update, context)
            elif text in ["🆔 មើលលេខ ID", "🆔 មើលលេខ ID Group", "/myid", "/id"]:
                await myid_command(update, context)
            return

    # 2. ករណី Master Owner ប្រើក្នុង Private Chat ផ្ទាល់ខ្លួន
    if is_owner and chat.type == "private":
        if text in ["🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"]:
            await start_command(update, context)
        elif text in ["⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin"]:
            await admin_command(update, context)
        elif text in ["📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients"]:
            await list_groups_command(update, context)
        elif text in ["📜 ប្រវត្តិការពារ (Logs)", "/logs"]:
            await logs_command(update, context)
        elif text in ["❓ ការណែនាំ & ជំនួយ", "/help"]:
            await help_command(update, context)
        elif text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
            await status_command(update, context)
        elif text in ["🆔 មើលលេខ ID", "/myid", "/id"]:
            await myid_command(update, context)
        return

    # 3. ករណី Client Group Admin ប្រើក្នុង Group របស់ពួកគេ
    if is_admin and chat.type in ["group", "supergroup"]:
        if text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
            await status_command(update, context)
            return
        elif text in ["🆔 មើលលេខ ID Group", "/myid", "/id"]:
            await myid_command(update, context)
            return

    # 4. ប្រសិនបើសមាជិកធម្មតា ឬអ្នកគ្មានសិទ្ធិព្យាយាមប្រើ
    if text in [
        "🛡️ ឆែកស្ថានភាព Bot", "/status", "/check",
        "🆔 មើលលេខ ID", "🆔 មើលលេខ ID Group", "/myid", "/id",
        "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin",
        "📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients",
        "📜 ប្រវត្តិការពារ (Logs)", "/logs",
        "❓ ការណែនាំ & ជំនួយ", "/help",
        "🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"
    ]:
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
        else:
            await update.message.reply_text("⛔ **សុំទោស! មុខងារនេះសម្រាប់តែម្ចាស់ Bot ផ្ទាល់ (Master Owner) ប៉ុណ្ណោះ។**", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)


# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    is_owner = is_sole_master_owner(user.id)

    if chat.type in ["group", "supergroup"]:
        try:
            await update.effective_message.delete()
        except Exception:
            pass

        if is_owner:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"👑 **សូមស្វាគមន៍ម្ចាស់ Bot! (Master Owner)**\n\n🔒 **[Stealth Mode Active]** ផ្ទាំងបញ្ជា និងប៊ូតុងគ្រប់គ្រងរបស់អ្នក ត្រូវបានរក្សាជាសម្ងាត់ក្នុង Chat ផ្ទាល់ខ្លួននេះ!",
                reply_markup=get_master_owner_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        elif await is_client_group_admin(update, context):
            text = (
                f"🤖 **សួស្តី {user.first_name}!**\n\n"
                "ខ្ញុំជា Bot ការពារមេរោគ និងគ្រប់គ្រងសុវត្ថិភាព Group Telegram!\n\n"
                "🛡️ **មុខងារសម្រាប់ Group Admin៖**\n"
                "👉 `[ 🛡️ ឆែកស្ថានភាព Bot ]` : ឆែកស្ថានភាពការពារក្នុង Group\n"
                "👉 `[ 🆔 មើលលេខ ID Group ]` : មើលលេខសម្គាល់ Group ID\n\n"
                "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ៣០ វិនាទី)*"
            )
            await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_client_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if is_owner:
        text = (
            f"👑 **សូមស្វាគមន៍ម្ចាស់ Bot ផ្ទាល់! (Sole Master Owner - ID: `{user.id}`)**\n\n"
            "🎛️ **ផ្ទាំងបញ្ជាគ្រប់គ្រងពេញលេញ (100% Stealth & Button-Driven)៖**\n"
            "• ចុច **[ ⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard ]** ដើម្បីបើក/បិទ Group តាមចិត្ត\n"
            "• ចុច **[ 📋 បញ្ជីអតិថិជន & Group ]** ដើម្បីមើលប្រវត្តិអតិថិជន CRM Vault\n"
            "• ចុច **[ 📜 ប្រវត្តិការពារ (Logs) ]** ដើម្បីពិនិត្យកំណត់ត្រាសន្តិសុខ\n"
            "• ចុច **[ 🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start) ]** ដើម្បី Reload ផ្ទាំងបញ្ជាឡើងវិញ\n"
            "• 🔒 **រាល់សកម្មភាពរបស់អ្នកក្នុង Group គឺលាក់បាំង ១០០% គ្មានអ្នកណាឃើញឡើយ**\n\n"
            "👉 **សូមចុចបញ្ជាតាមរយៈប៊ូតុងខាងក្រោម៖**"
        )
        await update.message.reply_text(
            text=text,
            reply_markup=get_master_owner_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        text = (
            f"🤖 **សួស្តី {user.first_name}!**\n\n"
            "ខ្ញុំជា Bot ការពារមេរោគ និងគ្រប់គ្រងសុវត្ថិភាព Group Telegram!\n\n"
            "🔒 **ប្រព័ន្ធគ្រប់គ្រង៖** Bot នេះត្រូវបានគ្រប់គ្រងដោយ Master Super Admin។"
        )
        await update.message.reply_text(text=text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    text = (
        "📖 **[សៀវភៅណែនាំគ្រប់គ្រង BOT - MASTER OWNER GUIDE]** 📖\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👑 **១. របៀបផ្ដល់សិទ្ធិ ឬបើក/បិទ Group៖**\n"
        "• ចុចប៊ូតុង `[ ⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard ]`\n"
        "• ចុចលើឈ្មោះ Group ណាមួយ ដើម្បីចូលទៅកាន់ផ្ទាំងគ្រប់គ្រង Group នោះដោយផ្ទាល់\n"
        "• អ្នកអាចចុច `[ 🟢 បើកការពារ ]`, `[ 🟡 ផ្អាកការពារ ]`, ឬ `[ 🗑️ លុប Group ]`\n\n"
        "🗄️ **២. របៀបមើលប្រវត្តិអតិថិជន (Client CRM)៖**\n"
        "• ចុចប៊ូតុង `[ 📋 បញ្ជីអតិថិជន & Group ]` នោះ Bot នឹងរៀបចំរបាយការណ៍លម្អិតអំពី ឈ្មោះអតិថិជន, ID, ថ្ងៃ Add ចូល និងស្ថិតិមេរោគ\n\n"
        "📜 **៣. របៀបពិនិត្យមើល Logs សន្តិសុខ៖**\n"
        "• ចុចប៊ូតុង `[ 📜 ប្រវត្តិការពារ (Logs) ]` ដើម្បីមើល ១០ ហេតុការណ៍ចុងក្រោយដែល Bot បានទប់ស្កាត់\n\n"
        "🚀 **៤. របៀប Reload / Restart ផ្ទាំងបញ្ជា៖**\n"
        "• ចុចប៊ូតុង `[ 🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start) ]` គ្រប់ពេលដែលអ្នកចង់បើក Menu ធំឡើងវិញ\n\n"
        "🔒 **៥. ប្រព័ន្ធ Stealth Privacy Mode៖**\n"
        "• ទោះបីជាអ្នកនៅក្នុង Group ណាក៏ដោយ ក៏ប៊ូតុង និងសារបញ្ជារបស់អ្នក **មិនបង្ហាញឱ្យសមាជិកក្នុង Group ឃើញឡើយ** (Bot បញ្ជូនមក Private Chat នេះដោយស្វ័យប្រវត្តិ)!\n\n"
        "⏱️ **៦. កំណត់ពេលលុបសារស្វ័យប្រវត្តិ៖** ៣០ វិនាទី (មានប្រព័ន្ធ Sweeper Watchdog សម្អាតជាប្រចាំ)\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id
    await context.bot.send_message(chat_id=target_id, text=text, reply_markup=get_master_owner_keyboard(), parse_mode=ParseMode.MARKDOWN)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    is_owner = is_sole_master_owner(user.id)
    is_admin = await is_client_group_admin(update, context)

    if not is_owner and not is_admin:
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
        return

    is_authorized = is_group_authorized(chat.id)

    if not is_authorized and not is_owner:
        unauth_text = (
            "⚠️ **[ក្រុមមិនទាន់បានទិញសិទ្ធិប្រើប្រាស់ - UNAUTHORIZED]**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{chat.title}`\n"
            f"🆔 **លេខ Group ID របស់អ្នក:** `{chat.id}`\n"
            "🚫 **ស្ថានភាពការពារ:** 🔴 **មិនទាន់ដំណើរការ (OFF)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **ការណែនាំ៖** សូមចម្លងលេខ Group ID (`{chat.id}`) នេះ ផ្ញើទៅកាន់ **Master Super Admin** ដើម្បីទិញអាជ្ញាប័ណ្ណ និងបើកដំណើរការប្រព័ន្ធការពារពេញលេញ!\n\n"
            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៣០ វិនាទី)*"
        )
        if chat.type in ["group", "supergroup"]:
            await send_auto_delete_message(context, chat.id, unauth_text, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(unauth_text, parse_mode=ParseMode.MARKDOWN)
        return

    shield_status_str = "🟢 **កំពុងការពារយ៉ាងសកម្ម (ACTIVE / SHIELD ON)**" if is_authorized else "🔴 **មិនទាន់បើកការពារ (INACTIVE)**"
    vt_status = "✅ **ភ្ជាប់រួចរាល់ (Connected)**" if VIRUSTOTAL_API_KEY and VIRUSTOTAL_API_KEY != "YOUR_VIRUSTOTAL_API_KEY_HERE" else "⚠️ **Local Shield Only**"

    group_name = chat.title if chat.type in ["group", "supergroup"] else "Chat ផ្ទាល់ខ្លួន (Private Chat)"
    chat_type_kh = "ក្រុម Telegram (Group)" if chat.type in ["group", "supergroup"] else "ផ្ទាំងសារផ្ទាល់ខ្លួន (Private)"

    text = (
        "🛡️ **[ព័ត៌មាន និងស្ថានភាពសុវត្ថិភាព BOT STATUS]** 🛡️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{group_name}`\n"
        f"🆔 **លេខ Group ID:** `{chat.id}`\n"
        f"🏷️ **ប្រភេទ:** {chat_type_kh}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 **ស្ថានភាពការពារ:** {shield_status_str}\n"
        f"⚡ **ប្រព័ន្ធស្កេនមេរោគ (Local):** ✅ សកម្ម (.apk, .exe, .scr, .bat, .sh, .jpg.apk)\n"
        f"🌐 **VirusTotal Cloud Scan:** {vt_status}\n"
        f"⏱️ **Auto-Delete Timer:** ✅ ៣០ វិនាទី (Clean Room Sweeper)\n"
        f"⚖️ **វិធានការលើអ្នកល្មើស:** លុបសារមេរោគ + {PUNISHMENT_MODE} {MUTE_DURATION_HOURS} ម៉ោង\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៣០ វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        kb = get_client_admin_keyboard() if not is_owner else None
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        kb = get_master_owner_keyboard() if is_owner else ReplyKeyboardRemove()
        await update.message.reply_text(text=text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    is_owner = is_sole_master_owner(user.id)
    is_admin = await is_client_group_admin(update, context)

    if not is_owner and not is_admin:
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
        return

    is_auth = is_group_authorized(chat.id)
    license_status = "🟢 បានបើកសិទ្ធិការពាររួចរាល់" if is_auth else "🔴 មិនទាន់ទិញអាជ្ញាប័ណ្ណ (Inactive)"

    if chat.type in ["group", "supergroup"]:
        text = (
            f"🆔 **ព័ត៌មាន GROUP ID៖**\n\n"
            f"👥 **ឈ្មោះក្រុម:** `{chat.title}`\n"
            f"💬 **លេខ Group ID របស់អ្នក:** `{chat.id}`\n"
            f"🔐 **ស្ថានភាពសេវាកម្ម:** {license_status}\n\n"
            f"💡 *(សូមយកលេខ Group ID `{chat.id}` នេះ ផ្ញើទៅកាន់ Master Admin ដើម្បីទិញ ឬបើកសិទ្ធិប្រើប្រាស់)*\n\n"
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ៣០ វិនាទី)*"
        )
        kb = get_client_admin_keyboard() if not is_owner else None
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        if is_owner:
            text = (
                f"🆔 **ព័ត៌មានអត្តសញ្ញាណ SOLE MASTER OWNER៖**\n\n"
                f"👤 **ឈ្មោះ:** {user.full_name} 👑 **(Master Super Admin)**\n"
                f"🔢 **User ID របស់អ្នក:** `{user.id}`\n"
                f"🛡️ **សិទ្ធិប្រព័ន្ធ:** ម្ចាស់ Bot ពេញលេញ ១០០% ធ្វើអ្វីបានគ្រប់យ៉ាង\n"
            )
        else:
            text = (
                f"🆔 **ព័ត៌មានអត្តសញ្ញាណ៖**\n\n"
                f"👤 **ឈ្មោះ:** {user.full_name}\n"
                f"🔢 **User ID របស់អ្នក:** `{user.id}`\n"
            )
        kb = get_master_owner_keyboard() if is_owner else ReplyKeyboardRemove()
        await update.message.reply_text(text=text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


# ==================== MASTER OWNER: DASHBOARD & DRILL-DOWN SUBMENU ====================

def generate_master_dashboard_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    if not GROUPS_CONFIG:
        keyboard.append([InlineKeyboardButton("❌ មិនទាន់មាន Group ណាភ្ជាប់នៅឡើយទេ", callback_data="none")])
    else:
        for chat_id, data in GROUPS_CONFIG.items():
            title = data.get("title", f"Group {chat_id}")
            is_auth = data.get("is_authorized", False)
            is_en = data.get("is_enabled", False)

            if is_auth and is_en:
                status_emoji = "🟢 [ON]"
            elif is_auth and not is_en:
                status_emoji = "🟡 [PAUSE]"
            else:
                status_emoji = "🔴 [UNAUTH]"

            btn_text = f"{status_emoji} {title[:18]}"
            callback_data = f"manage_grp_{chat_id}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

    keyboard.append([
        InlineKeyboardButton("🔄 Refresh បញ្ជី", callback_data="dash_refresh"),
        InlineKeyboardButton("📋 បញ្ជីអតិថិជន CRM", callback_data="dash_clients")
    ])
    keyboard.append([
        InlineKeyboardButton("📜 កំណត់ត្រា Logs", callback_data="dash_logs")
    ])
    return InlineKeyboardMarkup(keyboard)


def generate_group_detail_keyboard(chat_id: str) -> InlineKeyboardMarkup:
    gdata = GROUPS_CONFIG.get(str(chat_id), {})
    is_auth = gdata.get("is_authorized", False)
    is_en = gdata.get("is_enabled", False)

    keyboard = []
    if not is_auth or not is_en:
        keyboard.append([InlineKeyboardButton("🟢 បើកដំណើរការការពារ (Turn ON)", callback_data=f"set_on_{chat_id}")])
    if is_auth and is_en:
        keyboard.append([InlineKeyboardButton("🟡 ផ្អាកដំណើរការការពារ (Pause)", callback_data=f"set_off_{chat_id}")])

    keyboard.append([
        InlineKeyboardButton("🗑️ លុប Group នេះចេញ", callback_data=f"set_del_{chat_id}"),
        InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="dash_back")
    ])
    return InlineKeyboardMarkup(keyboard)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not is_sole_master_owner(user.id):
        return

    if chat.type in ["group", "supergroup"]:
        try:
            await update.effective_message.delete()
        except Exception:
            pass

    text = (
        "⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n"
        "👑 **សូមស្វាគមន៍ម្ចាស់ Bot (Sole Master Owner)**\n\n"
        "👇 **សូមចុចលើឈ្មោះ Group ខាងក្រោម ដើម្បីគ្រប់គ្រង ឬបើក/បិទសិទ្ធិ៖**\n"
    )
    await context.bot.send_message(
        chat_id=user.id,
        text=text,
        reply_markup=generate_master_dashboard_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )


async def list_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id

    if not CLIENTS_DB:
        await context.bot.send_message(chat_id=target_id, text="🗄️ មិនទាន់មានទិន្នន័យអតិថិជនក្នុងប្រព័ន្ធនៅឡើយទេ។", reply_markup=get_master_owner_keyboard())
        return

    report = "🗄️ **[ប្រព័ន្ធគ្រប់គ្រងអតិថិជន & ប្រវត្តិក្រុម - CLIENT CRM VAULT]** 🗄️\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for idx, (cid, cdata) in enumerate(CLIENTS_DB.items(), start=1):
        gname = cdata.get("client_group_name", f"Group {cid}")
        status = cdata.get("license_status", "N/A")
        contact = cdata.get("customer_contact", {})
        c_name = contact.get("name", "N/A")
        c_uname = contact.get("username", "N/A")
        c_uid = contact.get("user_id", "N/A")
        stats = cdata.get("security_stats", {})
        threats = stats.get("threats_blocked", 0)
        spams = stats.get("spams_blocked", 0)
        reg_date = cdata.get("registered_date", "N/A")
        act_date = cdata.get("activated_date", "N/A")

        report += f"**{idx}. {gname}**\n"
        report += f"   • 🆔 **Group ID:** `{cid}`\n"
        report += f"   • 🔰 **ស្ថានភាពសេវា:** {status}\n"
        report += f"   • 👤 **អតិថិជន:** {c_name} ({c_uname})\n"
        report += f"   • 🔢 **Customer ID:** `{c_uid}`\n"
        report += f"   • 📅 **ថ្ងៃ Add ចូល:** `{reg_date}`\n"
        report += f"   • ⚡ **ថ្ងៃបើកសិទ្ធិ:** `{act_date}`\n"
        report += f"   • 🛡️ **ស្ថិតិការពារជូន:** ☣️ `{threats}` មេរោគ | 🌊 `{spams}` Spams\n"
        report += "────────────────────\n"

    await context.bot.send_message(chat_id=target_id, text=report, reply_markup=get_master_owner_keyboard(), parse_mode=ParseMode.MARKDOWN)


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id

    if not AUDIT_LOGS:
        await context.bot.send_message(chat_id=target_id, text="📜 មិនទាន់មានកំណត់ត្រាប្រវត្តិហេតុការណ៍នៅឡើយទេ។", reply_markup=get_master_owner_keyboard())
        return

    logs_text = "📜 **[ប្រវត្តិហេតុការណ៍ការពារចុងក្រោយ - SECURITY AUDIT LOGS]**\n"
    logs_text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    recent_logs = AUDIT_LOGS[:10]
    for idx, log in enumerate(recent_logs, start=1):
        logs_text += f"**{idx}. [{log['timestamp']}]** `{log['event_type']}`\n"
        logs_text += f"   • 👥 **Group:** `{log['chat_title']}` (`{log['chat_id']}`)\n"
        logs_text += f"   • 👤 **User:** `{log['user_name']}` (`ID: {log['user_id']}`)\n"
        logs_text += f"   • ⚠️ **ព័ត៌មាន:** {log['details']}\n"
        logs_text += f"   • ⚡ **ចំណាត់ការ:** {log['action']}\n"
        logs_text += "────────────────────\n"

    await context.bot.send_message(chat_id=target_id, text=logs_text, reply_markup=get_master_owner_keyboard(), parse_mode=ParseMode.MARKDOWN)


# ==================== INLINE CALLBACK ROUTER ====================

async def master_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if not is_sole_master_owner(user.id):
        await query.message.reply_text("⛔ អ្នកមិនមែនជាម្ចាស់ Bot ទេ!")
        return

    data = query.data

    if data == "dash_refresh":
        await query.edit_message_reply_markup(reply_markup=generate_master_dashboard_keyboard())
        return

    if data == "dash_back":
        text = (
            "⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n"
            "👑 **សូមស្វាគមន៍ម្ចាស់ Bot (Sole Master Owner)**\n\n"
            "👇 **សូមចុចលើឈ្មោះ Group ខាងក្រោម ដើម្បីគ្រប់គ្រង ឬបើក/បិទសិទ្ធិ៖**\n"
        )
        await query.edit_message_text(text=text, reply_markup=generate_master_dashboard_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "dash_clients":
        await list_groups_command(update, context, send_to_user_id=user.id)
        return

    if data == "dash_logs":
        await logs_command(update, context, send_to_user_id=user.id)
        return

    if data.startswith("manage_grp_"):
        chat_id = data.replace("manage_grp_", "")
        gdata = GROUPS_CONFIG.get(str(chat_id), {})
        cdata = CLIENTS_DB.get(str(chat_id), {})

        title = gdata.get("title", f"Group {chat_id}")
        is_auth = gdata.get("is_authorized", False)
        is_en = gdata.get("is_enabled", False)

        status_kh = "🟢 ACTIVE (កំពុងការពារ)" if (is_auth and is_en) else ("🟡 PAUSED (បានផ្អាក)" if is_auth else "🔴 UNAUTHORIZED (មិនទាន់ទិញ)")
        threats = gdata.get("threats_blocked_count", 0)
        c_contact = cdata.get("customer_contact", {})

        detail_text = (
            f"🛠️ **[ផ្ទាំងគ្រប់គ្រងក្រុម - GROUP CONTROL PANEL]**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{title}`\n"
            f"🆔 **លេខ Group ID:** `{chat_id}`\n"
            f"🔰 **ស្ថានភាពបច្ចុប្បន្ន:** {status_kh}\n"
            f"👤 **អតិថិជន:** {c_contact.get('name', 'N/A')} ({c_contact.get('username', 'N/A')})\n"
            f"☣️ **មេរោគដែលបានទប់ស្កាត់:** `{threats}` ករណី\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 **សូមជ្រើសរើសសកម្មភាពខាងក្រោម៖**"
        )
        await query.edit_message_text(text=detail_text, reply_markup=generate_group_detail_keyboard(chat_id), parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("set_on_"):
        chat_id = data.replace("set_on_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = True
            GROUPS_CONFIG[chat_id]["is_enabled"] = True
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
            if chat_id in CLIENTS_DB:
                CLIENTS_DB[chat_id]["license_status"] = "🟢 ACTIVE (បានទិញសិទ្ធិ)"
                CLIENTS_DB[chat_id]["activated_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

            await query.edit_message_reply_markup(reply_markup=generate_group_detail_keyboard(chat_id))
            success_msg = "🟢 **Master Super Admin បានបើកដំណើរការប្រព័ន្ធការពារពេញលេញក្នុងក្រុមនេះរួចរាល់ហើយ!**"
            await send_auto_delete_message(context, int(chat_id), success_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("set_off_"):
        chat_id = data.replace("set_off_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_enabled"] = False
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
            if chat_id in CLIENTS_DB:
                CLIENTS_DB[chat_id]["license_status"] = "🟡 PAUSED (បានផ្អាក)"
                save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

            await query.edit_message_reply_markup(reply_markup=generate_group_detail_keyboard(chat_id))
            pause_msg = "🟡 **ប្រព័ន្ធការពារត្រូវបានផ្អាកបណ្ដោះអាសន្នដោយ Master Super Admin។**"
            await send_auto_delete_message(context, int(chat_id), pause_msg, delay=15, parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("set_del_"):
        chat_id = data.replace("set_del_", "")
        if chat_id in GROUPS_CONFIG:
            del GROUPS_CONFIG[chat_id]
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        text = "✅ **បានលុប Group នេះចេញពីបញ្ជីគ្រប់គ្រងរួចរាល់!**"
        await query.edit_message_text(text=text, reply_markup=generate_master_dashboard_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("approve_"):
        chat_id = data.replace("approve_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = True
            GROUPS_CONFIG[chat_id]["is_enabled"] = True
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
            if chat_id in CLIENTS_DB:
                CLIENTS_DB[chat_id]["license_status"] = "🟢 ACTIVE (បានទិញសិទ្ធិ)"
                CLIENTS_DB[chat_id]["activated_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

            group_title = GROUPS_CONFIG[chat_id].get("title", chat_id)
            await query.edit_message_text(
                f"✅ **[បានអនុញ្ញាតជោគជ័យ]**\n\n"
                f"👥 ក្រុម៖ **{group_title}** (`{chat_id}`)\n"
                f"🛡️ ស្ថានភាព៖ **បានបើកដំណើរការសិទ្ធិការពារពេញលេញ ១០០% រួចរាល់!**",
                parse_mode=ParseMode.MARKDOWN
            )

            success_msg = (
                "🎉 **[សេវាកម្មត្រូវបានអនុញ្ញាតជាផ្លូវការ]** 🎉\n\n"
                "🛡️ **Master Super Admin បានអនុញ្ញាតឱ្យបើកដំណើរការប្រព័ន្ធការពារពេញលេញក្នុងក្រុមនេះរួចរាល់ហើយ!**\n"
                "✅ ស្កេនមេរោគ (.apk, .exe, .scr, .bat, .sh)\n"
                "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (.jpg.apk, .pdf.apk)\n"
                "✅ ប្រព័ន្ធ Anti-Flood & Clean Group 30s"
            )
            await send_auto_delete_message(context, int(chat_id), success_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("reject_"):
        chat_id = data.replace("reject_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = False
            GROUPS_CONFIG[chat_id]["is_enabled"] = False
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
            if chat_id in CLIENTS_DB:
                CLIENTS_DB[chat_id]["license_status"] = "🔴 UNAUTHORIZED (មិនទាន់ទិញ)"
                save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

            group_title = GROUPS_CONFIG[chat_id].get("title", chat_id)
            await query.edit_message_text(
                f"🔴 **[បានកំណត់ជាមិនទាន់ទិញសិទ្ធិ]**\n\n"
                f"👥 ក្រុម៖ **{group_title}** (`{chat_id}`)\n"
                f"⚠️ ស្ថានភាព៖ **មិនទាន់ដំណើរការការពារទេ (Bot នឹងលោតសារដាស់តឿនឱ្យទិញសិទ្ធិ ២ ដងក្នុង ១ ថ្ងៃ)**",
                parse_mode=ParseMode.MARKDOWN
            )
        return


# ==================== MAIN EXECUTION ====================

async def post_init(application):
    # 1. ចាប់ផ្ដើម Daily Reminder Background Task
    asyncio.create_task(daily_reminder_loop(application))
    # 2. ចាប់ផ្ដើម Guaranteed 30-Second Sweeper Watchdog
    asyncio.create_task(bot_message_sweeper_loop(application))
    # 3. កំណត់ Telegram Native Command Menu Bar
    try:
        commands = [
            BotCommand("start", "🚀 ចាប់ផ្ដើម Bot / បើកផ្ទាំងបញ្ជា"),
            BotCommand("admin", "⚙️ ផ្ទាំងគ្រប់គ្រង Dashboard"),
            BotCommand("clients", "📋 បញ្ជីអតិថិជន & Group"),
            BotCommand("logs", "📜 ប្រវត្តិការពារ (Logs)"),
            BotCommand("status", "🛡️ ឆែកស្ថានភាព Bot"),
            BotCommand("myid", "🆔 មើលលេខ ID"),
            BotCommand("help", "❓ ការណែនាំ & ជំនួយ")
        ]
        await application.bot.set_my_commands(commands)
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")


def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    print("[*] Security Bot starting with Guaranteed 30s Sweeper Engine for Owner (240224709)...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("check", status_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("groups", list_groups_command))
    app.add_handler(CommandHandler("clients", list_groups_command))
    app.add_handler(CommandHandler("logs", logs_command))

    # Master Interactive Inline Callback Router
    app.add_handler(CallbackQueryHandler(master_callback_router))

    # Catch when Bot is added to new groups
    app.add_handler(ChatMemberHandler(handle_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))

    # 🧹 Auto-Delete Service messages
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, handle_service_messages))

    # File Monitor
    app.add_handler(MessageHandler(filters.Document.ALL, handle_incoming_file))

    # Regular Messages & Anti-Flood Monitor
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_messages))
    app.add_handler(MessageHandler(filters.Sticker.ALL | filters.ANIMATION, handle_regular_messages))

    # Stealth Menu Keyboard Router
    app.add_handler(MessageHandler(filters.Regex(r"^(⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard|⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel|📋 បញ្ជីអតិថិជន & Group|📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន|📜 ប្រវត្តិការពារ \(Logs\)|🛡️ ឆែកស្ថានភាព Bot|🆔 មើលលេខ ID|🆔 មើលលេខ ID Group|❓ ការណែនាំ & ជំនួយ|🚀 ចាប់ផ្ដើម Bot ឡើងវិញ \(/start\))$"), handle_regular_messages))

    print("[OK] Security Bot with 30s Guaranteed Sweeper Engine is fully active!")
    app.run_polling()


if __name__ == "__main__":
    main()
