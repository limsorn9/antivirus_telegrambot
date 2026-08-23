# 🛡️ Telegram Group Malware & Security Guard Bot (Admin Dashboard Edition)

Bot ការពារ Group Telegram ពីមេរោគ និង Trojan (Banking Trojan .apk, .jpg.apk, .exe, .scr, .bat, .sh) និងស្កេន VirusTotal SHA-256 ជាមួយប្រព័ន្ធគ្រប់គ្រងបិទ/បើកតាម Group ដោយមេ Admin!

---

## 👑 មុខងារគ្រប់គ្រងសម្រាប់ Admin (Admin Features)
- **`/admin`** : បើកផ្ទាំង Dashboard ចុចប៊ូតុង **🟢 [បើក-ON]** ឬ **🔴 [បិទ-OFF]** ប្រព័ន្ធការពារសម្រាប់ Group នីមួយៗបានយ៉ាងងាយស្រួល។
- **`/myid`** : បញ្ជាឆែកមើលលេខ **Telegram User ID** ផ្ទាល់ខ្លួន ដើម្បីយកទៅដាក់ក្នុង `.env`។
- **`/protect_on`** : បញ្ជាបើកការពារផ្ទាល់ក្នុង Group។
- **`/protect_off`** : បញ្ជាបិទការពារផ្ទាល់ក្នុង Group។
- **រក្សាទុកទិន្នន័យ (Auto-Save)** : រាល់ Group និងស្ថានភាព ON/OFF ត្រូវបាន Save ទុកក្នុងឯកសារ `groups_config.json` ដោយស្វ័យប្រវត្តិ។

---

## 🚀 របៀបតម្លើង និងដំណើរការ (Quick Setup)

### ១. ដំឡើង Python Dependencies
```bash
pip install -r requirements.txt
```

### ២. កំណត់ Configuration (`.env`)
បង្កើត File `.env` ដោយ Copy ចេញពី `.env.example`៖
```env
TELEGRAM_BOT_TOKEN=TOKEN_យកពី_BotFather
VIRUSTOTAL_API_KEY=API_KEY_យកពី_VirusTotal
SUPER_ADMIN_ID=Telegram_User_ID_របស់អ្នក_យកពី_myid
PUNISHMENT_MODE=MUTE
MUTE_DURATION_HOURS=24
```

### ៣. ដំណើរការ Bot
- **Windows:** ចុច Double-Click លើ File **`run_bot.bat`**
- **Terminal:** វាយពាក្យ `python telegram_security_bot.py`

### ៤. កំណត់សិទ្ធិក្នុង Telegram Group
- Add Bot ចូលទៅក្នុង Group
- Promote Bot ទៅជា **Admin** ដោយបើកសិទ្ធិ៖
  - ✅ **Delete Messages** (លុបសារ)
  - ✅ **Ban / Restrict Users** (បិទសិទ្ធិ ឬទាត់អ្នកផ្ញើមេរោគចេញ)
