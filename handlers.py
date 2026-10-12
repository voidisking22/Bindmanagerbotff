import urllib.parse
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import *
from keyboards import main_menu, join_keyboard
from utils import is_member, player_info, bind_info, convert_seconds, esc, PLATFORM_MAP

# ── /start ───────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    name = esc(u.first_name or "User")

    if not (is_member(ctx.bot, CHANNEL_ID, u.id) and is_member(ctx.bot, GROUP_ID, u.id)):
        await update.message.reply_text(
            f"🔐 <b>ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʀᴇǫᴜɪʀᴇᴅ</b>\n\n"
            f"ʜɪ {name} (<code>{u.id}</code>)\n"
            f"ᴋɪɴᴅʟʏ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ & ɢʀᴏᴜᴘ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ.",
            reply_markup=join_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    await send_main_menu(update, ctx)

async def verify_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u = q.from_user
    if is_member(ctx.bot, CHANNEL_ID, u.id) and is_member(ctx.bot, GROUP_ID, u.id):
        try: await q.message.delete()
        except Exception: pass
        await send_main_menu(update, ctx, from_query=True)
    else:
        await q.answer("❌ ʏᴏᴜ ꜱᴛɪʟʟ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ!", show_alert=True)

async def send_main_menu(update, ctx, from_query=False):
    u = update.effective_user
    text = (
        f"👋 ʜɪ <b>{esc(u.first_name)}</b> (<code>{u.id}</code>)\n"
        f"ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <b>{BRAND}</b>\n\n"
        f"<b>⚙️ ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ :</b>\n"
        f"╭──────────────\n"
        f"│ 🔍 ᴄʜᴇᴄᴋ ʙɪɴᴅ ɪɴꜰᴏ\n"
        f"│ 📧 ʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"│ 🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"│ ♻️ ᴄʜᴀɴɢᴇ ʙɪɴᴅ ᴇᴍᴀɪʟ\n"
        f"│ 🛑 ᴄᴀɴᴄᴇʟ ʙɪɴᴅ ʀᴇǫᴜᴇꜱᴛ\n"
        f"│ 🎟 ᴇᴀᴛ → ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ\n"
        f"│ 🚫 ʀᴇᴠᴏᴋᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ\n"
        f"│ 📜 ɢᴇᴛ ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ\n"
        f"│ 🕹 ᴄʜᴇᴄᴋ ʙᴏᴜɴᴅ ᴘʟᴀᴛꜰᴏʀᴍꜱ\n"
        f"│ 🔑 ᴛᴏᴋᴇɴ → ᴊᴡᴛ\n"
        f"│ ☠️ ᴛᴏᴋᴇɴ → ʙᴀɴ\n"
        f"│ 👑 ᴏᴡɴᴇʀ ᴅᴇᴛᴀɪʟꜱ\n"
        f"╰──────────────\n\n"
        f"🚀 ᴘɪᴄᴋ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ\n\n"
        f"⚠️ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ → ᴍᴇꜱꜱᴀɢᴇ {SUPPORT_1} ᴏʀ {SUPPORT_2}\n\n"
        f"╰━━━「 📱 ʀᴇᴀᴅʏ ᴛᴏ ᴅᴇᴘʟᴏʏ 」━━━╯"
    )
    if from_query:
        await ctx.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                   reply_markup=main_menu(), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)

# ── Menu router ──────────────────────────────────────────
async def menu_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data

    prompts = {
        "menu_check":    ("🔍 ᴄʜᴇᴄᴋ ʙɪɴᴅ",       "ꜱᴇɴᴅ ʏᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_bind":     ("📧 ʙɪɴᴅ ᴇᴍᴀɪʟ",       "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_unbind":   ("🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ",     "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_change":   ("♻️ ᴄʜᴀɴɢᴇ ʙɪɴᴅ",     "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_cancel":   ("🛑 ᴄᴀɴᴄᴇʟ ʀᴇǫᴜᴇꜱᴛ",  "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_eat":      ("🎟 ᴇᴀᴛ ᴛᴏ ᴛᴏᴋᴇɴ",    "ᴘᴀꜱᴛᴇ ᴇᴀᴛ ᴛᴏᴋᴇɴ ᴏʀ ᴇᴀᴛ ᴜʀʟ"),
        "menu_revoke":   ("🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ",    "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_history":  ("📜 ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ",   "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_platform": ("🕹 ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ",  "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_jwt":      ("🔑 ᴛᴏᴋᴇɴ → ᴊᴡᴛ",     "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
        "menu_ban":      ("☠️ ᴛᴏᴋᴇɴ → ʙᴀɴ",     "ꜱᴇɴᴅ ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ"),
    }

    if action == "menu_owner":
        text = (
            f"👑 <b>ᴏᴡɴᴇʀ ᴅᴇᴛᴀɪʟꜱ</b>\n\n"
            f"╭──────────────\n"
            f"│ ᴅᴇᴠ  : ᴠᴏɪᴅ ɪꜱ ᴋɪɴɢ\n"
            f"│ ᴛɢ   : {SUPPORT_1}\n"
            f"│ ᴛɢ   : {SUPPORT_2}\n"
            f"│ ᴄʜᴀɴ : {FORCE_CHANNEL}\n"
            f"│ ɢʀᴘ  : {FORCE_GROUP}\n"
            f"╰──────────────\n\n"
            f"ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ <b>{BRAND}</b> 🤍"
        )
        await q.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    if action in prompts:
        title, hint = prompts[action]
        ctx.user_data["pending"] = action.replace("menu_", "")
        await q.message.reply_text(f"{title}\n\n📩 {hint}", parse_mode=ParseMode.HTML)
    else:
        await q.message.reply_text("❓ ᴜɴᴋɴᴏᴡɴ ᴀᴄᴛɪᴏɴ.")

# ── Token input handler ──────────────────────────────────
async def token_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
            cd    = convert_seconds(b.get("request_exec_countdown", 0))
            await update.message.reply_text(
                f"🔍 <b>ʙɪɴᴅ ɪɴꜰᴏ</b>\n\n"
                f"╭──────────────\n"
                f"│ 🎮 ɴɪᴄᴋ : {esc(info['nickname'])}\n"
                f"│ 🆔 ᴜɪᴅ  : <code>{info['uid']}</code>\n"
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
                f"🎟 <b>ᴀᴄᴄᴇꜱꜱ ᴛᴏᴋᴇɴ</b>\n\n"
                f"╭──────────────\n"
                f"│ 🎮 ɴɪᴄᴋ : {esc(urllib.parse.unquote(q.get('nickname',['?'])[0]))}\n"
                f"│ 🆔 ᴜɪᴅ  : <code>{q.get('account_id',['?'])[0]}</code>\n"
                f"│ 🌍 ʀɢɴ  : {q.get('region',['?'])[0]}\n"
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
                f"🎮 {esc(info['nickname'])}\n🆔 <code>{info['uid']}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action == "jwt":
            r = requests.get(f"https://acesstojwt-sigma.vercel.app/token?access_token={token}", timeout=15)
            await update.message.reply_text(
                f"🔑 <b>ᴊᴡᴛ ᴛᴏᴋᴇɴ</b>\n\n<code>{esc(r.text[:3500])}</code>",
                parse_mode=ParseMode.HTML,
            )

        elif action == "ban":
            r = requests.get(f"https://toji-api-jwt.vercel.app/ban?token={token}", timeout=20)
            await update.message.reply_text(
                f"☠️ <b>ʙᴀɴ ʀᴇꜱᴘᴏɴꜱᴇ</b>\n\n<code>{esc(r.text[:3500])}</code>",
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

        elif action in ("bind", "unbind", "change", "cancel", "history"):
            await update.message.reply_text(
                f"⚠️ <b>{action.upper()}</b> ɪꜱ ᴜɴᴅᴇʀ ᴄᴏɴꜱᴛʀᴜᴄᴛɪᴏɴ.\n"
                f"ᴄᴏɴᴛᴀᴄᴛ {SUPPORT_1} ᴏʀ {SUPPORT_2}",
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text("❓ ᴜɴᴋɴᴏᴡɴ ᴀᴄᴛɪᴏɴ.")

    except Exception as e:
        await update.message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{esc(e)}</code>", parse_mode=ParseMode.HTML)
