
import { makeWASocket, useMultiFileAuthState, Browsers } from '@whiskeysockets/baileys';
import express from "express";
import bodyParser from "body-parser";
import fs from "fs";
import path from "path";
import mime from "mime-types";
import qrcode from 'qrcode-terminal';

// Load config
const BASE_DIR = path.resolve(path.join(import.meta.dirname, ".."));
const waConfPath = path.join(BASE_DIR, "config", "whatsapp_config.json");
const waConf = JSON.parse(fs.readFileSync(waConfPath, "utf8"));
const RECIPIENTS = waConf.recipient_numbers_msisdn.map(num => `${num}@s.whatsapp.net`); // Array of JIDs

async function start() {
  const { state, saveCreds } = await useMultiFileAuthState(path.join(BASE_DIR, "whatsapp", "auth_info"));
  const sock = makeWASocket({
    auth: state,
    browser: Browsers.ubuntu("Chrome"),
    syncFullHistory: false,
  });

  sock.ev.on("creds.update", saveCreds);
  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    console.log("[WA] Connection:", connection || "", lastDisconnect?.error?.message || "");
    if (qr) {
      qrcode.generate(qr, { small: true });
    }
  });

  // Express server for bridge
  const app = express();
  app.use(bodyParser.json({ limit: "25mb" }));

  app.get("/", (req, res) => res.json({ ok: true, service: "whatsapp-bridge" }));

  // Send text to all recipients
  app.post("/send-text", async (req, res) => {
    try {
      const { text } = req.body || {};
      if (!text) return res.status(400).json({ error: "text required" });
      for (const recipient of RECIPIENTS) {
        await sock.sendMessage(recipient, { text });
        console.log(`[WA] Sent to ${recipient}`);
      }
      return res.json({ ok: true });
    } catch (e) {
      console.error("[WA] send-text error:", e);
      return res.status(500).json({ error: String(e) });
    }
  });

  // Send file by local filesystem path
  app.post("/send-file", async (req, res) => {
    try {
      const { path: filePath, filename } = req.body || {};
      if (!filePath) return res.status(400).json({ error: "path required" });

      const resolved = path.resolve(filePath);
      if (!fs.existsSync(resolved)) return res.status(404).json({ error: "file not found" });

      const name = filename || path.basename(resolved);
      const mimeType = mime.lookup(name) || "application/octet-stream";

      for (const recipient of RECIPIENTS) {
        await sock.sendMessage(recipient, {
          document: { url: resolved },
          mimetype: mimeType,
          fileName: name,
        });
        console.log(`[WA] Sent file to ${recipient}`);
      }

      return res.json({ ok: true });
    } catch (e) {
      console.error("[WA] send-file error:", e);
      return res.status(500).json({ error: String(e) });
    }
  });

  const PORT = 3000;
  app.listen(PORT, "127.0.0.1", () => {
    console.log(`[WA] Bridge listening on http://127.0.0.1:${PORT}`);
    console.log(`[WA] Recipient JIDs: ${RECIPIENTS.join(", ")}`);
  });
}

start().catch((e) => console.error("Fatal:", e));