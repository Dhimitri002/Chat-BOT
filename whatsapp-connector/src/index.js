/**
 * WhatsApp Connector — Flora Platform
 * =====================================
 * Node.js connector using Baileys v6 for WhatsApp Web connection.
 * Communicates with Python backend via stdin/stdout JSON protocol.
 *
 * Events emitted (stdout → Python):
 *   qr              — QR code string for scanning
 *   qr_expired      — QR code expired, needs regeneration
 *   connected       — Successfully connected to WhatsApp
 *   disconnected    — Connection closed (with reason & statusCode)
 *   reconnecting    — Auto-reconnect initiated
 *   message         — Incoming message
 *   message_sent    — Outgoing message confirmed
 *   send_error      — Failed to send message
 *   status          — Connection status response
 *   error           — Fatal or connection error
 *   creds_update    — Auth credentials updated
 *
 * Commands accepted (stdin ← Python):
 *   send_message    — Send a text message
 *   send_media      — Send media (image, video, audio, document)
 *   disconnect      — Gracefully disconnect
 *   check_status    — Request current connection status
 *
 * Environment variables:
 *   SESSION_ID       — Unique session identifier
 *   BOT_ID           — Bot identifier
 *   AUTH_DIR         — Directory for Baileys auth files (default: .wa_auth)
 *   LOG_LEVEL        — Logging verbosity (default: info)
 */

const {
  makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  proto,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const pino = require("pino");
const fs = require("fs");
const path = require("path");

// ─── Configuration ───────────────────────────────────────────────────

const SESSION_ID = process.env.SESSION_ID || "default";
const BOT_ID = process.env.BOT_ID || "default";
const AUTH_DIR = process.env.AUTH_DIR || "./.wa_auth";
const LOG_LEVEL = process.env.LOG_LEVEL || "info";

const SESSION_PATH = path.join(AUTH_DIR, `session_${BOT_ID}_${SESSION_ID}`);

// ─── Logging ──────────────────────────────────────────────────────────

const logger = pino({ level: LOG_LEVEL });

function log(level, msg, data = {}) {
  const entry = { level, session_id: SESSION_ID, bot_id: BOT_ID, msg, ...data };
  if (level === "error") logger.error(entry);
  else if (level === "warn") logger.warn(entry);
  else logger.info(entry);
}

// ─── JSON Protocol (stdout → Python) ─────────────────────────────────

function sendToPython(payload) {
  try {
    process.stdout.write(JSON.stringify(payload) + "\n");
  } catch (err) {
    logger.error({ msg: "Failed to write to stdout", error: err.message });
  }
}

// ─── State ────────────────────────────────────────────────────────────

let sock = null;
let isConnected = false;
let isConnecting = false;
let qrTimeout = null;
let reconnectCount = 0;
const MAX_RECONNECT = 10;
const saveCredsDebounce = () => {
  let timeout;
  return (creds) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
      log("debug", "Credentials saved");
      sendToPython({ type: "creds_update", timestamp: Date.now() });
    }, 500);
  };
};

// ─── Auth State ───────────────────────────────────────────────────────

async function loadAuthState() {
  await fs.promises.mkdir(SESSION_PATH, { recursive: true });
  const { state, saveCreds: save } = await useMultiFileAuthState(SESSION_PATH);
  return { state, saveCreds: save, saveCredsDebounced: saveCredsDebounce() };
}

// ─── Connection ───────────────────────────────────────────────────────

async function startConnection() {
  if (isConnecting) {
    log("warn", "Already connecting, skipping");
    return;
  }
  isConnecting = true;

  try {
    log("info", "Starting WhatsApp connection...", { session: SESSION_PATH });

    const { version, isLatest } = await fetchLatestBaileysVersion();
    log("info", `Baileys v${version.join(".")}, latest: ${isLatest}`);

    const { state, saveCreds, saveCredsDebounced } = await loadAuthState();

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

    // ── Creds update ──────────────────────────────────────────────
    sock.ev.on("creds.update", () => {
      saveCreds();
      saveCredsDebounced(state.creds);
    });

    // ── Connection lifecycle ──────────────────────────────────────
    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      // QR code
      if (qr) {
        log("info", "QR code generated");
        sendToPython({ type: "qr", qr, timestamp: Date.now() });

        if (qrTimeout) clearTimeout(qrTimeout);
        qrTimeout = setTimeout(() => {
          if (!isConnected) {
            log("info", "QR code expired");
            sendToPython({ type: "qr_expired", timestamp: Date.now() });
          }
        }, 60000);
      }

      // Connection closed
      if (connection === "close") {
        isConnected = false;
        isConnecting = false;
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        log("warn", "Connection closed", { statusCode, shouldReconnect });
        sendToPython({
          type: "disconnected",
          reason: shouldReconnect ? "connection_lost" : "logged_out",
          statusCode,
          timestamp: Date.now(),
        });

        if (shouldReconnect) {
          reconnectCount++;
          if (reconnectCount > MAX_RECONNECT) {
            log("error", "Max reconnect attempts reached", { max: MAX_RECONNECT });
            sendToPython({
              type: "error",
              message: "Max reconnect attempts reached",
              fatal: true,
            });
            return;
          }

          const delay = Math.min(2000 * Math.pow(2, reconnectCount - 1), 60000);
          log("info", `Reconnecting in ${delay}ms (attempt ${reconnectCount}/${MAX_RECONNECT})`);
          sendToPython({ type: "reconnecting", attempt: reconnectCount, delay });

          setTimeout(() => startConnection(), delay);
        }
      }

      // Connection open
      if (connection === "open") {
        isConnected = true;
        isConnecting = false;
        reconnectCount = 0;
        if (qrTimeout) clearTimeout(qrTimeout);

        const phoneNumber = sock.user?.id?.split(":")[0];
        const phoneName = sock.user?.name || "Unknown";

        log("info", "Connected!", { phoneNumber, phoneName });
        sendToPython({
          type: "connected",
          phone_number: phoneNumber,
          phone_name: phoneName,
          timestamp: Date.now(),
        });
      }
    });

    // ── Incoming messages ─────────────────────────────────────────
    sock.ev.on("messages.upsert", async (m) => {
      if (m.type !== "notify" && m.type !== "append") return;

      const messages = m.messages || [];

      for (const msg of messages) {
        if (!msg.message) continue;
        if (msg.key.fromMe) continue;
        if (msg.key.remoteJid === "status@broadcast") continue;

        const sender = msg.key.remoteJid;
        const senderNumber = sender.split("@")[0];
        const messageType = Object.keys(msg.message)[0];

        let content = "";
        let metadata = {};

        switch (messageType) {
          case "conversation":
            content = msg.message.conversation;
            break;

          case "extendedTextMessage":
            content = msg.message.extendedTextMessage.text || "";
            if (msg.message.extendedTextMessage.contextInfo?.quotedMessage) {
              metadata.quoted = true;
            }
            break;

          case "imageMessage":
            content = msg.message.imageMessage.caption || "[Imagem]";
            metadata.mediaType = "image";
            metadata.mediaUrl = msg.message.imageMessage.url;
            metadata.mimetype = msg.message.imageMessage.mimetype;
            break;

          case "videoMessage":
            content = msg.message.videoMessage.caption || "[Vídeo]";
            metadata.mediaType = "video";
            metadata.mediaUrl = msg.message.videoMessage.url;
            metadata.mimetype = msg.message.videoMessage.mimetype;
            break;

          case "audioMessage":
            content = "[Áudio]";
            metadata.mediaType = "audio";
            metadata.ptt = msg.message.audioMessage.ptt || false;
            break;

          case "documentMessage":
            content = `[Documento: ${msg.message.documentMessage.fileName || "arquivo"}]`;
            metadata.mediaType = "document";
            metadata.fileName = msg.message.documentMessage.fileName;
            metadata.mimetype = msg.message.documentMessage.mimetype;
            break;

          case "stickerMessage":
            content = "[Sticker]";
            metadata.mediaType = "sticker";
            break;

          case "locationMessage":
            content = "[Localização]";
            metadata.mediaType = "location";
            metadata.latitude = msg.message.locationMessage.degreesLatitude;
            metadata.longitude = msg.message.locationMessage.degreesLongitude;
            break;

          case "contactMessage":
            content = `[Contato: ${msg.message.contactMessage.displayName || ""}]`;
            metadata.mediaType = "contact";
            break;

          case "reactionMessage":
            content = msg.message.reactionMessage.text || "[Reação]";
            metadata.mediaType = "reaction";
            break;

          default:
            content = `[${messageType}]`;
            metadata.mediaType = messageType;
        }

        if (content) {
          sendToPython({
            type: "message",
            data: {
              message_id: msg.key.id,
              sender: senderNumber,
              sender_name: msg.pushName || senderNumber,
              content,
              timestamp: new Date(
                Number(msg.messageTimestamp) * 1000
              ).toISOString(),
              message_type: messageType,
              metadata,
              is_group: sender.endsWith("@g.us"),
            },
          });
        }
      }
    });

    // ── Group participant changes ─────────────────────────────────
    sock.ev.on("group-participants.update", async (update) => {
      sendToPython({
        type: "group_participants_update",
        data: {
          group_id: update.id,
          participants: update.participants,
          action: update.action, // add, remove, promote, demote
          timestamp: Date.now(),
        },
      });
    });

    // ── Presence updates ──────────────────────────────────────────
    sock.ev.on("presence.update", async ({ id, presences }) => {
      sendToPython({
        type: "presence_update",
        data: {
          jid: id,
          presences,
          timestamp: Date.now(),
        },
      });
    });

  } catch (error) {
    isConnecting = false;
    log("error", "Fatal connection error", { error: error.message, stack: error.stack });
    sendToPython({ type: "error", message: error.message, fatal: true });

    // Attempt recovery after fatal error
    setTimeout(() => {
      if (!isConnected) {
        startConnection();
      }
    }, 5000);
  }
}

// ─── Send Message ─────────────────────────────────────────────────────

async function sendMessage(to, message, messageId) {
  try {
    if (!sock || !isConnected) {
      sendToPython({
        type: "send_error",
        message_id: messageId,
        error: "not_connected",
      });
      return;
    }

    let formattedNumber = to.replace(/\D/g, "");
    if (!formattedNumber.endsWith("@s.whatsapp.net")) {
      formattedNumber += "@s.whatsapp.net";
    }

    const result = await sock.sendMessage(formattedNumber, { text: message });

    sendToPython({
      type: "message_sent",
      message_id: messageId,
      wa_message_id: result.key.id,
      to: formattedNumber,
      status: "sent",
      timestamp: Date.now(),
    });
  } catch (error) {
    log("error", "Send message failed", { error: error.message, to });
    sendToPython({
      type: "send_error",
      message_id: messageId,
      error: error.message,
    });
  }
}

// ─── Send Media ───────────────────────────────────────────────────────

async function sendMedia(cmd) {
  try {
    if (!sock || !isConnected) {
      sendToPython({
        type: "send_error",
        message_id: cmd.message_id,
        error: "not_connected",
      });
      return;
    }

    let formattedNumber = cmd.to.replace(/\D/g, "");
    if (!formattedNumber.endsWith("@s.whatsapp.net")) {
      formattedNumber += "@s.whatsapp.net";
    }

    const buffer = Buffer.from(cmd.media_data, "base64");
    const messageOptions = { caption: cmd.caption || "" };
    let messageContent;

    switch (cmd.media_type) {
      case "image":
        messageContent = { image: buffer, caption: cmd.caption || "" };
        break;
      case "video":
        messageContent = { video: buffer, caption: cmd.caption || "" };
        break;
      case "audio":
        messageContent = { audio: buffer, ptt: cmd.ptt || false };
        break;
      case "document":
        messageContent = {
          document: buffer,
          mimetype: cmd.mimetype || "application/octet-stream",
          fileName: cmd.file_name || "document",
        };
        break;
      default:
        sendToPython({
          type: "send_error",
          message_id: cmd.message_id,
          error: `Unsupported media type: ${cmd.media_type}`,
        });
        return;
    }

    const result = await sock.sendMessage(formattedNumber, messageContent);

    sendToPython({
      type: "message_sent",
      message_id: cmd.message_id,
      wa_message_id: result.key.id,
      to: formattedNumber,
      status: "sent",
      timestamp: Date.now(),
    });
  } catch (error) {
    log("error", "Send media failed", { error: error.message, to: cmd.to });
    sendToPython({
      type: "send_error",
      message_id: cmd.message_id,
      error: error.message,
    });
  }
}

// ─── Stdin Command Handler ────────────────────────────────────────────

let stdinBuffer = "";

process.stdin.setEncoding("utf8");
process.stdin.on("data", async (data) => {
  stdinBuffer += data;
  const lines = stdinBuffer.split("\n");
  stdinBuffer = lines.pop(); // Keep the incomplete last chunk

  for (const line of lines) {
    if (!line.trim()) continue;

    let command;
    try {
      command = JSON.parse(line);
    } catch (parseErr) {
      log("warn", "Invalid JSON from stdin", { line: line.substring(0, 200) });
      sendToPython({ type: "error", message: "Invalid JSON command" });
      continue;
    }

    try {
      switch (command.type) {
        case "send_message":
          await sendMessage(command.to, command.message, command.message_id);
          break;

        case "send_media":
          await sendMedia(command);
          break;

        case "disconnect":
          if (sock) {
            await sock.logout();
            isConnected = false;
            sendToPython({ type: "disconnected", reason: "manual" });
          }
          break;

        case "check_status":
          sendToPython({
            type: "status",
            connected: isConnected,
            phone_number: sock?.user?.id?.split(":")[0] || null,
            timestamp: Date.now(),
          });
          break;

        default:
          log("warn", "Unknown command", { command: command.type });
          sendToPython({ type: "unknown_command", command: command.type });
      }
    } catch (err) {
      log("error", "Command handler error", { error: err.message, type: command.type });
      sendToPython({ type: "error", message: err.message });
    }
  }
});

// ─── Graceful Shutdown ────────────────────────────────────────────────

async function shutdown(signal) {
  log("info", `Received ${signal}, shutting down...`);
  if (sock) {
    try {
      await sock.logout();
    } catch (e) {
      // ignore
    }
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

log("info", "WhatsApp Connector starting...", {
  session_id: SESSION_ID,
  bot_id: BOT_ID,
  auth_dir: SESSION_PATH,
});
startConnection();
