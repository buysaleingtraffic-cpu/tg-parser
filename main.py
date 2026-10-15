import os
import asyncio
import threading
import http.server
import socketserver
import requests
from collections import defaultdict
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

# Буферы для склейки альбомов
album_buffers = defaultdict(list)
album_timers = {}

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    message = event.message
    chat_title = event.chat.title if event.chat else ""

    # Обработка альбомов (сообщений с несколькими фото/видео)
    if message.grouped_id:
        group_id = str(message.grouped_id)

        file_path = None
        media_type = None
        if message.photo:
            media_type = "photo"
            file_path = await message.download_media(file="downloads/")
        elif message.video:
            media_type = "video"
            file_path = await message.download_media(file="downloads/")

        album_buffers[group_id].append({
            "file_path": file_path,
            "media_type": media_type,
            "text": message.text or message.raw_text or ""
        })

        if group_id in album_timers:
            album_timers[group_id].cancel()

        async def send_album_later(g_id, c_id, c_title, m_date, m_id):
            await asyncio.sleep(2.5)  # Ждем 2.5 секунды дозагрузки всех файлов альбома
            items = album_buffers.pop(g_id, [])
            if not items:
                return

            # Ищем подпись к альбому среди всех сообщений группы
            combined_text = next((i["text"] for i in items if i["text"].strip()), "")
            
            # Если в альбоме вообще нет текста — пропускаем, чтобы не генерировать спам
            if not combined_text.strip():
                for item in items:
                    if item["file_path"] and os.path.exists(item["file_path"]):
                        os.remove(item["file_path"])
                return

            first_item = next((i for i in items if i["file_path"]), None)
            first_file = first_item["file_path"] if first_item else None
            first_media = first_item["media_type"] if first_item else "photo"

            payload = {
                "chat_id": str(c_id),
                "chat_title": c_title,
                "message_id": str(m_id),
                "text": combined_text,
                "date": str(m_date),
                "media_type": first_media,
            }

            try:
                if first_file and os.path.exists(first_file):
                    with open(first_file, "rb") as f:
                        files = {"file": f}
                        requests.post(WEBHOOK_URL, data=payload, files=files)
                else:
                    requests.post(WEBHOOK_URL, json=payload)
                print(f"Альбом из {c_title} обработан как 1 пост.")
            except Exception as e:
                print(f"Ошибка отправки альбома: {e}")
            finally:
                # Очищаем временные файлы на сервере
                for item in items:
                    if item["file_path"] and os.path.exists(item["file_path"]):
                        os.remove(item["file_path"])

        album_timers[group_id] = asyncio.create_task(
            send_album_later(group_id, event.chat_id, chat_title, message.date, message.id)
        )
        return

    # Одиночные сообщения (без альбома)
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

    text_content = message.text or message.raw_text or ""

    payload = {
        "chat_id": str(event.chat_id),
        "chat_title": chat_title,
        "message_id": str(message.id),
        "text": text_content,
        "date": str(message.date),
        "media_type": media_type or "",
    }

    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                files = {"file": f}
                requests.post(WEBHOOK_URL, data=payload, files=files)
            os.remove(file_path)
        else:
            requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {payload['chat_title']} успешно отправлен.")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

print("Парсер запущен и слушает каналы...")
client.start()
client.run_until_disconnected()
