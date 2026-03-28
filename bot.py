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
    for result in response["result"]:
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
                payload = {
                    "chatId": chat_id,
                    "text": message["text"],
                    "session": "default"
                }
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=waha_headers, json=payload)

            # 2. PHOTO MESSAGE
            elif "photo" in message:
                photo = message["photo"][-1] # Sabse high quality wali photo
                file_id = photo["file_id"]
                caption = message.get("caption", "")
                
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                if file_res["ok"]:
                    file_path = file_res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    payload = {
                        "chatId": chat_id,
                        "file": {
                            "url": download_url,
                            "mimetype": "image/jpeg"
                        },
                        "caption": caption,
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendImage", headers=waha_headers, json=payload)

            # 3. DOCUMENT / PDF MESSAGE
            elif "document" in message:
                document = message["document"]
                file_id = document["file_id"]
                file_name = document.get("file_name", "document.file")
                mime_type = document.get("mime_type", "application/octet-stream")
                caption = message.get("caption", "")
                
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                if file_res["ok"]:
                    file_path = file_res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    payload = {
                        "chatId": chat_id,
                        "file": {
                            "url": download_url,
                            "filename": file_name,
                            "mimetype": mime_type
                        },
                        "caption": caption,
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendFile", headers=waha_headers, json=payload)

            # 4. VIDEO MESSAGE
            elif "video" in message:
                video = message["video"]
                file_id = video["file_id"]
                file_name = video.get("file_name", "video.mp4")
                mime_type = video.get("mime_type", "video/mp4")
                caption = message.get("caption", "")
                
                file_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
                if file_res["ok"]:
                    file_path = file_res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    payload = {
                        "chatId": chat_id,
                        "file": {
                            "url": download_url,
                            "filename": file_name,
                            "mimetype": mime_type
                        },
                        "caption": caption,
                        "session": "default"
                    }
                    requests.post(f"{WAHA_API_URL}/api/sendFile", headers=waha_headers, json=payload)

    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
