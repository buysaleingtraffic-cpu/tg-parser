import os
import requests
from telethon import TelegramClient, events

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

TARGET_CHANNELS = [
    "channel_username_1",
    "channel_username_2",
    "channel_username_3",
    "channel_username_4",
    "channel_username_5",
]

client = TelegramClient("morzen_parser_session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    message = event.message
    payload = {
        "chat_id": event.chat_id,
        "chat_title": event.chat.title if event.chat else "",
        "message_id": message.id,
        "text": message.text or "",
        "date": str(message.date),
        "has_media": message.media is not None,
    }
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

print("Парсер запущен...")
client.start()
client.run_until_disconnected()
