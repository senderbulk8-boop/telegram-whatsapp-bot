import os
import requests

# GitHub Secrets se Tokens uthana
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Yahan URL ke aage se '/' hatane ke liye rstrip ka use kiya hai
WAHA_API_URL = os.environ.get("WAHA_API_URL", "https://waha-8vbc.onrender.com").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

# --- YAHAN HUMNE ERROR THEEK KIYA HAI ---
try:
    with open("last_update_id.txt", "r") as f:
        content = f.read().strip()
        # Agar file khali hai, toh crash mat ho, use 0 maan lo
        last_update_id = int(content) if content else 0
except FileNotFoundError:
    last_update_id = 0
# ----------------------------------------

# Telegram se naye messages lana
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

# Naye WAHA Server ke liye Headers
waha_headers = {
    "X-Api-Key": WAHA_API_KEY,  # Whapi ke 'Bearer' token ki jagah WAHA ki API Key
    "Accept": "application/json",
    "Content-Type": "application/json"
}

if response.get("ok"):
    for result in response["result"]:
        update_id = result["update_id"]
        last_update_id = max(last_update_id, update_id)
        
        # Channel post ya normal message dono handle karne ke liye
        message = result.get("channel_post") or result.get("message")
        if not message:
            continue

        # HAR GROUP/CHAT KE LIYE LOOP CHALANA
        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            if not chat_id:
                continue

            # 1. Agar TEXT message hai
            if "text" in message:
                payload = {
                    "chatId": chat_id,
                    "text": message["text"],
                    "session": "default"
                }
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=waha_headers, json=payload)

            # 2. Agar PHOTO hai
            elif "photo" in message:
                photo = message["photo"][-1]
                file_id = photo["file_id"]
                caption = message.get("caption", "")
                
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                if file_res["ok"]:
                    file_path = file_res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    payload = {
                        "chatId": chat_id,
                        "file": {"url": download_url},
                        "caption": caption,
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendFile", headers=waha_headers, json=payload)

            # 3. Agar PDF/DOCUMENT hai
            elif "document" in message:
                document = message["document"]
                file_id = document["file_id"]
                file_name = document.get("file_name", "document.pdf")
                caption = message.get("caption", "")
                
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                if file_res["ok"]:
                    file_path = file_res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    payload = {
                        "chatId": chat_id,
                        "file": {
                            "url": download_url,
                            "filename": file_name
                        },
                        "caption": caption,
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendFile", headers=waha_headers, json=payload)

    # Naye update ID ko save karna (taaki next time khali na rahe)
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
