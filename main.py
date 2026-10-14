import os
import threading
import http.server
import socketserver
import requests
from telethon import TelegramClient, events

os.makedirs("downloads", exist_ok=True)

PORT = int(os.environ.get("PORT", 10000))

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

TARGET_CHANNELS = [
    "ggreat_of_development",
    "CREconsultant",
    "belaya_kaska",
    "Jelezobetonniyzames",
    "dvizhenieru",
    "cool_construction",
    "domostroy_channel",
    "propertyinsider",
    "stroi_mos_ru",
    "developers_policy",
]

client = TelegramClient("morzen_parser_session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    message = event.message

    media_type = None
    file_path = None

    if message.photo:
        media_type = "photo"
        file_path = await message.download_media(file="downloads/")
    elif message.video:
        media_type = "video"
        file_path = await message.download_media(file="downloads/")
    elif message.document:
        media_type = "document"
        file_path = await message.download_media(file="downloads/")

    payload = {
        "chat_id": str(event.chat_id),
        "chat_title": event.chat.title if event.chat else "",
        "message_id": str(message.id),
        "text": message.text or message.raw_text or "",
        "date": str(message.date),
        "media_type": media_type or "",
    }

    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                files = {"file": f}
                requests.post(WEBHOOK_URL, data=payload, files=files)
            os.remove(file_path)  # Удаляем временный файл
        else:
            requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {payload['chat_title']} успешно отправлен.")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

print("Парсер запущен и слушает каналы...")
client.start()
client.run_until_disconnected()
