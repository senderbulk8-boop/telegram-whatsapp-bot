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
            
            # 1. TEXT MESSAGE
            if "text" in msg:
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={
                    "chatId": chat_id, "text": msg["text"], "session": "default"
                })

            # 2. PHOTO/DOC J जुगाड़ (Link Preview method)
            media_type = None
            if "photo" in msg: media_type = "photo"
            elif "document" in msg: media_type = "document"

            if media_type:
                file_obj = msg[media_type][-1] if media_type == "photo" else msg[media_type]
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    # यह फाइल का सीधा डाउनलोड लिंक है
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    # NOWEB के फ्री वर्जन में हम लिंक भेजेंगे जो फोटो जैसा दिखेगा
                    caption = msg.get("caption", "Positron Academy Document")
                    text_with_link = f"{caption}\n\n📥 View/Download: {d_url}"
                    
                    res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={
                        "chatId": chat_id, 
                        "text": text_with_link, 
                        "session": "default"
                    })
                    print(f"Sent as Link to {chat_id}: {res.status_code}")

    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
