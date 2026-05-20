/**
 * WhatsApp Bot Bridge - Flora Platform
 *
 * Gerencia conexões WhatsApp usando whatsapp-web.js
 * Comunica com o backend FastAPI via WebSocket/stdio
 *
 * Uso: node index.js
 * Variáveis de ambiente:
 *   BOT_ID - ID do bot
 *   SESSION_ID - ID da sessão
 *   SESSION_DIR - Diretório de sessão
 *   WS_PORT - Porta do WebSocket
 *   BACKEND_URL - URL do backend
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');

// Configuração
const BOT_ID = process.env.BOT_ID || 'default';
const SESSION_ID = process.env.SESSION_ID || 'default';
const SESSION_DIR = process.env.SESSION_DIR || `./sessions/${BOT_ID}`;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// Estado
let client = null;
let isConnected = false;
let qrCode = null;
let reconnectCount = 0;
const MAX_RECONNECT = 10;

// Utilitários
function log(level, message, data = {}) {
    const entry = {
        timestamp: new Date().toISOString(),
        level,
        bot_id: BOT_ID,
        session_id: SESSION_ID,
        message,
        ...data
    };
    console.log(JSON.stringify(entry));
}

function sendEvent(type, data = {}) {
    const event = { type, bot_id: BOT_ID, session_id: SESSION_ID, ...data };
    console.log(JSON.stringify(event));
}

// Garantir diretório de sessão
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// Criar cliente WhatsApp
function createClient() {
    log('info', 'Criando cliente WhatsApp...');

    client = new Client({
        authStrategy: new LocalAuth({
            clientId: `${BOT_ID}_${SESSION_ID}`,
            dataPath: SESSION_DIR
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ]
        },
        qrMaxRetries: 5,
        takeoverOnConflict: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    // Evento: QR Code gerado
    client.on('qr', (qr) => {
        log('info', 'QR Code gerado');
        qrCode = qr;
        sendEvent('qr', {
            qr: qr,
            expires_in: 60
        });
    });

    // Evento: Autenticando
    client.on('authenticating', () => {
        log('info', 'Autenticando...');
        sendEvent('authenticating');
    });

    // Evento: Conectado
    client.on('ready', () => {
        isConnected = true;
        reconnectCount = 0;
        const info = client.info;
        log('info', 'WhatsApp conectado!', { phone: info.wid.user, name: info.pushname });
        sendEvent('connected', {
            phone: info.wid.user,
            name: info.pushname,
            platform: info.platform
        });
    });

    // Evento: Desconectado
    client.on('disconnected', (reason) => {
        isConnected = false;
        log('warn', 'WhatsApp desconectado', { reason });
        sendEvent('disconnected', { reason: String(reason) });

        // Tentar reconexão se não foi logout intencional
        if (reason !== 'intentional' && reason !== 'LOGOUT') {
            attemptReconnect();
        }
    });

    // Evento: Mudança de estado
    client.on('change_state', (state) => {
        log('info', 'Mudança de estado', { state });
        sendEvent('state_change', { state });
    });

    // Evento: Mudança na bateria
    client.on('change_battery', (batteryInfo) => {
        sendEvent('battery', {
            level: batteryInfo.battery,
            is_charging: batteryInfo.plugged
        });
    });

    // Evento: Mensagem recebida
    client.on('message', async (msg) => {
        try {
            // Ignorar mensagens de status/grupos (configurável)
            if (msg.from === 'status@broadcast') return;

            const messageData = {
                id: msg.id._serialized,
                from: msg.from,
                to: msg.to,
                body: msg.body || '',
                type: msg.type,
                timestamp: msg.timestamp,
                has_media: msg.hasMedia,
                is_group: msg.from.endsWith('@g.us'),
                is_forwarded: msg.isForwarded,
                author: msg.author || null,
                // Dados adicionais
                notify_name: msg._data?.notifyName || null,
                caption: msg._data?.caption || null,
            };

            // Se tem mídia, baixar e incluir dados
            if (msg.hasMedia) {
                try {
                    const media = await msg.downloadMedia();
                    messageData.media = {
                        mimetype: media.mimetype,
                        filename: media.filename || null,
                        data: media.data, // base64
                        filesize: media.filesize || null
                    };
                } catch (mediaErr) {
                    log('warn', 'Erro ao baixar mídia', { error: mediaErr.message });
                }
            }

            sendEvent('message', { message: messageData });
        } catch (err) {
            log('error', 'Erro ao processar mensagem', { error: err.message });
        }
    });

    // Evento: Mensagem criada (enviada)
    client.on('message_create', async (msg) => {
        // Só notificar mensagens enviadas pelo próprio bot
        if (msg.fromMe) {
            sendEvent('message_sent', {
                id: msg.id._serialized,
                to: msg.to,
                body: msg.body || '',
                type: msg.type,
                timestamp: msg.timestamp
            });
        }
    });

    // Evento: Entrou em grupo
    client.on('group_join', (notification) => {
        sendEvent('group_join', {
            group_id: notification.chatId,
            group_name: notification.chatName,
            timestamp: Date.now()
        });
    });

    // Evento: Saiu de grupo
    client.on('group_leave', (notification) => {
        sendEvent('group_leave', {
            group_id: notification.chatId,
            group_name: notification.chatName,
            timestamp: Date.now()
        });
    });

    return client;
}

// Reconexão automática
function attemptReconnect() {
    if (reconnectCount >= MAX_RECONNECT) {
        log('error', 'Máximo de reconexões atingido');
        sendEvent('error', { error: 'Máximo de reconexões atingido' });
        return;
    }

    reconnectCount++;
    const delay = Math.min(2000 * Math.pow(2, reconnectCount - 1), 120000);

    log('info', `Reconectando em ${delay}ms (tentativa ${reconnectCount})`);
    sendEvent('reconnecting', { attempt: reconnectCount, delay });

    setTimeout(() => {
        if (client) {
            client.destroy().catch(() => {});
        }
        client = createClient();
        client.initialize().catch(err => {
            log('error', 'Erro ao reinicializar', { error: err.message });
        });
    }, delay);
}

// Processar comandos do backend (via stdin)
process.stdin.setEncoding('utf8');
process.stdin.on('data', async (data) => {
    try {
        const lines = data.toString().trim().split('\n');
        for (const line of lines) {
            if (!line.trim()) continue;
            const cmd = JSON.parse(line);
            await handleCommand(cmd);
        }
    } catch (err) {
        log('error', 'Erro ao processar comando', { error: err.message });
    }
});

// Handler de comandos do backend
async function handleCommand(cmd) {
    const action = cmd.action || cmd.type;

    switch (action) {
        case 'send_message':
            await cmdSendMessage(cmd);
            break;

        case 'send_media':
            await cmdSendMedia(cmd);
            break;

        case 'get_contacts':
            await cmdGetContacts();
            break;

        case 'get_groups':
            await cmdGetGroups();
            break;

        case 'get_chats':
            await cmdGetChats();
            break;

        case 'get_profile':
            await cmdGetProfile(cmd);
            break;

        case 'set_status':
            await cmdSetStatus(cmd);
            break;

        case 'refresh_qr':
            // Forçar novo QR code
            if (client) {
                client.destroy().catch(() => {});
                client = createClient();
                client.initialize().catch(err => {
                    log('error', 'Erro ao gerar novo QR', { error: err.message });
                });
            }
            break;

        case 'logout':
            if (client) {
                await client.logout();
                sendEvent('disconnected', { reason: 'intentional' });
            }
            break;

        case 'get_info':
            sendEvent('info', {
                connected: isConnected,
                phone: client?.info?.wid?.user || null,
                name: client?.info?.pushname || null,
                platform: client?.info?.platform || null,
                state: client?.info?.wid ? 'connected' : 'disconnected'
            });
            break;

        default:
            log('warn', 'Comando desconhecido', { action });
    }
}

// Enviar mensagem de texto
async function cmdSendMessage(cmd) {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado', message_id: cmd.message_id });
        return;
    }

    try {
        const to = cmd.to.includes('@c.us') ? cmd.to : `${cmd.to}@c.us`;
        const sent = await client.sendMessage(to, cmd.text);

        sendEvent('message_sent', {
            message_id: cmd.message_id,
            id: sent.id._serialized,
            to: to,
            timestamp: Date.now()
        });
    } catch (err) {
        log('error', 'Erro ao enviar mensagem', { error: err.message });
        sendEvent('error', { error: err.message, message_id: cmd.message_id });
    }
}

// Enviar mídia
async function cmdSendMedia(cmd) {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado', message_id: cmd.message_id });
        return;
    }

    try {
        let mediaPath = cmd.media_path;

        // Se é base64, salvar temporariamente
        if (cmd.media_data) {
            const ext = cmd.media_mimetype ? cmd.media_mimetype.split('/')[1] : 'bin';
            mediaPath = path.join(SESSION_DIR, `temp_${Date.now()}.${ext}`);
            const buffer = Buffer.from(cmd.media_data, 'base64');
            fs.writeFileSync(mediaPath, buffer);
        }

        const media = MessageMedia.fromFilePath(mediaPath);
        const to = cmd.to.includes('@c.us') ? cmd.to : `${cmd.to}@c.us`;
        const sent = await client.sendMessage(to, media, {
            caption: cmd.caption || ''
        });

        // Limpar arquivo temporário
        if (cmd.media_data && mediaPath && fs.existsSync(mediaPath)) {
            fs.unlinkSync(mediaPath);
        }

        sendEvent('message_sent', {
            message_id: cmd.message_id,
            id: sent.id._serialized,
            to: to,
            timestamp: Date.now()
        });
    } catch (err) {
        log('error', 'Erro ao enviar mídia', { error: err.message });
        sendEvent('error', { error: err.message, message_id: cmd.message_id });
    }
}

// Obter contatos
async function cmdGetContacts() {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado' });
        return;
    }

    try {
        const contacts = await client.getContacts();
        const result = contacts.map(c => ({
            id: c.id._serialized,
            name: c.name || c.pushname || '',
            number: c.number || '',
            is_business: c.isBusiness,
            is_me: c.isMe
        }));
        sendEvent('contacts', { contacts: result });
    } catch (err) {
        log('error', 'Erro ao obter contatos', { error: err.message });
    }
}

// Obter grupos
async function cmdGetGroups() {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado' });
        return;
    }

    try {
        const chats = await client.getChats();
        const groups = chats.filter(c => c.isGroup).map(g => ({
            id: g.id._serialized,
            name: g.name,
            participants: g.participants?.length || 0,
            is_archived: g.archived,
            last_message: g.lastMessage?.body || null
        }));
        sendEvent('groups', { groups });
    } catch (err) {
        log('error', 'Erro ao obter grupos', { error: err.message });
    }
}

// Obter chats
async function cmdGetChats() {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado' });
        return;
    }

    try {
        const chats = await client.getChats();
        const result = chats.slice(0, 50).map(c => ({
            id: c.id._serialized,
            name: c.name,
            is_group: c.isGroup,
            unread_count: c.unreadCount,
            last_message: c.lastMessage?.body || null,
            timestamp: c.timestamp
        }));
        sendEvent('chats', { chats: result });
    } catch (err) {
        log('error', 'Erro ao obter chats', { error: err.message });
    }
}

// Obter perfil
async function cmdGetProfile(cmd) {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado' });
        return;
    }

    try {
        const number = cmd.number.includes('@c.us') ? cmd.number : `${cmd.number}@c.us`;
        const contact = await client.getContactById(number);
        const profilePic = await contact.getProfilePicUrl();

        sendEvent('profile', {
            number: contact.number,
            name: contact.name || contact.pushname || '',
            profile_pic: profilePic || null,
            is_business: contact.isBusiness,
            status: contact.status || null
        });
    } catch (err) {
        log('error', 'Erro ao obter perfil', { error: err.message });
    }
}

// Definir status
async function cmdSetStatus(cmd) {
    if (!isConnected || !client) {
        sendEvent('error', { error: 'Não conectado' });
        return;
    }

    try {
        await client.setStatus(cmd.status);
        sendEvent('status_set', { status: cmd.status });
    } catch (err) {
        log('error', 'Erro ao definir status', { error: err.message });
    }
}

// Tratamento de erros não capturados
process.on('uncaughtException', (err) => {
    log('error', 'Exceção não capturada', { error: err.message, stack: err.stack });
    sendEvent('error', { error: err.message, fatal: true });
});

process.on('unhandledRejection', (reason) => {
    log('error', 'Promise rejeitada', { error: String(reason) });
    sendEvent('error', { error: String(reason) });
});

// Sinais de sistema
process.on('SIGINT', async () => {
    log('info', 'Recebido SIGINT, encerrando...');
    if (client) {
        await client.destroy().catch(() => {});
    }
    process.exit(0);
});

process.on('SIGTERM', async () => {
    log('info', 'Recebido SIGTERM, encerrando...');
    if (client) {
        await client.destroy().catch(() => {});
    }
    process.exit(0);
});

// Inicializar
log('info', 'Iniciando WhatsApp Bot Bridge...', { bot_id: BOT_ID, session_id: SESSION_ID });
client = createClient();
client.initialize().catch(err => {
    log('error', 'Erro ao inicializar cliente', { error: err.message });
    sendEvent('error', { error: err.message, fatal: true });
    process.exit(1);
});
