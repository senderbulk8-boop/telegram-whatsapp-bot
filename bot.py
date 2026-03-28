import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

try:
    with open("last_update_id.txt", "r") as f:
        last_update_id = int(f.read().strip() or 0)
except:
    last_update_id = 0

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}

if response.get("ok"):
    for result in response["result"]:
        last_update_id = max(last_update_id, result["update_id"])
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            
            # 1. सिर्फ टेक्स्ट मैसेज
            if "text" in msg and "photo" not in msg:
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={
                    "chatId": chat_id, "text": msg["text"], "session": "default"
                })

            # 2. फोटो के साथ टेक्स्ट (NOWEB JUGAD)
            if "photo" in msg:
                file_obj = msg["photo"][-1]
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    # यह फीचर फ्री वर्जन में काम करता है और फोटो + टेक्स्ट का लुक देता है
                    payload = {
                        "chatId": chat_id,
                        "url": d_url,
                        "title": "Positron Academy Update",
                        "text": msg.get("caption", ""), # फोटो के नीचे वाला टेक्स्ट
                        "session": "default"
                    }
                    
                    res = requests.post(f"{WAHA_API_URL}/api/send/link-custom-preview", headers=headers, json=payload)
                    print(f"Image Link Preview to {chat_id}: {res.status_code}")

    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
