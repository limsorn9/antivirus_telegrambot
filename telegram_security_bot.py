"""
=============================================================================
🛡️ TELEGRAM GROUP MALWARE & THREAT GUARD BOT (PRO CLEAN & MASTER ADMIN)
=============================================================================
Author: Cybersecurity & Telegram Defense Bot
Super Admin: 240224709 (Full Master Permissions Everywhere)
Features:
- Master Super Admin (ID: 240224709) មានសិទ្ធិពេញលេញ ១០០% គ្រប់ទីកន្លែង
- Work-Friendly Link Policy (អនុញ្ញាតឱ្យផ្ញើ Link ការងារបានធម្មតា ១០០%)
- 🧹 Auto-Delete Service Messages (លុបសារ "User joined/left" ស្វ័យប្រវត្តិ)
- ⏱️ Self-Destructing Bot Messages (សារ Bot លុបបាត់ទៅវិញក្នុង ៦០ វិនាទី)
- 🌊 Smart Anti-Flood & Spam Shield (ទប់ស្កាត់ការបាចសារ/Sticker ញាប់ពេក)
- 👑 Group Admin & Master Super Admin Authorization
- ⌨️ Bottom Reply Keyboard (ប៊ូតុងជាប់ខាងក្រោមកន្លែងសរសេរ)
- 🚨 Instant Blacklist Deletion (.apk, .exe, .scr, .bat, .sh, .jpg.apk, etc.)
- 🌐 VirusTotal Cloud SHA-256 Hash Scanner
=============================================================================
"""

import os
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

CONFIG_FILE = "groups_config.json"

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("MalwareGuardBot")

# In-Memory Trackers
SCAN_CACHE = {}
FLOOD_TRACKER = {}


# ==================== CONFIG & STORAGE ====================

def load_groups_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {CONFIG_FILE}: {e}")
    return {}

def save_groups_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {CONFIG_FILE}: {e}")

GROUPS_CONFIG = load_groups_config()


def is_super_admin(user_id: int) -> bool:
    """ពិនិត្យមើលថាតើជា Master Super Admin ឬទេ (ID: 240224709)"""
    return str(user_id) in SUPER_ADMIN_IDS


async def is_authorized_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    ពិនិត្យសិទ្ធិ៖ Super Admin (240224709) មានសិទ្ធិពេញលេញ ១០០% គ្រប់ទីកន្លែង
    """
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return False

    # 1. Master Super Admin មានសិទ្ធិគ្រប់កន្លែងទាំងអស់
    if is_super_admin(user.id):
        return True

    # 2. បើនៅក្នុង Chat ផ្ទាល់ខ្លួន (Private Chat)
    if chat.type == "private":
        return True

    # 3. បើនៅក្នុង Group ឆែកមើលថាតើគាត់ជា Admin នៃ Group នោះឬទេ
    try:
        member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


def is_group_shield_active(chat_id: int) -> bool:
    chat_key = str(chat_id)
    if chat_key in GROUPS_CONFIG:
        return GROUPS_CONFIG[chat_key].get("is_enabled", True)
    return True


# ==================== HELPER: AUTO-DELETE BOT MESSAGES ====================

async def delete_message_after_delay(bot, chat_id: int, message_id: int, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def send_temp_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = BOT_MSG_DELETE_SECONDS, **kwargs):
    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        asyncio.create_task(delete_message_after_delay(context.bot, chat_id, msg.message_id, delay))
        return msg
    except Exception as e:
        logger.error(f"Error sending temp message: {e}")
        return None


# ==================== BOTTOM KEYBOARD ====================

def get_bottom_menu_keyboard() -> ReplyKeyboardMarkup:
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
    # Super Admin can NEVER be punished
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

    # Super Admin and Group Admins are completely immune to anti-flood
    if is_super_admin(user.id) or await is_authorized_admin(update, context):
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
        warning_text = (
            f"⚠️ **[ប្រព័ន្ធទប់ស្កាត់ SPAM / ANTI-FLOOD]** ⚠️\n\n"
            f"👤 **អ្នកប្រើប្រាស់:** {user.mention_markdown_v2() if user.username else user.full_name}\n"
            f"🚫 **មូលហេតុ:** ផ្ញើសារ/Sticker ញាប់ពេក (លើសពី {FLOOD_MAX_MSGS} សារក្នុង {FLOOD_WINDOW_SECONDS} វិនាទី)\n"
            f"⚡ **ចំណាត់ការ:** {action_msg}\n\n"
            f"*(សារព្រមាននេះនឹងរលាយបាត់ទៅវិញស្វ័យប្រវត្តិក្នង 15 វិនាទី)*"
        )
        await send_temp_message(context, chat.id, warning_text, delay=15, parse_mode=ParseMode.MARKDOWN)
        return True

    return False


# ==================== FILE & MALWARE SCANNER ====================

async def handle_incoming_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.document:
        return

    if await handle_anti_flood(update, context):
        return

    chat = update.effective_chat
    sender = message.from_user
    chat_key = str(chat.id)

    if chat.type in ["group", "supergroup"]:
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {
                "title": chat.title or "Unknown Group",
                "is_enabled": True,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_groups_config(GROUPS_CONFIG)
        else:
            if GROUPS_CONFIG[chat_key].get("title") != chat.title:
                GROUPS_CONFIG[chat_key]["title"] = chat.title or "Unknown Group"
                save_groups_config(GROUPS_CONFIG)

    if not is_group_shield_active(chat.id):
        return

    file_name = message.document.file_name or "unnamed_file"
    file_size = message.document.file_size or 0

    analysis = analyze_filename(file_name)

    # ករណីទី ១៖ រកឃើញ File គ្រោះថ្នាក់ភ្លាមៗ
    if analysis.get("is_dangerous"):
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Cannot delete message: {e}")

        action_taken = await punish_user(chat.id, sender.id, context)

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
            f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល {BOT_MSG_DELETE_SECONDS} វិនាទី)*"
        )

        await send_temp_message(
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

                warning_text = (
                    f"☣️ **[រកឃើញមេរោគក្នុង Archive ដោយ VirusTotal]** ☣️\n\n"
                    f"👤 **អ្នកផ្ញើ:** {sender.full_name} (`ID: {sender.id}`)\n"
                    f"📁 **ឈ្មោះហ្វាល់:** `{file_name}`\n"
                    f"🔬 **ពិន្ទុគ្រោះថ្នាក់:** {vt_result['malicious_count']} Security Engines ចាត់ទុកជាមេរោគ!\n"
                    f"🧬 **SHA-256:** `{vt_result['sha256']}`\n"
                    f"⚡ **ចំណាត់ការ:** សារត្រូវបានលុប | {action_taken}\n\n"
                    f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល {BOT_MSG_DELETE_SECONDS} វិនាទី)*"
                )
                await send_temp_message(
                    context,
                    chat_id=chat.id,
                    text=warning_text,
                    delay=BOT_MSG_DELETE_SECONDS,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Error inspecting archive: {e}")


# ==================== TEXT MESSAGE & FLOOD MONITOR ====================

async def handle_regular_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ត្រួតពិនិត្យសារអក្សរធម្មតា និងប៊ូតុងចុច"""
    if await handle_anti_flood(update, context):
        return

    text = update.message.text.strip() if update.message and update.message.text else ""

    if text in ["🛡️ ឆែកស្ថានភាព Bot", "/status", "/check"]:
        await status_command(update, context)
    elif text in ["🆔 មើលលេខ ID Group", "/myid", "/id"]:
        await myid_command(update, context)


# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role_tag = "👑 **(Master Super Admin)**" if is_super_admin(user.id) else "🛡️ (Group Member/Admin)"

    text = (
        f"🤖 **សួស្តី {user.first_name}! {role_tag}**\n\n"
        "ខ្ញុំជា Bot ការពារមេរោគ និងគ្រប់គ្រងសុវត្ថិភាព Group Telegram!\n\n"
        "🛡️ **មុខងារការពារ និងគ្រប់គ្រង៖**\n"
        "✅ ស្កេន និងលុប `.apk`, `.exe`, `.scr`, `.bat`, `.sh` ដោយស្វ័យប្រវត្តិ\n"
        "✅ ចាប់ហ្វាល់បន្លំកន្ទុយពីរ (Double Extension ដូចជា `.jpg.apk`, `.pdf.apk`)\n"
        "✅ ឆែកស្កេន Cloud Hash លើ VirusTotal សម្រាប់ហ្វាល់ `.zip` និង `.rar`\n"
        "✅ 🧹 លុបសារ System Service Messages (Join/Leave)\n"
        "✅ 🌊 ប្រព័ន្ធ Anti-Flood ទប់ស្កាត់ការបាច Spam\n"
        "✅ ⏱️ សារ Bot នឹងលុបបាត់ទៅវិញស្វ័យប្រវត្តិក្នង ៦០ វិនាទី\n\n"
        "⚙️ **ពាក្យបញ្ជាសម្រាប់ Admin៖**\n"
        "👉 `/admin` : ផ្ទាំងគ្រប់គ្រង Dashboard បើក/បិទ Bot តាម Group\n"
        "👉 `/status` : ឆែកស្ថានភាពប្រព័ន្ធការពារ\n"
        "👉 `/myid` : មើលលេខ ID ផ្ទាល់ខ្លួន"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=get_bottom_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Master Super Admin 240224709 always has access
    if not is_super_admin(user.id) and not await is_authorized_admin(update, context):
        msg = await update.message.reply_text(
            f"⛔ **សុំទោស {user.first_name}!**\nមានតែ **Admin នៃក្រុមនេះ** ប៉ុណ្ណោះ ទើបមានសិទ្ធិបញ្ជា និងឆែកស្ថានភាព Bot បាន។",
            parse_mode=ParseMode.MARKDOWN
        )
        if chat.type in ["group", "supergroup"]:
            asyncio.create_task(delete_message_after_delay(context.bot, chat.id, msg.message_id, 10))
        return

    chat_key = str(chat.id)
    if chat.type in ["group", "supergroup"]:
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {
                "title": chat.title or "Unknown Group",
                "is_enabled": True,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_groups_config(GROUPS_CONFIG)

    is_active = is_group_shield_active(chat.id)
    shield_status_str = "🟢 **កំពុងការពារយ៉ាងសកម្ម (SHIELD ON)**" if is_active else "🔴 **ត្រូវបានបិទបណ្ដោះអាសន្ន (SHIELD OFF)**"
    vt_status = "✅ **ភ្ជាប់រួចរាល់ (Connected)**" if VIRUSTOTAL_API_KEY and VIRUSTOTAL_API_KEY != "YOUR_VIRUSTOTAL_API_KEY_HERE" else "⚠️ **Local Shield Only**"

    group_name = chat.title if chat.type in ["group", "supergroup"] else "Chat ផ្ទាល់ខ្លួន (Private Chat)"
    chat_type_kh = "ក្រុម Telegram (Group)" if chat.type in ["group", "supergroup"] else "ផ្ទាំងសារផ្ទាល់ខ្លួន (Private)"
    admin_status = "👑 Master Super Admin" if is_super_admin(user.id) else "🛡️ Group Admin"

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
        f"🧹 **Auto-Clean Service Msgs:** ✅ បើកដំណើរការ\n"
        f"🌊 **Anti-Flood Shield:** ✅ បើកដំណើរការ\n"
        f"⚖️ **វិធានការលើអ្នកល្មើស:** លុបសារមេរោគ + {PUNISHMENT_MODE} {MUTE_DURATION_HOURS} ម៉ោង\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *(សារនេះនឹងរលាយបាត់ទៅវិញក្នុងរយៈពេល {BOT_MSG_DELETE_SECONDS} វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        await send_temp_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_bottom_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text=text, reply_markup=get_bottom_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not is_super_admin(user.id) and not await is_authorized_admin(update, context):
        msg = await update.message.reply_text("⛔ មានតែ Admin នៃក្រុមនេះទេ ទើបអាចឆែកមើលព័ត៌មានបាន!")
        if chat.type in ["group", "supergroup"]:
            asyncio.create_task(delete_message_after_delay(context.bot, chat.id, msg.message_id, 10))
        return

    admin_tag = "👑 **(Master Super Admin)**" if is_super_admin(user.id) else "🛡️ (Group Admin)"

    text = (
        f"🆔 **ព័ត៌មានអត្តសញ្ញាណ និង GROUP ID:**\n\n"
        f"👥 **ឈ្មោះ Group / Chat:** `{chat.title or user.full_name}`\n"
        f"💬 **លេខ Group ID:** `{chat.id}`\n"
        f"👤 **Admin ឈ្មោះ:** {user.full_name} {admin_tag}\n"
        f"🔢 **លេខ User ID របស់អ្នក:** `{user.id}`\n\n"
        f"*(សារនេះនឹងរលាយបាត់ទៅវិញក្នុង {BOT_MSG_DELETE_SECONDS} វិនាទី)*"
    )

    if chat.type in ["group", "supergroup"]:
        await send_temp_message(context, chat.id, text, delay=BOT_MSG_DELETE_SECONDS, reply_markup=get_bottom_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text=text, reply_markup=get_bottom_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)


async def protect_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ["group", "supergroup"]:
        if not is_super_admin(user.id) and not await is_authorized_admin(update, context):
            return
        chat_key = str(chat.id)
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {"title": chat.title, "is_enabled": True}
        else:
            GROUPS_CONFIG[chat_key]["is_enabled"] = True
        save_groups_config(GROUPS_CONFIG)
        await send_temp_message(context, chat.id, "🟢 **ប្រព័ន្ធការពារ Malware Shield ត្រូវបានបើកដំណើរការ (ON) ក្នុង Group នេះ!**", delay=15, parse_mode=ParseMode.MARKDOWN)


async def protect_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ["group", "supergroup"]:
        if not is_super_admin(user.id) and not await is_authorized_admin(update, context):
            return
        chat_key = str(chat.id)
        if chat_key not in GROUPS_CONFIG:
            GROUPS_CONFIG[chat_key] = {"title": chat.title, "is_enabled": False}
        else:
            GROUPS_CONFIG[chat_key]["is_enabled"] = False
        save_groups_config(GROUPS_CONFIG)
        await send_temp_message(context, chat.id, "🔴 **ប្រព័ន្ធការពារ Malware Shield ត្រូវបានបិទដំណើរការ (OFF) ជាបណ្ដោះអាសន្ន!**", delay=15, parse_mode=ParseMode.MARKDOWN)


# ==================== MASTER SUPER ADMIN PANEL ====================

def generate_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    if not GROUPS_CONFIG:
        keyboard.append([InlineKeyboardButton("❌ មិនទាន់មាន Group ណាភ្ជាប់នៅឡើយទេ", callback_data="none")])
    else:
        for chat_id, data in GROUPS_CONFIG.items():
            title = data.get("title", f"Group {chat_id}")
            is_enabled = data.get("is_enabled", True)
            status_emoji = "🟢 [បើក-ON]" if is_enabled else "🔴 [បិទ-OFF]"
            btn_text = f"{status_emoji} {title[:20]}"
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
        "គ្រប់គ្រងបើក/បិទប្រព័ន្ធការពារតាម Group នីមួយៗ៖\n"
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

    if data.startswith("toggle_"):
        chat_id = data.replace("toggle_", "")
        if chat_id in GROUPS_CONFIG:
            current_status = GROUPS_CONFIG[chat_id].get("is_enabled", True)
            new_status = not current_status
            GROUPS_CONFIG[chat_id]["is_enabled"] = new_status
            save_groups_config(GROUPS_CONFIG)

            logger.info(f"Master Admin {user.id} toggled {chat_id} to {new_status}")
            await query.edit_message_reply_markup(reply_markup=generate_admin_keyboard())


# ==================== MAIN EXECUTION ====================

def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Error: សូមកំណត់ TELEGRAM_BOT_TOKEN ក្នុងឯកសារ .env ជាមុនសិន!")
        return

    print("🛡️ Security Bot is starting with Master Super Admin (240224709)...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("check", status_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("protect_on", protect_on_command))
    app.add_handler(CommandHandler("protect_off", protect_off_command))

    # Master Admin Callback
    app.add_handler(CallbackQueryHandler(admin_button_callback))

    # 🧹 Auto-Delete Service messages
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, handle_service_messages))

    # File Monitor
    app.add_handler(MessageHandler(filters.Document.ALL, handle_incoming_file))

    # Regular Messages & Anti-Flood Monitor
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_messages))
    app.add_handler(MessageHandler(filters.Sticker.ALL | filters.ANIMATION, handle_regular_messages))

    print("✅ Bot is fully active and Master Super Admin is recognized!")
    app.run_polling()


if __name__ == "__main__":
    main()
