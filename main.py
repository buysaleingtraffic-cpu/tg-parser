import os
import threading
import http.server
import socketserver
import requests
from telethon import TelegramClient, events

# Настройка веб-сервера для Render (чтобы проходил тест портов)
PORT = int(os.environ.get("PORT", 10000))

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        print(f"Web server started on port {PORT}")
        httpd.serve_forever()

# Запускаем веб-сервер в фоновом потоке
threading.Thread(target=run_web_server, daemon=True).start()

# Основной парсер Telegram
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
    if message.photo:
        media_type = "photo"
    elif message.video:
        media_type = "video"
    elif message.document:
        media_type = "document"

    payload = {
        "chat_id": event.chat_id,
        "chat_title": event.chat.title if event.chat else "",
        "message_id": message.id,
        "text": message.text or message.raw_text or "",
        "date": str(message.date),
        "media_type": media_type,
    }

    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {payload['chat_title']} успешно отправлен.")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

print("Парсер запущен и слушает каналы...")
client.start()
client.run_until_disconnected()
