import os
import asyncio
import threading
import http.server
import socketserver
import requests
from collections import defaultdict
from telethon import TelegramClient, events, types

# Папка downloads больше не нужна для альбомов, но оставим для одиночных файлов
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

    # --- Обработка АЛЬБОМОВ (группы медиа) ---
    if message.grouped_id:
        group_id = str(message.grouped_id)

        # Получаем file_id и тип медиа без скачивания
        file_id = None
        media_type = None
        
        if message.photo:
            media_type = "photo"
            # Достаем file_id самой большой версии фото
            file_id = pack_bot_file_id(message.photo)
        elif message.video:
            media_type = "video"
            file_id = pack_bot_file_id(message.video)

        if file_id:
            album_buffers[group_id].append({
                "file_id": file_id,
                "media_type": media_type,
                "text": message.text or message.raw_text or ""
            })

        # Перезапускаем таймер ожидания альбома
        if group_id in album_timers:
            album_timers[group_id].cancel()

        async def send_album_later(g_id, c_id, c_title, m_date, m_id):
            await asyncio.sleep(3.0)  # Ждем чуть дольше, чтобы все файлы собрались
            items = album_buffers.pop(g_id, [])
            if not items:
                return

            # Ищем подпись к альбому среди всех сообщений группы
            combined_text = next((i["text"] for i in items if i["text"].strip()), "")
            
            # Собираем список всех file_id для альбома
            file_ids = [i["file_id"] for i in items if i["file_id"]]
            
            if not file_ids:
                return # Нет медиафайлов

            payload = {
                "chat_id": str(c_id),
                "chat_title": c_title,
                "message_id": str(m_id),
                "text": combined_text,
                "date": str(m_date),
                "media_type": "album", # Указываем, что это альбом
                "album_files": file_ids, # Передаем массив file_id
            }

            try:
                # Всегда отправляем JSON, так как используем file_id
                requests.post(WEBHOOK_URL, json=payload)
                print(f"Альбом из {c_title} ({len(file_ids)} ф.) отправлен в Activepieces.")
            except Exception as e:
                print(f"Ошибка отправки альбома в вебхук: {e}")

        album_timers[group_id] = asyncio.create_task(
            send_album_later(group_id, event.chat_id, chat_title, message.date, message.id)
        )
        return

    # --- Обработка ОДИНОЧНЫХ сообщений ---
    # (Эта часть остается почти без изменений, но тоже переводим на file_id для скорости)
    
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
        "file_id": file_id or "", # Передаем file_id для одиночного файла
    }

    try:
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Пост из {payload['chat_title']} успешно отправлен.")
    except Exception as e:
        print(f"Ошибка отправки: {e}")


# --- Вспомогательная функция для получения file_id (совместимого с ботами) ---
def pack_bot_file_id(media):
    """Преобразует объект медиа Telethon в file_id, понятный Telegram Bot API"""
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
