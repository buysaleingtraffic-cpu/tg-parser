{\rtf1\ansi\ansicpg1251\cocoartf2868
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import os\
import requests\
from telethon import TelegramClient, events\
\
# \uc0\u1044 \u1072 \u1085 \u1085 \u1099 \u1077  \u1073 \u1077 \u1088 \u1091 \u1090 \u1089 \u1103  \u1080 \u1079  \u1085 \u1072 \u1089 \u1090 \u1088 \u1086 \u1077 \u1082  Render (\u1073 \u1077 \u1079 \u1086 \u1087 \u1072 \u1089 \u1085 \u1086 )\
API_ID = int(os.environ.get("API_ID", 0))\
API_HASH = os.environ.get("API_HASH", "")\
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")\
\
# \uc0\u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1090 \u1074 \u1086 \u1080 \u1093  5 \u1082 \u1072 \u1085 \u1072 \u1083 \u1086 \u1074 \
TARGET_CHANNELS = [\
    "channel_username_1",\
    "channel_username_2",\
    "channel_username_3",\
    "channel_username_4",\
    "channel_username_5",\
]\
\
client = TelegramClient("morzen_parser_session", API_ID, API_HASH)\
\
\
@client.on(events.NewMessage(chats=TARGET_CHANNELS))\
async def handler(event):\
  message = event.message\
  payload = \{\
      "chat_id": event.chat_id,\
      "chat_title": event.chat.title if event.chat else "",\
      "message_id": message.id,\
      "text": message.text or "",\
      "date": str(message.date),\
      "has_media": message.media is not None,\
  \}\
  try:\
    requests.post(WEBHOOK_URL, json=payload)\
  except Exception as e:\
    print(f"\uc0\u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1082 \u1080 : \{e\}")\
\
\
print("\uc0\u1055 \u1072 \u1088 \u1089 \u1077 \u1088  \u1079 \u1072 \u1087 \u1091 \u1097 \u1077 \u1085 ...")\
client.start()\
client.run_until_disconnected()}