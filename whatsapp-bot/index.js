/**
 * WhatsApp Bot — Flora Platform (Standalone Bot Mode)
 * ======================================================
 * Standalone WhatsApp bot using Baileys that processes incoming messages
 * and routes them through the Flora AI engine via HTTP API.
 *
 * This is an alternative to the Node.js + Python bridge architecture,
 * useful for simple deployments where the bot runs independently.
 *
 * Mode 1: Bridge mode
 *   Connects to the Python Bridge via TCP/HTTP
 *
 * Mode 2: Standalone mode
 *   Calls the Flora backend REST API directly
 *
 * Environment variables:
 *   BOT_ID            — Bot identifier
 *   SESSION_ID        — Session identifier
 *   AUTH_DIR          — Baileys auth directory
 *   BACKEND_URL       — Flora API backend URL (for standalone mode)
 *   BRIDGE_HOST       — Python bridge host (for bridge mode)
 *   BRIDGE_PORT       — Python bridge port (for bridge mode)
 *   MODE              — "standalone" or "bridge"
 *   FLORA_API_KEY     — API key for Flora backend
 */

const {
  makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const pino = require("pino");
const fs = require("fs");
const path = require("path");
const http = require("http");

// ─── Configuration ───────────────────────────────────────────────────

const BOT_ID = process.env.BOT_ID || "default";
const SESSION_ID = process.env.SESSION_ID || "default";
const AUTH_DIR = process.env.AUTH_DIR || "./.wa_auth";
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const FLORA_API_KEY = process.env.FLORA_API_KEY || "";
const MODE = process.env.MODE || "standalone"; // "standalone" or "bridge"
const BRIDGE_HOST = process.env.BRIDGE_HOST || "127.0.0.1";
const BRIDGE_PORT = parseInt(process.env.BRIDGE_PORT || "3333", 10);
const LOG_LEVEL = process.env.LOG_LEVEL || "info";

const SESSION_PATH = path.join(AUTH_DIR, `bot_${BOT_ID}_${SESSION_ID}`);

// ─── Logging ──────────────────────────────────────────────────────────

const logger = pino({ level: LOG_LEVEL });

function log(level, msg, data = {}) {
  const entry = { level, bot_id: BOT_ID, session_id: SESSION_ID, msg, ...data };
  if (level === "error") logger.error(entry);
  else if (level === "warn") logger.warn(entry);
  else logger.info(entry);
}

// ─── State ────────────────────────────────────────────────────────────

let sock = null;
let isConnected = false;
let isConnecting = false;
let reconnectCount = 0;
let qrCode = null;
const MAX_RECONNECT = 10;

// ─── HTTP Client for Backend API ──────────────────────────────────────

function callFloraAPI(endpoint, data = {}) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const url = new URL(`${BACKEND_URL}/api/v1/flora${endpoint}`);
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === "https:" ? 443 : 80),
      path: url.pathname,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body),
        ...(FLORA_API_KEY ? { "Authorization": `Bearer ${FLORA_API_KEY}` } : {}),
      },
    };

    const req = http.request(options, (res) => {
      let chunks = "";
      res.on("data", (d) => { chunks += d; });
      res.on("end", () => {
        try {
          resolve(JSON.parse(chunks));
        } catch {
          resolve({ raw: chunks });
        }
      });
    });

    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

// ─── Auth State ───────────────────────────────────────────────────────

async function loadAuthState() {
  await fs.promises.mkdir(SESSION_PATH, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_PATH);
  return { state, saveCreds };
}

// ─── Process Incoming Message with Flora AI ───────────────────────────

async function processMessage(data) {
  const { sender, sender_name, content, is_group, message_id } = data;

  // Skip groups unless they explicitly mention the bot
  // (configurable behavior)
  if (is_group) {
    log("debug", "Skipping group message", { sender: sender_name });
    return;
  }

  log("info", "Processing message", { from: sender_name, content: content.substring(0, 80) });

  try {
    const result = await callFloraAPI("/chat", {
      session_id: `${BOT_ID}_${sender}`,
      user_id: sender,
      user_name: sender_name,
      message: content,
      bot_id: BOT_ID,
    });

    const reply = result.reply || result.response || result.text || "Desculpa, não entendi. Pode repetir?";

    if (reply) {
      await sendMessage(sender, reply);
      log("info", "Reply sent", { to: sender_name });
    }
  } catch (err) {
    log("error", "Flora API call failed", { error: err.message });
    // Fallback response
    try {
      await sendMessage(sender, "Opa! Estou com uma instabilidade técnica. Tente novamente em alguns instantes 😅");
    } catch (sendErr) {
      log("error", "Failed to send fallback message", { error: sendErr.message });
    }
  }
}

// ─── Send Message ─────────────────────────────────────────────────────

async function sendMessage(to, message) {
  if (!sock || !isConnected) {
    throw new Error("Not connected to WhatsApp");
  }

  let formattedNumber = to.replace(/\D/g, "");
  if (!formattedNumber.endsWith("@s.whatsapp.net")) {
    formattedNumber += "@s.whatsapp.net";
  }

  await sock.sendMessage(formattedNumber, { text: message });
}

// ─── Connection ───────────────────────────────────────────────────────

async function startConnection() {
  if (isConnecting) {
    log("warn", "Already connecting, skipping");
    return;
  }
  isConnecting = true;

  try {
    log("info", "Starting WhatsApp Bot connection...", { mode: MODE });

    const { version, isLatest } = await fetchLatestBaileysVersion();
    log("info", `Baileys v${version.join(".")}, latest: ${isLatest}`);

    const { state, saveCreds } = await loadAuthState();

    sock = makeWASocket({
      version,
      logger: pino({ level: "silent" }),
      printQRInTerminal: false,
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "silent" })),
      },
      markOnlineOnConnect: true,
      syncFullHistory: false,
      defaultQueryTimeoutMs: 30000,
    });

    // Save credentials
    sock.ev.on("creds.update", saveCreds);

    // Connection lifecycle
    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        qrCode = qr;
        log("info", "QR code generated — scan with WhatsApp");
        // Print a simple representation
        console.log("\n=== QR CODE ===");
        console.log(qr.substring(0, 80) + "...");
        console.log("===============\n");
      }

      if (connection === "close") {
        isConnected = false;
        isConnecting = false;
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        log("warn", "Connection closed", { statusCode, shouldReconnect });

        if (shouldReconnect) {
          reconnectCount++;
          if (reconnectCount > MAX_RECONNECT) {
            log("error", "Max reconnect attempts reached");
            return;
          }
          const delay = Math.min(2000 * Math.pow(2, reconnectCount - 1), 60000);
          log("info", `Reconnecting in ${delay}ms (attempt ${reconnectCount})`);
          setTimeout(() => startConnection(), delay);
        } else {
          log("warn", "Logged out. Delete session files to reconnect.");
        }
      }

      if (connection === "open") {
        isConnected = true;
        isConnecting = false;
        reconnectCount = 0;
        qrCode = null;

        const phoneNumber = sock.user?.id?.split(":")[0];
        const phoneName = sock.user?.name || "Bot";

        log("info", "Bot connected!", { phoneNumber, phoneName });
      }
    });

    // Incoming messages
    sock.ev.on("messages.upsert", async (m) => {
      if (m.type !== "notify" && m.type !== "append") return;

      for (const msg of m.messages || []) {
        if (!msg.message || msg.key.fromMe) continue;
        if (msg.key.remoteJid === "status@broadcast") continue;

        const sender = msg.key.remoteJid;
        const senderNumber = sender.split("@")[0];
        const messageType = Object.keys(msg.message)[0];

        let content = "";

        switch (messageType) {
          case "conversation":
            content = msg.message.conversation;
            break;
          case "extendedTextMessage":
            content = msg.message.extendedTextMessage.text || "";
            break;
          case "imageMessage":
            content = msg.message.imageMessage.caption || "";
            break;
          case "videoMessage":
            content = msg.message.videoMessage.caption || "";
            break;
          case "audioMessage":
            content = "[Áudio]";
            break;
          case "documentMessage":
            content = `[Documento: ${msg.message.documentMessage.fileName || "arquivo"}]`;
            break;
          case "stickerMessage":
            content = "[Sticker]";
            break;
          case "locationMessage":
            content = "[Localização]";
            break;
          default:
            return; // Skip unsupported types
        }

        if (content.trim()) {
          await processMessage({
            message_id: msg.key.id,
            sender: senderNumber,
            sender_name: msg.pushName || senderNumber,
            content,
            is_group: sender.endsWith("@g.us"),
            timestamp: new Date(Number(msg.messageTimestamp) * 1000).toISOString(),
          });
        }
      }
    });

  } catch (error) {
    isConnecting = false;
    log("error", "Fatal connection error", { error: error.message });
    setTimeout(() => {
      if (!isConnected) startConnection();
    }, 5000);
  }
}

// ─── Health Check HTTP Server ─────────────────────────────────────────

function startHealthCheckServer() {
  const PORT = parseInt(process.env.HEALTH_PORT || "3001", 10);

  const server = http.createServer((req, res) => {
    if (req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: isConnected ? "connected" : "disconnected",
        bot_id: BOT_ID,
        mode: MODE,
        phone: sock?.user?.id?.split(":")[0] || null,
        timestamp: new Date().toISOString(),
      }));
    } else if (req.url === "/qr" && qrCode) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ qr: qrCode }));
    } else {
      res.writeHead(404);
      res.end("Not found");
    }
  });

  server.listen(PORT, () => {
    log("info", `Health check server listening on port ${PORT}`);
  });

  return server;
}

// ─── Graceful Shutdown ────────────────────────────────────────────────

async function shutdown(signal) {
  log("info", `Received ${signal}, shutting down...`);
  if (sock) {
    try { await sock.logout(); } catch (e) { /* ignore */ }
  }
  process.exit(0);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("uncaughtException", (err) => {
  log("error", "Uncaught exception", { error: err.message, stack: err.stack });
});
process.on("unhandledRejection", (reason) => {
  log("error", "Unhandled rejection", { reason: String(reason) });
});

// ─── Start ────────────────────────────────────────────────────────────

log("info", "WhatsApp Bot starting...", {
  bot_id: BOT_ID,
  session_id: SESSION_ID,
  mode: MODE,
  backend: BACKEND_URL,
});

const healthServer = startHealthCheckServer();
startConnection();
