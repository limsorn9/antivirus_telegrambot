"""
=============================================================================
🛡️ TELEGRAM GROUP MALWARE & THREAT GUARD BOT (COMMERCIAL LICENSE EDITION)
=============================================================================
Author: Cybersecurity & Telegram Defense Bot
Master Super Admin: 240224709 (Global Authority Everywhere)

Business & Security Features:
1. 🔐 Master License System: ក្រុមដែលមិនទាន់ទិញសិទ្ធិ Bot មិនការពារឡើយ
2. 📢 2x/Day Upsell Reminders: លោតសារដាស់តឿនឱ្យទិញសិទ្ធិ ២ ដងក្នុងមួយថ្ងៃ (លុបក្នុង 60s)
3. 🆔 Limited Group Admin Access: Admin នៃក្រុមដែលគ្មានសិទ្ធិ អាចឆែកមើលបានតែលេខ Group ID ប៉ុណ្ណោះ
4. ⏱️ 60-Second Strict Auto-Delete: គ្រប់សារទាំងអស់របស់ Bot ក្នុង Group រលាយបាត់ក្នុង 60s
5. 🔒 Strict Admin Lock: សមាជិកទូទៅគ្មានសិទ្ធិបញ្ជា Bot ដាច់ខាត
6. 📜 Audit Logging & Registry: ចងក្រងប្រវត្តិ និងបញ្ជីក្រុមដែលបានអនុញ្ញាត
7. 💼 Work-Friendly: Link & Document ការងារ មិនលុបដាច់ខាត
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
    ChatPermissions,
    ChatMemberUpdated,
    ReplyKeyboardMarkup,
    KeyboardButton,
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

# កំណត់ Super Admin IDs (បញ្ចូល ID: 240224709 ជា Master Admin អចិន្ត្រៃយ៍)
SUPER_ADMIN_IDS = {"240224709"}
raw_env_admins = os.getenv("SUPER_ADMIN_ID", os.getenv("ADMIN_ID", "")).split(",")
for aid in raw_env_admins:
    if aid.strip():
        SUPER_ADMIN_IDS.add(aid.strip())

PUNISHMENT_MODE = os.getenv("PUNISHMENT_MODE", "MUTE").upper().strip()
MUTE_DURATION_HOURS = int(os.getenv("MUTE_DURATION_HOURS", "24"))

# Settings សម្រាប់ភាពស្អាតក្នុង Group
AUTO_DELETE_SERVICE_MSGS = os.getenv("AUTO_DELETE_SERVICE_MSGS", "true").lower() == "true"
BOT_MSG_DELETE_SECONDS = int(os.getenv("BOT_MSG_DELETE_SECONDS", "60"))
ANTI_FLOOD_ENABLED = os.getenv("ANTI_FLOOD_ENABLED", "true").lower() == "true"
FLOOD_MAX_MSGS = int(os.getenv("FLOOD_MAX_MSGS", "5"))
FLOOD_WINDOW_SECONDS = int(os.getenv("FLOOD_WINDOW_SECONDS", "3"))

GROUPS_CONFIG_FILE = "groups_config.json"
AUDIT_LOG_FILE = "security_audit_logs.json"

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("MalwareGuardBot")

# In-Memory Trackers
SCAN_CACHE = {}
FLOOD_TRACKER = {}


# ==================== PERSISTENT STORAGE ====================

def load_json_file(file_path: str, default_val: any) -> any:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    return default_val


def save_json_file(file_path: str, data: any):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")


GROUPS_CONFIG = load_json_file(GROUPS_CONFIG_FILE, {})
AUDIT_LOGS = load_json_file(AUDIT_LOG_FILE, [])


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


# ==================== MASTER APPROVAL & PERMISSIONS ====================

def is_super_admin(user_id: int) -> bool:
    """ពិនិត្យមើលថាតើជា Master Super Admin ឬទេ (ID: 240224709)"""
    return str(user_id) in SUPER_ADMIN_IDS


def is_group_authorized(chat_id: int) -> bool:
    """ពិនិត្យថាតើ Group នេះ ត្រូវបាន Master Super Admin អនុញ្ញាតសិទ្ធិ (Approved) ឬនៅ"""
    chat_key = str(chat_id)
    if chat_key in GROUPS_CONFIG:
        return GROUPS_CONFIG[chat_key].get("is_authorized", False) and GROUPS_CONFIG[chat_key].get("is_enabled", False)
    return False


async def is_authorized_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ពិនិត្យសិទ្ធិ Admin ក្នុង Group"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    if is_super_admin(user.id):
        return True

    if chat.type == "private":
        return True

    try:
        member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


# ==================== ⏱️ 60-SECOND AUTO-DELETE HELPER ====================

async def delete_message_after_delay(bot, chat_id: int, message_id: int, delay_seconds: int = BOT_MSG_DELETE_SECONDS):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def send_auto_delete_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = BOT_MSG_DELETE_SECONDS, **kwargs):
    """ផ្ញើសាររបស់ Bot ដែលនឹងរលាយបាត់ទៅវិញក្នុង ៦០ វិនាទី"""
    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        asyncio.create_task(delete_message_after_delay(context.bot, chat_id, msg.message_id, delay))
        return msg
    except Exception as e:
        logger.error(f"Error sending auto-delete message: {e}")
        return None


# ==================== 📢 TWICE-DAILY REMINDER BACKGROUND JOB ====================

async def daily_reminder_loop(app):
    """
    រត់ស្វ័យប្រវត្តិក្នង Background៖ ឆែកមើល Group ដែលមិនទាន់មានសិទ្ធិ
    ហើយផ្ញើសារដាស់តឿនឱ្យទិញសិទ្ធិប្រើប្រាស់ ២ ដងក្នុងមួយថ្ងៃ (រៀងរាល់ ១២ ម៉ោងម្ដង)
    """
    logger.info("Daily Reminder background job started (2x per day for unauthorized groups)...")
    while True:
        try:
            now_ts = time.time()
            for chat_id_str, gdata in list(GROUPS_CONFIG.items()):
                is_auth = gdata.get("is_authorized", False)
                # ប្រសិនបើ Group មិនទាន់បានទិញសិទ្ធិ / មិនទាន់អនុញ្ញាត
                if not is_auth:
                    last_reminder = gdata.get("last_reminder_ts", 0)
                    # 12 ម៉ោង = 43200 វិនាទី (២ ដងក្នុង ១ ថ្ងៃ)
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
                            "👉 **សូមទាក់ទង Master Super Admin (ID: `240224709`) ដើម្បីទិញអាជ្ញាប័ណ្ណប្រើប្រាស់!**\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៦០ វិនាទី)*"
                        )
                        try:
                            msg = await app.bot.send_message(chat_id=chat_id, text=reminder_text, parse_mode=ParseMode.MARKDOWN)
                            asyncio.create_task(delete_message_after_delay(app.bot, chat_id, msg.message_id, BOT_MSG_DELETE_SECONDS))
                            GROUPS_CONFIG[chat_id_str]["last_reminder_ts"] = now_ts
                            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
                            logger.info(f"Sent 2x/day reminder to unauthorized group {chat_id_str}")
                        except Exception as e:
                            logger.error(f"Cannot send reminder to {chat_id_str}: {e}")
        except Exception as err:
            logger.error(f"Error in daily_reminder_loop: {err}")

        # ឆែកមើលរៀងរាល់ ៣០ នាទីម្ដង
        await asyncio.sleep(1800)


# ==================== NEW GROUP NOTIFICATION TO MASTER ADMIN ====================

async def notify_master_admin_new_group(context: ContextTypes.DEFAULT_TYPE, chat, added_by_user=None):
    added_name = added_by_user.full_name if added_by_user else "Admin Group"
    added_id = added_by_user.id if added_by_user else "N/A"

    text = (
        "🔔 **[ការស្នើសុំសិទ្ធិប្រើប្រាស់ BOT ថ្មី - NEW GROUP ADDED]** 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{chat.title or 'Unknown Group'}`\n"
        f"🆔 **លេខ Group ID:** `{chat.id}`\n"
        f"👤 **អ្នក Add ចូល:** {added_name} (`ID: {added_id}`)\n"
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
        chat_key = str(chat.id)
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {
                "title": chat.title or "Unknown Group",
                "chat_id": chat.id,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_authorized": False,  # Default: មិនទាន់មានសិទ្ធិ
                "is_enabled": False,     # Default: មិនទាន់បើក
                "last_reminder_ts": time.time(),
                "added_by_id": user.id if user else None,
                "added_by_name": user.full_name if user else None,
                "threats_blocked_count": 0
            }
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

            await notify_master_admin_new_group(context, chat, user)

            pending_msg = (
                "🤖 **[ប្រព័ន្ធសុវត្ថិភាព TELEGUARD BOT]**\n\n"
                "សូមអរគុណដែលបាន Add Bot ចូលក្នុងក្រុមនេះ! 🎉\n"
                "⚠️ **ស្ថានភាព៖** មិនទាន់មានអាជ្ញាប័ណ្ណប្រើប្រាស់ (Inactive) នៅឡើយទេ។\n"
                f"🆔 **លេខ Group ID របស់អ្នក៖** `{chat.id}`\n\n"
                "👉 សូមទាក់ទង **Master Super Admin (ID: `240224709`)** ដើម្បីទិញសិទ្ធិ និងបើកដំណើរការប្រព័ន្ធការពារពេញលេញ!\n"
                "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ៦០ វិនាទី)*"
            )
            await send_auto_delete_message(context, chat.id, pending_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)


# ==================== DYNAMIC BOTTOM KEYBOARD ====================

def get_bottom_menu_keyboard(is_master: bool = False) -> ReplyKeyboardMarkup:
    if is_master:
        keyboard = [
            [
                KeyboardButton("🛡️ ឆែកស្ថានភាព Bot"),
                KeyboardButton("🆔 មើលលេខ ID Group")
            ],
            [
                KeyboardButton("⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel"),
                KeyboardButton("📋 បញ្ជីឈ្មោះក្រុម & សេវាកម្ម")
            ],
            [
                KeyboardButton("📜 ប្រវត្តិការពារ (Logs)")
            ]
        ]
    else:
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
    if is_super_admin(user_id):
        return "👑 (Super Admin Protected)"

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

    if is_super_admin(user.id) or await is_authorized_group_admin(update, context):
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

    # បើជា Group ដែលមិនទាន់មានអាជ្ញាប័ណ្ណ ➡️ មិនទាន់ការពារឡើយ
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
            f"👤 **អ្នកផ្ញើ:** {sender_name} (`ID: {sender.id}`)\n"
            f"📁 **ឈ្មោះហ្វាល់:** `{file_name}`\n"
            f"🔍 **ប្រភេទគ្រោះថ្នាក់:** {analysis['reason']}\n"
            f"⚡ **ចំណាត់ការ:** សារត្រូវបានលុបភ្លាមៗ | {action_taken}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **ការណែនាំសុវត្ថិភាព:** សូមប្រុងប្រយ័ត្នខ្ពស់ចំពោះហ្វាល់ដែលបង្កប់កន្ទុយ `.apk` ឬ `.exe` ព្រោះវាអាចជា Banking Trojan លួចគណនីធនាគាររបស់អ្នក!\n\n"
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញស្វ័យប្រវត្តិក្នងរយៈពេល ៦០ វិនាទី)*"
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
                    f"👤 **អ្នកផ្ញើ:** {sender.full_name} (`ID: {sender.id}`)\n"
                    f"📁 **ឈ្មោះហ្វាល់:** `{file_name}`\n"
                    f"🔬 **ពិន្ទុគ្រោះថ្នាក់:** {vt_result['malicious_count']} Security Engines ចាត់ទុកជាមេរោគ!\n"
                    f"🧬 **SHA-256:** `{vt_result['sha256']}`\n"
                    f"⚡ **ចំណាត់ការ:** សារត្រូវបានលុប | {action_taken}\n\n"
                    f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៦០ វិនាទី)*"
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


# ==================== TEXT MESSAGE & BUTTON MONITOR ====================

async def handle_regular_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if await handle_anti_flood(update, context):
        return

    text = update.message.text.strip() if update.message and update.message.text else ""

    if text in [
        "🛡️ ឆែកស្ថានភាព Bot", "/status", "/check",
        "🆔 មើលលេខ ID Group", "/myid", "/id",
        "⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin",
        "📋 បញ្ជីឈ្មោះក្រុម & សេវាកម្ម", "/groups",
        "📜 ប្រវត្តិការពារ (Logs)", "/logs"
    ]:
        if chat.type in ["group", "supergroup"]:
            # ប្រសិនបើសមាជិកធម្មតាចុច ➡️ បដិសេធភ្លាម
            if not await is_authorized_group_admin(update, context):
                try:
                    await update.effective_message.delete()
                except Exception:
                    pass
                await send_auto_delete_message(
                    context,
                    chat.id,
                    f"⛔ **សុំទោស {user.first_name}!**\nសមាជិកទូទៅមិនមានសិទ្ធិបញ្ជា ឬឆែក Bot ក្នុងក្រុមនេះឡើយ (សម្រាប់តែ Admin ប៉ុណ្ណោះ)។",
                    delay=5,
                    parse_mode=ParseMode.MARKDOWN
                )
                return

        if text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
            await status_command(update, context)
        elif text in ["🆔 មើលលេខ ID Group", "/myid", "/id"]:
            await myid_command(update, context)
        elif text in ["⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel", "/admin"]:
            await admin_command(update, context)
        elif text in ["📋 បញ្ជីឈ្មោះក្រុម & សេវាកម្ម", "/groups"]:
            await list_groups_command(update, context)
        elif text in ["📜 ប្រវត្តិការពារ (Logs)", "/logs"]:
            await logs_command(update, context)


# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    is_master = is_super_admin(user.id)
    role_tag = "👑 **(Master Super Admin)**" if is_master else "🛡️ (Group Admin)"

    if chat.type in ["group", "supergroup"] and not await is_authorized_group_admin(update, context):
        try:
            await update.effective_message.delete()
        except Exception:
            pass
        return

    text = (
        f"🤖 **សួស្តី {user.first_name}! {role_tag}**\n\n"
        "ខ្ញុំជា Bot ការពារមេរោគ និងគ្រប់គ្រងសុវត្ថិភាព Group Telegram!\n\n"
        "🛡️ **មុខងារការពារ និងគ្រប់គ្រង៖**\n"
        "✅ ស្កេន និងលុប `.apk`, `.exe`, `.scr`, `.bat`, `.sh` ដោយស្វ័យប្រវត្តិ\n"
        "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (Double Extension ដូចជា `.jpg.apk`, `.pdf.apk`)\n"
        "✅ ឆែកស្កេន Cloud Hash លើ VirusTotal សម្រាប់ហ្វាល់ `.zip` និង `.rar`\n"
        "✅ ⏱️ **រាល់សារទាំងអស់ក្នុង Group នឹងលុបបាត់ទៅវិញក្នុង ៦០ វិនាទី**\n"
        "✅ 🔐 **ទាល់តែទិញអាជ្ញាប័ណ្ណពី Master Admin ទើប Bot បើកការពារ**\n"
        "✅ 💼 អនុញ្ញាត Link & Document ការងារ ១០០%\n\n"
        "🔐 **ចំណាំ៖** មានតែ **Admin នៃក្រុមនីមួយៗ** និង **Master Super Admin** ប៉ុណ្ណោះ ទើបមានសិទ្ធិបញ្ជា Bot។"
    )

    if chat.type in ["group", "supergroup"]:
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text=text, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    is_master = is_super_admin(user.id)

    if not is_master and not await is_authorized_group_admin(update, context):
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
            await send_auto_delete_message(
                context,
                chat.id,
                f"⛔ **សុំទោស {user.first_name}!**\nសមាជិកទូទៅមិនមានសិទ្ធិបញ្ជា ឬឆែកស្ថានភាព Bot ក្នុងក្រុមនេះឡើយ (សម្រាប់តែ Admin ប៉ុណ្ណោះ)។",
                delay=5,
                parse_mode=ParseMode.MARKDOWN
            )
        return

    is_authorized = is_group_authorized(chat.id)

    # ប្រសិនបើ Group មិនទាន់មានអាជ្ញាប័ណ្ណ ➡️ បង្ហាញត្រឹមតែលេខ ID និងការណែនាំឱ្យទិញសិទ្ធិ
    if not is_authorized and not is_master:
        unauth_text = (
            "⚠️ **[ក្រុមមិនទាន់បានទិញសិទ្ធិប្រើប្រាស់ - UNAUTHORIZED]**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **ឈ្មោះក្រុម:** `{chat.title}`\n"
            f"🆔 **លេខ Group ID របស់អ្នក:** `{chat.id}`\n"
            "🚫 **ស្ថានភាពការពារ:** 🔴 **មិនទាន់ដំណើរការ (OFF)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **ការណែនាំ៖** សូមចម្លងលេខ Group ID (`{chat.id}`) នេះ ផ្ញើទៅកាន់ **Master Super Admin (ID: `240224709`)** ដើម្បីទិញអាជ្ញាប័ណ្ណ និងបើកដំណើរការប្រព័ន្ធការពារពេញលេញ!\n\n"
            "*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៦០ វិនាទី)*"
        )
        if chat.type in ["group", "supergroup"]:
            await send_auto_delete_message(context, chat.id, unauth_text, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(unauth_text, parse_mode=ParseMode.MARKDOWN)
        return

    # ករណីក្រុមដែលមានសិទ្ធិពេញលេញ
    shield_status_str = "🟢 **កំពុងការពារយ៉ាងសកម្ម (ACTIVE / SHIELD ON)**" if is_authorized else "🔴 **មិនទាន់ដំណើរការ (INACTIVE)**"
    vt_status = "✅ **ភ្ជាប់រួចរាល់ (Connected)**" if VIRUSTOTAL_API_KEY and VIRUSTOTAL_API_KEY != "YOUR_VIRUSTOTAL_API_KEY_HERE" else "⚠️ **Local Shield Only**"

    group_name = chat.title if chat.type in ["group", "supergroup"] else "Chat ផ្ទាល់ខ្លួន (Private Chat)"
    chat_type_kh = "ក្រុម Telegram (Group)" if chat.type in ["group", "supergroup"] else "ផ្ទាំងសារផ្ទាល់ខ្លួន (Private)"
    admin_status = "👑 Master Super Admin" if is_master else "🛡️ Group Admin"

    text = (
        "🛡️ **[ព័ត៌មាន និងស្ថានភាពសុវត្ថិភាព BOT STATUS]** 🛡️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **ឈ្មោះក្រុម:** `{group_name}`\n"
        f"🆔 **លេខ Group ID:** `{chat.id}`\n"
        f"🏷️ **ប្រភេទ:** {chat_type_kh}\n"
        f"👤 **Admin ពិនិត្យ:** {user.full_name} (`{admin_status}`)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 **ស្ថានភាពការពារ:** {shield_status_str}\n"
        f"⚡ **ប្រព័ន្ធស្កេនមេរោគ (Local):** ✅ សកម្ម (.apk, .exe, .scr, .bat, .sh, .jpg.apk)\n"
        f"🌐 **VirusTotal Cloud Scan:** {vt_status}\n"
        f"🔐 **Master License:** ✅ ទទួលបានអាជ្ញាប័ណ្ណផ្លូវការ\n"
        f"⏱️ **Auto-Delete Timer:** ✅ ៦០ វិនាទី\n"
        f"⚖️ **វិធានការលើអ្នកល្មើស:** លុបសារមេរោគ + {PUNISHMENT_MODE} {MUTE_DURATION_HOURS} ម៉ោង\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល ៦០ វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text=text, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin គ្រប់រូប (ទោះក្រុមមិនទាន់ទិញសិទ្ធិក៏ដោយ) អាចមើលឃើញលេខ Group ID ដើម្បីយកទៅទិញសិទ្ធិបាន"""
    user = update.effective_user
    chat = update.effective_chat
    is_master = is_super_admin(user.id)

    # សមាជិកធម្មតាមិនអាចឆែកបានទេ
    if not is_master and not await is_authorized_group_admin(update, context):
        if chat.type in ["group", "supergroup"]:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
            await send_auto_delete_message(context, chat.id, "⛔ សមាជិកទូទៅមិនមានសិទ្ធិឆែកព័ត៌មាននេះឡើយ!", delay=5)
        return

    admin_tag = "👑 **(Master Super Admin)**" if is_master else "🛡️ (Group Admin)"
    is_auth = is_group_authorized(chat.id)
    license_status = "🟢 បានបើកសិទ្ធិការពាររួចរាល់" if is_auth else "🔴 មិនទាន់ទិញអាជ្ញាប័ណ្ណ (Inactive)"

    text = (
        f"🆔 **ព័ត៌មានអត្តសញ្ញាណ និង GROUP ID:**\n\n"
        f"👥 **ឈ្មោះ Group / Chat:** `{chat.title or user.full_name}`\n"
        f"💬 **លេខ Group ID របស់អ្នក:** `{chat.id}`\n"
        f"👤 **Admin ឈ្មោះ:** {user.full_name} {admin_tag}\n"
        f"🔐 **ស្ថានភាពសេវាកម្ម:** {license_status}\n\n"
        f"💡 *(សូមយកលេខ Group ID `{chat.id}` នេះ ផ្ញើទៅកាន់ Master Admin ដើម្បីទិញសិទ្ធិប្រើប្រាស់)*\n\n"
        f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង ៦០ វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        await send_auto_delete_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text=text, reply_markup=get_bottom_menu_keyboard(is_master=is_master), parse_mode=ParseMode.MARKDOWN)


async def protect_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ["group", "supergroup"]:
        if not is_super_admin(user.id) and not await is_authorized_group_admin(update, context):
            return
        chat_key = str(chat.id)
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {"title": chat.title, "is_authorized": True, "is_enabled": True}
        else:
            GROUPS_CONFIG[chat_key]["is_authorized"] = True
            GROUPS_CONFIG[chat_key]["is_enabled"] = True
        save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        await send_auto_delete_message(context, chat.id, "🟢 **ប្រព័ន្ធការពារ Malware Shield ត្រូវបានបើកដំណើរការ (ON) ក្នុង Group នេះ!**", delay=15, parse_mode=ParseMode.MARKDOWN)


async def protect_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ["group", "supergroup"]:
        if not is_super_admin(user.id) and not await is_authorized_group_admin(update, context):
            return
        chat_key = str(chat.id)
        if chat_key in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key]["is_enabled"] = False
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
        await send_auto_delete_message(context, chat.id, "🔴 **ប្រព័ន្ធការពារ Malware Shield ត្រូវបានបិទដំណើរការ (OFF) ជាបណ្ដោះអាសន្ន!**", delay=15, parse_mode=ParseMode.MARKDOWN)


# ==================== MASTER SUPER ADMIN: GROUPS REGISTRY & LOGS ====================

async def list_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_super_admin(user.id):
        return

    if not GROUPS_CONFIG:
        await update.message.reply_text("📋 មិនទាន់មាន Group ណាត្រូវបានកត់ត្រាក្នុងប្រព័ន្ធនៅឡើយទេ។")
        return

    report = "📋 **[បញ្ជីឈ្មោះក្រុម លេខ ID & សេវាកម្មអនុញ្ញាតដោយ MASTER ADMIN]** 📋\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for idx, (cid, gdata) in enumerate(GROUPS_CONFIG.items(), start=1):
        title = gdata.get("title", f"Group {cid}")
        is_auth = gdata.get("is_authorized", False)
        is_en = gdata.get("is_enabled", False)

        if is_auth and is_en:
            status = "🟢 ACTIVE (បានទិញសិទ្ធិ & កំពុងការពារ)"
        elif is_auth and not is_en:
            status = "🟡 PAUSED (បានទិញសិទ្ធិ តែបិទការពារ)"
        else:
            status = "🔴 UNAUTHORIZED (មិនទាន់ទិញសិទ្ធិ - លោតសារ ២ ដង/ថ្ងៃ)"

        threats = gdata.get("threats_blocked_count", 0)
        added_at = gdata.get("added_at", "N/A")

        report += f"**{idx}. {title}**\n"
        report += f"   • 🆔 **Group ID:** `{cid}`\n"
        report += f"   • 🔰 **ស្ថានភាពសិទ្ធិ:** {status}\n"
        report += f"   • ☣️ **មេរោគដែលបានទប់ស្កាត់:** `{threats}` ករណី\n"
        report += f"   • 📅 **កាលបរិច្ឆេទ Add ចូល:** `{added_at}`\n"
        report += "   • 📦 **កញ្ចប់សេវាកម្ម:** Malware Shield, Anti-Flood, Strict Lock, 60s Clean\n"
        report += "────────────────────\n"

    await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_super_admin(user.id):
        return

    if not AUDIT_LOGS:
        await update.message.reply_text("📜 មិនទាន់មានកំណត់ត្រាប្រវត្តិហេតុការណ៍នៅឡើយទេ។")
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

    await update.message.reply_text(logs_text, parse_mode=ParseMode.MARKDOWN)


# ==================== MASTER SUPER ADMIN DASHBOARD ====================

def generate_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    if not GROUPS_CONFIG:
        keyboard.append([InlineKeyboardButton("❌ មិនទាន់មាន Group ណាភ្ជាប់នៅឡើយទេ", callback_data="none")])
    else:
        for chat_id, data in GROUPS_CONFIG.items():
            title = data.get("title", f"Group {chat_id}")
            is_auth = data.get("is_authorized", False)
            is_en = data.get("is_enabled", False)

            if is_auth and is_en:
                status_emoji = "🟢 [បើក-ON]"
            elif is_auth and not is_en:
                status_emoji = "🟡 [ផ្អាក-PAUSE]"
            else:
                status_emoji = "🔴 [មិនទាន់ទិញសិទ្ធិ]"

            btn_text = f"{status_emoji} {title[:18]}"
            callback_data = f"toggle_{chat_id}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("🔄 Refresh បញ្ជី Group", callback_data="refresh_groups")])
    return InlineKeyboardMarkup(keyboard)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_super_admin(user.id):
        await update.message.reply_text(
            f"⛔ **សុំទោស! មានតែ Master Super Admin ប៉ុណ្ណោះដែលអាចបើក Dashboard នេះបាន។**\n(Telegram ID របស់អ្នក: `{user.id}`)",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    text = (
        "⚙️ **[ផ្ទាំងគ្រប់គ្រង MASTER BOT DASHBOARD]** ⚙️\n\n"
        "👑 **សូមស្វាគមន៍ Master Super Admin (ID: 240224709)**\n\n"
        "គ្រប់គ្រងផ្ដល់សិទ្ធិអាជ្ញាប័ណ្ណ និងបើក/បិទប្រព័ន្ធការពារតាម Group នីមួយៗ៖\n"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=generate_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )


async def admin_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if not is_super_admin(user.id):
        await query.message.reply_text("⛔ អ្នកមិនមានសិទ្ធិប្រើប្រាស់ប៊ូតុងនេះទេ!")
        return

    data = query.data

    if data == "refresh_groups":
        await query.edit_message_reply_markup(reply_markup=generate_admin_keyboard())
        return

    # ការ Approve តាម Inline Button ពេលមាន Group ថ្មី Add ចូល
    if data.startswith("approve_"):
        chat_id = data.replace("approve_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = True
            GROUPS_CONFIG[chat_id]["is_enabled"] = True
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

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
                "✅ ប្រព័ន្ធ Anti-Flood & Clean Group 60s"
            )
            await send_auto_delete_message(context, int(chat_id), success_msg, delay=BOT_MSG_DELETE_SECONDS, parse_mode=ParseMode.MARKDOWN)
        return

    # ពេលចុចបដិសេធ ➡️ Bot នៅតែក្នុង Group ដដែល គ្រាន់តែមិនទាន់ការពារ និងលោតសារដាស់តឿនឱ្យទិញសិទ្ធិ ២ ដង/ថ្ងៃ
    if data.startswith("reject_"):
        chat_id = data.replace("reject_", "")
        if chat_id in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_id]["is_authorized"] = False
            GROUPS_CONFIG[chat_id]["is_enabled"] = False
            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)

            group_title = GROUPS_CONFIG[chat_id].get("title", chat_id)
            await query.edit_message_text(
                f"🔴 **[បានកំណត់ជាមិនទាន់ទិញសិទ្ធិ]**\n\n"
                f"👥 ក្រុម៖ **{group_title}** (`{chat_id}`)\n"
                f"⚠️ ស្ថានភាព៖ **មិនទាន់ដំណើរការការពារទេ (Bot នឹងលោតសារដាស់តឿនឱ្យទិញសិទ្ធិ ២ ដងក្នុង ១ ថ្ងៃ)**",
                parse_mode=ParseMode.MARKDOWN
            )
        return

    # Toggle ក្នុង Dashboard
    if data.startswith("toggle_"):
        chat_id = data.replace("toggle_", "")
        if chat_id in GROUPS_CONFIG:
            current_auth = GROUPS_CONFIG[chat_id].get("is_authorized", False)
            current_en = GROUPS_CONFIG[chat_id].get("is_enabled", False)

            if not current_auth:
                GROUPS_CONFIG[chat_id]["is_authorized"] = True
                GROUPS_CONFIG[chat_id]["is_enabled"] = True
            elif current_auth and current_en:
                GROUPS_CONFIG[chat_id]["is_enabled"] = False
            else:
                GROUPS_CONFIG[chat_id]["is_enabled"] = True

            save_json_file(GROUPS_CONFIG_FILE, GROUPS_CONFIG)
            await query.edit_message_reply_markup(reply_markup=generate_admin_keyboard())


# ==================== MAIN EXECUTION ====================

async def post_init(application):
    """ចាប់ផ្ដើម Background Task ផ្ញើសារដាស់តឿន ២ ដងក្នុង ១ ថ្ងៃ"""
    asyncio.create_task(daily_reminder_loop(application))


def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    print("[*] Commercial Security Bot starting with Master Super Admin (240224709)...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("check", status_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("groups", list_groups_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("protect_on", protect_on_command))
    app.add_handler(CommandHandler("protect_off", protect_off_command))

    # Master Admin Inline Callback
    app.add_handler(CallbackQueryHandler(admin_button_callback))

    # Catch when Bot is added to new groups
    app.add_handler(ChatMemberHandler(handle_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))

    # 🧹 Auto-Delete Service messages
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, handle_service_messages))

    # File Monitor
    app.add_handler(MessageHandler(filters.Document.ALL, handle_incoming_file))

    # Regular Messages & Anti-Flood Monitor
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_messages))
    app.add_handler(MessageHandler(filters.Sticker.ALL | filters.ANIMATION, handle_regular_messages))

    # Bottom Menu Keyboard Button Filter
    app.add_handler(MessageHandler(filters.Regex(r"^(🛡️ ឆែកស្ថានភាព Bot|🆔 មើលលេខ ID Group|⚙️ ផ្ទាំងគ្រប់គ្រង Admin Panel|📋 បញ្ជីឈ្មោះក្រុម & សេវាកម្ម|📜 ប្រវត្តិការពារ \(Logs\))$"), handle_regular_messages))

    print("[OK] Commercial Security Bot is fully active!")
    app.run_polling()


if __name__ == "__main__":
    main()
