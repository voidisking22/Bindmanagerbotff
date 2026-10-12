# ═══════════════════════════════════════════════════════════
#  KING VOID BIND MANAGER — single-file build
# ═══════════════════════════════════════════════════════════

import os, sys, json, time, base64, hashlib, urllib.parse
import logging
import requests, urllib3
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── config ────────────────────────────────────────────────
BOT_TOKEN      = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
FORCE_CHANNEL  = os.getenv("FORCE_CHANNEL", "https://t.me/kingvoidofficials")
FORCE_GROUP    = os.getenv("FORCE_GROUP",   "https://t.me/kingvoidofficialgc")
CHANNEL_ID     = os.getenv("CHANNEL_ID",    "@kingvoidofficials")
GROUP_ID       = os.getenv("GROUP_ID",      "@kingvoidofficialgc")
SUPPORT_1      = os.getenv("SUPPORT_1",     "@voidisking")
SUPPORT_2      = os.getenv("SUPPORT_2",     "@lordofzone")
BRAND          = "ᴛʜᴇ ᴠᴏɪᴅ ɢᴀʀᴇɴᴀ ʙɪɴᴅ ᴍᴀɴᴀɢᴇʀ"

PORT   = int(os.getenv("PORT", "8080"))
PUBLIC = os.getenv("RENDER_EXTERNAL_URL", "")
PATH   = "webhook"

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("kvbm")

# ── helpers ───────────────────────────────────────────────
PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line",
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok",
}

def esc(t):
    return str(t).replace("<", "&lt;").replace(">", "&gt;")

def secs(s):
    d, h = divmod(int(s), 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d}d {h}h {m}m {s}s"

def is_member(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        ok = m.status in ("member", "administrator", "creator")
        log.info(f"[verify] chat={chat_id} user={user_id} status={m.status} ok={ok}")
        return ok
    except Exception as e:
        log.warning(f"[verify] chat={chat_id} user={user_id} ERR={e}")
        return False

def player_info(token):
    url = f"https://api-otrss.garena.com/support/callback/?access_token={token}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                     allow_redirects=True, timeout=15)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
    return {
        "uid":      q.get("account_id", ["?"])[0],
        "nickname": urllib.parse.unquote(q.get("nickname", ["?"])[0]),
        "region":   q.get("region", ["?"])[0],
        "valid":    "access_token" in q,
    }

def bind_info(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {"app_id": "100067", "access_token": token}
    h = {"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=params, headers=h, timeout=15)
    return r.json() if r.status_code == 200 else None

# ── keyboards ─────────────────────────────────────────────
def join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=FORCE_CHANNEL)],
        [InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ",   url=FORCE_GROUP)],
        [InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ", callback_data="verify_join")],
    ])

def main_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 ᴄʜᴇᴄᴋ ʙɪɴᴅ",         callback_data="menu_check"),
            InlineKeyboardButton("🔗 ʙɪɴᴅ ᴇᴍᴀɪʟ",         callback_data="menu_bind"),
        ],
        [
            InlineKeyboardButton("🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ",       callback_data="menu_unbind"),
            InlineKeyboardButton("🔄 ᴄʜᴀɴɢᴇ ʙɪɴᴅ ᴇᴍᴀɪʟ",  callback_data="menu_change"),
        ],
        [
            InlineKeyboardButton("⚠️ ᴄᴀɴᴄᴇʟ ʀᴇǫᴜᴇꜱᴛ",   callback_data="menu_cancel"),
            InlineKeyboardButton("🎁 ᴇᴀᴛ → ᴛᴏᴋᴇɴ",       callback_data="menu_eat"),
        ],
        [
            InlineKeyboardButton("🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ",      callback_data="menu_revoke"),
            InlineKeyboardButton("📧 ꜱɪɴɢʟᴇ ᴜɴꜱᴜʙ ᴏᴛᴘ",  callback_data="menu_unsub"),
        ],
        [
            InlineKeyboardButton("✨ ᴜᴘᴅᴀᴛᴇ ʙɪᴏ",         callback_data="menu_bio"),
            InlineKeyboardButton("🕹 ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ",    callback_data="menu_platform"),
        ],
        [
            InlineKeyboardButton("📜 ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ",    callback_data="menu_history"),
            InlineKeyboardButton("🔑 ᴛᴏᴋᴇɴ → ᴊᴡᴛ",       callback_data="menu_jwt"),
        ],
        [
            InlineKeyboardButton("👑 ᴏᴡɴᴇʀ ᴅᴇᴛᴀɪʟꜱ",    callback_data="menu_owner"),
        ],
    ])

# ── /start & verify ───────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not (is_member(ctx.bot, CHANNEL_ID, u.id) and is_member(ctx.bot, GROUP_ID, u.id)):
        await update.message.reply_text(
            f"🔐 <b>ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʀᴇǫᴜɪʀᴇᴅ</b>\n\n"
            f"ʜɪ <b>{esc(u.first_name)}</b> (<code>{u.id}</code>)\n"
            f"ᴋɪɴᴅʟʏ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ & ɢʀᴏᴜᴘ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ.\n\n"
            f"ᴀꜰᴛᴇʀ ᴊᴏɪɴɪɴɢ ᴛᴀᴘ ✅ ᴠᴇʀɪꜰʏ",
            reply_markup=join_kb(),
            parse_mode=ParseMode.HTML,
        )
        return
    await show_menu(update, ctx)

async def cb_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    u = q.from_user
    ok = is_member(ctx.bot, CHANNEL_ID, u.id) and is_member(ctx.bot, GROUP_ID, u.id)
    if ok:
        await q.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ!", show_alert=False)
        try: await q.message.delete()
        except Exception: pass
        await show_menu(update, ctx, from_query=True)
    else:
        await q.answer("❌ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ꜰɪʀꜱᴛ!", show_alert=True)

async def show_menu(update, ctx, from_query=False):
    u = update.effective_user
    text = (
        f"✨  <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {BRAND}</b>  ✨\n\n"
        f"😎 ᴜꜱᴇʀ : <b>{esc(u.first_name)}</b>\n"
        f"👑 ɪᴅ : <code>{u.id}</code>\n\n"
        f"🚀 <b>ꜰᴇᴀᴛᴜʀᴇꜱ :</b>\n"
        f"• 📊 ᴄʜᴇᴄᴋ ʙɪɴᴅ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ\n"
        f"• 🔗 ʙɪɴᴅ ᴇᴍᴀɪʟ ᴛᴏ ᴀᴄᴄᴏᴜɴᴛ\n"
        f"• 🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"• 🔄 ᴄʜᴀɴɢᴇ ʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"• ⚠️ ᴄᴀɴᴄᴇʟ ʙɪɴᴅ ʀᴇQᴜᴇꜱᴛ\n"
        f"• 🎁 ᴄᴏɴᴠᴇʀᴛ ᴇᴀᴛ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ\n"
        f"• 🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ\n"
        f"• 📧 ꜱᴇɴᴅ ꜱɪɴɢʟᴇ ᴜɴꜱᴜʙꜱᴄʀɪʙᴇ ᴏᴛᴘ\n"
        f"• ✨ ᴜᴘᴅᴀᴛᴇ ʙɪᴏ ᴘʀᴏꜰɪʟᴇ\n\n"
        f"❤️ <b>ᴘʀᴇᴍɪᴜᴍ & ꜱᴇᴄᴜʀᴇ ᴛᴏᴏʟ</b>\n"
        f"📱 ꜱᴜᴘᴘᴏʀᴛ : {SUPPORT_1} ᴏʀ {SUPPORT_2}\n\n"
        f"👇 ꜱᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ꜰʀᴏᴍ ʙᴇʟᴏᴡ:"
    )
    kb = main_kb()
    if from_query:
        await ctx.bot.send_message(chat_id=update.effective_chat.id,
                                   text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

# ── menu router ───────────────────────────────────────────
PROMPTS = {
    "menu_check":    ("📊 ᴄʜᴇᴄᴋ ʙɪɴᴅ",           "ꜱᴇɴᴅ ʏᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_bind":     ("🔗 ʙɪɴᴅ ᴇᴍᴀɪʟ",           "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_unbind":   ("🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ",         "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_change":   ("🔄 ᴄʜᴀɴɢᴇ ʙɪɴᴅ ᴇᴍᴀɪʟ",    "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_cancel":   ("⚠️ ᴄᴀɴᴄᴇʟ ʀᴇǫᴜᴇꜱᴛ",      "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_eat":      ("🎁 ᴇᴀᴛ → ᴛᴏᴋᴇɴ",          "ᴘᴀꜱᴛᴇ ᴇᴀᴛ ᴛᴏᴋᴇɴ ᴏʀ ᴇᴀᴛ ᴜʀʟ"),
    "menu_revoke":   ("🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ",         "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_unsub":    ("📧 ꜱɪɴɢʟᴇ ᴜɴꜱᴜʙ ᴏᴛᴘ",    "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_bio":      ("✨ ᴜᴘᴅᴀᴛᴇ ʙɪᴏ",            "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_platform": ("🕹 ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ",       "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_history":  ("📜 ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ",        "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    "menu_jwt":      ("🔑 ᴛᴏᴋᴇɴ → ᴊᴡᴛ",           "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
}

async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data

    if action == "menu_owner":
        await q.message.reply_text(
            f"👑 <b>ᴏᴡɴᴇʀ ᴅᴇᴛᴀɪʟꜱ</b>\n\n"
            f"╭──────────────\n"
            f"│ ᴅᴇᴠ  : ᴠᴏɪᴅ ɪꜱ ᴋɪɴɢ\n"
            f"│ ᴛɢ   : {SUPPORT_1}\n"
            f"│ ᴛɢ   : {SUPPORT_2}\n"
            f"│ ᴄʜᴀɴ : {FORCE_CHANNEL}\n"
            f"│ ɢʀᴘ  : {FORCE_GROUP}\n"
            f"╰──────────────\n\n"
            f"ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ <b>{BRAND}</b> 🤍",
            parse_mode=ParseMode.HTML,
        )
        return

    if action in PROMPTS:
        title, hint = PROMPTS[action]
        ctx.user_data["pending"] = action.replace("menu_", "")
        await q.message.reply_text(
            f"{title}\n\n📩 {hint}\n\n<i>ᴄᴀɴᴄᴇʟ : /cancel</i>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await q.message.reply_text("❓ ᴜɴᴋɴᴏᴡɴ ᴀᴄᴛɪᴏɴ.")

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending"] = None
    await update.message.reply_text("✅ ᴄᴀɴᴄᴇʟʟᴇᴅ.")

# ── token input dispatcher ────────────────────────────────
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    action = ctx.user_data.get("pending")
    if not action:
        return
    token = update.message.text.strip()
    ctx.user_data["pending"] = None

    try:
        if action == "check":
            info = player_info(token)
            if not info["valid"]:
                await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ᴛᴏᴋᴇɴ.")
                return
            b = bind_info(token) or {}
            email = b.get("email") or "None"
            pend  = b.get("email_to_be") or "None"
            cd    = secs(b.get("request_exec_countdown", 0))
            await update.message.reply_text(
                f"📊 <b>ʙɪɴᴅ ɪɴꜰᴏ</b>\n\n"
                f"╭──────────────\n"
                f"│ 🎮 ɴɪᴄᴋ : {esc(info['nickname'])}\n"
                f"│ 🆔 ᴜɪᴅ  : <code>{esc(info['uid'])}</code>\n"
                f"│ 🌍 ʀɢɴ  : {esc(info['region'])}\n"
                f"│ 📧 ᴇᴍᴀɪʟ: {esc(email)}\n"
                f"│ ⏳ ᴘᴇɴᴅ : {esc(pend)}\n"
                f"│ ⏱ ᴄᴅ   : {cd}\n"
                f"╰──────────────",
                parse_mode=ParseMode.HTML,
            )

        elif action == "eat":
            eat = token
            if "http" in token or "?" in token:
                q = urllib.parse.parse_qs(urllib.parse.urlparse(token).query)
                eat = q.get("eat", [""])[0]
            if not eat:
                await update.message.reply_text("❌ ɴᴏ ᴇᴀᴛ ᴛᴏᴋᴇɴ ꜰᴏᴜɴᴅ.")
                return
            url = f"https://api-otrss.garena.com/support/callback/?access_token={eat}"
            r = requests.get(url, allow_redirects=True, timeout=15)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
            at = q.get("access_token", [""])[0]
            if not at:
                await update.message.reply_text("❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ.")
                return
            await update.message.reply_text(
                f"🎁 <b>ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ</b>\n\n"
                f"╭──────────────\n"
                f"│ 🎮 ɴɪᴄᴋ : {esc(urllib.parse.unquote(q.get('nickname',['?'])[0]))}\n"
                f"│ 🆔 ᴜɪᴅ  : <code>{esc(q.get('account_id',['?'])[0])}</code>\n"
                f"│ 🌍 ʀɢɴ  : {esc(q.get('region',['?'])[0])}\n"
                f"╰──────────────\n\n"
                f"🔑 <code>{esc(at)}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action == "revoke":
            info = player_info(token)
            if not info["valid"]:
                await update.message.reply_text("❌ ᴛᴏᴋᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠᴀʟɪᴅ/ʀᴇᴠᴏᴋᴇᴅ.")
                return
            rt = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
            url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={rt}"
            r = requests.get(url, timeout=15)
            ok = r.status_code == 200 and "error" not in r.text
            await update.message.reply_text(
                f"{'✅' if ok else '❌'} ʀᴇᴠᴏᴋᴇ {'ꜱᴜᴄᴄᴇꜱꜱ' if ok else 'ꜰᴀɪʟᴇᴅ'}\n\n"
                f"🎮 {esc(info['nickname'])}\n🆔 <code>{esc(info['uid'])}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action == "unsub":
            url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
            data = {"email": "", "locale": "en_PK", "region": "PK",
                    "app_id": "100067", "access_token": token}
            r = requests.post(url, data=data,
                              headers={"User-Agent": "GarenaMSDK/4.0.30"})
            await update.message.reply_text(
                f"📧 <b>ᴜɴꜱᴜʙ ᴏᴛᴘ</b>\n\n<code>{esc(r.text[:1500])}</code>",
                parse_mode=ParseMode.HTML)

        elif action == "bio":
            await update.message.reply_text(
                f"✨ ᴜᴘᴅᴀᴛᴇ ʙɪᴏ ɪꜱ ᴄᴏᴍɪɴɢ ꜱᴏᴏɴ.\nᴘɪɴɢ {SUPPORT_1} ᴏʀ {SUPPORT_2}.",
                parse_mode=ParseMode.HTML)

        elif action == "jwt":
            r = requests.get(f"https://acesstojwt-sigma.vercel.app/token?access_token={token}", timeout=15)
            await update.message.reply_text(
                f"🔑 <b>ᴊᴡᴛ ᴛᴏᴋᴇɴ</b>\n\n<code>{esc(r.text[:3500])}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action == "platform":
            url = "https://100067.connect.garena.com/bind/app/platform/info/get"
            r = requests.get(url, params={"access_token": token},
                             headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
            d = r.json()
            b = "\n".join(f"│ ✅ {PLATFORM_MAP.get(x, x)}" for x in d.get("bounded_accounts", [])) or "│ — ɴᴏɴᴇ"
            a = "\n".join(f"│ ➕ {PLATFORM_MAP.get(x, x)}" for x in d.get("available_platforms", [])) or "│ — ɴᴏɴᴇ"
            await update.message.reply_text(
                f"🕹 <b>ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ</b>\n\n"
                f"╭─ ʙᴏᴜɴᴅ\n{b}\n╰──────────────\n\n"
                f"╭─ ᴀᴠᴀɪʟᴀʙʟᴇ\n{a}\n╰──────────────",
                parse_mode=ParseMode.HTML,
            )

        elif action == "cancel":
            url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
            data = {"app_id": "100067", "access_token": token}
            r = requests.post(url, data=data,
                              headers={"User-Agent": "GarenaMSDK/4.0.30",
                                       "Content-Type": "application/x-www-form-urlencoded"})
            ok = '"result": 0' in r.text.replace(" ", "")
            await update.message.reply_text(
                f"{'✅' if ok else '❌'} ᴄᴀɴᴄᴇʟ {'ᴏᴋ' if ok else 'ꜰᴀɪʟᴇᴅ'}\n\n"
                f"<code>{esc(r.text[:1200])}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action in ("bind", "unbind", "change", "history"):
            await update.message.reply_text(
                f"⚠️ <b>{action.upper()}</b> ɪꜱ ᴜɴᴅᴇʀ ᴄᴏɴꜱᴛʀᴜᴄᴛɪᴏɴ.\n"
                f"ᴄᴏɴᴛᴀᴄᴛ {SUPPORT_1} ᴏʀ {SUPPORT_2}",
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text("❓ ᴜɴᴋɴᴏᴡɴ ᴀᴄᴛɪᴏɴ.")

    except Exception as e:
        log.exception("token_input fail")
        await update.message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{esc(e)}</code>",
                                        parse_mode=ParseMode.HTML)

# ── boot ──────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CallbackQueryHandler(cb_verify, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(cb_menu,   pattern="^menu_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if PUBLIC:
        log.info(f"🚀 ᴡᴇʙʜᴏᴏᴋ ᴏɴ :{PORT}/{PATH}")
        app.run_webhook(
            listen="0.0.0.0", port=PORT, url_path=PATH,
            webhook_url=f"{PUBLIC}/{PATH}",
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        log.info("🚀 ᴘᴏʟʟɪɴɢ ᴍᴏᴅᴇ (local)")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
