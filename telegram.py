import os

import requests, json
from dotenv import load_dotenv

load_dotenv()
def handle_attach(attach: dict) -> str:
    match attach["_type"]:
        case "FILE":
            return attach["name"]
        case _:
            return attach["_type"]

def send_to_telegram(
        TG_BOT_TOKEN: str="",
        TG_CHAT_ID: int = 0,
        caption: str = "",
        attachments: list[dict] = [],
        TG_TOPIC_ID: int = os.getenv("TG_TOPIC_ID")
    ):

    # -----------------------------
    # 1) Отправка обычного текста
    # -----------------------------
    if not attachments:
        if caption == "":
            return
        api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": caption,
            "parse_mode": "HTML"
        }
        if TG_TOPIC_ID is not None:
            payload["message_thread_id"] = TG_TOPIC_ID

        resp = requests.post(api_url, data=payload)
        print(resp.json())
        return

    # -----------------------------
    # 2) Отправка альбома (до 10 фото)
    # -----------------------------
    if 1 <= len(attachments) <= 10:
        api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup"
        media = []
        not_handled_attachs = attachments.copy()

        for i, attach in enumerate(attachments):
            if attach["_type"] == "PHOTO":
                item = {"type": "photo", "media": attach["baseUrl"]}
                not_handled_attachs.remove(attach)
                if i == 0 and caption:
                    item["caption"] = caption
                    item["parse_mode"] = "HTML"
                media.append(item)

        if not_handled_attachs:
            if media:
                media[0]["caption"] += (
                    "\n\nНеобработанные файлы: " +
                    ', '.join(handle_attach(a) for a in not_handled_attachs)
                )
            else:
                send_to_telegram(
                    TG_BOT_TOKEN, TG_CHAT_ID,
                    caption + "\n\nНеобработанные файлы: " +
                    ', '.join(handle_attach(a) for a in not_handled_attachs),
                    TG_TOPIC_ID=TG_TOPIC_ID,
                )
                return

        payload = {
            "chat_id": TG_CHAT_ID,
            "media": json.dumps(media)
        }
        if TG_TOPIC_ID is not None:
            payload["message_thread_id"] = TG_TOPIC_ID

        resp = requests.post(api_url, data=payload)
        print(resp.json())
        return

    # -----------------------------
    # 3) Если фото > 10 — разбиваем
    # -----------------------------
    for i in range(0, len(attachments), 10):
        chunk = attachments[i:i+10]
        send_to_telegram(
            TG_BOT_TOKEN, TG_CHAT_ID,
            caption if i == 0 else "",
            chunk,
            TG_TOPIC_ID=TG_TOPIC_ID
        )
