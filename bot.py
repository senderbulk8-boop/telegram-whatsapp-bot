import os
import requests
import base64  # <-- जादुई Base64 लाइब्रेरी जोड़ दी गई है

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
            
            # ==========================================
            # 1. सिर्फ टेक्स्ट मैसेज (बिना फोटो/फाइल के)
            # ==========================================
            if "text" in msg and "photo" not in msg and "document" not in msg:
                requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={
                    "chatId": chat_id, "text": msg["text"], "session": "default"
                })

            # ==========================================
            # 2. फोटो और डॉक्यूमेंट (Base64 मास्टर स्ट्रोक)
            # ==========================================
            if "photo" in msg or "document" in msg:
                file_obj = None
                mime_type = ""
                file_name = ""

                # तय करें कि यह फोटो है या PDF डॉक्यूमेंट
                if "photo" in msg:
                    file_obj = msg["photo"][-1] # सबसे हाई-क्वालिटी वाली फोटो लें
                    mime_type = "image/jpeg"
                    file_name = "Positron_Update.jpg"
                elif "document" in msg:
                    file_obj = msg["document"]
                    mime_type = file_obj.get("mime_type", "application/pdf")
                    file_name = file_obj.get("file_name", "Positron_Notes.pdf")

                # टेलीग्राम से फाइल का रास्ता (Path) मंगवाएं
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res.get("ok"):
                    file_path = f_res['result']['file_path']
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                    
                    try:
                        # फाइल को टेलीग्राम से डाउनलोड करें
                        file_data = requests.get(d_url).content
                        
                        # असली जादू: फाइल को Base64 में पैक करें
                        encoded_data = base64.b64encode(file_data).decode('utf-8')
                        
                        # Render (NOWEB) को भेजने के लिए पैकेट तैयार करें
                        payload = {
                            "chatId": chat_id,
                            "session": "default",
                            "caption": msg.get("caption", ""), # अगर फोटो के नीचे कुछ लिखा है, तो वो भी जाएगा
                            "file": {
                                "mimetype": mime_type,
                                "filename": file_name,
                                "data": encoded_data
                            }
                        }
                        
                        # WAHA के sendFile API पर फायर करें!
                        res = requests.post(f"{WAHA_API_URL}/api/sendFile", headers=headers, json=payload)
                        print(f"File sent to {chat_id}: Status {res.status_code}")
                        
                    except Exception as e:
                        print(f"Error in Base64 processing/sending: {e}")

    # आख़िरी अपडेट ID सेव करें ताकि मैसेज रिपीट न हों
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
