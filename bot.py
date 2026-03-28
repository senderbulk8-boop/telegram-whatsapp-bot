import os
import requests

# GitHub Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "https://waha-8vbc.onrender.com").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

try:
    with open("last_update_id.txt", "r") as f:
        content = f.read().strip()
        last_update_id = int(content) if content else 0
except FileNotFoundError:
    last_update_id = 0

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

waha_headers = {
    "X-Api-Key": WAHA_API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

if response.get("ok"):
    messages = response.get("result", [])
    print(f"Found {len(messages)} new messages on Telegram.")
    
    for result in messages:
        update_id = result["update_id"]
        last_update_id = max(last_update_id, update_id)
        
        message = result.get("channel_post") or result.get("message")
        if not message:
            continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            if not chat_id:
                continue

            # 1. TEXT MESSAGE
            if "text" in message:
                payload = {"chatId": chat_id, "text": message["text"], "session": "default"}
                res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=waha_headers, json=payload)
                print(f"TEXT sent to {chat_id} | Response: {res.status_code} - {res.text}")

            # 2. PHOTO MESSAGE
            elif "photo" in message:
                photo = message["photo"][-1]
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={photo['file_id']}").json()
                if file_res["ok"]:
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_res['result']['file_path']}"
                    payload = {
                        "chatId": chat_id,
                        "file": {"url": download_url},
                        "caption": message.get("caption", ""),
                        "session": "default"
                    }
                    res = requests.post(f"{WAHA_API_URL}/api/sendImage", headers=waha_headers, json=payload)
                    print(f"PHOTO sent to {chat_id} | Response: {res.status_code} - {res.text}")

            # 3. DOCUMENT MESSAGE
            elif "document" in message:
                document = message["document"]
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={document['file_id']}").json()
                if file_res["ok"]:
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_res['result']['file_path']}"
                    payload = {
                        "chatId": chat_id,
                        "file": {"url": download_url, "filename": document.get("file_name", "document.pdf")},
                        "caption": message.get("caption", ""),
                        "session": "default"
                    }
                    res = requests.post(f"{WAHA_API_URL}/api/sendFile", headers=waha_headers, json=payload)
                    print(f"DOCUMENT sent to {chat_id} | Response: {res.status_code} - {res.text}")

    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
else:
    print("Telegram API Error:", response)
