/**
 * Flora Platform - WhatsApp Bot Connector
 * Conecta o WhatsApp ao backend FastAPI via HTTP
 */
const wppconnect = require('@wppconnect-team/wppconnect');
const axios = require('axios');

const API_URL = process.env.FLORA_API_URL || 'http://localhost:8000';

// Cache simples de sessoes de chat
const chatSessions = new Map();

async function sendMessageToBot(client, message) {
    try {
        const chatId = message.from;
        const text = message.body;

        // Ignorar mensagens de grupo
        if (message.isGroupMsg) return;

        // Montar payload para o backend
        const payload = {
            text: text,
            contact_id: chatId,
            contact_name: message.sender?.name || message.sender?.pushname || 'Usuario',
            timestamp: new Date().toISOString(),
        };

        // Enviar para o backend
        const response = await axios.post(`${API_URL}/api/v1/chat`, payload, {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
        });

        const reply = response.data?.reply || response.data?.message || 'Desculpa, nao entendi.';

        // Enviar resposta de volta ao WhatsApp
        await client.sendText(chatId, reply);

    } catch (error) {
        console.error('[Flora] Erro ao processar mensagem:', error.message);
        try {
            await client.sendText(
                message.from,
                'Ops! Tive um problema tecnico. Tente novamente em alguns instantes.'
            );
        } catch (e) {
            // Ignorar erro secundario
        }
    }
}

async function start() {
    console.log('[Flora] Iniciando WhatsApp Bot Connector...');
    console.log(`[Flora] Backend: ${API_URL}`);

    try {
        const client = await wppconnect.create({
            session: 'flora-bot',
            catchQR: (qrcode) => {
                console.log('\n[Flora] Escaneie este QR Code com seu WhatsApp:');
                console.log(qrcode);
            },
            statusFind: (statusSession) => {
                console.log('[Flora] Status:', statusSession);
            },
            headless: true,
            devtools: false,
            useChrome: true,
            debug: false,
            logQR: true,
            browserArgs: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ],
        });

        console.log('[Flora] WhatsApp conectado com sucesso!');

        // Listener de mensagens
        client.onMessage(async (message) => {
            console.log(`[Flora] Mensagem recebida de ${message.from}: ${message.body}`);
            await sendMessageToBot(client, message);
        });

        // Listener de status de conexao
        client.onStateChange((state) => {
            console.log('[Flora] Estado da conexao:', state);
            if (state === 'DISCONNECTED') {
                console.log('[Flora] Desconectado. Tentando reconectar...');
            }
        });

    } catch (error) {
        console.error('[Flora] Erro ao iniciar:', error);
        process.exit(1);
    }
}

start();
