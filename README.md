
# Telegram → WhatsApp Job Forwarder (Server-Ready)

This project forwards ONLY **job-related** messages and **documents** (Excel/CSV/PDF/Docs) from a Telegram group to a WhatsApp number using:
- **Telethon (Python)** for Telegram
- **Baileys (Node.js)** for WhatsApp (headless, no GUI)
- A local HTTP bridge (Express) to receive messages/files

## Features
- Filters messages by keywords: `job, hiring, opening, shortlist, shortlisted, interview, vacancy, walk-in, requirement`.
- Forwards text **and** documents (xlsx, xls, csv, pdf, docx, doc).
- Runs on a headless server (Linux/VPS). No browser automation.

---

## 1) Configuration

Edit `config/telegram_config.json`:
```json
{
  "api_id": 123456,
  "api_hash": "YOUR_API_HASH",
  "group": "YOUR_GROUP_USERNAME_OR_LINK",
  "keywords": ["job", "hiring", "opening", "shortlist", "shortlisted", "interview", "vacancy", "walk-in", "requirement"]
}
```

Edit `config/whatsapp_config.json`:
```json
{
  "recipient_number_msisdn": "917989316376"
}
```
> Use full international number without `+`. Example: India `91` + number.

---

## 2) Install Dependencies

### Python
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Node.js
```
npm install
```

---

## 3) Run

### Start WhatsApp bot (first time will show a QR code in the terminal)
```
node whatsapp/whatsapp_client.js
```
- Scan the QR using WhatsApp > Linked Devices.
- The session is saved in `whatsapp/auth_info/` and reused next time.

### Start Telegram listener
```
python telegram/telegram_client.py
```
- First run will ask your Telegram phone number and OTP in the terminal.

---

## 4) How it Works

1. `telegram/telegram_client.py` listens to the configured Telegram group.
2. It filters messages by keywords and downloads documents to `downloads/`.
3. It POSTs text or file path to the local Express server in `whatsapp/whatsapp_client.js`:
   - `POST /send-text` with `{ "text": "..." }`
   - `POST /send-file` with `{ "path": "/absolute/path/to/file", "filename": "doc.xlsx" }`
4. Baileys sends the text/file to your configured WhatsApp number.

---

## 5) Notes / Tips
- Ensure both processes run on the same machine so Node can access the downloaded file path.
- To forward to a **WhatsApp group**, replace the JID with your group JID (e.g., `1234567890-123456@g.us`). See code comments.
- To join **private Telegram groups**, your Telegram account must already be a member; otherwise, use an invite link manually to join first, then set `group` to the group's title/username/link.
- To run 24/7, use `pm2` (Node) and `systemd`/`tmux`/`screen` for Python.

---

## 6) Security
- Keep your `api_hash` private.
- The Express server listens on `127.0.0.1` by default. If you expose it, add auth.

---

## 7) Troubleshooting
- If WhatsApp sends fail: check the terminal where `whatsapp_client.js` runs for errors.
- If Telegram fetch fails: ensure `api_id`/`api_hash` are correct and the group value resolves.
- If files don't send: verify the absolute file path exists and Node has read permissions.

