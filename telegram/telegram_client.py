import os
import json
import asyncio
import mimetypes
from telethon import TelegramClient, events
import requests

# Load config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "config", "telegram_config.json"), "r", encoding="utf-8") as f:
    TG_CONF = json.load(f)

API_ID = TG_CONF["api_id"]
API_HASH = TG_CONF["api_hash"]
GROUP = TG_CONF["group"]  # Group title or chat ID
KEYWORDS = [k.lower() for k in TG_CONF.get("keywords", [])]

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# WhatsApp bridge endpoint (local only)
BRIDGE_TEXT_URL = "http://127.0.0.1:3000/send-text"
BRIDGE_FILE_URL = "http://127.0.0.1:3000/send-file"

client = TelegramClient(os.path.join(BASE_DIR, "config", "tg_session"), API_ID, API_HASH)

def is_job_related(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in KEYWORDS)

def is_allowed_document(mime: str, filename: str) -> bool:
    # Allowed extensions
    allowed_ext = (".xlsx", ".xls", ".csv", ".pdf", ".docx", ".doc")
    if filename and filename.lower().endswith(allowed_ext):
        return True
    # Fallback on mime if available
    allowed_mime_prefixes = ("application/", "text/")
    return bool(mime and (mime.startswith(allowed_mime_prefixes)))

async def send_text_to_bridge(text: str):
    try:
        resp = requests.post(BRIDGE_TEXT_URL, json={"text": text}, timeout=10)
        resp.raise_for_status()
        print(f"[Bridge] Text forwarded OK to {BRIDGE_TEXT_URL}")
    except Exception as e:
        print(f"[Bridge] Failed to forward text to {BRIDGE_TEXT_URL}: {e}")

async def send_file_to_bridge(path: str, filename: str):
    try:
        # Ensure absolute path
        abspath = os.path.abspath(path)
        payload = {"path": abspath, "filename": filename}
        resp = requests.post(BRIDGE_FILE_URL, json=payload, timeout=20)
        resp.raise_for_status()
        print(f"[Bridge] File forwarded OK: {abspath} to {BRIDGE_FILE_URL}")
    except Exception as e:
        print(f"[Bridge] Failed to forward file to {BRIDGE_FILE_URL}: {e}")

@client.on(events.NewMessage())
async def on_new_message(event):
    try:
        # Debug: Log all incoming message events with detailed context
        print(f"[TG] New message event triggered - Chat ID: {event.chat_id}, Peer ID: {event.peer_id}, "
              f"Message ID: {event.message.id}, Date: {event.message.date}")

        # Filter for messages from the target group
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", None)
        chat_id = getattr(chat, "id", None)

        print(f"[TG] Message from chat: title={chat_title}, id={chat_id}, Target: {GROUP}")

        # Check if the message is from the target group
        if not (chat_title == GROUP or str(chat_id) == GROUP):
            print(f"[TG] Skipping message, not from {GROUP}")
            return  # Skip if not from the target group

        msg_text = event.message.message or ""
        print(f"[TG] Received from {chat_title or chat_id}: {msg_text[:120]}")

        # Forward job-related text
        if is_job_related(msg_text):
            print(f"[TG] Job text matched: {msg_text[:120]}")
            await send_text_to_bridge(msg_text)
        else:
            print(f"[TG] No job keywords matched in: {msg_text[:120]}")

        # Handle documents/media
        if event.message.media:
            filename = None
            try:
                if event.message.file and event.message.file.name:
                    filename = event.message.file.name
            except Exception:
                filename = None
            mime, _ = mimetypes.guess_type(filename or "")
            if not filename:
                filename = "file"
            if is_allowed_document(mime, filename):
                saved_path = await event.download_media(file=DOWNLOAD_DIR)
                print(f"[TG] Downloaded file: {saved_path}")
                await send_file_to_bridge(saved_path, os.path.basename(saved_path))
            else:
                print(f"[TG] Skipped unsupported media: {filename}")

    except Exception as e:
        print(f"[TG] Error processing message: {e}")

async def main():
    # Resolve group entity for efficient listening
    try:
        entity = await client.get_entity(GROUP)
        client.add_event_handler(on_new_message, events.NewMessage(chats=entity))
        print(f"[TG] Listening to: {GROUP}")
    except Exception as e:
        print(f"[TG] Warning: could not resolve '{GROUP}' precisely ({e}). Listening globally and filtering by group details.")

    print("[TG] Running. Press Ctrl+C to stop.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.start()  # will prompt for phone & code on first run
    with client:
        client.loop.run_until_complete(main())