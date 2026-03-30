import os
import requests

# ==========================================
# 1. आपके सीक्रेट टोकन
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GREENAPI_ID = os.environ.get("GREENAPI_ID")        
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")  
WHATSAPP_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",") 

# आपका असली GreenAPI सर्वर (Host) URL जो आपने अभी बताया
GREENAPI_HOST = "https://7107.api.greenapi.com"

try:
    with open("last_update_id.txt", "r") as f:
        last_update_id = int(f.read().strip() or 0)
except:
    last_update_id = 0

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

if response.get("ok"):
    for result in response["result"]:
        last_update_id = max(last_update_id, result["update_id"])
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WHATSAPP_CHAT_IDS:
            chat_id = chat_id.strip()
            if not chat_id: continue
            
            # सही सर्वर और ID को जोड़ना
            greenapi_base_url = f"{GREENAPI_HOST}/waInstance{GREENAPI_ID}"

            # ==========================================
            # A. सिर्फ टेक्स्ट मैसेज
            # ==========================================
            if "text" in msg and "photo" not in msg and "document" not in msg:
                url = f"{greenapi_base_url}/sendMessage/{GREENAPI_TOKEN}"
                payload = {"chatId": chat_id, "message": msg["text"]}
                res = requests.post(url, json=payload)
                print(f"Text sent to {chat_id}: Status {res.status_code} | {res.text}")

            # ==========================================
            # B. फोटो और डॉक्यूमेंट (PDF) भेजना
            # ==========================================
            elif "photo" in msg or "document" in msg:
                file_obj = None
                file_name = ""

                if "photo" in msg:
                    file_obj = msg["photo"][-1]
                    file_name = "Positron_Update.jpg"
                elif "document" in msg:
                    file_obj = msg["document"]
                    file_name = file_obj.get("file_name", "Positron_Notes.pdf")

                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    try:
                        url = f"{greenapi_base_url}/sendFileByUrl/{GREENAPI_TOKEN}"
                        payload = {
                            "chatId": chat_id,
                            "urlFile": d_url,
                            "fileName": file_name,
                            "caption": msg.get("caption", "") 
                        }
                        res = requests.post(url, json=payload)
                        print(f"File sent to {chat_id}: Status {res.status_code} | {res.text}")
                    except Exception as e:
                        print(f"Error sending file: {e}")

    # आख़िरी अपडेट ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
