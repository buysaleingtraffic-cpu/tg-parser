import os
import requests
from telethon import TelegramClient, events

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Твои 10 каналов (укажи без знака @)
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

  # Определяем тип медиа, если оно есть
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
