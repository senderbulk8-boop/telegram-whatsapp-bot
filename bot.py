import os
import requests
import base64

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

# JSON के लिए पक्के Headers
json_headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}

if response.get("ok"):
    for result in response["result"]:
        last_update_id = max(last_update_id, result["update_id"])
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            
            # ==========================================
            # A. सिर्फ टेक्स्ट मैसेज (यह पहले से मक्खन चल रहा है)
            # ==========================================
            if "text" in msg and "photo" not in msg and "document" not in msg:
                payload = {"chatId": chat_id, "text": msg["text"], "session": "default"}
                res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=json_headers, json=payload)
                print(f"Text sent to {chat_id}: {res.status_code}")

            # ==========================================
            # B. फोटो और डॉक्यूमेंट (JSON + Base64 + Smart Caption)
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
                        print(f"Downloading {file_name} from Telegram...")
                        downloaded_file = requests.get(d_url).content
                        encoded_data = base64.b64encode(downloaded_file).decode('utf-8')
                        
                        # शुद्ध JSON पेलोड (बिना कैप्शन के)
                        payload = {
                            "chatId": chat_id,
                            "session": "default",
                            "file": {
                                "mimetype": mime_type,
                                "filename": file_name,
                                "data": encoded_data
                            }
                        }
                        
                        # स्मार्ट लॉजिक: अगर कैप्शन सच में लिखा है, तभी पेलोड में डालें
                        caption_text = msg.get("caption")
                        if caption_text:
                            payload["caption"] = caption_text
                        
                        print(f"Sending {file_name} to WAHA ({endpoint})...")
                        res = requests.post(f"{WAHA_API_URL}/api/{endpoint}", headers=json_headers, json=payload)
                        
                        # अब एरर छुप नहीं पाएगा!
                        print(f"[{endpoint}] to {chat_id}: Status {res.status_code} | Response: {res.text}")
                        
                    except Exception as e:
                        print(f"Error sending file: {e}")

    # आख़िरी अपडेट ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
