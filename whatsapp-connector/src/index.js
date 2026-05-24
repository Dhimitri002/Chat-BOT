/**
 * WhatsApp Connector - Flora Platform
 * Usa Baileys (@whiskeysockets/baileys) para conexão WhatsApp Web
 *
 * Comunica com o backend Python via stdin/stdout (JSON lines)
 *
 * Uso: node src/index.js --session-id <id> --session-dir <dir>
 */

const {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');

// Parse CLI args
const args = process.argv.slice(2);
const sessionId = args[args.indexOf('--session-id') + 1] || 'default';
const sessionDir = args[args.indexOf('--session-dir') + 1] || './sessions/default';

// Garantir diretório de sessão
fs.mkdirSync(sessionDir, { recursive: true });

// Estado da conexão
let sock = null;
let isConnected = false;
let qrTimeout = null;

/**
 * Envia mensagem JSON para o stdout (lida pelo Python)
 */
function sendToPython(data) {
  console.log(JSON.stringify(data));
}

/**
 * Envia erro para o stderr
 */
function logError(error) {
  const errorMsg = error instanceof Error ? error.message : String(error);
  process.stderr.write(`[ERROR] ${errorMsg}\n`);
}

/**
 * Inicializa conexão WhatsApp
 */
async function startConnection() {
  try {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version, isLatest } = await fetchLatestBaileysVersion();

    sendToPython({
      type: 'info',
      message: `Baileys v${version.join('.')}, latest: ${isLatest}`
    });

    sock = makeWASocket({
      version,
      auth: state,
      printQRInTerminal: false,
      logger: {
        level: 'silent',
        ...console,
      },
      browser: ['Flora Platform', 'Chrome', '1.0.0'],
      syncFullHistory: false,
      markOnlineOnConnect: true,
    });

    // Salvar credenciais quando atualizadas
    sock.ev.on('creds.update', saveCreds);

    // Handler de conexão
    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        sendToPython({ type: 'qr', qr });
        // QR expira em 60 segundos
        if (qrTimeout) clearTimeout(qrTimeout);
        qrTimeout = setTimeout(() => {
          if (!isConnected) {
            sendToPython({ type: 'qr_expired' });
          }
        }, 60000);
      }

      if (connection === 'close') {
        isConnected = false;
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        sendToPython({
          type: 'disconnected',
          reason: shouldReconnect ? 'connection_lost' : 'logged_out',
          statusCode
        });

        if (shouldReconnect) {
          sendToPython({ type: 'reconnecting' });
          setTimeout(() => startConnection(), 3000);
        }
      } else if (connection === 'open') {
        isConnected = true;
        if (qrTimeout) clearTimeout(qrTimeout);

        const phoneNumber = sock.user?.id?.split(':')[0];
        const phoneName = sock.user?.name || 'Unknown';

        sendToPython({
          type: 'connected',
          phone_number: phoneNumber,
          phone_name: phoneName
        });
      }
    });

    // Handler de mensagens recebidas
    sock.ev.on('messages.upsert', async (m) => {
      const messages = m.messages || [];

      for (const msg of messages) {
        // Ignorar mensagens enviadas pelo próprio bot
        if (msg.key.fromMe) continue;

        // Ignorar mensagens de status
        if (msg.key.remoteJid === 'status@broadcast') continue;

        const sender = msg.key.remoteJid;
        const senderNumber = sender.split('@')[0];
        const messageType = Object.keys(msg.message || {})[0];

        let content = '';
        let metadata = {};

        switch (messageType) {
          case 'conversation':
            content = msg.message.conversation;
            break;
          case 'extendedTextMessage':
            content = msg.message.extendedTextMessage.text;
            break;
          case 'imageMessage':
            content = msg.message.imageMessage.caption || '[Imagem]';
            metadata.mediaType = 'image';
            metadata.mediaUrl = msg.message.imageMessage.url;
            break;
          case 'videoMessage':
            content = msg.message.videoMessage.caption || '[Vídeo]';
            metadata.mediaType = 'video';
            break;
          case 'audioMessage':
            content = '[Áudio]';
            metadata.mediaType = 'audio';
            break;
          case 'documentMessage':
            content = `[Documento: ${msg.message.documentMessage.fileName || 'arquivo'}]`;
            metadata.mediaType = 'document';
            metadata.fileName = msg.message.documentMessage.fileName;
            break;
          default:
            content = `[${messageType}]`;
        }

        if (content) {
          sendToPython({
            type: 'message',
            data: {
              message_id: msg.key.id,
              sender: senderNumber,
              sender_name: msg.pushName || senderNumber,
              content,
              timestamp: new Date(msg.messageTimestamp * 1000).toISOString(),
              message_type: messageType,
              metadata,
            },
          });
        }
      }
    });

  } catch (error) {
    logError(error);
    sendToPython({ type: 'error', message: error.message });
    setTimeout(() => startConnection(), 5000);
  }
}

/**
 * Envia mensagem pelo WhatsApp
 */
async function sendMessage(to, message, messageId) {
  try {
    if (!sock || !isConnected) {
      sendToPython({
        type: 'send_error',
        message_id: messageId,
        error: 'not_connected'
      });
      return;
    }

    // Formatar número
    let formattedNumber = to.replace(/\D/g, '');
    if (!formattedNumber.endsWith('@s.whatsapp.net')) {
      formattedNumber += '@s.whatsapp.net';
    }

    const result = await sock.sendMessage(formattedNumber, { text: message });

    sendToPython({
      type: 'message_sent',
      message_id: messageId,
      wa_message_id: result.key.id,
      to: formattedNumber,
      status: 'sent',
    });
  } catch (error) {
    logError(error);
    sendToPython({
      type: 'send_error',
      message_id: messageId,
      error: error.message
    });
  }
}

/**
 * Handler de comandos recebidos via stdin (do Python)
 */
process.stdin.setEncoding('utf8');
process.stdin.on('data', async (data) => {
  try {
    const lines = data.trim().split('\n');

    for (const line of lines) {
      if (!line.trim()) continue;

      const command = JSON.parse(line);

      switch (command.type) {
        case 'send_message':
          await sendMessage(command.to, command.message, command.message_id);
          break;

        case 'disconnect':
          if (sock) {
            await sock.logout();
            isConnected = false;
            sendToPython({ type: 'disconnected', reason: 'manual' });
          }
          break;

        case 'check_status':
          sendToPython({
            type: 'status',
            connected: isConnected,
            phone_number: sock?.user?.id?.split(':')[0],
          });
          break;

        default:
          sendToPython({ type: 'unknown_command', command: command.type });
      }
    }
  } catch (error) {
    logError(error);
    sendToPython({ type: 'error', message: error.message });
  }
});

// Iniciar conexão
sendToPython({ type: 'starting', session_id: sessionId });
startConnection();

// Graceful shutdown
process.on('SIGTERM', async () => {
  if (sock) {
    await sock.logout();
  }
  process.exit(0);
});

process.on('SIGINT', async () => {
  if (sock) {
    await sock.logout();
  }
  process.exit(0);
});
