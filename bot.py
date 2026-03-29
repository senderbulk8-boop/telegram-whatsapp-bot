import os
import requests

# ==========================================
# 1. आपके सीक्रेट टोकन और सेटिंग्स
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY", "")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

# पिछले मैसेज का ID पढ़ना ताकि मैसेज रिपीट न हों
try:
    with open("last_update_id.txt", "r") as f:
        last_update_id = int(f.read().strip() or 0)
except:
    last_update_id = 0

# ==========================================
# 2. Telegram से नए मैसेज उठाना
# ==========================================
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
            
            # ==========================================
            # A. सिर्फ टेक्स्ट मैसेज भेजना
            # ==========================================
            if "text" in msg and "photo" not in msg and "document" not in msg:
                payload = {
                    "chatId": chat_id, 
                    "text": msg["text"], 
                    "session": "default"
                }
                res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json=payload)
                print(f"Text sent to {chat_id}: Status {res.status_code}")

            # ==========================================
            # B. फोटो और डॉक्यूमेंट (PDF) भेजना (Direct URL)
            # ==========================================
            elif "photo" in msg or "document" in msg:
                file_obj = None
                mime_type = ""
                file_name = ""
                endpoint = ""

                # तय करें कि यह फोटो है या डॉक्यूमेंट
                if "photo" in msg:
                    file_obj = msg["photo"][-1] # सबसे हाई-क्वालिटी फोटो
                    mime_type = "image/jpeg"
                    file_name = "Positron_Update.jpg"
                    endpoint = "sendImage"      # इमेज के लिए सही API
                elif "document" in msg:
                    file_obj = msg["document"]
                    mime_type = file_obj.get("mime_type", "application/pdf")
                    file_name = file_obj.get("file_name", "Positron_Notes.pdf")
                    endpoint = "sendFile"       # डॉक्यूमेंट के लिए सही API

                # टेलीग्राम से फाइल का डायरेक्ट लिंक (URL) मंगवाएं
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    try:
                        # WAHA को सीधा URL दें (सबसे फ़ास्ट तरीका)
                        payload = {
                            "chatId": chat_id,
                            "session": "default",
                            "caption": msg.get("caption", ""), # फोटो/PDF के नीचे का टेक्स्ट
                            "file": {
                                "mimetype": mime_type,
                                "filename": file_name,
                                "url": d_url  # सीधा टेलीग्राम का डाउनलोड लिंक
                            }
                        }
                        
                        # WAHA के सही API पर रिक्वेस्ट भेजें
                        res = requests.post(f"{WAHA_API_URL}/api/{endpoint}", headers=headers, json=payload)
                        print(f"[{endpoint}] sent to {chat_id}: Status {res.status_code}")
                        
                    except Exception as e:
                        print(f"Error sending file: {e}")

    # आख़िरी अपडेट ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
