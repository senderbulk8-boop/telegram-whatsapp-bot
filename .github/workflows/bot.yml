import os
import requests

# 1. कॉन्फ़िगरेशन
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WAHA_API_URL = os.environ.get("WAHA_API_URL", "").rstrip("/")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY")
WAHA_CHAT_IDS = os.environ.get("WAHA_CHAT_ID", "").split(",")

# 2. पिछला मैसेज ट्रैक करने के लिए फाइल
try:
    with open("last_update_id.txt", "r") as f:
        content = f.read().strip()
        last_update_id = int(content) if content else 0
except:
    last_update_id = 0

print(f"--- बॉट शुरू हो रहा है (Last ID: {last_update_id}) ---")

# 3. टेलीग्राम से नए मैसेज लाओ
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
try:
    response = requests.get(telegram_url).json()
except Exception as e:
    print(f"❌ टेलीग्राम से कनेक्ट नहीं हो पाए: {e}")
    exit()

# 4. WAHA के लिए हेडर्स
headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}

if response.get("ok"):
    updates = response["result"]
    print(f"📩 टेलीग्राम पर {len(updates)} नए मैसेज मिले।")
    
    for result in updates:
        update_id = result["update_id"]
        last_update_id = max(last_update_id, update_id)
        
        msg = result.get("channel_post") or result.get("message")
        if not msg: continue

        for chat_id in WAHA_CHAT_IDS:
            chat_id = chat_id.strip()
            
            # --- टेक्स्ट मैसेज के लिए ---
            if "text" in msg:
                print(f"📝 टेक्स्ट मैसेज भेज रहे हैं: {chat_id}")
                res = requests.post(f"{WAHA_API_URL}/api/sendText", headers=headers, json={
                    "chatId": chat_id, "text": msg["text"], "session": "default"
                })
                print(f"   उत्तर: {res.status_code} - {res.text}")
            
            # --- फोटो, डॉक्यूमेंट या वीडियो के लिए ---
            media_type = "photo" if "photo" in msg else ("document" if "document" in msg else ("video" if "video" in msg else None))
            
            if media_type:
                print(f"🖼️ {media_type.upper()} मिल गया, व्हाट्सएप पर भेज रहे हैं: {chat_id}")
                file_obj = msg[media_type][-1] if media_type == "photo" else msg[media_type]
                
                f_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_obj['file_id']}").json()
                
                if f_res["ok"]:
                    d_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{f_res['result']['file_path']}"
                    payload = {
                        "chatId": chat_id,
                        "file": {"url": d_url, "filename": f_res['result']['file_path'].split('/')[-1]},
                        "caption": msg.get("caption", ""),
                        "session": "default"
                    }
                    res = requests.post(f"{WAHA_API_URL}/api/sendFile", headers=headers, json=payload)
                    print(f"   मीडिया उत्तर: {res.status_code} - {res.text}")
                else:
                    print("   ❌ टेलीग्राम से फाइल डाउनलोड करने में गलती हुई।")

    # अगली बार के लिए ID सेव करें
    with open("last_update_id.txt", "w") as f:
        f.write(str(last_update_id))
    print(f"--- काम पूरा हुआ (New Last ID: {last_update_id}) ---")
else:
    print("❌ टेलीग्राम API ने एरर दिया। टोकन चेक करें।")
