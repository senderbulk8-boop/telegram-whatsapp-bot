import os
import requests

# GitHub Secrets se Tokens uthana
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WHAPI_TOKEN = os.environ.get("WHAPI_TOKEN")
# Yahan humne comma se IDs ko alag karke ek List bana li hai
WHAPI_GROUP_IDS = os.environ.get("WHAPI_GROUP_ID", "").split(",")

# Pichla padha hua message ID nikalna
try:
    with open("last_update_id.txt", "r") as f:
        last_update_id = int(f.read().strip())
except FileNotFoundError:
    last_update_id = 0

# Telegram se naye messages lana
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

whapi_headers = {
    "Authorization": f"Bearer {WHAPI_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

if response.get("ok"):
    for result in response["result"]:
        update_id = result["update_id"]
        last_update_id = max(last_update_id, update_id)
        
        message = result.get("channel_post")
        if not message:
            continue

        # HAR GROUP KE LIYE LOOP CHALANA
        for group_id in WHAPI_GROUP_IDS:
            group_id = group_id.strip() # Faltu space hatane ke liye
            if not group_id:
                continue

            # 1. Agar TEXT message hai
            if "text" in message:
                payload = {
                    "to": group_id,
                    "body": message["text"]
                }
                requests.post("https://gate.whapi.cloud/messages/text", headers=whapi_headers, json=payload)

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
                        "to": group_id,
                        "media": download_url,
                        "caption": caption
                    }
                    requests.post("https://gate.whapi.cloud/messages/image", headers=whapi_headers, json=payload)

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
                        "to": group_id,
                        "media": download_url,
                        "caption": caption,
                        "filename": file_name
                    }
                    requests.post("https://gate.whapi.cloud/messages/document", headers=whapi_headers, json=payload)

    # Naye update ID ko save karna
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
