import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

try:
    with open("last_update_id.txt", "r") as f:
        content = f.read().strip()
        last_update_id = int(content) if content else 0
except:
    last_update_id = 0

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}

if response.get("ok"):
    for result in response["result"]:
        update_id = result["update_id"]
        last_update_id = max(last_update_id, update_id)
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            # TEXT
            if "text" in msg:
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={"chatId": chat_id, "text": msg["text"], "session": "default"})
            
            # PHOTO / DOCUMENT / VIDEO (Combined for NOWEB)
            media_type = "photo" if "photo" in msg else ("document" if "document" in msg else ("video" if "video" in msg else None))
            if media_type:
                file_obj = msg[media_type][-1] if media_type == "photo" else msg[media_type]
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                if f_res["ok"]:
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{f_res['result']['file_path']}"
                    # NOWEB uses /api/sendFile for everything!
                    payload = {
                        "chatId": chat_id,
                        "file": {"url": d_url, "filename": "file"},
                        "caption": msg.get("caption", ""),
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendFile", headers=headers, json=payload)

    with open("last_update_id.txt", "w") as f: f.write(str(last_update_id))
