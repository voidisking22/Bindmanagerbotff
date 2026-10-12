import requests, urllib3, urllib.parse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line",
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
}

def is_member(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return False

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d}d {h}h {m}m {s}s"

def esc(text):
    return str(text).replace("<", "&lt;").replace(">", "&gt;")

def player_info(access_token):
    url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                     allow_redirects=True, timeout=15)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
    return {
        "uid":      q.get("account_id", ["Unknown"])[0],
        "nickname": urllib.parse.unquote(q.get("nickname", ["Unknown"])[0]),
        "region":   q.get("region", ["Unknown"])[0],
        "valid":    "access_token" in q,
    }

def bind_info(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {"app_id": "100067", "access_token": access_token}
    h = {"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=params, headers=h, timeout=15)
    return r.json() if r.status_code == 200 else None
