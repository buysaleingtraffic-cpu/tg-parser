import os
import asyncio
import threading
import http.server
import socketserver
import requests
from collections import defaultdict
from telethon import TelegramClient, events, types

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

# Буферы для склейки альбомов
album_buffers = defaultdict(list)
album_timers = {}

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    message = event.message
    chat_title = event.chat.title if event.chat else ""

    # --- Обработка АЛЬБОМОВ (группы медиа) ---
    if message.grouped_id:
        group_id = str(message.grouped_id)

        file_id = None
        media_type = None
        
        if message.photo:
            media_type = "photo"
            file_id = pack_bot_file_id(message.photo)
        elif message.video:
            media_type = "video"
            file_id = pack_bot_file_id(message.video)

        if file_id:
            album_buffers[group_id].append({
                "file_id": file_id,
                "media_type": media_type, # Сохраняем тип каждого конкретного файла (photo/video)
                "text": message.text or message.raw_text or ""
            })

        if group_id in album_timers:
            album_timers[group_id].cancel()

        async def send_album_later(g_id, c_id, c_title, m_date, m_id):
            await asyncio.sleep(3.0)  # Ждем сбора всех файлов альбома
            items = album_buffers.pop(g_id, [])
            if not items:
                return

            combined_text = next((i["text"] for i in items if i["text"].strip()), "")
            
            # Собираем массив объектов с id и реальным типом медиа для каждого файла
            file_items = [{"file_id": i["file_id"], "media_type": i["media_type"]} for i in items if i["file_id"]]
            
            if not file_items:
                return

            payload = {
                "chat_id": str(c_id),
                "chat_title": c_title,
                "message_id": str(m_id),
                "text": combined_text,
                "date": str(m_date),
                "media_type": "album",
                "album_files": file_items, # Передаем детальный массив объектов
            }

            try:
                requests.post(WEBHOOK_URL, json=payload)
                print(f"Альбом из {c_title} ({len(file_items)} файлов) отправлен в Activepieces.")
            except Exception as e:
                print(f"Ошибка отправки альбома в вебхук: {e}")

        album_timers[group_id] = asyncio.create_task(
            send_album_later(group_id, event.chat_id, chat_title, message.date, message.id)
        )
        return

    # --- Обработка ОДИНОЧНЫХ сообщений ---
    file_id = None
    media_type = None

    if message.photo:
        media_type = "photo"
        file_id = pack_bot_file_id(message.photo)
    elif message.video:
        media_type = "video"
        file_id = pack_bot_file_id(message.video)
    elif message.document:
        media_type = "document"
        file_id = pack_bot_file_id(message.document)

    text_content = message.text or message.raw_text or ""

    payload = {
        "chat_id": str(event.chat_id),
        "chat_title": chat_title,
        "message_id": str(message.id),
        "text": text_content,
        "date": str(message.date),
        "media_type": media_type or "",
        "file_id": file_id or "",
    }

    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {payload['chat_title']} успешно отправлен.")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def pack_bot_file_id(media):
    try:
        if isinstance(media, types.Photo):
            return media.id
        elif isinstance(media, types.Document):
            return media.id
        return None
    except Exception:
        return None

print("Парсер запущен и слушает каналы...")
client.start()
client.run_until_disconnected()
