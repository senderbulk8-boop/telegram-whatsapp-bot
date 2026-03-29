import os
import requests

# ==========================================
# 1. आपके सीक्रेट टोकन और सेटिंग्स
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY", "")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

try:
    with open("last_update_id.txt", "r") as f:
        last_update_id = int(f.read().strip() or 0)
except:
    last_update_id = 0

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

# सिर्फ टेक्स्ट मैसेज के लिए Headers
json_headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}
# फाइल भेजने के लिए Headers (इसमें Content-Type की ज़रूरत नहीं होती)
file_headers = {"X-Api-Key": WAHA_API_KEY}

if response.get("ok"):
    for result in response["result"]:
        last_update_id = max(last_update_id, result["update_id"])
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            
            # ==========================================
            # A. सिर्फ टेक्स्ट मैसेज (यह एकदम सही चल रहा है)
            # ==========================================
            if "text" in msg and "photo" not in msg and "document" not in msg:
                payload = {"chatId": chat_id, "text": msg["text"], "session": "default"}
                res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=json_headers, json=payload)
                print(f"Text sent: {res.status_code}")

            # ==========================================
            # B. ब्रह्मास्त्र: फाइल को पहले GitHub में डाउनलोड करना, फिर WAHA को असली फाइल देना
            # ==========================================
            elif "photo" in msg or "document" in msg:
                file_obj = None
                mime_type = ""
                file_name = ""
                endpoint = ""

                if "photo" in msg:
                    file_obj = msg["photo"][-1]
                    mime_type = "image/jpeg"
                    file_name = "Positron_Update.jpg"
                    endpoint = "sendImage"
                elif "document" in msg:
                    file_obj = msg["document"]
                    mime_type = file_obj.get("mime_type", "application/pdf")
                    file_name = file_obj.get("file_name", "Positron_Notes.pdf")
                    endpoint = "sendFile"

                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    try:
                        # 1. टेलीग्राम से असली फाइल को GitHub सर्वर की मेमोरी में डाउनलोड करना
                        print(f"Downloading {file_name} from Telegram...")
                        downloaded_file = requests.get(d_url).content
                        
                        # 2. WAHA को 'Multipart Form-Data' के ज़रिए असली फाइल भेजना
                        data_payload = {
                            "chatId": chat_id,
                            "session": "default",
                            "caption": msg.get("caption", "")
                        }
                        
                        files_payload = {
                            "file": (file_name, downloaded_file, mime_type)
                        }
                        
                        print(f"Uploading {file_name} to WAHA Render Server...")
                        res = requests.post(
                            f"{WAHA_API_URL}/api/{endpoint}", 
                            headers=file_headers, 
                            data=data_payload, 
                            files=files_payload
                        )
                        print(f"[{endpoint}] sent to {chat_id}: Status {res.status_code}")
                        
                    except Exception as e:
                        print(f"Error sending file: {e}")

    # आख़िरी अपडेट ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
