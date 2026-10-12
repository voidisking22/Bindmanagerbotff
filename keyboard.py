from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url="https://t.me/kingvoidofficials")],
        [InlineKeyboardButton("💬 ᴊᴏɪɴ ɢʀᴏᴜᴘ",   url="https://t.me/kingvoidofficialgc")],
        [InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ", callback_data="verify_join")],
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ ʙɪɴᴅ",     callback_data="menu_check"),
            InlineKeyboardButton("📧 ʙɪɴᴅ ᴇᴍᴀɪʟ",     callback_data="menu_bind"),
        ],
        [
            InlineKeyboardButton("🔓 ᴜɴʙɪɴᴅ ᴇᴍᴀɪʟ",   callback_data="menu_unbind"),
            InlineKeyboardButton("♻️ ᴄʜᴀɴɢᴇ ᴇᴍᴀɪʟ",  callback_data="menu_change"),
        ],
        [
            InlineKeyboardButton("🛑 ᴄᴀɴᴄᴇʟ ʀᴇǫᴜᴇꜱᴛ", callback_data="menu_cancel"),
            InlineKeyboardButton("🎟 ᴇᴀᴛ ᴛᴏ ᴛᴏᴋᴇɴ",  callback_data="menu_eat"),
        ],
        [
            InlineKeyboardButton("🚫 ʀᴇᴠᴏᴋᴇ ᴛᴏᴋᴇɴ",   callback_data="menu_revoke"),
            InlineKeyboardButton("📜 ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ", callback_data="menu_history"),
        ],
        [
            InlineKeyboardButton("🕹 ᴘʟᴀᴛꜰᴏʀᴍ ʙɪɴᴅꜱ", callback_data="menu_platform"),
            InlineKeyboardButton("🔑 ᴛᴏᴋᴇɴ → ᴊᴡᴛ",    callback_data="menu_jwt"),
        ],
        [
            InlineKeyboardButton("☠️ ᴛᴏᴋᴇɴ → ʙᴀɴ",    callback_data="menu_ban"),
            InlineKeyboardButton("👑 ᴏᴡɴᴇʀ",            callback_data="menu_owner"),
        ],
    ])