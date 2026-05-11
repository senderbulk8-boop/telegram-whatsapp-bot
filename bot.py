import os
import requests
import re

# Tokens and Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
REPLACEMENT_USERNAME = "@KapilRJ06"

# WhatsApp recipients (CHATS_1 variable se uthayega)
CHATS_STR = os.environ.get("CHATS_1", "").strip()

def replace_usernames(text):
    if not text:
        return text
    return re.sub(r"@\w+", REPLACEMENT_USERNAME, text)

def send_meta_whatsapp(to_number, message_text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number.strip(),
        "type": "text",
        "text": {"body": message_text}
    }
    try:
        res = requests.post(url, json=payload, headers=headers)
        print(f"WhatsApp sent to {to_number}: Status {res.status_code}")
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")

# Load Last Update ID
try:
    with open("last_update_id.txt", "r", encoding="utf-8") as f:
        last_update_id = int(f.read().strip() or 0)
except:
    last_update_id = 0

# Get Telegram Updates
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
response = requests.get(telegram_url).json()

if response.get("ok") and CHATS_STR:
    chat_ids = CHATS_STR.split(",")
    
    for result in response["result"]:
        last_update_id = max(last_update_id, result["update_id"])
        msg = result.get("channel_post") or result.get("message")
        
        if not msg:
            continue

        # Extract Text or Caption
        original_text = msg.get("text") or msg.get("caption") or ""
        updated_text = replace_usernames(original_text)

        if updated_text:
            for chat_id in chat_ids:
                send_meta_whatsapp(chat_id, updated_text)

    # Save Last Update ID
    with open("last_update_id.txt", "w", encoding="utf-8") as f:
        f.write(str(last_update_id))
