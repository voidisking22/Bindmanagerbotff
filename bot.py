# ═══════════════════════════════════════════════════════════
#  VOID GARENA BIND MANAGER — single file, full
# ═══════════════════════════════════════════════════════════

import os, logging, urllib.parse, hashlib, base64, json
import requests, urllib3

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── config ────────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "https://t.me/kingvoidofficials")
FORCE_GROUP   = os.getenv("FORCE_GROUP",   "https://t.me/kingvoidofficialgc")
FORCE_WA      = os.getenv("FORCE_WA",      "https://whatsapp.com/channel/0029Vb8qn4YC1Fu8k2Ydy72P")
CHANNEL_ID    = os.getenv("CHANNEL_ID",    "@kingvoidofficials")
GROUP_ID      = os.getenv("GROUP_ID",      "@kingvoidofficialgc")
SUPPORT_1     = os.getenv("SUPPORT_1",     "@voidisking")
SUPPORT_2     = os.getenv("SUPPORT_2",     "@lordofzone")
SUPPORT_WA_N  = os.getenv("SUPPORT_WA_N",  "+2349077561145")
BRAND         = "ᴛʜᴇ ᴠᴏɪᴅ ɢᴀʀᴇɴᴀ ʙɪɴᴅ ᴍᴀɴᴀɢᴇʀ"

PORT   = int(os.getenv("PORT", "8080"))
PUBLIC = os.getenv("RENDER_EXTERNAL_URL", "")
PATH   = "webhook"

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("vgbm")

# ── endpoints ─────────────────────────────────────────────
E_BIND_INFO    = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
E_SEND_OTP     = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
E_VERIFY_OTP   = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
E_CREATE_BIND  = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
E_VERIFY_ID    = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
E_REBIND       = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
E_UNBIND       = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
E_CANCEL       = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
E_PLATFORM     = "https://100067.connect.garena.com/bind/app/platform/info/get"
E_LOGOUT       = "https://100067.connect.garena.com/oauth/logout"
E_INSPECT      = "https://100067.connect.garena.com/oauth/token/inspect"
E_PLAYER_INFO  = "https://api-otrss.garena.com/support/callback/"
E_LOGIN_HIST   = "https://clientbp.ggblueshark.com/GetLoginHistory"
E_ACC_INFO     = "https://clientbp.ggblueshark.com/GetAccountInfoByAccountID"
E_STATS        = "https://clientbp.ggblueshark.com/GetPlayerStats"
E_BRANK        = "https://clientbp.ggblueshark.com/GetBRRankingInfo"
E_BANCHECK     = "https://clientbp.ggblueshark.com/CheckHackBehavior"
E_FUZZY        = "https://clientbp.ggblueshark.com/FuzzySearchAccountByName"
E_NICKNAME     = "https://loginbp.ggpolarbear.com/MajorModifyNickname"

RT = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line",
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok",
}

# ── helpers ───────────────────────────────────────────────
def esc(t):
    return str(t).replace("<", "&lt;").replace(">", "&gt;")

def secs(s):
    d, h = divmod(int(s), 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d}d {h}h {m}m {s}s"

async def is_member(bot, chat_id, user_id):
    try:
        m = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        ok = m.status in ("member", "administrator", "creator")
        log.info(f"[verify] chat={chat_id} user={user_id} status={m.status} ok={ok}")
        return ok
    except Exception as e:
        log.warning(f"[verify] chat={chat_id} user={user_id} ERR={e}")
        return False

def garena_headers():
    return {"User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"}

def player_info(token):
    r = requests.get(E_PLAYER_INFO, params={"access_token": token},
                     headers={"User-Agent": "Mozilla/5.0"},
                     allow_redirects=True, timeout=15)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
    return {
        "uid":      q.get("account_id", ["?"])[0],
        "nickname": urllib.parse.unquote(q.get("nickname", ["?"])[0]),
        "region":   q.get("region", ["?"])[0],
        "valid":    "access_token" in q,
    }

def inspect_token(token):
    try:
        r = requests.get(E_INSPECT, params={"token": token},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        return r
    except Exception:
        return {}

def bind_info(token):
    r = requests.get(E_BIND_INFO, params={"app_id": "100067", "access_token": token},
                     headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json() if r.status_code == 200 else None

def access_to_jwt(token):
    """Get a game JWT via MajorLogin using protobuf. Falls back gracefully."""
    try:
        oid = inspect_token(token).get("open_id")
        if not oid:
            return None
        # MajorLogin requires protobuf — if you don't have the .py files, bail
        try:
            import MajoRLogin_pb2 as mLpB
            import MajorLoginRes_pb2 as mLrPb
        except ImportError:
            return None
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad
        from datetime import datetime
        KEY, IV = b"Yg&tc%DEuh6%Zc^8", b"6oyZDr22E3ychjM%"
        m = mLpB.MajorLogin()
        m.event_time = str(datetime.now())[:-7]
        m.game_name = "free fire"
        m.platform_id = 8
        m.client_version = "1.120.1"
        m.system_software = "Android OS 9 / API-28"
        m.system_hardware = "Handheld"
        m.telecom_operator = "Verizon"
        m.network_type = "WIFI"
        m.screen_width = 1920; m.screen_height = 1080
        m.screen_dpi = "280"
        m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
        m.memory = 3003
        m.gpu_renderer = "Adreno (TM) 640"
        m.gpu_version = "OpenGL ES 3.1 v1.46"
        m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
        m.client_ip = "223.191.51.89"
        m.language = "en"
        m.open_id = oid
        m.open_id_type = "8"
        m.device_type = "Handheld"
        m.access_token = token
        m.platform_sdk_id = 1
        m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
        m.login_by = 3; m.channel_type = 3; m.cpu_type = 2
        m.cpu_architecture = "64"
        m.client_version_code = "2019118695"
        m.login_open_id_type = 8
        m.origin_platform_type = "8"; m.primary_platform_type = "8"
        payload = AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(m.SerializeToString(), 16))
        r = requests.post("https://loginbp.ggpolarbear.com/MajorLogin",
                          headers={"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11)",
                                   "Content-Type": "application/octet-stream",
                                   "X-GA": "v1 1", "ReleaseVersion": "OB52"},
                          data=payload, timeout=10, verify=False)
        if r.status_code != 200:
            return None
        try:
            res = mLrPb.MajorLoginRes()
            try: res.ParseFromString(unpad(AES.new(KEY, AES.MODE_CBC, IV).decrypt(r.content), 16))
            except Exception: res.ParseFromString(r.content)
            return res.token or None
        except Exception:
            return None
    except Exception as e:
        log.warning(f"access_to_jwt: {e}")
        return None

# ── verify screen ─────────────────────────────────────────
def join_inline_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ᴛɢ ᴄʜᴀɴɴᴇʟ", url=FORCE_CHANNEL)],
        [InlineKeyboardButton("💬 ᴛɢ ɢʀᴏᴜᴘ", url=FORCE_GROUP)],
        [InlineKeyboardButton("🟢 ᴡʜᴀᴛꜱᴀᴘᴘ ᴄʜᴀɴɴᴇʟ", url=FORCE_WA)],
        [InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ", callback_data="verify_join")],
    ])

def verify_text(u):
    return (
        f"🔐 <b>ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʀᴇǫᴜɪʀᴇᴅ</b>\n\n"
        f"👋 ʜɪ, <b>{esc(u.first_name)}</b>\n"
        f"😎 ᴜꜱᴇʀ : <b>{esc(u.first_name)}</b>\n"
        f"👑 ɪᴅ   : <code>{u.id}</code>\n\n"
        f"ᴛᴏ ᴜꜱᴇ <b>{BRAND}</b>, ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ & ɢʀᴏᴜᴘ.\n"
        f"ᴛʜᴇɴ ᴛᴀᴘ ✅ ᴠᴇʀɪꜰʏ.\n\n"
        f"📢 ᴛɢ ᴄʜᴀɴɴᴇʟ : {FORCE_CHANNEL}\n"
        f"💬 ᴛɢ ɢʀᴏᴜᴘ   : {FORCE_GROUP}\n"
        f"🟢 ᴡʜᴀᴛꜱᴀᴘᴘ     : {FORCE_WA}"
    )

async def require_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    u = update.effective_user
    in_channel = await is_member(ctx.bot, CHANNEL_ID, u.id)
    in_group   = await is_member(ctx.bot, GROUP_ID,   u.id)
    if in_channel and in_group:
        return True
    text = verify_text(u); kb = join_inline_kb()
    if update.callback_query:
        try: await update.callback_query.message.delete()
        except Exception: pass
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                   reply_markup=kb, parse_mode=ParseMode.HTML,
                                   disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, reply_markup=kb,
                                        parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=True)
    return False

# ── keyboard ──────────────────────────────────────────────
BTN_BIND_INFO   = "📊 Bind Info"
BTN_BIND_EMAIL  = "🔗 Bind Email"
BTN_UNBIND      = "🔓 Unbind Email"
BTN_CHANGE      = "🔄 Change Email"
BTN_CANCEL      = "⚠️ Cancel Bind"
BTN_EAT         = "🎁 EAT to Token"
BTN_REVOKE      = "🚫 Revoke Token"
BTN_UNSUB       = "📧 Single Unsub OTP"
BTN_BIO         = "✨ Update Bio"
BTN_PLATFORM    = "🕹 Platform Binds"
BTN_HISTORY     = "📜 Login History"
BTN_JWT         = "🔑 Token → JWT"
BTN_SECCODE     = "🔐 Get Security Code"
BTN_STATS       = "📈 Player Stats"
BTN_OWNER       = "👑 Owner"
BTN_HOWTO       = "ℹ️ How to Use"

def reply_kb():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_BIND_INFO),  KeyboardButton(BTN_BIND_EMAIL)],
            [KeyboardButton(BTN_UNBIND),     KeyboardButton(BTN_CHANGE)],
            [KeyboardButton(BTN_CANCEL),     KeyboardButton(BTN_EAT)],
            [KeyboardButton(BTN_REVOKE),     KeyboardButton(BTN_UNSUB)],
            [KeyboardButton(BTN_BIO),        KeyboardButton(BTN_PLATFORM)],
            [KeyboardButton(BTN_HISTORY),    KeyboardButton(BTN_JWT)],
            [KeyboardButton(BTN_SECCODE),    KeyboardButton(BTN_STATS)],
            [KeyboardButton(BTN_OWNER),      KeyboardButton(BTN_HOWTO)],
        ],
        resize_keyboard=True, is_persistent=True,
        input_field_placeholder="ᴘɪᴄᴋ ᴀɴ ᴏᴘᴛɪᴏɴ...",
    )

MENU_ACTIONS = {
    BTN_BIND_INFO:  ("check",    "ꜱᴇɴᴅ ʏᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_BIND_EMAIL: ("bind",     "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_UNBIND:     ("unbind",   "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_CHANGE:     ("change",   "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_CANCEL:     ("cancel",   "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_EAT:        ("eat",      "ᴘᴀꜱᴛᴇ ᴇᴀᴛ ᴛᴏᴋᴇɴ ᴏʀ ᴇᴀᴛ ᴜʀʟ"),
    BTN_REVOKE:     ("revoke",   "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_UNSUB:      ("unsub",    "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_BIO:        ("bio",      "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_PLATFORM:   ("platform", "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_HISTORY:    ("history",  "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_JWT:        ("jwt",      "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_SECCODE:    ("seccode",  "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    BTN_STATS:      ("stats",    "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
}

DEV_LINES = [
    "🚧 <b>ᴜɴᴅᴇʀ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ</b>\nᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴄᴏᴏᴋɪɴɢ ɪɴ ᴛʜᴇ ʟᴀʙ 🔬",
    "🛠 <b>ᴄᴏᴍɪɴɢ ꜱᴏᴏɴ</b>\nᴛʜᴇ ᴠᴏɪᴅ ɪꜱ ꜱᴛɪʟʟ ʙᴜɪʟᴅɪɴɢ ᴛʜɪꜱ ᴏɴᴇ.",
    "⚙️ <b>ᴡᴏʀᴋ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ</b>\nɴᴏᴛ ʟɪᴠᴇ ʏᴇᴛ — ꜱᴏᴏɴ™",
    "🔒 <b>ʟᴏᴄᴋᴇᴅ ꜰᴇᴀᴛᴜʀᴇ</b>\nᴛʜɪꜱ ᴏɴᴇ ᴅʀᴏᴘꜱ ɪɴ ᴛʜᴇ ɴᴇxᴛ ᴜᴘᴅᴀᴛᴇ.",
    "🧪 <b>ᴛᴇꜱᴛɪɴɢ ᴘʜᴀꜱᴇ</b>\nʙᴇᴛᴀ ɪꜱ ɪɴᴛᴇʀɴᴀʟ ᴏɴʟʏ ʀɴ.",
]

def dev_msg(key):
    idx = sum(ord(c) for c in key) % len(DEV_LINES)
    return DEV_LINES[idx].format(s1=SUPPORT_1, s2=SUPPORT_2)

HOWTO_TEXT = (
    "ℹ️ <b>ʜᴏᴡ ᴛᴏ ᴜꜱᴇ</b>\n\n"
    "1️⃣ ᴛᴀᴘ ᴀɴʏ ᴍᴇɴᴜ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ\n"
    "2️⃣ ᴘᴀꜱᴛᴇ ʏᴏᴜʀ <b>ɢᴀʀᴇɴᴀ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ</b>\n"
    "3️⃣ ʙᴏᴛ ʀᴇᴛᴜʀɴꜱ ᴛʜᴇ ʀᴇꜱᴜʟᴛ\n\n"
    "🔐 <b>ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ</b> ɪꜱ ʏᴏᴜʀ 6-ᴅɪɢɪᴛ ʙɪɴᴅ ᴘᴀꜱꜱᴡᴏʀᴅ.\n"
    "ᴋᴇᴇᴘ ɪᴛ ꜱᴀꜰᴇ — ᴅᴏ ɴᴏᴛ ꜱʜᴀʀᴇ ᴡɪᴛʜ ᴀɴʏᴏɴᴇ.\n\n"
    "📱 ꜱᴜᴘᴘᴏʀᴛ :\n"
    f"• ᴛɢ : {SUPPORT_1}\n"
    f"• ᴛɢ : {SUPPORT_2}\n"
    f"• ᴡᴀ : {SUPPORT_WA_N}"
)

# ── /start ────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, ctx):
        return
    await show_menu(update, ctx)

async def show_menu(update, ctx, from_query=False):
    u = update.effective_user
    text = (
        f"👋 ʜɪ, <b>{esc(u.first_name)}</b>  ✨\n\n"
        f"😎 ᴜꜱᴇʀ : <b>{esc(u.first_name)}</b>\n"
        f"👑 ɪᴅ   : <code>{u.id}</code>\n\n"
        f"✨ <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {BRAND}</b> ✨\n\n"
        f"🚀 <b>ꜰᴇᴀᴛᴜʀᴇꜱ :</b>\n"
        f"• 📊 ᴄʜᴇᴄᴋ ʙɪɴᴅ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ\n"
        f"• 🔗 ʙɪɴᴅ ᴇᴍᴀɪʟ ᴛᴏ ᴀᴄᴄᴏᴜɴᴛ\n"
        f"• 🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"• 🔄 ᴄʜᴀɴɢᴇ ʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"• ⚠️ ᴄᴀɴᴄᴇʟ ʙɪɴᴅ ʀᴇǫᴜᴇꜱᴛ\n"
        f"• 🎁 ᴄᴏɴᴠᴇʀᴛ ᴇᴀᴛ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ\n"
        f"• 🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ\n"
        f"• 📧 ꜱᴇɴᴅ ꜱɪɴɢʟᴇ ᴜɴꜱᴜʙꜱᴄʀɪʙᴇ ᴏᴛᴘ\n"
        f"• 🔐 ɢᴇᴛ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ\n"
        f"• 📈 ᴘʟᴀʏᴇʀ ꜱᴛᴀᴛꜱ\n"
        f"• ✨ ᴜᴘᴅᴀᴛᴇ ʙɪᴏ ᴘʀᴏꜰɪʟᴇ\n\n"
        f"❤️ <b>ᴘʀᴇᴍɪᴜᴍ & ꜱᴇᴄᴜʀᴇ ᴛᴏᴏʟ</b>\n"
        f"📱 ᴛɢ ꜱᴜᴘᴘᴏʀᴛ : {SUPPORT_1} ᴏʀ {SUPPORT_2}\n"
        f"🟢 ᴡʜᴀᴛꜱᴀᴘᴘ     : {SUPPORT_WA_N}\n\n"
        f"👇 ᴜꜱᴇ ᴛʜᴇ ᴋᴇʏʙᴏᴀʀᴅ ʙᴇʟᴏᴡ ᴛᴏ ꜱᴛᴀʀᴛ"
    )
    kb = reply_kb()
    if from_query:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                   reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

async def cb_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; u = q.from_user
    in_channel = await is_member(ctx.bot, CHANNEL_ID, u.id)
    in_group   = await is_member(ctx.bot, GROUP_ID,   u.id)
    if in_channel and in_group:
        await q.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ!", show_alert=False)
        try: await q.message.delete()
        except Exception: pass
        await show_menu(update, ctx, from_query=True)
    else:
        await q.answer("❌ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ꜰɪʀꜱᴛ!", show_alert=True)

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending"] = None
    await update.message.reply_text("✅ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=reply_kb())

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await require_join(update, ctx): return
    await update.message.reply_text(HOWTO_TEXT, reply_markup=reply_kb(),
                                    parse_mode=ParseMode.HTML)

# ── flows that need multi-step state ──────────────────────
# state stored in ctx.user_data: {"flow": "...", "step": N, "data": {...}}

async def start_bind_flow(update, ctx, token):
    """Bind new email: token → email → OTP → verify → sec code → create bind."""
    info = player_info(token)
    if not info["valid"]:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
    ctx.user_data["flow"] = "bind"
    ctx.user_data["flow_step"] = "email"
    ctx.user_data["flow_data"] = {"token": token}
    await update.message.reply_text(
        f"🔗 <b>ʙɪɴᴅ ᴇᴍᴀɪʟ</b>\n\n"
        f"🎮 {esc(info['nickname'])}\n🆔 <code>{esc(info['uid'])}</code>\n\n"
        f"📩 ꜱᴇɴᴅ ᴛʜᴇ <b>ᴇᴍᴀɪʟ</b> ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙɪɴᴅ\n<i>ᴄᴀɴᴄᴇʟ : /cancel</i>",
        reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

async def start_unbind_flow(update, ctx, token):
    """Unbind: token → method (otp/sec) → verify → create unbind."""
    info = player_info(token)
    if not info["valid"]:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
    b = bind_info(token) or {}
    email = b.get("email") or ""
    if not email:
        await update.message.reply_text(
            "⚠️ ɴᴏ ᴇᴍᴀɪʟ ʙᴏᴜɴᴅ ᴛᴏ ᴛʜɪꜱ ᴀᴄᴄᴏᴜɴᴛ.", reply_markup=reply_kb()); return
    ctx.user_data["flow"] = "unbind"
    ctx.user_data["flow_step"] = "method"
    ctx.user_data["flow_data"] = {"token": token, "email": email}
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 ᴠɪᴀ ᴏᴛᴘ", callback_data="unbind_otp")],
        [InlineKeyboardButton("🔐 ᴠɪᴀ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ", callback_data="unbind_sec")],
    ])
    await update.message.reply_text(
        f"🔓 <b>ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ</b>\n\nᴄᴜʀʀᴇɴᴛ : <code>{esc(email)}</code>\n\n"
        f"ᴄʜᴏᴏꜱᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴍᴇᴛʜᴏᴅ:",
        reply_markup=kb, parse_mode=ParseMode.HTML)

async def start_change_flow(update, ctx, token):
    """Change bind: token → method → verify old → new email → OTP → verify → rebind."""
    info = player_info(token)
    if not info["valid"]:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
    b = bind_info(token) or {}
    email = b.get("email") or ""
    if not email:
        await update.message.reply_text("⚠️ ɴᴏ ᴇᴍᴀɪʟ ʙᴏᴜɴᴅ.", reply_markup=reply_kb()); return
    ctx.user_data["flow"] = "change"
    ctx.user_data["flow_step"] = "method"
    ctx.user_data["flow_data"] = {"token": token, "old_email": email}
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 ᴠɪᴀ ᴏᴛᴘ", callback_data="change_otp")],
        [InlineKeyboardButton("🔐 ᴠɪᴀ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ", callback_data="change_sec")],
    ])
    await update.message.reply_text(
        f"🔄 <b>ᴄʜᴀɴɢᴇ ʙɪɴᴅ</b>\n\nᴄᴜʀʀᴇɴᴛ : <code>{esc(email)}</code>\n\n"
        f"ᴠᴇʀɪꜰʏ ʜᴏᴡ ʏᴏᴜ ᴏᴡɴ ᴛʜɪꜱ ᴀᴄᴄᴏᴜɴᴛ:",
        reply_markup=kb, parse_mode=ParseMode.HTML)

# ── input router ──────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not await require_join(update, ctx): return

    # multi-step flow handlers first
    flow = ctx.user_data.get("flow")
    if flow:
        try:
            await flow_dispatch(update, ctx, flow, text)
        except Exception as e:
            log.exception("flow fail")
            await update.message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{esc(e)}</code>",
                                            reply_markup=reply_kb(),
                                            parse_mode=ParseMode.HTML)
        return

    if text == BTN_OWNER:
        await update.message.reply_text(
            f"👑 <b>ᴏᴡɴᴇʀ ᴅᴇᴛᴀɪʟꜱ</b>\n\n"
            f"╭──────────────\n"
            f"│ ᴅᴇᴠ : ᴠᴏɪᴅ ɪꜱ ᴋɪɴɢ\n"
            f"│ ᴛɢ  : {SUPPORT_1}\n"
            f"│ ᴛɢ  : {SUPPORT_2}\n"
            f"│ ᴡᴀ  : {SUPPORT_WA_N}\n"
            f"╰──────────────\n\n"
            f"ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ <b>{BRAND}</b> 🤍",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML); return

    if text == BTN_HOWTO:
        await update.message.reply_text(HOWTO_TEXT, reply_markup=reply_kb(),
                                        parse_mode=ParseMode.HTML); return

    if text in MENU_ACTIONS:
        action, hint = MENU_ACTIONS[text]
        ctx.user_data["pending"] = action
        await update.message.reply_text(
            f"📩 {hint}\n\n<i>ᴄᴀɴᴄᴇʟ : /cancel</i>",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML); return

    action = ctx.user_data.get("pending")
    if not action: return
    ctx.user_data["pending"] = None
    token = text

    try:
        if action == "check":
            info = player_info(token)
            if not info["valid"]:
                await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
            b = bind_info(token) or {}
            await update.message.reply_text(
                f"📊 <b>ʙɪɴᴅ ɪɴꜰᴏ</b>\n\n"
                f"╭──────────────\n"
                f"│ 🎮 ɴɪᴄᴋ : {esc(info['nickname'])}\n"
                f"│ 🆔 ᴜɪᴅ  : <code>{esc(info['uid'])}</code>\n"
                f"│ 🌍 ʀɢɴ  : {esc(info['region'])}\n"
                f"│ 📧 ᴇᴍᴀɪʟ: {esc(b.get('email') or 'None')}\n"
                f"│ ⏳ ᴘᴇɴᴅ : {esc(b.get('email_to_be') or 'None')}\n"
                f"│ ⏱ ᴄᴅ   : {secs(b.get('request_exec_countdown', 0))}\n"
                f"╰──────────────",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "eat":
            eat = token
            if "http" in token or "?" in token:
                q = urllib.parse.parse_qs(urllib.parse.urlparse(token).query)
                eat = q.get("eat", [""])[0]
            if not eat:
                await update.message.reply_text("❌ ɴᴏ ᴇᴀᴛ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
            r = requests.get(E_PLAYER_INFO, params={"access_token": eat},
                             allow_redirects=True, timeout=15)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
            at = q.get("access_token", [""])[0]
            if not at:
                await update.message.reply_text("❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴ ᴛᴏᴋᴇɴ.", reply_markup=reply_kb()); return
            await update.message.reply_text(
                f"🎁 <b>ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ</b>\n\n"
                f"🎮 {esc(urllib.parse.unquote(q.get('nickname',['?'])[0]))}\n"
                f"🆔 <code>{esc(q.get('account_id',['?'])[0])}</code>\n\n"
                f"🔑 <code>{esc(at)}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "revoke":
            info = player_info(token)
            if not info["valid"]:
                await update.message.reply_text("❌ ᴛᴏᴋᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠᴀʟɪᴅ.", reply_markup=reply_kb()); return
            r = requests.get(E_LOGOUT,
                             params={"access_token": token, "refresh_token": RT},
                             timeout=15)
            ok = r.status_code == 200 and "error" not in r.text
            await update.message.reply_text(
                f"{'✅ ʀᴇᴠᴏᴋᴇᴅ' if ok else '❌ ꜰᴀɪʟᴇᴅ'}\n\n"
                f"🎮 {esc(info['nickname'])}\n🆔 <code>{esc(info['uid'])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "unsub":
            r = requests.post(E_SEND_OTP,
                              data={"email": "", "locale": "en_PK", "region": "PK",
                                    "app_id": "100067", "access_token": token},
                              headers=garena_headers())
            await update.message.reply_text(
                f"📧 <b>ᴜɴꜱᴜʙ ᴏᴛᴘ</b>\n\n<code>{esc(r.text[:1500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "jwt":
            r = requests.get("https://acesstojwt-sigma.vercel.app/token",
                             params={"access_token": token}, timeout=20)
            await update.message.reply_text(
                f"🔑 <b>ᴊᴡᴛ ᴛᴏᴋᴇɴ</b>\n\n<code>{esc(r.text[:3500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "platform":
            r = requests.get(E_PLATFORM, params={"access_token": token},
                             headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
            d = r.json()
            b = "\n".join(f"│ ✅ {PLATFORM_MAP.get(x, x)}" for x in d.get("bounded_accounts", [])) or "│ — ɴᴏɴᴇ"
            a = "\n".join(f"│ ➕ {PLATFORM_MAP.get(x, x)}" for x in d.get("available_platforms", [])) or "│ — ɴᴏɴᴇ"
            await update.message.reply_text(
                f"🕹 <b>ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ</b>\n\n"
                f"╭─ ʙᴏᴜɴᴅ\n{b}\n╰──────────────\n\n"
                f"╭─ ᴀᴠᴀɪʟᴀʙʟᴇ\n{a}\n╰──────────────",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "cancel":
            r = requests.post(E_CANCEL,
                              data={"app_id": "100067", "access_token": token},
                              headers=garena_headers())
            ok = '"result": 0' in r.text.replace(" ", "")
            await update.message.reply_text(
                f"{'✅ ᴄᴀɴᴄᴇʟʟᴇᴅ' if ok else '❌ ꜰᴀɪʟᴇᴅ'}\n\n"
                f"<code>{esc(r.text[:1200])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "seccode":
            await update.message.reply_text(
                "🔐 <b>ɢᴇᴛ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ</b>\n\n"
                "🚧 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴜɴᴅᴇʀ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ.\n"
                f"📱 ᴘɪɴɢ {SUPPORT_1} ᴏʀ {SUPPORT_2} ꜰᴏʀ ᴇᴀʀʟʏ ᴀᴄᴄᴇꜱꜱ.",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "stats":
            jwt = access_to_jwt(token)
            if not jwt:
                await update.message.reply_text(
                    "❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ɢᴇɴ ᴊᴡᴛ ꜰᴏʀ ꜱᴛᴀᴛꜱ. ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
                    reply_markup=reply_kb()); return
            h = {"Authorization": f"Bearer {jwt}",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9)",
                 "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1",
                 "ReleaseVersion": "OB52"}
            # GetAccountInfoByAccountID typically needs a uid — inspect token gives one
            insp = inspect_token(token)
            uid = insp.get("uid") or insp.get("account_id")
            r = requests.post(E_STATS, headers=h,
                              data=f"{{}}", timeout=15, verify=False)
            await update.message.reply_text(
                f"📈 <b>ᴘʟᴀʏᴇʀ ꜱᴛᴀᴛꜱ</b>\n\n<code>{esc(r.text[:3000])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "bind":
            await start_bind_flow(update, ctx, token)

        elif action == "unbind":
            await start_unbind_flow(update, ctx, token)

        elif action == "change":
            await start_change_flow(update, ctx, token)

        elif action == "history":
            jwt = access_to_jwt(token)
            if not jwt:
                await update.message.reply_text(
                    "⚠️ ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ ɴᴇᴇᴅꜱ ᴛʜᴇ ᴘʀᴏᴛᴏʙᴜꜰ ᴍᴏᴅᴜʟᴇꜱ (MajoRLogin_pb2 / MajorLoginRes_pb2).\n"
                    "ᴜᴘʟᴏᴀᴅ ᴛʜᴏꜱᴇ ᴛᴡᴏ ꜰɪʟᴇꜱ ᴛᴏ ᴛʜᴇ ʀᴇᴘᴏ ᴀɴᴅ ᴛʜɪꜱ ᴡᴏʀᴋꜱ.",
                    reply_markup=reply_kb(), parse_mode=ParseMode.HTML); return
            await update.message.reply_text(
                "📜 ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ — ᴜɴᴅᴇʀ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ (ᴘʀᴏᴛᴏʙᴜꜰ ᴘᴀʀꜱᴇʀ ɴᴇᴇᴅᴇᴅ).\n"
                "ᴛʜᴇ ᴊᴡᴛ ɢᴇɴ ᴡᴏʀᴋꜱ ᴛʜᴏᴜɢʜ — ᴘɪɴɢ ᴍᴇ ꜰᴏʀ ᴛʜᴇ ᴍᴏᴅᴜʟᴇꜱ.",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)

        elif action == "bio":
            await update.message.reply_text(dev_msg(action),
                                            reply_markup=reply_kb(),
                                            parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(dev_msg(action or "x"),
                                            reply_markup=reply_kb(),
                                            parse_mode=ParseMode.HTML)

    except Exception as e:
        log.exception("on_message fail")
        await update.message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{esc(e)}</code>",
                                        reply_markup=reply_kb(),
                                        parse_mode=ParseMode.HTML)

# ── multi-step flow dispatcher ────────────────────────────
async def flow_dispatch(update, ctx, flow, text):
    step = ctx.user_data.get("flow_step")
    data = ctx.user_data.get("flow_data", {})

    if flow == "bind":
        if step == "email":
            data["email"] = text
            r = requests.post(E_SEND_OTP,
                              data={"email": text, "locale": "en_PK", "region": "PK",
                                    "app_id": "100067", "access_token": data["token"]},
                              headers=garena_headers())
            ctx.user_data["flow_data"] = data
            ctx.user_data["flow_step"] = "otp"
            await update.message.reply_text(
                f"📩 ᴏᴛᴘ ꜱᴇɴᴛ ᴛᴏ <code>{esc(text)}</code>\n"
                f"ꜱᴇɴᴅ ᴛʜᴇ 6-ᴅɪɢɪᴛ ᴄᴏᴅᴇ:",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        elif step == "otp":
            data["otp"] = text
            r = requests.post(E_VERIFY_OTP,
                              data={"app_id": "100067", "access_token": data["token"],
                                    "email": data["email"], "code": text, "otp": text,
                                    "type": "1"},
                              headers=garena_headers())
            vt = ""
            try: vt = r.json().get("verifier_token", "")
            except Exception: pass
            if not vt:
                await update.message.reply_text(
                    f"❌ ᴏᴛᴘ ᴠᴇʀɪꜰʏ ꜰᴀɪʟᴇᴅ:\n<code>{esc(r.text[:500])}</code>",
                    reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
                ctx.user_data.clear(); return
            data["verifier_token"] = vt
            ctx.user_data["flow_data"] = data
            ctx.user_data["flow_step"] = "sec"
            await update.message.reply_text(
                "✅ ᴏᴛᴘ ᴠᴇʀɪꜰɪᴇᴅ.\n\n"
                "🔐 ꜱᴇᴛ ᴀ 6-ᴅɪɢɪᴛ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ (ᴡɪʟʟ ʙᴇ ʜᴀꜱʜᴇᴅ):",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        elif step == "sec":
            sec = hashlib.sha256(text.encode()).hexdigest()
            r = requests.post(E_CREATE_BIND,
                              data={"email": data["email"], "app_id": "100067",
                                    "access_token": data["token"],
                                    "verifier_token": data["verifier_token"],
                                    "secondary_password": sec},
                              headers=garena_headers())
            ok = '"result": 0' in r.text.replace(" ", "")
            await update.message.reply_text(
                f"{'✅ ʙɪɴᴅ ꜱᴜᴄᴄᴇꜱꜱ' if ok else '❌ ʙɪɴᴅ ꜰᴀɪʟᴇᴅ'}\n\n"
                f"<code>{esc(r.text[:1500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
            ctx.user_data.clear()

    elif flow in ("unbind", "change"):
        # method chosen via inline callback; see cb_flow
        pass

async def cb_flow(update, ctx):
    q = update.callback_query; await q.answer()
    d = q.data
    data = ctx.user_data.get("flow_data", {})

    if d == "unbind_otp" or d == "unbind_sec":
        method = "otp" if d.endswith("otp") else "sec"
        data["method"] = method
        ctx.user_data["flow_data"] = data
        if method == "otp":
            requests.post(E_SEND_OTP,
                          data={"email": data["email"], "locale": "en_PK", "region": "PK",
                                "app_id": "100067", "access_token": data["token"]},
                          headers=garena_headers())
            ctx.user_data["flow_step"] = "otp"
            await q.message.reply_text(
                f"📩 ᴏᴛᴘ ꜱᴇɴᴛ ᴛᴏ <code>{esc(data['email'])}</code>\nꜱᴇɴᴅ ᴛʜᴇ ᴄᴏᴅᴇ:",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        else:
            ctx.user_data["flow_step"] = "sec"
            await q.message.reply_text("🔐 ꜱᴇɴᴅ ʏᴏᴜʀ 6-ᴅɪɢɪᴛ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ:",
                                       reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        # register flow = unbind already set
        return

    if d == "change_otp" or d == "change_sec":
        method = "otp" if d.endswith("otp") else "sec"
        data["method"] = method
        ctx.user_data["flow_data"] = data
        if method == "otp":
            requests.post(E_SEND_OTP,
                          data={"email": data["old_email"], "locale": "en_PK",
                                "region": "PK", "app_id": "100067",
                                "access_token": data["token"]},
                          headers=garena_headers())
            ctx.user_data["flow_step"] = "otp_old"
            await q.message.reply_text(
                f"📩 ᴏᴛᴘ ꜱᴇɴᴛ ᴛᴏ ᴏʟᴅ ᴇᴍᴀɪʟ\nꜱᴇɴᴅ ᴛʜᴇ ᴄᴏᴅᴇ:",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        else:
            ctx.user_data["flow_step"] = "sec_old"
            await q.message.reply_text(
                "🔐 ꜱᴇɴᴅ ʏᴏᴜʀ <b>ᴏʟᴅ</b> 6-ᴅɪɢɪᴛ ꜱᴇᴄᴜʀɪᴛʏ ᴄᴏᴅᴇ:",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        return

# hook the flow step machine into on_message
async def on_message_wrapper(update, ctx):
    flow = ctx.user_data.get("flow")
    step = ctx.user_data.get("flow_step")
    if flow in ("unbind",) and step in ("otp", "sec"):
        data = ctx.user_data.get("flow_data", {})
        token = data["token"]
        if step == "otp":
            r = requests.post(E_VERIFY_ID,
                              data={"email": data["email"], "app_id": "100067",
                                    "access_token": token, "otp": update.message.text.strip()},
                              headers=garena_headers())
        else:
            sec = hashlib.sha256(update.message.text.strip().encode()).hexdigest()
            r = requests.post(E_VERIFY_ID,
                              data={"email": data["email"], "app_id": "100067",
                                    "access_token": token, "secondary_password": sec},
                              headers=garena_headers())
        it = ""
        try: it = r.json().get("identity_token", "")
        except Exception: pass
        if not it:
            await update.message.reply_text(
                f"❌ ᴠᴇʀɪꜰʏ ꜰᴀɪʟᴇᴅ:\n<code>{esc(r.text[:500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
            ctx.user_data.clear(); return
        r2 = requests.post(E_UNBIND,
                           data={"app_id": "100067", "access_token": token,
                                 "identity_token": it},
                           headers=garena_headers())
        ok = '"result": 0' in r2.text.replace(" ", "")
        await update.message.reply_text(
            f"{'✅ ᴜɴʙɪɴᴅ ꜱᴜᴄᴄᴇꜱꜱ' if ok else '❌ ꜰᴀɪʟᴇᴅ'}\n\n"
            f"<code>{esc(r2.text[:1200])}</code>",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        ctx.user_data.clear(); return

    if flow == "change" and step in ("otp_old", "sec_old"):
        data = ctx.user_data.get("flow_data", {})
        token = data["token"]
        if step == "otp_old":
            r = requests.post(E_VERIFY_ID,
                              data={"email": data["old_email"], "app_id": "100067",
                                    "access_token": token,
                                    "otp": update.message.text.strip()},
                              headers=garena_headers())
        else:
            sec = hashlib.sha256(update.message.text.strip().encode()).hexdigest()
            r = requests.post(E_VERIFY_ID,
                              data={"email": data["old_email"], "app_id": "100067",
                                    "access_token": token, "secondary_password": sec},
                              headers=garena_headers())
        it = ""
        try: it = r.json().get("identity_token", "")
        except Exception: pass
        if not it:
            await update.message.reply_text(
                f"❌ ᴏʟᴅ ᴀᴄᴄᴏᴜɴᴛ ᴠᴇʀɪꜰʏ ꜰᴀɪʟᴇᴅ:\n<code>{esc(r.text[:500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
            ctx.user_data.clear(); return
        data["identity_token"] = it
        ctx.user_data["flow_data"] = data
        ctx.user_data["flow_step"] = "new_email"
        await update.message.reply_text(
            "✅ ᴏʟᴅ ᴠᴇʀɪꜰɪᴇᴅ.\n📩 ꜱᴇɴᴅ ɴᴇᴡ ᴇᴍᴀɪʟ:",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        return

    if flow == "change" and step == "new_email":
        data = ctx.user_data["flow_data"]; token = data["token"]
        data["new_email"] = update.message.text.strip()
        ctx.user_data["flow_data"] = data
        ctx.user_data["flow_step"] = "new_otp"
        requests.post(E_SEND_OTP,
                      data={"email": data["new_email"], "locale": "en_PK",
                            "region": "PK", "app_id": "100067",
                            "access_token": token},
                      headers=garena_headers())
        await update.message.reply_text(
            f"📩 ᴏᴛᴘ ꜱᴇɴᴛ ᴛᴏ <code>{esc(data['new_email'])}</code>\nꜱᴇɴᴅ ᴛʜᴇ ᴄᴏᴅᴇ:",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        return

    if flow == "change" and step == "new_otp":
        data = ctx.user_data["flow_data"]; token = data["token"]
        r = requests.post(E_VERIFY_OTP,
                          data={"email": data["new_email"], "app_id": "100067",
                                "access_token": token, "otp": update.message.text.strip()},
                          headers=garena_headers())
        vt = ""
        try: vt = r.json().get("verifier_token", "")
        except Exception: pass
        if not vt:
            await update.message.reply_text(
                f"❌ ɴᴇᴡ ᴇᴍᴀɪʟ ᴠᴇʀɪꜰʏ ꜰᴀɪʟᴇᴅ:\n<code>{esc(r.text[:500])}</code>",
                reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
            ctx.user_data.clear(); return
        r2 = requests.post(E_REBIND,
                           data={"identity_token": data["identity_token"],
                                 "email": data["new_email"], "app_id": "100067",
                                 "verifier_token": vt, "access_token": token},
                           headers=garena_headers())
        ok = '"result": 0' in r2.text.replace(" ", "")
        await update.message.reply_text(
            f"{'✅ ᴄʜᴀɴɢᴇ ʙɪɴᴅ ꜱᴜᴄᴄᴇꜱꜱ' if ok else '❌ ꜰᴀɪʟᴇᴅ'}\n\n"
            f"<code>{esc(r2.text[:1200])}</code>",
            reply_markup=reply_kb(), parse_mode=ParseMode.HTML)
        ctx.user_data.clear(); return

    # fall through: not a flow input — normal handler
    await on_message(update, ctx)

# ── boot ──────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CallbackQueryHandler(cb_verify, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(cb_flow,
                    pattern="^(unbind|change)_(otp|sec)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message_wrapper))

    if PUBLIC:
        log.info(f"🚀 ᴡᴇʙʜᴏᴏᴋ ᴏɴ :{PORT}/{PATH}")
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=PATH,
                        webhook_url=f"{PUBLIC}/{PATH}",
                        drop_pending_updates=True,
                        allowed_updates=Update.ALL_TYPES)
    else:
        log.info("🚀 ᴘᴏʟʟɪɴɢ ᴍᴏᴅᴇ")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
