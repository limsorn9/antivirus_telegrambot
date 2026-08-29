"""
=============================================================================
🛡️ TELEGRAM GROUP MALWARE & THREAT GUARD BOT (FULL COMMERCIAL CRM & CHANNEL)
=============================================================================
Author: Cybersecurity & Telegram Defense Bot
Sole Bot Owner: 240224709 (Master Super Admin)
Official Channel: https://t.me/sornsecurityrobot (@sornsecurityrobot)

Core Features:
1. 📋 Client Database & CRM: មើលបញ្ជីអតិថិជន កញ្ចប់សេវា ថ្ងៃទិញ និងរយៈពេលនៅសល់
2. 📜 Security & Purchase Logs: ប្រវត្តិកំចាត់មេរោគ និងប្រវត្តិទិញបតលម្អិត
3. ⚙️ Interactive Group Profile & License Config:
   - ចុចលើឈ្មោះ Group នីមួយៗក្នុង Dashboard ដើម្បីមើល៖
     • ឈ្មោះ Group & ID, ឈ្មោះអតិថិជន & Contact
     • ប្រវត្តិទិញបត, ថ្ងៃចាប់ផ្តើមទិញ, ថ្ងៃផុតកំណត់, រយៈពេលនៅសល់ (Days Left)
   - ប៊ូតុងកំណត់សិទ្ធិ៖ [ ➕ 30 ថ្ងៃ ], [ ➕ 90 ថ្ងៃ ], [ 👑 ពេញមួយជីវិត ], [ 🔴 ដកសិទ្ធិ ], [ 🟢 បើក ], [ 🟡 ផ្អាក ], [ 🗑️ លុប ]
4. 📢 Channel Marketing Broadcast: ផ្សាយពាណិជ្ជកម្មទៅកាន់ Channel @sornsecurityrobot ផ្ដាច់មុខ
5. 🚀 Start Bot Button & Native Command Menu
6. ⏱️ 30-Second Auto-Delete & Sweeper Watchdog
7. 👻 Stealth Master Privacy: លាក់បាំងសកម្មភាព Master ក្នុង Group ១០០%
8. 🛡️ Two-Tier Clean Isolation: Master Owner (ពេញលេញ) vs Client Admin (២ ប៊ូតុង)
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
    KeyboardButtonRequestChat,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands,
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

# Official Marketing Channel របស់ម្ចាស់ Bot
OFFICIAL_CHANNEL_USERNAME = "@sornsecurityrobot"
OFFICIAL_CHANNEL_LINK = "https://t.me/sornsecurityrobot"

PUNISHMENT_MODE = os.getenv("PUNISHMENT_MODE", "MUTE").upper().strip()
MUTE_DURATION_HOURS = int(os.getenv("MUTE_DURATION_HOURS", "24"))

# Settings សម្រាប់ភាពស្អាតក្នុង Chat និង Group (កំណត់លុបត្រឹម ១៥ វិនាទី)
AUTO_DELETE_SERVICE_MSGS = os.getenv("AUTO_DELETE_SERVICE_MSGS", "true").lower() == "true"
BOT_MSG_DELETE_SECONDS = int(os.getenv("BOT_MSG_DELETE_SECONDS", "15"))
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
ACTIVE_DELETION_TASKS = {}  # (chat_id, message_id) -> asyncio.Task
WAITING_FOR_GROUP_ID = {}  # user_id -> True (ពេលកំពុងរង់ចាំ Master វាយលេខ Group ID)


# ==================== 🗄️ PRODUCTION STORAGE (REAL GROUPS ONLY) ====================

DEFAULT_GROUPS_VAULT = {}
DEFAULT_CLIENTS_VAULT = {}
DEFAULT_AUDIT_LOGS_VAULT = []


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


def get_remaining_time_str(expiry_date_str: str, is_lifetime: bool = False) -> str:
    """គណនារយៈពេលនៅសល់ច្បាស់លាស់ (ថ្ងៃ និងម៉ោង)"""
    if is_lifetime or expiry_date_str == "Lifetime":
        return "👑 គ្មានថ្ងៃផុតកំណត់ (Lifetime VIP)"
    if not expiry_date_str or expiry_date_str in ["N/A", "Not Yet Activated"]:
        return "🔴 មិនទាន់ទិញ (0 ថ្ងៃ)"
    try:
        exp = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = exp - now
        if diff.total_seconds() <= 0:
            return "🔴 ផុតកំណត់ហើយ (Expired)"
        days = diff.days
        hours = int(diff.seconds // 3600)
        return f"⏳ នៅសល់ {days} ថ្ងៃ {hours} ម៉ោង"
    except Exception:
        return f"⏳ {expiry_date_str}"


def sync_client_record(chat, user=None, is_auth=None, is_enabled=None, plan_days=None, is_lifetime=False):
    chat_key = str(chat.id)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    exp_str = "Not Yet Activated"
    plan_name = "Trial / Not Activated"

    if is_lifetime:
        exp_str = "Lifetime"
        plan_name = "👑 Lifetime VIP (ពេញមួយជីវិត)"
    elif plan_days:
        exp_dt = now + timedelta(days=plan_days)
        exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
        plan_name = f"Plan {plan_days} Days (កញ្ចប់ {plan_days} ថ្ងៃ)"

    if chat_key not in GROUPS_CONFIG:
        GROUPS_CONFIG[chat_key] = {
            "title": chat.title or "Unknown Group",
            "chat_id": chat.id,
            "added_at": now_str,
            "is_authorized": False if is_auth is None else is_auth,
            "is_enabled": False if is_enabled is None else is_enabled,
            "plan_type": plan_name,
            "is_lifetime": is_lifetime,
            "activated_date": now_str if (is_auth is True) else "Not Yet Activated",
            "expiry_date": exp_str,
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
        if is_lifetime:
            GROUPS_CONFIG[chat_key]["is_lifetime"] = True
            GROUPS_CONFIG[chat_key]["plan_type"] = "👑 Lifetime VIP"
            GROUPS_CONFIG[chat_key]["expiry_date"] = "Lifetime"
        elif plan_days:
            GROUPS_CONFIG[chat_key]["is_lifetime"] = False
            GROUPS_CONFIG[chat_key]["plan_type"] = f"Plan {plan_days} Days"
            GROUPS_CONFIG[chat_key]["expiry_date"] = exp_str

    save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

    if chat_key not in CLIENTS_DB:
        CLIENTS_DB[chat_key] = {
            "client_group_id": chat.id,
            "client_group_name": chat.title or "Unknown Group",
            "registered_date": now_str,
            "activated_date": now_str if (is_auth is True) else "Not Yet Activated",
            "expiry_date": exp_str,
            "plan_type": plan_name,
            "is_lifetime": is_lifetime,
            "license_status": "🟢 ACTIVE (បានទិញសិទ្ធិ)" if (is_auth is True) else "🔴 UNAUTHORIZED (មិនទាន់ទិញ)",
            "customer_contact": {
                "name": user.full_name if user else "Group Admin",
                "user_id": str(user.id) if user else "N/A",
                "username": f"@{user.username}" if user and user.username else "N/A"
            },
            "purchase_history": [
                {
                    "package": plan_name,
                    "purchased_date": now_str if (is_auth is True) else "N/A",
                    "duration": f"{plan_days} Days" if plan_days else ("Lifetime" if is_lifetime else "None"),
                    "status": "Active" if (is_auth is True) else "Pending"
                }
            ],
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

        if is_lifetime:
            CLIENTS_DB[chat_key]["is_lifetime"] = True
            CLIENTS_DB[chat_key]["expiry_date"] = "Lifetime"
            CLIENTS_DB[chat_key]["plan_type"] = "👑 Lifetime VIP (ពេញមួយជីវិត)"
            CLIENTS_DB[chat_key].setdefault("purchase_history", []).append({
                "package": "👑 Lifetime VIP",
                "purchased_date": now_str,
                "duration": "Lifetime",
                "status": "Active"
            })
        elif plan_days:
            CLIENTS_DB[chat_key]["is_lifetime"] = False
            CLIENTS_DB[chat_key]["expiry_date"] = exp_str
            CLIENTS_DB[chat_key]["plan_type"] = f"Plan {plan_days} Days (កញ្ចប់ {plan_days} ថ្ងៃ)"
            CLIENTS_DB[chat_key].setdefault("purchase_history", []).append({
                "package": f"Plan {plan_days} Days",
                "purchased_date": now_str,
                "duration": f"{plan_days} Days",
                "status": "Active"
            })

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
        gdata = GROUPS_CONFIG[chat_key]
        if not (gdata.get("is_authorized", False) and gdata.get("is_enabled", False)):
            return False
        # ពិនិត្យមើលថ្ងៃផុតកំណត់
        if gdata.get("is_lifetime", False):
            return True
        exp_str = gdata.get("expiry_date", "")
        if exp_str and exp_str != "Lifetime" and exp_str != "Not Yet Activated":
            try:
                exp = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > exp:
                    return False
            except Exception:
                pass
        return True
    return False


# ==================== ⏱️ DUAL 30-SECOND AUTO-DELETE & SWEEPER ENGINE ====================

async def delete_message_after_delay(bot, chat_id: int, message_id: int, delay_seconds: int = BOT_MSG_DELETE_SECONDS):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def send_auto_delete_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = BOT_MSG_DELETE_SECONDS, **kwargs):
    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        if msg:
            asyncio.create_task(delete_message_after_delay(context.bot, chat_id, msg.message_id, delay))
            if chat_id < 0:
                PENDING_BOT_DELETIONS.append((chat_id, msg.message_id, time.time() + delay))
        return msg
    except Exception as e:
        logger.error(f"Error sending auto-delete message: {e}")
        return None


# -------------------------------------------------------------
# 🧹 COMMAND AUTO-CLEAN ENGINE (លុបពាក្យបញ្ជា និងលុបការឆ្លើយតបចាស់ៗ)
# -------------------------------------------------------------
LAST_BOT_RESPONSES = {}  # chat_id -> list of message_ids sent by bot in response to commands

async def send_clean_command_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    reply_markup=None,
    parse_mode=ParseMode.MARKDOWN,
    user_message=None,
    auto_delete_seconds: int = BOT_MSG_DELETE_SECONDS
):
    """
    គ្រប់គ្រងការឆ្លើយតបយ៉ាងស្អាតបាត ១០០%៖
    ១. លុបសារឆ្លើយតបចាស់ៗរបស់ Bot ក្នុង Chat នេះភ្លាមៗ (Delete previous bot responses immediately)
    ២. លុបសារបញ្ជា ឬប៊ូតុងដែល User បានចុចភ្លាមៗ (Delete incoming user command immediately)
    ៣. ផ្ញើសារឆ្លើយតបថ្មី និងកត់ត្រា Message ID របស់វា
    ៤. កំណត់ពេលលុបចម្លើយបតស្វ័យប្រវត្តិក្នងរយៈពេល ១៥ វិនាទី បើគ្មានពាក្យបញ្ជាថ្មីទេ (Auto-delete in 15s if no new command)
    """
    # ១. លុបសារឆ្លើយតបចាស់ៗរបស់ Bot ភ្លាមៗ
    if chat_id in LAST_BOT_RESPONSES:
        old_ids = list(LAST_BOT_RESPONSES[chat_id])
        for mid in old_ids:
            task = ACTIVE_DELETION_TASKS.pop((chat_id, mid), None)
            if task and not task.done():
                task.cancel()
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass
        LAST_BOT_RESPONSES[chat_id] = []

    # ២. លុបពាក្យបញ្ជារបស់ User ភ្លាមៗ (ប្រសិនបើមាន)
    if user_message:
        try:
            await user_message.delete()
        except Exception:
            pass

    # ៣. ផ្ញើសារឆ្លើយតបថ្មី
    sent_msg = None
    try:
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as err:
        logger.error(f"Error in send_clean_command_response send_message: {err}")

    # ៤. កត់ត្រាទុកសម្រាប់លុបពេលមានពាក្យបញ្ជាថ្មី និងកំណត់លុបស្វ័យប្រវត្តិក្នង ១៥ វិនាទី បើគ្មានបញ្ជាថ្មី
    if sent_msg:
        mid = sent_msg.message_id
        LAST_BOT_RESPONSES[chat_id] = [mid]
        if auto_delete_seconds and auto_delete_seconds > 0:
            async def _auto_clean_worker(bot, c_id, m_id, delay):
                try:
                    await asyncio.sleep(delay)
                    await bot.delete_message(chat_id=c_id, message_id=m_id)
                except Exception:
                    pass
                finally:
                    ACTIVE_DELETION_TASKS.pop((c_id, m_id), None)
                    if c_id in LAST_BOT_RESPONSES and m_id in LAST_BOT_RESPONSES[c_id]:
                        LAST_BOT_RESPONSES[c_id].remove(m_id)

            t = asyncio.create_task(_auto_clean_worker(context.bot, chat_id, mid, auto_delete_seconds))
            ACTIVE_DELETION_TASKS[(chat_id, mid)] = t
            PENDING_BOT_DELETIONS.append((chat_id, mid, time.time() + auto_delete_seconds))

    return sent_msg


async def bot_message_sweeper_loop(application):
    logger.info("Bot Message Sweeper Watchdog started (Guaranteed 15-second clean)...")
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
                is_auth = is_group_authorized(int(chat_id_str))
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
                            f"👉 **ឆានែលផ្លូវការ៖** [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
                            "👉 **សូមទាក់ទង Master Super Admin ដើម្បីទិញអាជ្ញាប័ណ្ណប្រើប្រាស់ពេញលេញ!**\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ១៥ វិនាទី)*"
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
        f"👤 **អតិថិជន/អ្នកទាញចូល:** {added_name} ({added_uname})\n"
        f"🔢 **Customer User ID:** `{added_id}`\n"
        f"📅 **កាលបរិច្ឆេទ:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 **តើអ្នកយល់ព្រមបើកសិទ្ធិឱ្យ Bot ការពារក្នុងក្រុមនេះដែរឬទេ?**\n"
        "• បើចុច **[ 🟢 អនុញ្ញាត ]** ➡️ ក្រុមនេះនឹងទទួលបានសិទ្ធិប្រើប្រាស់ **៧ ថ្ងៃ (7-Day Trial)** ដោយស្វ័យប្រវត្តិ!\n"
        "• បើចុច **[ 🚪 ចាកចេញ ]** ➡️ Bot នឹងចាកចេញពីក្រុមនោះភ្លាមៗ\n"
        "• បើចុច **[ 🔴 បដិសេធ ]** ➡️ រក្សាទុកជាមិនទាន់ទិញ (Bot នៅស្ងៀមមិនការពារ)"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 អនុញ្ញាតប្រើ ៧ ថ្ងៃ (Approve 7 Days)", callback_data=f"approve_{chat.id}"),
            InlineKeyboardButton("🔴 បដិសេធ (Keep Off)", callback_data=f"reject_{chat.id}")
        ],
        [
            InlineKeyboardButton("🚪 បញ្ជាឱ្យ Bot ចាកចេញពីក្រុមភ្លាម", callback_data=f"leave_{chat.id}")
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


async def send_group_welcome_and_admin_prompt(context: ContextTypes.DEFAULT_TYPE, chat, added_by_user=None):
    """
    ផ្ញើសារស្វាគមន៍ទៅក្នុង Group ពេល Bot ត្រូវបានគេ Add ចូល
    និងជំរុញ/ដាស់តឿនម្ចាស់ក្រុម (Group Owner/Admin) ឱ្យផ្ដល់សិទ្ធិជា Administrator ដល់ Bot
    ដើម្បីអាចការពារក្រុម ស្កេនមេរោគ និងទប់ស្កាត់ Spammer បាន។
    """
    added_name = added_by_user.full_name if added_by_user else "Admin Group"
    prompt_msg = (
        f"🤖 **[ប្រព័ន្ធសុវត្ថិភាព TELEGUARD CYBERSECURITY]** 🎉\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 សូមស្វាគមន៍មកកាន់ក្រុម៖ **{chat.title or 'Unknown Group'}**\n"
        f"👤 **អ្នក Add បញ្ចូល៖** {added_name}\n\n"
        f"⚡ **[សេចក្ដីណែនាំបន្ទាន់សម្រាប់ម្ចាស់ក្រុម (Group Owner/Admin)]** ⚡\n"
        f"👉 **សូម Promote / Set Bot ជា ADMINISTRATOR ជាបន្ទាន់!**\n"
        f"⚠️ **មូលហេតុ៖** ប្រសិនបើ Bot មិនទាន់ជា Administrator ទេ Telegram នឹងមិនអនុញ្ញាតឱ្យ Bot លុបសារមេរោគ ឬកម្ចាត់ Spammer បានឡើយ!\n\n"
        f"🔐 **សូមផ្ដល់សិទ្ធិ (Admin Permissions) ដូចខាងក្រោម៖**\n"
        f"✅ **Delete Messages** (សិទ្ធិស្កេន និងលុបសារមេរោគស្វ័យប្រវត្តិ)\n"
        f"✅ **Ban/Restrict Users** (សិទ្ធិទប់ស្កាត់អ្នកផ្ញើមេរោគ)\n\n"
        f"🆔 **លេខ Group ID របស់អ្នក៖** `{chat.id}`\n"
        f"⏳ **ស្ថានភាព៖** រង់ចាំការអនុញ្ញាតពី Master Super Admin (Pending Approval)\n"
        f"👉 ឆានែលផ្លូវការ៖ [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ១៥ វិនាទី)*"
    )
    await send_auto_delete_message(context, chat.id, prompt_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)


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
        record_audit_event(
            event_type="BOT_ADDED_TO_GROUP",
            chat_id=chat.id,
            chat_title=chat.title or "Unknown Group",
            user_id=user.id if user else 0,
            user_name=user.full_name if user else "Unknown",
            details=f"Bot added to group (Status: {new_status})",
            action="Auto-synced into CRM Vault, waiting for Master approval"
        )
        await notify_master_admin_new_group(context, chat, user)
        await send_group_welcome_and_admin_prompt(context, chat, user)


# ==================== DYNAMIC KEYBOARD BUILDER ====================

def get_master_owner_keyboard() -> ReplyKeyboardRemove:
    """
    ដកប៊ូតុងខាងក្រោមឆាត (ReplyKeyboardMarkup) ចេញទាំងអស់
    តាមការស្នើសុំរបស់អ្នកប្រើប្រាស់ (ប្រើតែ Telegram Native Menu Button & Inline Buttons)
    """
    return ReplyKeyboardRemove()


def get_client_admin_keyboard() -> ReplyKeyboardRemove:
    """ដកប៊ូតុងខាងក្រោមឆាតចេញទាំងអស់សម្រាប់ Client Admins"""
    return ReplyKeyboardRemove()


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
    message = update.effective_message
    if not message:
        return
    if message.chat_shared:
        return

    # ប្រសិនបើ Bot ត្រូវបាន Add ចូល Group តាមរយៈ StatusUpdate New Chat Member
    if message.new_chat_members:
        for m in message.new_chat_members:
            if m.id == context.bot.id:
                chat = update.effective_chat
                user = message.from_user
                sync_client_record(chat, user, is_auth=False, is_enabled=False)
                record_audit_event(
                    event_type="BOT_ADDED_TO_GROUP",
                    chat_id=chat.id,
                    chat_title=chat.title or "Unknown Group",
                    user_id=user.id if user else 0,
                    user_name=user.full_name if user else "Unknown",
                    details="Bot added to group via new_chat_members",
                    action="Auto-synced into CRM Vault, waiting for Master approval"
                )
                await notify_master_admin_new_group(context, chat, user)
                await send_group_welcome_and_admin_prompt(context, chat, user)

    if not AUTO_DELETE_SERVICE_MSGS:
        return
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
        await notify_master_admin_new_group(context, chat, message.from_user)

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
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញស្វ័យប្រវត្តិក្នងរយៈពេល ១៥ វិនាទី)*"
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
                    f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ១៥ វិនាទី)*"
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


# ==================== 📢 BROADCAST TO OFFICIAL CHANNEL ====================

async def broadcast_to_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    promo_text = (
        "🛡️ **[ការប្រកាសសេវាកម្មសុវត្ថិភាព - TELEGUARD CYBERSECURITY]** 🛡️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **ការពារក្រុម Telegram របស់អ្នកពីមេរោគ និងចោរលួចគណនីធនាគារ!**\n\n"
        "⚡ **សមត្ថភាពការពារពិសេសរបស់ Bot៖**\n"
        "• 🛑 ស្កេន និងកម្ចាត់មេរោគ `.apk` (Banking Trojan លួចលុយធនាគារ)\n"
        "• 🛑 ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (`.jpg.apk`, `.pdf.apk`)\n"
        "• 🛑 ទប់ស្កាត់មេរោគកុំព្យូទ័រ `.exe`, `.scr`, `.bat`\n"
        "• 🌊 ប្រព័ន្ធ Anti-Flood Spam & Clean Service Join/Leave\n"
        "• ⏱️ ប្រព័ន្ធ 15s Auto-Clean Message មិនរំខានការងារ\n"
        "• 🗄️ ប្រព័ន្ធកត់ត្រាទិន្នន័យអតិថិជន និងរបាយការណ៍ Security Logs\n\n"
        "👑 **កញ្ចប់សេវាកម្មពេញនិយម៖**\n"
        "• 🥉 កញ្ចប់ប្រចាំខែ (30 ថ្ងៃ)\n"
        "• 🥈 កញ្ចប់ ៣ ខែ (90 ថ្ងៃ)\n"
        "• 🥇 កញ្ចប់ VIP ពេញមួយជីវិត (Lifetime VIP)\n\n"
        "👉 **ទាក់ទងទិញសិទ្ធិប្រើប្រាស់ភ្លាមៗ៖** [Master Super Admin](tg://user?id=240224709)\n"
        f"📢 **ឆានែលផ្លូវការ៖** {OFFICIAL_CHANNEL_USERNAME}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    success = False
    result_text = ""
    try:
        await context.bot.send_message(
            chat_id=OFFICIAL_CHANNEL_USERNAME,
            text=promo_text,
            parse_mode=ParseMode.MARKDOWN
        )
        result_text = f"✅ **បានផ្សាយពាណិជ្ជកម្មទៅកាន់ Channel {OFFICIAL_CHANNEL_USERNAME} ជោគជ័យ!** 🎉\n🔗 {OFFICIAL_CHANNEL_LINK}"
    except Exception as e:
        logger.error(f"Failed to post to channel: {e}")
        result_text = f"⚠️ **មិនអាចផ្សាយទៅ Channel បានទេ!**\nមូលហេតុ៖ សូមប្រាកដថាអ្នកបាន Add Bot ជា **Administrator (មានសិទ្ធិ Post Messages)** ក្នុង Channel `{OFFICIAL_CHANNEL_USERNAME}` រួចរាល់។\n\nError: `{e}`"

    user_msg = update.effective_message if (update and update.effective_chat and update.effective_chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=user.id,
        text=result_text,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


# ==================== 👻 STEALTH MASTER ROUTER ====================

async def handle_regular_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    is_owner = is_sole_master_owner(user.id)
    is_admin = await is_client_group_admin(update, context)

    # ហៅ និងកត់ត្រាក្រុមដែល Bot កំពុងនៅស្រាប់ ចូលក្នុងបញ្ជីដោយស្វ័យប្រវត្តិ
    if chat.type in ["group", "supergroup"] and str(chat.id) not in GROUPS_CONFIG:
        if is_owner:
            sync_client_record(chat, user, is_auth=True, is_enabled=True, plan_days=7)
            await context.bot.send_message(
                chat_id=user.id,
                text=f"✅ **[បានទាញក្រុមចូលបញ្ជីស្វ័យប្រវត្តិ]**\n\n👥 ក្រុម៖ **{chat.title}** (`{chat.id}`)\n🛒 បានបើកសិទ្ធិការពារ ៧ ថ្ងៃ (Trial 7 Days) ដោយជោគជ័យ!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            sync_client_record(chat, user, is_auth=False, is_enabled=False)
            await notify_master_admin_new_group(context, chat, user)

    if await handle_anti_flood(update, context):
        return

    text = update.message.text.strip() if update.message and update.message.text else ""

    # 1. ករណី Master Owner វាយពាក្យបញ្ជា ឬចុចប៊ូតុងក្នុង Group ➡️ លុបសារពី Group ចោលភ្លាម & ផ្ញើទៅ Private Chat
    if is_owner and chat.type in ["group", "supergroup"]:
        if text in [
            "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin",
            "👥 ចុចរើសក្រុម (Select Group)", "👥 ចុចរើសក្រុម",
            "➕ បន្ថែម Group តាម ID", "➕ បន្ថែមក្រុម", "/addgroup",
            "🔄 Sync ក្រុមនេះចូលបញ្ជី", "/sync",
            "📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients",
            "📜 ប្រវត្តិការពារ & ការទិញបត", "📜 ប្រវត្តិការពារ (Logs)", "/logs",
            "📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel", "/broadcast", "/channel",
            "❓ ការណែនាំ & ជំនួយ", "/help",
            "🛡️ ឆែកស្ថានភាព Bot", "/status", "/check",
            "🆔 មើលលេខ ID", "🆔 មើលលេខ ID Group", "/myid", "/id",
            "🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"
        ]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass

            if text in ["/sync", "🔄 Sync ក្រុមនេះចូលបញ្ជី"]:
                await sync_group_command(update, context)
            elif text in ["👥 ចុចរើសក្រុម (Select Group)", "👥 ចុចរើសក្រុម"]:
                await prompt_select_group(context, user.id)
            elif text in ["➕ បន្ថែម Group តាម ID", "➕ បន្ថែមក្រុម", "/addgroup"]:
                await prompt_add_group(context, user.id)
            elif text in ["🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"]:
                await start_command(update, context)
            elif text in ["⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin"]:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n👑 **សូមស្វាគមន៍ម្ចាស់ Bot**\n👇 សូមចុចលើឈ្មោះ Group ដើម្បីមើលព័ត៌មានលម្អិត ឬកំណត់សិទ្ធិ/បន្ថែមថ្ងៃ៖",
                    reply_markup=generate_master_dashboard_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            elif text in ["📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients"]:
                await list_groups_command(update, context, send_to_user_id=user.id)
            elif text in ["📜 ប្រវត្តិការពារ & ការទិញបត", "📜 ប្រវត្តិការពារ (Logs)", "/logs"]:
                await logs_command(update, context, send_to_user_id=user.id)
            elif text in ["📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel", "/broadcast", "/channel"]:
                await broadcast_to_channel_command(update, context)
            elif text in ["❓ ការណែនាំ & ជំនួយ", "/help"]:
                await help_command(update, context, send_to_user_id=user.id)
            elif text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
                await status_command(update, context)
            elif text in ["🆔 មើលលេខ ID", "🆔 មើលលេខ ID Group", "/myid", "/id"]:
                await myid_command(update, context)
            return

    # 2. ករណី Master Owner ប្រើក្នុង Private Chat ផ្ទាល់ខ្លួន
    if is_owner and chat.type == "private":
        # ពិនិត្យមើលថាតើ Master បាន Forward សារពី Group ចាស់ណាមួយមកកាន់ Bot ឬទេ
        fwd_chat = None
        if update.message:
            if update.message.forward_from_chat:
                fwd_chat = update.message.forward_from_chat
            elif hasattr(update.message, "forward_origin") and update.message.forward_origin:
                fwd_chat = getattr(update.message.forward_origin, "chat", None)

        if fwd_chat and fwd_chat.type in ["group", "supergroup"]:
            fwd_id = fwd_chat.id
            fwd_title = fwd_chat.title or f"Group {fwd_id}"
            
            real_c = None
            try:
                real_c = await context.bot.get_chat(chat_id=fwd_id)
            except Exception:
                pass

            c_obj = real_c if real_c else type('obj', (object,), {'id': fwd_id, 'title': fwd_title})
            sync_client_record(c_obj, user=user, is_auth=True, is_enabled=True, plan_days=7)
            record_audit_event(
                event_type="OLD_GROUP_DISCOVERED_FORWARD",
                chat_id=fwd_id,
                chat_title=fwd_title,
                user_id=user.id,
                user_name=user.full_name,
                details="Master Owner forwarded message from old group",
                action="Auto-synced into CRM Vault with 7 Days Trial"
            )
            success_text = (
                "🎉 **[បានទាញក្រុមចាស់ចូលបញ្ជីជោគជ័យតាមសារ FORWARD]** 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 **ឈ្មោះក្រុម:** `{fwd_title}`\n"
                f"🆔 **លេខ Group ID:** `{fwd_id}`\n"
                f"🛒 **កញ្ចប់សេវា:** Plan 7 Days (សាកល្បង ៧ ថ្ងៃ)\n"
                f"🔰 **ស្ថានភាពការពារ:** 🟢 កំពុងការពារយ៉ាងសកម្ម (SHIELD ON)\n\n"
                f"✨ ក្រុមនេះត្រូវបានបញ្ចូលទៅក្នុងបញ្ជីគ្រប់គ្រង CRM Vault រួចរាល់ ១០០%!\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
            await send_clean_command_response(
                context,
                chat_id=user.id,
                text=success_text,
                reply_markup=get_master_owner_keyboard(),
                parse_mode=ParseMode.MARKDOWN,
                user_message=update.effective_message
            )
            return

        # ពិនិត្យមើលថាតើកំពុងស្ថិតក្នុង State រង់ចាំវាយលេខ Group ID ឬទេ
        if WAITING_FOR_GROUP_ID.get(user.id):
            if text in ["/cancel", "❌ បោះបង់"]:
                WAITING_FOR_GROUP_ID.pop(user.id, None)
                await send_clean_command_response(
                    context,
                    chat_id=user.id,
                    text="❌ **បានបោះបង់ការបន្ថែម Group រួចរាល់!**",
                    reply_markup=get_master_owner_keyboard(),
                    parse_mode=ParseMode.MARKDOWN,
                    user_message=update.effective_message
                )
                return
            WAITING_FOR_GROUP_ID.pop(user.id, None)
            await process_manual_add_group(context, user.id, text, user_message=update.effective_message)
            return

        if text in ["👥 ចុចរើសក្រុម (Select Group)", "👥 ចុចរើសក្រុម"]:
            await prompt_select_group(context, user.id, user_message=update.effective_message)
            return
        elif text in ["➕ បន្ថែម Group តាម ID", "➕ បន្ថែមក្រុម", "/addgroup"]:
            await prompt_add_group(context, user.id, user_message=update.effective_message)
            return
        elif text in ["/sync", "🔄 Sync ក្រុមនេះចូលបញ្ជី"]:
            await sync_group_command(update, context)
            return
        elif text in ["🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start)", "/start"]:
            await start_command(update, context)
        elif text in ["⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin"]:
            await admin_command(update, context)
        elif text in ["📋 បញ្ជីអតិថិជន & Group", "📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន", "/groups", "/clients"]:
            await list_groups_command(update, context)
        elif text in ["📜 ប្រវត្តិការពារ & ការទិញបត", "📜 ប្រវត្តិការពារ (Logs)", "/logs"]:
            await logs_command(update, context)
        elif text in ["📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel", "/broadcast", "/channel"]:
            await broadcast_to_channel_command(update, context)
        elif text in ["❓ ការណែនាំ & ជំនួយ", "/help"]:
            await help_command(update, context)
        elif text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
            await status_command(update, context)
        elif text in ["🆔 មើលលេខ ID", "/myid", "/id"]:
            await myid_command(update, context)
        return

    # 3. ករណី Client Group Admin ប្រើក្នុង Group របស់ពួកគេ
    if is_admin and chat.type in ["group", "supergroup"]:
        if text in ["🔄 Sync ក្រុមនេះចូលបញ្ជី", "/sync"]:
            sync_client_record(chat, user, is_auth=False, is_enabled=False)
            await notify_master_admin_new_group(context, chat, user)
            await send_auto_delete_message(
                context,
                chat.id,
                "✅ **[បានបញ្ជូនសំណើសុំបើកសិទ្ធិ]** សំណើត្រូវបានបញ្ជូនទៅ Master Super Admin ដើម្បីពិនិត្យ និងអនុញ្ញាត!",
                delay=BOT_MSG_DELETE_SECONDS,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        elif text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
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
        "📜 ប្រវត្តិការពារ & ការទិញបត", "📜 ប្រវត្តិការពារ (Logs)", "/logs",
        "📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel", "/broadcast", "/channel",
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
                "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ១៥ វិនាទី)*"
            )
            await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_client_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if is_owner:
        text = (
            f"👑 **សូមស្វាគមន៍ម្ចាស់ Bot ផ្ទាល់! (Sole Master Owner - ID: `{user.id}`)**\n\n"
            "🎛️ **ផ្ទាំងបញ្ជាគ្រប់គ្រងពេញលេញ (100% Full Commercial & CRM Control)៖**\n"
            "• ចុច **[ ⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard ]** ➡️ មើល Profile Group, ថ្ងៃទិញ, ថ្ងៃនៅសល់, និងកំណត់សិទ្ធិ\n"
            "• ចុច **[ 📋 បញ្ជីអតិថិជន CRM ]** ➡️ ពិនិត្យបញ្ជីអតិថិជន CRM និងកញ្ចប់សេវា\n"
            "• ចុច **[ 📜 ប្រវត្តិការពារ & ការទិញបត ]** ➡️ មើល Logs មេរោគ និងប្រវត្តិទិញបត\n"
            f"• ចុច **[ 📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel ]** ➡️ ផ្សាយទៅ Channel `{OFFICIAL_CHANNEL_USERNAME}`\n"
            "• ចុច **[ 🚀 ចាប់ផ្ដើម Bot ឡើងវិញ (/start) ]** ➡️ Reload ផ្ទាំងបញ្ជា\n\n"
            "👇 **សូមចុចលើប៊ូតុង Dashboard ខាងក្រោម ឬចុចលើ Menu (ឆ្វេងដៃក្រោម) ដើម្បីជ្រើសរើសមុខងារ៖**"
        )
        await send_clean_command_response(
            context,
            chat_id=chat.id,
            text=text,
            reply_markup=generate_master_dashboard_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
            user_message=update.effective_message
        )
    else:
        text = (
            f"🤖 **សួស្តី {user.first_name}!**\n\n"
            "ខ្ញុំជា Bot ការពារមេរោគ និងគ្រប់គ្រងសុវត្ថិភាព Group Telegram!\n\n"
            f"📢 **ឆានែលផ្លូវការ៖** [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
            "🔒 **ប្រព័ន្ធគ្រប់គ្រង៖** Bot នេះត្រូវបានគ្រប់គ្រងដោយ Master Super Admin។"
        )
        await send_clean_command_response(
            context,
            chat_id=chat.id,
            text=text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN,
            user_message=update.effective_message
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    text = (
        "📖 **[សៀវភៅណែនាំគ្រប់គ្រង BOT - MASTER OWNER GUIDE]** 📖\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👑 **១. របៀបគ្រប់គ្រង Group, ពិនិត្យថ្ងៃនៅសល់ និងបន្ថែមសិទ្ធិ៖**\n"
        "• ចុចប៊ូតុង `[ ⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard ]`\n"
        "• ចុចលើឈ្មោះ Group ណាមួយ ដើម្បីមើលព័ត៌មានលម្អិត៖ ឈ្មោះអតិថិជន, ថ្ងៃទិញ, ថ្ងៃផុតកំណត់, និងចំនួនថ្ងៃនៅសល់\n"
        "• អ្នកអាចចុច `[ ➕ បន្ថែម 30 ថ្ងៃ ]`, `[ ➕ បន្ថែម 90 ថ្ងៃ ]`, `[ 👑 ពេញមួយជីវិត ]`, ឬ `[ 🔴 ដកសិទ្ធិ ]`\n\n"
        "🗄️ **២. របៀបមើលប្រវត្តិអតិថិជន (Client CRM)៖**\n"
        "• ចុចប៊ូតុង `[ 📋 បញ្ជីអតិថិជន & Group ]` នោះ Bot នឹងរៀបចំរបាយការណ៍លម្អិតអំពី ឈ្មោះអតិថិជន, ID, ថ្ងៃ Add ចូល, កញ្ចប់ទិញ, និងស្ថិតិមេរោគ\n\n"
        "📜 **៣. របៀបពិនិត្យមើល Logs សន្តិសុខ & ប្រវត្តិទិញបត៖**\n"
        "• ចុចប៊ូតុង `[ 📜 ប្រវត្តិការពារ & ការទិញបត ]` ដើម្បីមើល ១០ ហេតុការណ៍ចុងក្រោយដែល Bot បានទប់ស្កាត់ និងប្រវត្តិទិញបត\n\n"
        "📢 **៤. របៀបផ្សាយពាណិជ្ជកម្មទៅ Channel៖**\n"
        f"• ចុចប៊ូតុង `[ 📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel ]` ដើម្បីផ្ញើសារប្រកាសលក់សេវាកម្មទៅកាន់ Channel `{OFFICIAL_CHANNEL_USERNAME}` របស់អ្នកភ្លាមៗ\n\n"
        "🔒 **៥. ប្រព័ន្ធ Stealth Privacy Mode៖**\n"
        "• ទោះបីជាអ្នកនៅក្នុង Group ណាក៏ដោយ ក៏ប៊ូតុង និងសារបញ្ជារបស់អ្នក **មិនបង្ហាញឱ្យសមាជិកក្នុង Group ឃើញឡើយ** (Bot បញ្ជូនមក Private Chat នេះដោយស្វ័យប្រវត្តិ)!\n\n"
        "🔍 **៧. របៀបហៅក្រុមចាស់ៗដែល Bot កំពុងនៅ ចូលក្នុងបញ្ជី (៤ វិធីងាយៗ)៖**\n"
        "• **វិធីទី ១ (លឿនបំផុត):** គ្រាន់តែ **Forward សារណាមួយពីក្រុមចាស់នោះ** មកកាន់ Bot ក្នុង Chat នេះផ្ទាល់ នោះ Bot នឹងទាញក្រុមនោះចូល CRM និងបើកសិទ្ធិ ៧ ថ្ងៃជូនភ្លាម!\n"
        "• **វិធីទី ២:** ចុចប៊ូតុង `[ 👥 ចុចរើសក្រុម (Select Group) ]` រួចចុចលើឈ្មោះក្រុម Telegram របស់អ្នក\n"
        "• **វិធីទី ៣:** ចុចប៊ូតុង `[ ➕ បន្ថែម Group តាម ID ]` រួចវាយលេខ Group ID ឬ `@groupname`\n"
        "• **វិធីទី ៤:** ចូលទៅក្នុងក្រុមចាស់នោះ រួចវាយពាក្យ `/sync` ឬចុចប៊ូតុង `[ 🔄 Sync ក្រុមនេះចូលបញ្ជី ]`\n\n"
        "⏱️ **៨. កំណត់ពេលលុបសារស្វ័យប្រវត្តិ៖** ១៥ វិនាទី (មានប្រព័ន្ធ Sweeper Watchdog សម្អាតជាប្រចាំ)\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id
    user_msg = update.effective_message if (update and update.effective_message and update.effective_chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=target_id,
        text=text,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


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
            f"👉 **ឆានែលផ្លូវការ៖** [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
            f"💡 **ការណែនាំ៖** សូមចម្លងលេខ Group ID (`{chat.id}`) នេះ ផ្ញើទៅកាន់ **Master Super Admin** ដើម្បីទិញអាជ្ញាប័ណ្ណ និងបើកដំណើរការប្រព័ន្ធការពារពេញលេញ!\n\n"
            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ១៥ វិនាទី)*"
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

    gdata = GROUPS_CONFIG.get(str(chat.id), {})
    plan_type = gdata.get("plan_type", "N/A")
    exp_date = gdata.get("expiry_date", "N/A")
    is_life = gdata.get("is_lifetime", False)
    rem_str = get_remaining_time_str(exp_date, is_life)

    text = (
        "🛡️ **[ព័ត៌មាន និងស្ថានភាពសុវត្ថិភាព BOT STATUS]** 🛡️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{group_name}`\n"
        f"🆔 **លេខ Group ID:** `{chat.id}`\n"
        f"🏷️ **ប្រភេទ:** {chat_type_kh}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 **ស្ថានភាពការពារ:** {shield_status_str}\n"
        f"🛒 **កញ្ចប់សេវាកម្ម:** {plan_type}\n"
        f"⏳ **រយៈពេលនៅសល់:** {rem_str}\n"
        f"⚡ **ប្រព័ន្ធស្កេនមេរោគ (Local):** ✅ សកម្ម (.apk, .exe, .scr, .bat, .sh, .jpg.apk)\n"
        f"🌐 **VirusTotal Cloud Scan:** {vt_status}\n"
        f"⏱️ **Auto-Delete Timer:** ✅ ១៥ វិនាទី (Clean Room Sweeper)\n"
        f"⚖️ **វិធានការលើអ្នកល្មើស:** លុបសារមេរោគ + {PUNISHMENT_MODE} {MUTE_DURATION_HOURS} ម៉ោង\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ១៥ វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        kb = get_client_admin_keyboard() if not is_owner else None
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        kb = get_master_owner_keyboard() if is_owner else ReplyKeyboardRemove()
        await send_clean_command_response(
            context,
            chat_id=chat.id,
            text=text,
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
            user_message=update.effective_message
        )


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
            f"👉 ឆានែលផ្លូវការ៖ [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
            f"💡 *(សូមយកលេខ Group ID `{chat.id}` នេះ ផ្ញើទៅកាន់ Master Admin ដើម្បីទិញ ឬបើកសិទ្ធិប្រើប្រាស់)*\n\n"
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ១៥ វិនាទី)*"
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
        await send_clean_command_response(
            context,
            chat_id=chat.id,
            text=text,
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
            user_message=update.effective_message
        )


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
        InlineKeyboardButton("➕ បន្ថែម Group តាម ID/Link", callback_data="dash_add_group"),
        InlineKeyboardButton("🔄 Refresh បញ្ជី", callback_data="dash_refresh")
    ])
    keyboard.append([
        InlineKeyboardButton("📋 បញ្ជីអតិថិជន CRM", callback_data="dash_clients"),
        InlineKeyboardButton("📜 កំណត់ត្រា Logs", callback_data="dash_logs")
    ])
    keyboard.append([
        InlineKeyboardButton("📢 ផ្សាយទៅ Channel", callback_data="dash_broadcast"),
        InlineKeyboardButton("🚪 បញ្ជាឱ្យ Bot ចេញពីក្រុម", callback_data="dash_leave_list")
    ])
    return InlineKeyboardMarkup(keyboard)


def generate_leave_groups_keyboard() -> InlineKeyboardMarkup:
    """
    បង្កើតបញ្ជីក្រុមទាំងអស់សម្រាប់ Master Owner ជ្រើសរើសបញ្ជាឱ្យ Bot ចាកចេញ
    """
    keyboard = []
    if not GROUPS_CONFIG:
        keyboard.append([InlineKeyboardButton("❌ គ្មានក្រុមណាក្នុងបញ្ជីទេ", callback_data="none")])
    else:
        for chat_id, data in GROUPS_CONFIG.items():
            title = data.get("title", f"Group {chat_id}")
            plan = data.get("plan_type", "")
            is_left = "ចាកចេញ" in plan or "LEFT" in plan
            status_prefix = "🚪 [បានចេញរួច]" if is_left else "👥"
            btn_text = f"{status_prefix} ចេញពី៖ {title[:16]}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"confirm_leave_{chat_id}")])

    keyboard.append([
        InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data="dash_back")
    ])
    return InlineKeyboardMarkup(keyboard)


def generate_group_detail_keyboard(chat_id: str) -> InlineKeyboardMarkup:
    """
    Sub-menu បញ្ជា និងកំណត់សិទ្ធិ/រយៈពេលប្រើប្រាស់របស់ Group នីមួយៗ
    """
    gdata = GROUPS_CONFIG.get(str(chat_id), {})
    is_auth = gdata.get("is_authorized", False)
    is_en = gdata.get("is_enabled", False)

    keyboard = [
        [
            InlineKeyboardButton("🎁 សាកល្បង ៧ ថ្ងៃ (+7D)", callback_data=f"add_7_{chat_id}"),
            InlineKeyboardButton("➕ បន្ថែម 30 ថ្ងៃ (+30D)", callback_data=f"add_30_{chat_id}")
        ],
        [
            InlineKeyboardButton("➕ បន្ថែម 90 ថ្ងៃ (+90D)", callback_data=f"add_90_{chat_id}"),
            InlineKeyboardButton("👑 ពេញមួយជីវិត (Lifetime)", callback_data=f"set_life_{chat_id}")
        ],
        [
            InlineKeyboardButton("🟢 បើក (ON)" if not is_en else "🟡 ផ្អាក (PAUSE)", callback_data=f"toggle_en_{chat_id}"),
            InlineKeyboardButton("🔴 ដកសិទ្ធិ (Revoke)", callback_data=f"revoke_{chat_id}")
        ],
        [
            InlineKeyboardButton("🚪 បញ្ជាឱ្យ Bot ចាកចេញពីក្រុម", callback_data=f"leave_{chat_id}"),
            InlineKeyboardButton("🗑️ លុប Group ចេញ", callback_data=f"set_del_{chat_id}")
        ],
        [
            InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data="dash_back")
        ]
    ]
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
        "👇 **សូមចុចលើឈ្មោះ Group ខាងក្រោម ដើម្បីពិនិត្យ Profile, ប្រវត្តិទិញ, ថ្ងៃនៅសល់ និងកំណត់សិទ្ធិ៖**\n"
    )
    user_msg = update.effective_message if (update and update.effective_chat and update.effective_chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=user.id,
        text=text,
        reply_markup=generate_master_dashboard_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


async def list_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    """
    បង្ហាញបញ្ជីអតិថិជន និងព័ត៌មាន Group លម្អិត (Client CRM Database)
    """
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id

    if not CLIENTS_DB:
        user_msg = update.effective_message if (update and update.effective_chat and update.effective_chat.type == "private") else None
        await send_clean_command_response(
            context,
            chat_id=target_id,
            text="🗄️ មិនទាន់មានទិន្នន័យអតិថិជនក្នុងប្រព័ន្ធនៅឡើយទេ។",
            reply_markup=get_master_owner_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
            user_message=user_msg
        )
        return

    report = "🗄️ **[ប្រព័ន្ធគ្រប់គ្រងអតិថិជន & ប្រវត្តិក្រុម - CLIENT CRM VAULT]** 🗄️\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for idx, (cid, cdata) in enumerate(CLIENTS_DB.items(), start=1):
        gname = cdata.get("client_group_name", f"Group {cid}")
        status = cdata.get("license_status", "N/A")
        plan_type = cdata.get("plan_type", "N/A")
        is_life = cdata.get("is_lifetime", False)
        exp_date = cdata.get("expiry_date", "N/A")
        rem_str = get_remaining_time_str(exp_date, is_life)

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
        report += f"   • 🛒 **កញ្ចប់ទិញ:** {plan_type}\n"
        report += f"   • 👤 **អតិថិជន:** {c_name} ({c_uname})\n"
        report += f"   • 🔢 **Customer ID:** `{c_uid}`\n"
        report += f"   • 📅 **ថ្ងៃ Add ចូល:** `{reg_date}`\n"
        report += f"   • ⚡ **ថ្ងៃបើកសិទ្ធិ:** `{act_date}`\n"
        report += f"   • ⌛ **ថ្ងៃផុតកំណត់:** `{exp_date}`\n"
        report += f"   • ⏳ **រយៈពេលនៅសល់:** {rem_str}\n"
        report += f"   • 🛡️ **ស្ថិតិការពារជូន:** ☣️ `{threats}` មេរោគ | 🌊 `{spams}` Spams\n"
        report += "────────────────────\n"

    user_msg = update.effective_message if (update and update.effective_chat and update.effective_chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=target_id,
        text=report,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, send_to_user_id=None):
    """
    បង្ហាញកំណត់ត្រាប្រវត្តិកំចាត់មេរោគ និងប្រវត្តិទិញបត (Security & Purchase Audit Logs)
    """
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    target_id = send_to_user_id if send_to_user_id else update.effective_chat.id

    logs_text = "📜 **[ប្រវត្តិការពារសន្តិសុខ & ការទិញបត - SECURITY AUDIT LOGS]**\n"
    logs_text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    logs_text += "🛡️ **១. កំណត់ត្រាកំចាត់មេរោគចុងក្រោយ (Incident Logs)៖**\n"
    if AUDIT_LOGS:
        recent_logs = AUDIT_LOGS[:6]
        for idx, log in enumerate(recent_logs, start=1):
            logs_text += f"**{idx}. [{log['timestamp']}]** `{log['event_type']}`\n"
            logs_text += f"   • 👥 **Group:** `{log['chat_title']}` (`{log['chat_id']}`)\n"
            logs_text += f"   • 👤 **User:** `{log['user_name']}` (`ID: {log['user_id']}`)\n"
            logs_text += f"   • ⚠️ **ព័ត៌មាន:** {log['details']}\n"
            logs_text += f"   • ⚡ **ចំណាត់ការ:** {log['action']}\n"
    else:
        logs_text += "   *(មិនទាន់មានហេតុការណ៍ល្មើសនៅឡើយទេ)*\n"

    logs_text += "\n🛒 **២. ប្រវត្តិនៃការទិញ និងបើកសិទ្ធិប្រើប្រាស់ (Purchase History)៖**\n"
    has_purchases = False
    for cid, cdata in CLIENTS_DB.items():
        gtitle = cdata.get("client_group_name", cid)
        phist = cdata.get("purchase_history", [])
        if phist:
            has_purchases = True
            for p in phist[-2:]:
                logs_text += f"• **{gtitle}** ➡️ `{p.get('package', 'Standard')}` | 📅 `{p.get('purchased_date', 'N/A')}` | ⏳ `{p.get('duration', '30 Days')}`\n"
    if not has_purchases:
        logs_text += "   *(មិនទាន់មានប្រវត្តិទិញថ្មីនៅឡើយទេ)*\n"

    logs_text += "━━━━━━━━━━━━━━━━━━━━\n"

    user_msg = update.effective_message if (update and update.effective_chat and update.effective_chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=target_id,
        text=logs_text,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command សម្រាប់ Master Owner បញ្ជាឱ្យ Bot ចាកចេញពី Group
    • បើវាយ /leave ក្នុង Group ណាមួយ ➡️ Bot នឹងចាកចេញពី Group នោះភ្លាម
    • បើវាយ /leave <group_id> ក្នុង Private Chat ➡️ Bot នឹងចាកចេញពី Group ID នោះ
    """
    user = update.effective_user
    chat = update.effective_chat
    if not is_sole_master_owner(user.id):
        return

    args = context.args
    target_chat_id = None

    if chat.type in ["group", "supergroup"]:
        target_chat_id = str(chat.id)
    elif args:
        target_chat_id = args[0].strip()

    if not target_chat_id:
        user_msg = update.effective_message if (chat.type == "private") else None
        await send_clean_command_response(
            context,
            chat_id=user.id,
            text=(
                "ℹ️ **របៀបប្រើប្រាស់៖** `/leave <group_id>`\n"
                "ឧទាហរណ៍៖ `/leave -1002458931204`\n\n"
                "💡 ឬលោកអ្នកគ្រាន់តែវាយពាក្យ `/leave` ផ្ទាល់នៅក្នុង Group ណាមួយក៏បាន ឬចូលទៅកាន់ `/admin` ➡️ ចុចលើឈ្មោះក្រុម ➡️ ចុចប៊ូតុង **[ 🚪 បញ្ជាឱ្យ Bot ចាកចេញពីក្រុម ]**!"
            ),
            reply_markup=get_master_owner_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
            user_message=user_msg
        )
        return

    group_title = GROUPS_CONFIG.get(target_chat_id, {}).get("title", f"Group {target_chat_id}")
    leave_status = ""
    try:
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=int(target_chat_id),
                text="👋 **[លាហើយ!]** Bot ត្រូវបានបញ្ជាដោយម្ចាស់ (Master Owner) ឱ្យចាកចេញពីក្រុមនេះ។ សូមអរគុណ!",
                parse_mode=ParseMode.MARKDOWN
            )
        await context.bot.leave_chat(chat_id=int(target_chat_id))
        leave_status = f"✅ **បានបញ្ជាឱ្យ Bot ចាកចេញពីក្រុម {group_title} (`{target_chat_id}`) ដោយជោគជ័យ!**"
    except Exception as e:
        leave_status = f"⚠️ មិនអាចចាកចេញពីក្រុម `{target_chat_id}` បានទេ៖ {e}"

    if target_chat_id in GROUPS_CONFIG:
        GROUPS_CONFIG[target_chat_id]["is_authorized"] = False
        GROUPS_CONFIG[target_chat_id]["is_enabled"] = False
        GROUPS_CONFIG[target_chat_id]["plan_type"] = "🚪 Bot បានចាកចេញពីក្រុម"
        save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

    if target_chat_id in CLIENTS_DB:
        CLIENTS_DB[target_chat_id]["license_status"] = "🚪 LEFT (Bot ចាកចេញ)"
        save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

    user_msg = update.effective_message if (chat.type == "private") else None
    await send_clean_command_response(
        context,
        chat_id=user.id,
        text=leave_status,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_msg
    )


async def prompt_select_group(context: ContextTypes.DEFAULT_TYPE, user_id: int, user_message=None):
    """
    ណែនាំ Master Owner ពីវិធីហៅក្រុម ឬជ្រើសរើសក្រុមចាស់ៗ
    """
    prompt_text = (
        "👥 **[វិធីហៅក្រុមដែល BOT កំពុងនៅ ចូលក្នុងបញ្ជី]** 👥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 **វិធីទី ១ (ងាយស្រួលបំផុត & លឿនបំផុត):**\n"
        "ចូលទៅ Group ចាស់នោះ រួច **Forward សារ ឬ Sticker ណាមួយ** មកកាន់ Bot ក្នុង Chat នេះផ្ទាល់ នោះ Bot នឹងទាញក្រុមនោះចូល CRM និងបើកសិទ្ធិ ៧ ថ្ងៃជូនភ្លាមៗ!\n\n"
        "👉 **វិធីទី ២:**\n"
        "វាយពាក្យបញ្ជាកាត់៖ `/addgroup <ID_ឬ_Username>` (ឧទាហរណ៍៖ `/addgroup @mygroup`)\n\n"
        "👉 **វិធីទី ៣:**\n"
        "ចូលទៅក្នុង Group នោះ រួចវាយពាក្យបញ្ជា `/sync`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ បន្ថែម Group តាម ID/Link", callback_data="dash_add_group")],
        [InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data="dash_back")]
    ])
    await send_clean_command_response(
        context,
        chat_id=user_id,
        text=prompt_text,
        reply_markup=inline_kb,
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_message
    )


async def handle_chat_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ទទួលបានទិន្នន័យ Group ដែល Master Owner បានចុចរើសពី Native Chat Picker
    """
    user = update.effective_user
    if not is_sole_master_owner(user.id):
        return

    chat_shared = update.message.chat_shared if update.message else None
    if not chat_shared:
        return

    target_chat_id = chat_shared.chat_id
    raw_title = getattr(chat_shared, "title", None)
    input_str = f"{target_chat_id} {raw_title}" if raw_title else str(target_chat_id)
    await process_manual_add_group(context, user.id, input_str, user_message=update.effective_message)


async def prompt_add_group(context: ContextTypes.DEFAULT_TYPE, user_id: int, user_message=None):
    """
    បង្ហាញសារសួរនាំលេខ Group ID ពី Master Owner
    """
    WAITING_FOR_GROUP_ID[user_id] = True
    prompt_text = (
        "➕ **[បន្ថែម/ហៅ GROUP ចាស់ៗចូលបញ្ជីគ្រប់គ្រង]** ➕\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 **លោកអ្នកអាចជ្រើសរើសវិធីណាមួយខាងក្រោម៖**\n\n"
        "1️⃣ **Forward សារពី Group មកទីនេះ (ងាយស្រួលបំផុត):**\n"
        "   ចូលទៅ Group ចាស់នោះ រួច Forward សារណាមួយមកកាន់ Bot ក្នុង Chat នេះ!\n\n"
        "2️⃣ **វាយលេខ Group ID:**\n"
        "   ឧទាហរណ៍៖ `-1002458931204` ឬ `2458931204`\n\n"
        "3️⃣ **វាយ Username ក្រុម ឬ Link:**\n"
        "   ឧទាហរណ៍៖ `@groupusername` ឬ `t.me/groupusername`\n\n"
        "💡 *ក្រុមដែលបានបន្ថែម នឹងទទួលបានសិទ្ធិ **៧ ថ្ងៃ (7-Day Trial)** ភ្លាមៗ!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*(វាយ /cancel ដើម្បីបោះបង់)*"
    )
    await send_clean_command_response(
        context,
        chat_id=user_id,
        text=prompt_text,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_message
    )


async def process_manual_add_group(context: ContextTypes.DEFAULT_TYPE, user_id: int, raw_input: str, user_message=None):
    """
    ដំណើរការស្វែងរក និងបន្ថែម Group តាម ID ឬ Username ឬ Link ចូល Database ស្វ័យប្រវត្តិ
    """
    clean_text = raw_input.strip()
    parts = clean_text.split(maxsplit=1)
    id_part = parts[0].strip()
    custom_title = parts[1].strip() if len(parts) > 1 else None

    real_chat = None
    final_chat_id = None

    # ករណី User វាយ Username (@groupname) ឬតំណភ្ជាប់ (t.me/groupname)
    target_uname = id_part
    if "t.me/" in target_uname:
        target_uname = target_uname.split("t.me/")[-1].replace("/", "").strip()
        if not target_uname.startswith("@") and not target_uname.startswith("+"):
            target_uname = f"@{target_uname}"
    elif target_uname.startswith("@"):
        pass
    else:
        target_uname = None

    if target_uname and not target_uname.startswith("@+"):
        try:
            c = await context.bot.get_chat(chat_id=target_uname)
            if c:
                real_chat = c
                final_chat_id = c.id
        except Exception as e:
            logger.error(f"Cannot resolve chat by username {target_uname}: {e}")

    # បើមិនមែនជា username ឬរកមិនឃើញ ព្យាយាម parse ជាលេខ ID
    if not real_chat:
        possible_ids = []
        try:
            parsed_id = int(id_part)
            possible_ids.append(parsed_id)
            if parsed_id > 0:
                possible_ids.append(int(f"-100{parsed_id}"))
                possible_ids.append(-parsed_id)
        except ValueError:
            await send_clean_command_response(
                context,
                chat_id=user_id,
                text=(
                    "⚠️ **ទម្រង់ Group ID ឬ Link មិនត្រឹមត្រូវទេ!**\n\n"
                    "👉 **វិធីទី ១:** វាយលេខ ID (ឧទាហរណ៍៖ `-1002458931204` ឬ `2458931204`)\n"
                    "👉 **វិធីទី ២:** វាយ Username (ឧទាហរណ៍៖ `@groupname` ឬ `t.me/groupname`)\n"
                    "👉 **វិធីទី ៣ (ងាយស្រួលបំផុត):** គ្រាន់តែ **Forward សារពី Group ចាស់នោះ** មកកាន់ Bot ក្នុង Chat នេះផ្ទាល់!\n\n"
                    "*(ចុច /cancel ដើម្បីបោះបង់)*"
                ),
                reply_markup=get_master_owner_keyboard(),
                parse_mode=ParseMode.MARKDOWN,
                user_message=user_message
            )
            return

        final_chat_id = possible_ids[0]
        for try_id in possible_ids:
            try:
                c = await context.bot.get_chat(chat_id=try_id)
                if c:
                    real_chat = c
                    final_chat_id = try_id
                    break
            except Exception:
                continue

    group_title = custom_title or (real_chat.title if real_chat and real_chat.title else f"Group {final_chat_id}")
    chat_obj = real_chat if real_chat else type('obj', (object,), {'id': final_chat_id, 'title': group_title})

    # បើកសិទ្ធិការពារ ៧ ថ្ងៃអូតូ
    sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=7, is_lifetime=False)

    # ផ្ញើសារអបអរសាទរទៅកាន់ Group (បើ Bot នៅក្នុងនោះស្រាប់)
    try:
        success_msg = (
            "🎉 **[ប្រព័ន្ធសុវត្ថិភាព TELEGUARD BOT]** 🎉\n\n"
            "🛡️ **Master Super Admin បានបើកដំណើរការប្រព័ន្ធការពារក្នុងក្រុមនេះដោយជោគជ័យ!**\n"
            "🛒 កញ្ចប់៖ **Trial 7 Days (សាកល្បង ៧ ថ្ងៃ)**\n"
            "✅ ស្កេនមេរោគ (.apk, .exe, .scr, .bat, .sh)\n"
            "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (.jpg.apk, .pdf.apk)\n"
            "✅ ប្រព័ន្ធ Anti-Flood & Clean Group 15s"
        )
        await send_auto_delete_message(context, final_chat_id, success_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass

    found_in_tg = "✅ បានភ្ជាប់ និងទាញយកទិន្នន័យពី Telegram ដោយជោគជ័យ" if real_chat else "⚠️ បានកត់ត្រា ID ទុកជាមុន (Bot នឹងចាប់ផ្ដើមការពារពេលលោកអ្នក Add ចូលក្រុម)"

    confirm_text = (
        "✅ **[បានបន្ថែម GROUP ចូលបញ្ជីគ្រប់គ្រងជោគជ័យ]** ✅\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{group_title}`\n"
        f"🆔 **លេខ Group ID:** `{final_chat_id}`\n"
        f"🛒 **កញ្ចប់សេវា:** `Trial 7 Days (សាកល្បង ៧ ថ្ងៃ)`\n"
        f"🛡️ **ស្ថានភាព:** 🟢 **ACTIVE (បើកដំណើរការ)**\n"
        f"📡 **ការតភ្ជាប់:** {found_in_tg}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 លោកអ្នកអាចចូលទៅកាន់ `/admin` ដើម្បីពិនិត្យ ឬបន្ថែមថ្ងៃបានគ្រប់ពេល!"
    )

    await send_clean_command_response(
        context,
        chat_id=user_id,
        text=confirm_text,
        reply_markup=get_master_owner_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
        user_message=user_message
    )


async def addgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command សម្រាប់ Master Owner បន្ថែម Group តាមពាក្យបញ្ជា /addgroup
    """
    user = update.effective_user
    chat = update.effective_chat
    if not is_sole_master_owner(user.id):
        return

    args = context.args
    user_msg = update.effective_message if chat.type == "private" else None
    if not args:
        await prompt_add_group(context, user.id, user_message=user_msg)
        return

    raw_input = " ".join(args)
    await process_manual_add_group(context, user.id, raw_input, user_message=user_msg)


async def sync_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command សម្រាប់ Master Owner ហៅ/ទាញ Group ណាដែល Bot កំពុងនៅស្រាប់ ចូលក្នុងបញ្ជីភ្លាមៗ!
    • វាយ /sync ក្នុង Group ណាមួយ ➡️ Bot នឹងទាញ Group នោះចូលបញ្ជី និងបើកសិទ្ធិ ៧ ថ្ងៃអូតូ!
    • វាយ /sync ក្នុង Private Chat ➡️ បើកផ្ទាំងបន្ថែម Group
    """
    user = update.effective_user
    chat = update.effective_chat
    if not is_sole_master_owner(user.id):
        return

    if chat.type in ["group", "supergroup"]:
        try:
            await update.effective_message.delete()
        except Exception:
            pass

        # បើកសិទ្ធិ ៧ ថ្ងៃ និងកត់ត្រាចូលបញ្ជីភ្លាម
        sync_client_record(chat, user=user, is_auth=True, is_enabled=True, plan_days=7, is_lifetime=False)

        confirm_text = (
            "✅ **[បានទាញក្រុមដែល Bot កំពុងនៅ ចូលបញ្ជីជោគជ័យ]** ✅\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{chat.title}`\n"
            f"🆔 **លេខ Group ID:** `{chat.id}`\n"
            f"🛒 **កញ្ចប់សេវា:** `Trial 7 Days (សាកល្បង ៧ ថ្ងៃ)`\n"
            f"🛡️ **ស្ថានភាព:** 🟢 **ACTIVE (កំពុងការពារ)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 ក្រុមនេះត្រូវបានភ្ជាប់ និងបើកសិទ្ធិការពារ ៧ ថ្ងៃរួចរាល់ហើយ!"
        )
        await send_clean_command_response(
            context,
            chat_id=user.id,
            text=confirm_text,
            reply_markup=get_master_owner_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            welcome_msg = (
                "🎉 **[ប្រព័ន្ធសុវត្ថិភាព TELEGUARD BOT]** 🎉\n\n"
                "🛡️ **Master Super Admin បានបើកដំណើរការប្រព័ន្ធការពារក្នុងក្រុមនេះដោយជោគជ័យ!**\n"
                "🛒 កញ្ចប់៖ **Trial 7 Days (សាកល្បង ៧ ថ្ងៃ)**\n"
                "✅ ស្កេនមេរោគ (.apk, .exe, .scr, .bat, .sh)\n"
                "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (.jpg.apk, .pdf.apk)\n"
                "✅ ប្រព័ន្ធ Anti-Flood & Clean Group 15s"
            )
            await send_auto_delete_message(context, chat.id, welcome_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    else:
        await prompt_add_group(context, user.id, user_message=update.effective_message)


# ==================== INLINE CALLBACK ROUTER ====================

async def master_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.message:
        cid = query.message.chat_id
        mid = query.message.message_id
        LAST_BOT_RESPONSES[cid] = [mid]
        old_task = ACTIVE_DELETION_TASKS.pop((cid, mid), None)
        if old_task and not old_task.done():
            old_task.cancel()

        async def _auto_clean_cb(bot, c_id, m_id, delay):
            try:
                await asyncio.sleep(delay)
                await bot.delete_message(chat_id=c_id, message_id=m_id)
            except Exception:
                pass
            finally:
                ACTIVE_DELETION_TASKS.pop((c_id, m_id), None)
                if c_id in LAST_BOT_RESPONSES and m_id in LAST_BOT_RESPONSES[c_id]:
                    LAST_BOT_RESPONSES[c_id].remove(m_id)

        t = asyncio.create_task(_auto_clean_cb(context.bot, cid, mid, BOT_MSG_DELETE_SECONDS))
        ACTIVE_DELETION_TASKS[(cid, mid)] = t
        PENDING_BOT_DELETIONS.append((cid, mid, time.time() + BOT_MSG_DELETE_SECONDS))

    if not is_sole_master_owner(user.id):
        await query.message.reply_text("⛔ អ្នកមិនមែនជាម្ចាស់ Bot ទេ!")
        return

    data = query.data

    # 1. Main Navigation Callbacks
    if data == "dash_refresh":
        await query.edit_message_reply_markup(reply_markup=generate_master_dashboard_keyboard())
        return

    if data == "dash_add_group":
        await prompt_add_group(context, user.id)
        return

    if data == "dash_select_group":
        await prompt_select_group(context, user.id)
        return

    if data == "dash_leave_list":
        text = (
            "🚪 **[ជ្រើសរើសក្រុមដើម្បីបញ្ជាឱ្យ BOT ចាកចេញ]** 🚪\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 សូមចុចលើប៊ូតុងឈ្មោះក្រុមខាងក្រោមដែលលោកអ្នកចង់ឱ្យ Bot ចាកចេញ៖\n"
            "*(រាល់ទិន្នន័យអតិថិជន និងប្រវត្តិការពារ នឹងនៅតែរក្សាទុកក្នុង Vault យ៉ាងគង់វង្ស)*"
        )
        await query.edit_message_text(text=text, reply_markup=generate_leave_groups_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("confirm_leave_"):
        chat_id = data.replace("confirm_leave_", "")
        group_title = GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")
        confirm_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ បញ្ជាក់៖ ឱ្យ Bot ចេញភ្លាម", callback_data=f"leave_{chat_id}"),
                InlineKeyboardButton("❌ បោះបង់", callback_data="dash_leave_list")
            ]
        ])
        text = (
            f"⚠️ **[បញ្ជាក់ការបញ្ជាឱ្យ Bot ចាកចេញពីក្រុម]**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{group_title}`\n"
            f"🆔 **លេខ Group ID:** `{chat_id}`\n\n"
            f"👉 **តើលោកអ្នកពិតជាចង់ឱ្យ Bot ចាកចេញពីក្រុមនេះមែនឬទេ?**\n"
            f"*(Bot នឹងផ្ញើសារលាហើយក្នុងក្រុម រួចចាកចេញភ្លាមៗ)*"
        )
        await query.edit_message_text(text=text, reply_markup=confirm_keyboard, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "dash_back":
        text = (
            "⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n"
            "👑 **សូមស្វាគមន៍ម្ចាស់ Bot (Sole Master Owner)**\n\n"
            "👇 **សូមចុចលើឈ្មោះ Group ខាងក្រោម ដើម្បីពិនិត្យ Profile, ប្រវត្តិទិញ, ថ្ងៃនៅសល់ និងកំណត់សិទ្ធិ៖**\n"
        )
        await query.edit_message_text(text=text, reply_markup=generate_master_dashboard_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "dash_clients":
        await list_groups_command(update, context, send_to_user_id=user.id)
        return

    if data == "dash_logs":
        await logs_command(update, context, send_to_user_id=user.id)
        return

    if data == "dash_broadcast":
        await broadcast_to_channel_command(update, context)
        return

    # 2. Drill-Down: Manage Specific Group Profile
    if data.startswith("manage_grp_"):
        chat_id = data.replace("manage_grp_", "")
        gdata = GROUPS_CONFIG.get(str(chat_id), {})
        cdata = CLIENTS_DB.get(str(chat_id), {})

        title = gdata.get("title", f"Group {chat_id}")
        is_auth = gdata.get("is_authorized", False)
        is_en = gdata.get("is_enabled", False)
        is_life = gdata.get("is_lifetime", False)
        plan_type = gdata.get("plan_type", "Trial")
        act_date = gdata.get("activated_date", "Not Yet Activated")
        exp_date = gdata.get("expiry_date", "Not Yet Activated")
        rem_str = get_remaining_time_str(exp_date, is_life)

        status_kh = "🟢 ACTIVE (កំពុងការពារ)" if (is_auth and is_en) else ("🟡 PAUSED (បានផ្អាក)" if is_auth else "🔴 UNAUTHORIZED (មិនទាន់ទិញ)")
        threats = gdata.get("threats_blocked_count", 0)
        c_contact = cdata.get("customer_contact", {})

        # រៀបចំ Purchase History
        p_history_str = ""
        for p in cdata.get("purchase_history", [])[-2:]:
            p_history_str += f"  • {p.get('package')} ({p.get('purchased_date')})\n"
        if not p_history_str:
            p_history_str = "  • មិនទាន់មានប្រវត្តិទិញ\n"

        detail_text = (
            f"🛠️ **[ផ្ទាំងគ្រប់គ្រងក្រុម - GROUP CONTROL PANEL]**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{title}`\n"
            f"🆔 **លេខ Group ID:** `{chat_id}`\n"
            f"👤 **អតិថិជន:** {c_contact.get('name', 'N/A')} ({c_contact.get('username', 'N/A')})\n"
            f"🔢 **Customer ID:** `{c_contact.get('user_id', 'N/A')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔰 **ស្ថានភាពបច្ចុប្បន្ន:** {status_kh}\n"
            f"🛒 **កញ្ចប់សេវាកម្ម:** {plan_type}\n"
            f"📅 **ថ្ងៃចាប់ផ្ដើមទិញបត:** `{act_date}`\n"
            f"⌛ **ថ្ងៃផុតកំណត់:** `{exp_date}`\n"
            f"⏳ **រយៈពេលនៅសល់:** {rem_str}\n"
            f"☣️ **មេរោគដែលបានទប់ស្កាត់:** `{threats}` ករណី\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📜 **ប្រវត្តិទិញបត (Purchase History)៖**\n{p_history_str}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 **សូមចុចប៊ូតុងខាងក្រោមដើម្បីកំណត់សិទ្ធិ ឬបន្ថែមថ្ងៃប្រើប្រាស់៖**"
        )
        await query.edit_message_text(text=detail_text, reply_markup=generate_group_detail_keyboard(chat_id), parse_mode=ParseMode.MARKDOWN)
        return

    # 3. Actions: Add 7 Days / Add 30 Days / Add 90 Days / Set Lifetime / Revoke / Toggle / Delete / Leave
    if data.startswith("add_7_"):
        chat_id = data.replace("add_7_", "")
        chat_obj = type('obj', (object,), {'id': int(chat_id), 'title': GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")})
        sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=7, is_lifetime=False)
        await query.answer("🎁 បានបន្ថែមរយៈពេលសាកល្បង ៧ ថ្ងៃជោគជ័យ!", show_alert=True)
        await master_callback_router(update, context)
        return

    if data.startswith("add_30_"):
        chat_id = data.replace("add_30_", "")
        chat_obj = type('obj', (object,), {'id': int(chat_id), 'title': GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")})
        sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=30, is_lifetime=False)
        await query.answer("✅ បានបន្ថែមរយៈពេល 30 ថ្ងៃជោគជ័យ!", show_alert=True)
        # Reload group profile view
        await master_callback_router(update, context)
        return

    if data.startswith("add_90_"):
        chat_id = data.replace("add_90_", "")
        chat_obj = type('obj', (object,), {'id': int(chat_id), 'title': GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")})
        sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=90, is_lifetime=False)
        await query.answer("✅ បានបន្ថែមរយៈពេល 90 ថ្ងៃជោគជ័យ!", show_alert=True)
        await master_callback_router(update, context)
        return

    if data.startswith("set_life_"):
        chat_id = data.replace("set_life_", "")
        chat_obj = type('obj', (object,), {'id': int(chat_id), 'title': GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")})
        sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=None, is_lifetime=True)
        await query.answer("👑 បានកំណត់សិទ្ធិ VIP ពេញមួយជីវិត (Lifetime) ជោគជ័យ!", show_alert=True)
        await master_callback_router(update, context)
        return

    if data.startswith("revoke_"):
        chat_id = data.replace("revoke_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = False
            GROUPS_CONFIG[chat_id]["is_enabled"] = False
            GROUPS_CONFIG[chat_id]["plan_type"] = "🔴 Revoked / Expired"
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        if chat_id in CLIENTS_DB:
            CLIENTS_DB[chat_id]["license_status"] = "🔴 UNAUTHORIZED (បានដកសិទ្ធិ)"
            save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)
        await query.answer("🔴 បានដកសិទ្ធិប្រើប្រាស់ពី Group នេះរួចរាល់!", show_alert=True)
        await master_callback_router(update, context)
        return

    if data.startswith("toggle_en_"):
        chat_id = data.replace("toggle_en_", "")
        if chat_id in GROUPS_CONFIG:
            cur_en = GROUPS_CONFIG[chat_id].get("is_enabled", False)
            GROUPS_CONFIG[chat_id]["is_enabled"] = not cur_en
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        await query.answer("🔄 បានប្ដូរស្ថានភាព ON/PAUSE រួចរាល់!", show_alert=False)
        await master_callback_router(update, context)
        return

    if data.startswith("set_del_"):
        chat_id = data.replace("set_del_", "")
        if chat_id in GROUPS_CONFIG:
            del GROUPS_CONFIG[chat_id]
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        text = "✅ **បានលុប Group នេះចេញពីបញ្ជីគ្រប់គ្រងរួចរាល់!**"
        await query.edit_message_text(text=text, reply_markup=generate_master_dashboard_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("leave_"):
        chat_id = data.replace("leave_", "")
        group_title = GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")
        leave_status = ""
        try:
            try:
                goodbye_msg = (
                    "👋 **[ជម្រាបលា - TELEGUARD BOT]**\n\n"
                    "Bot ត្រូវបានបញ្ជាដោយ Master Super Admin ឱ្យចាកចេញពីក្រុមនេះ។\n"
                    f"👉 ប្រសិនបើត្រូវការប្រើប្រាស់ឡើងវិញ សូមទាក់ទង [{OFFICIAL_CHANNEL_USERNAME}]({OFFICIAL_CHANNEL_LINK})\n"
                    "សូមអរគុណ!"
                )
                await context.bot.send_message(chat_id=int(chat_id), text=goodbye_msg, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass

            await context.bot.leave_chat(chat_id=int(chat_id))
            leave_status = "✅ Bot បានចាកចេញពីក្រុម Telegram នោះដោយជោគជ័យ!"
        except Exception as e:
            leave_status = f"⚠️ មិនអាចចាកចេញពីក្រុមបានទេ (Bot ប្រហែលជាមិននៅក្នុងក្រុមនោះទៀតឡើយ)៖ {e}"

        if str(chat_id) in GROUPS_CONFIG:
            GROUPS_CONFIG[str(chat_id)]["is_authorized"] = False
            GROUPS_CONFIG[str(chat_id)]["is_enabled"] = False
            GROUPS_CONFIG[str(chat_id)]["plan_type"] = "🚪 Bot បានចាកចេញពីក្រុម"
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

        if str(chat_id) in CLIENTS_DB:
            CLIENTS_DB[str(chat_id)]["license_status"] = "🚪 LEFT (Bot ចាកចេញ)"
            save_json_file(CLIENTS_DB_FILE, CLIENTS_DB)

        record_audit_event(
            event_type="BOT_LEAVE_GROUP",
            chat_id=int(chat_id),
            chat_title=group_title,
            user_id=user.id,
            user_name=user.full_name,
            details="Master Owner forced bot to leave group",
            action=leave_status
        )

        confirm_text = (
            f"🚪 **[បានបញ្ជាឱ្យ Bot ចាកចេញពីក្រុម]**\n\n"
            f"👥 **ក្រុម៖** `{group_title}` (`{chat_id}`)\n"
            f"⚡ **ស្ថានភាព៖** {leave_status}\n\n"
            f"📁 *កំណត់សម្គាល់៖ ទិន្នន័យអតិថិជន និងប្រវត្តិការពារត្រូវបានរក្សាទុកក្នុង Vault យ៉ាងគង់វង្ស ១០០%!*"
        )
        await query.edit_message_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚪 បញ្ជីក្រុមសម្រាប់ឱ្យ Bot ចេញបន្ត", callback_data="dash_leave_list")],
                [InlineKeyboardButton("🔙 ត្រឡប់ទៅ Dashboard", callback_data="dash_back")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 4. Instant New Group Approval (Automatic 7-Day Free Trial)
    if data.startswith("approve_"):
        chat_id = data.replace("approve_", "")
        chat_obj = type('obj', (object,), {'id': int(chat_id), 'title': GROUPS_CONFIG.get(str(chat_id), {}).get("title", f"Group {chat_id}")})
        sync_client_record(chat_obj, user=None, is_auth=True, is_enabled=True, plan_days=7, is_lifetime=False)

        group_title = GROUPS_CONFIG.get(str(chat_id), {}).get("title", chat_id)
        await query.edit_message_text(
            f"✅ **[បានអនុញ្ញាតឱ្យសាកល្បង ៧ ថ្ងៃ ជោគជ័យ]**\n\n"
            f"👥 ក្រុម៖ **{group_title}** (`{chat_id}`)\n"
            f"🛒 កញ្ចប់៖ **Trial 7 Days (សាកល្បង ៧ ថ្ងៃ)**\n"
            f"🛡️ ស្ថានភាព៖ **បានបើកដំណើរការសិទ្ធិការពារពេញលេញ ១០០% រយៈពេល ៧ ថ្ងៃ!**",
            parse_mode=ParseMode.MARKDOWN
        )

        success_msg = (
            "🎉 **[សេវាកម្មត្រូវបានអនុញ្ញាតឱ្យសាកល្បង ៧ ថ្ងៃ]** 🎉\n\n"
            "🛡️ **Master Super Admin បានអនុញ្ញាតឱ្យក្រុមនេះប្រើប្រាស់ប្រព័ន្ធការពារដោយឥតគិតថ្លៃរយៈពេល ៧ ថ្ងៃ!**\n"
            "✅ ស្កេនមេរោគ (.apk, .exe, .scr, .bat, .sh)\n"
            "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (.jpg.apk, .pdf.apk)\n"
            "✅ ប្រព័ន្ធ Anti-Flood & Clean Group 15s"
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


# ==================== MAIN EXECUTION & RENDER HEALTH CHECK ====================

async def start_web_health_server():
    """
    🌐 Render Web Health Check Server:
    បើក HTTP Server ស្តាប់លើ $PORT (ដូចជា Port 10000 ឬ 8080)
    ឆ្លើយតប HTTP 200 OK ជូន Render Health Scan ដោយស្វ័យប្រវត្តិ
    ការពារបញ្ហា 'Port scan timeout' លើ Render Free Tier និងអនុញ្ញាតឱ្យ UptimeRobot ping រក្សា bot ឱ្យនៅរស់ ២៤/៧។
    """
    port_str = os.environ.get("PORT")
    if not port_str:
        logger.info("[Health Check] គ្មាន PORT ត្រូវបានកំណត់ទេ (រត់លើ Local/CLI ធម្មតា)")
        return

    try:
        port = int(port_str)
    except ValueError:
        port = 8080

    try:
        from aiohttp import web

        async def health_handler(request):
            return web.Response(
                text="🛡️ Telegram Security Bot is ALIVE & RUNNING on Render!\nStatus: 200 OK\nTimestamp: " + datetime.now().isoformat(),
                content_type="text/plain",
                status=200
            )

        health_app = web.Application()
        health_app.router.add_get("/", health_handler)
        health_app.router.add_get("/health", health_handler)
        health_app.router.add_get("/ping", health_handler)

        runner = web.AppRunner(health_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"🌐 [Render Health Server] បានបើក Port {port} (0.0.0.0:{port}) ជូន Render Health Check រួចរាល់!")
    except Exception as e:
        logger.error(f"⚠️ [Render Health Server] បរាជ័យក្នុងការបើក Web Server: {e}")


async def post_init(application):
    asyncio.create_task(start_web_health_server())
    asyncio.create_task(daily_reminder_loop(application))
    asyncio.create_task(bot_message_sweeper_loop(application))
    try:
        commands = [
            BotCommand("admin", "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard"),
            BotCommand("groups", "📋 បញ្ជីក្រុម និងអតិថិជន (CRM)"),
            BotCommand("addgroup", "➕ បន្ថែម ឬហៅក្រុមចាស់ចូលបញ្ជី"),
            BotCommand("sync", "🔄 ហៅ/ទាញក្រុមចូលបញ្ជី"),
            BotCommand("logs", "📜 កំណត់ត្រាសុវត្ថិភាព (Logs)"),
            BotCommand("status", "🛡️ ឆែកស្ថានភាពប្រព័ន្ធការពារ"),
            BotCommand("broadcast", "📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel"),
            BotCommand("leave", "🚪 បញ្ជាឱ្យ Bot ចាកចេញពីក្រុម"),
            BotCommand("myid", "🆔 មើលលេខ Telegram ID"),
            BotCommand("help", "❓ ការណែនាំ & ជំនួយ"),
            BotCommand("start", "🚀 ចាប់ផ្ដើម Bot / បើកផ្ទាំងបញ្ជា")
        ]
        await application.bot.set_my_commands(commands)
        try:
            await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")


def main():
    # Ensure active event loop exists for Python 3.12, 3.13, and 3.14+ (Render compatibility)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("❌ CRITICAL ERROR: TELEGRAM_BOT_TOKEN is missing! Please set TELEGRAM_BOT_TOKEN in Render Environment variables.")
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    print("[*] Full Commercial CRM & Marketing Bot starting for Owner (240224709)...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("addgroup", addgroup_command))
    app.add_handler(CommandHandler("sync", sync_group_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("check", status_command))
    app.add_handler(CommandHandler("leave", leave_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("groups", list_groups_command))
    app.add_handler(CommandHandler("clients", list_groups_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("broadcast", broadcast_to_channel_command))
    app.add_handler(CommandHandler("channel", broadcast_to_channel_command))

    # Master Interactive Inline Callback Router
    app.add_handler(CallbackQueryHandler(master_callback_router))

    # Catch when Bot is added to new groups
    app.add_handler(ChatMemberHandler(handle_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))

    # 👥 One-Click Native Chat Picker Receiver (CHAT_SHARED)
    app.add_handler(MessageHandler(filters.StatusUpdate.CHAT_SHARED, handle_chat_shared))

    # 🧹 Auto-Delete Service messages
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, handle_service_messages))

    # File Monitor
    app.add_handler(MessageHandler(filters.Document.ALL, handle_incoming_file))

    # Regular Messages & Anti-Flood Monitor
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_messages))
    app.add_handler(MessageHandler(filters.Sticker.ALL | filters.ANIMATION, handle_regular_messages))

    # Master Menu Keyboard Router
    app.add_handler(MessageHandler(filters.Regex(r"^(⚙️ ផ្ទាំងគ្រប់គ្រង Admin Dashboard|⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel|👥 ចុចរើសក្រុម \(Select Group\)|👥 ចុចរើសក្រុម|➕ បន្ថែម Group តាម ID|➕ បន្ថែមក្រុម|🔄 Sync ក្រុមនេះចូលបញ្ជី|📋 បញ្ជីអតិថិជន & Group|📋 បញ្ជីឈ្មោះក្រុម & អតិថិជន|📜 ប្រវត្តិការពារ & ការទិញបត|📜 ប្រវត្តិការពារ \(Logs\)|📢 ផ្សាយពាណិជ្ជកម្មទៅ Channel|🛡️ ឆែកស្ថានភាព Bot|🆔 មើលលេខ ID|🆔 មើលលេខ ID Group|❓ ការណែនាំ & ជំនួយ|🚀 ចាប់ផ្ដើម Bot ឡើងវិញ \(/start\))$"), handle_regular_messages))

    print("[OK] Full Commercial CRM & Marketing Bot is fully active!")
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Fatal polling exception: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
