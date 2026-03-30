import os
import requests

# टेलीग्राम टोकन
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()

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

        # हम 1 से लेकर 5 अकाउंट्स तक चेक करेंगे
        for i in range(1, 6):
            host = os.environ.get(f"GREENAPI_HOST_{i}", "").strip()
            api_id = os.environ.get(f"GREENAPI_ID_{i}", "").strip()
            api_token = os.environ.get(f"GREENAPI_TOKEN_{i}", "").strip()
            chat_ids_str = os.environ.get(f"CHATS_{i}", "").strip()

            # अगर किसी अकाउंट की चाबी नहीं मिली, तो उसे छोड़कर अगले पर जाएँ
            if not (host and api_id and api_token and chat_ids_str):
                continue

            chat_ids = chat_ids_str.split(",")
            greenapi_base_url = f"{host}/waInstance{api_id}"

            for chat_id in chat_ids:
                chat_id = chat_id.strip()
                if not chat_id: continue

                # ==========================================
                # A. सिर्फ टेक्स्ट मैसेज
                # ==========================================
                if "text" in msg and "photo" not in msg and "document" not in msg:
                    url = f"{greenapi_base_url}/sendMessage/{api_token}"
                    payload = {"chatId": chat_id, "message": msg["text"]}
                    res = requests.post(url, json=payload)
                    print(f"Text sent to {chat_id} (Acc {i}): Status {res.status_code}")

                # ==========================================
                # B. फोटो और डॉक्यूमेंट (PDF)
                # ==========================================
                elif "photo" in msg or "document" in msg:
                    file_obj = msg["photo"][-1] if "photo" in msg else msg["document"]
                    file_name = "Positron_Update.jpg" if "photo" in msg else file_obj.get("file_name", "Positron_Notes.pdf")

                    f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                    
                    if f_res.get("ok"):
                        file_path = f_res['result']['file_path']
                        d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                        
                        try:
                            url = f"{greenapi_base_url}/sendFileByUrl/{api_token}"
                            payload = {
                                "chatId": chat_id, "urlFile": d_url, "fileName": file_name, "caption": msg.get("caption", "") 
                            }
                            res = requests.post(url, json=payload)
                            print(f"File sent to {chat_id} (Acc {i}): Status {res.status_code}")
                        except Exception as e:
                            print(f"Error: {e}")

    # आख़िरी अपडेट ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
