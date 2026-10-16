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

# Веб-сервер на Render, который также раздает файлы из папки downloads
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)
    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active and running!")
        else:
            super().do_GET()

def run_web_server():
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
# Укажите в переменных окружения Render ваш публичный домен, например: https://morzen-parser.onrender.com
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

TARGET_CHANNELS = [
    "ggreat_of_development",
    "analizriska",
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

album_buffers = defaultdict(list)
album_timers = {}

async def delayed_cleanup(file_paths):
    await asyncio.sleep(60)  # Ждем минуту, пока Activepieces заберет файлы
    for fp in file_paths:
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except:
                pass

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    message = event.message
    chat_title = event.chat.title if event.chat else ""

    file_path = None
    media_type = "none"
    if message.photo:
        media_type = "photo"
        file_path = await message.download_media(file="downloads/")
    elif message.video:
        media_type = "video"
        file_path = await message.download_media(file="downloads/")
    elif message.document:
        media_type = "document"
        file_path = await message.download_media(file="downloads/")

    # Обработка альбомов
    if message.grouped_id:
        group_id = str(message.grouped_id)

        album_buffers[group_id].append({
            "file_path": file_path,
            "media_type": media_type,
            "text": message.text or message.raw_text or ""
        })

        if group_id in album_timers:
            album_timers[group_id].cancel()

        async def send_album_later(g_id, c_id, c_title, m_date, m_id):
            await asyncio.sleep(2.5)
            items = album_buffers.pop(g_id, [])
            if not items:
                return

            combined_text = next((i["text"] for i in items if i["text"].strip()), "")
            
            if not combined_text.strip():
                for item in items:
                    if item["file_path"] and os.path.exists(item["file_path"]):
                        os.remove(item["file_path"])
                return

            media_list = []
            for item in items:
                if item["file_path"] and os.path.exists(item["file_path"]):
                    filename = os.path.basename(item["file_path"])
                    file_url = f"{RENDER_EXTERNAL_URL}/downloads/{filename}" if RENDER_EXTERNAL_URL else f"/downloads/{filename}"
                    media_list.append({
                        "type": item["media_type"] if item["media_type"] in ["photo", "video"] else "photo",
                        "url": file_url
                    })

            payload = {
                "chat_id": str(c_id),
                "chat_title": c_title,
                "message_id": str(m_id),
                "text": combined_text,
                "date": str(m_date),
                "media_type": "album",
                "media_list": media_list
            }

            try:
                requests.post(WEBHOOK_URL, json=payload)
                print(f"Альбом из {c_title} ({len(media_list)} файлов) отправлен.")
            except Exception as e:
                print(f"Ошибка отправки альбома: {e}")
            finally:
                asyncio.create_task(delayed_cleanup([item["file_path"] for item in items if item["file_path"]]))

        album_timers[group_id] = asyncio.create_task(
            send_album_later(group_id, event.chat_id, chat_title, message.date, message.id)
        )
        return

    # Одиночные сообщения
    media_list = []
    if file_path and os.path.exists(file_path):
        filename = os.path.basename(file_path)
        file_url = f"{RENDER_EXTERNAL_URL}/downloads/{filename}" if RENDER_EXTERNAL_URL else f"/downloads/{filename}"
        media_list.append({
            "type": media_type if media_type in ["photo", "video", "document"] else "photo",
            "url": file_url
        })

    payload = {
        "chat_id": str(event.chat_id),
        "chat_title": chat_title,
        "message_id": str(message.id),
        "text": message.text or message.raw_text or "",
        "date": str(message.date),
        "media_type": media_type or "",
        "media_list": media_list
    }

    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {chat_title} успешно отправлен.")
        if file_path and os.path.exists(file_path):
            asyncio.create_task(delayed_cleanup([file_path]))
    except Exception as e:
        print(f"Ошибка отправки: {e}")

print("Парсер запущен и слушает каналы...")
client.start()
client.run_until_disconnected()
