# 📲 Integracao WhatsApp

> **Versao:** 1.0.0 | **Data:** 2026-05-26 | **Status:** Implementado (~75%)

---

## 1. Visao Geral

A integracao WhatsApp permite que cada bot se conecte a uma conta WhatsApp via QR Code e envie/receba mensagens.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  App Cliente │    │   Backend    │    │  WPPConnect  │    │   WhatsApp   │
│              │    │              │    │  Connector   │    │   Server     │
│ Tela QR Code │◄──►│ WhatsAppAPI  │◄──►│  (Node.js)   │◄──►│              │
│ Envia msg    │    │ /whatsapp/*  │    │ Sessions     │    │              │
│ Recebe msg   │    │              │    │ QR Code      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Solucao:** Usa o **WPPConnect** (biblioteca Node.js) como connector, comunicando-se com o backend via HTTP.

---

## 2. Arquitetura de Sessoes

```
WhatsAppService ──── SessionStore (sessions/)
                          │
                          ├── session_{bot_id}/
                          │   ├── tokens/
                          │   │   ├── {session}-tokenizer.json
                          │   │   └── ...
                          │   ├── session_store.json
                          │   └── metadata.json
                          │
                          ├── session_{outro_bot}/
                          │   └── ...
                          └── ...
```

**Persistencia:** Cada sessao WhatsApp e salva em disco, permitindo reconexao sem novo QR Code.

---

## 3. Estados de Conexao

```
                  ┌──────────────┐
                  │ DISCONNECTED │
                  └──────┬───────┘
                         │ POST /connect
                         ▼
                  ┌──────────────┐
                  │  CONNECTING  │
                  └──────┬───────┘
                         │
                    ┌────┴────┐
                    │ QR Code │
                    │ gerado? │
                    └────┬────┘
                   SIM   │   NAO (sessao existe)
                    ┌────┴────┐
                    ▼         ▼
           ┌──────────┐  ┌───────────┐
           │QR_WAITING│  │ CONNECTED │◄─── Reconexao
           └────┬─────┘  └─────┬─────┘
                │              │
         Escaneou QR          │
                │              │
                ▼              │
           ┌───────────┐      │
           │ CONNECTED │      │
           └─────┬─────┘      │
                 │            │
            Logout / Erro     │
                 │            │
                 ▼            ▼
         ┌──────────────┐ ┌─────────┐
         │  LOGGED_OUT  │ │  ERROR  │
         └──────────────┘ └─────────┘
```

---

## 4. Endpoints da API

### 4.1 Conectar

```
POST /api/v1/whatsapp/connect
```

**Request:**
```json
{
  "bot_id": "uuid-do-bot",
  "session_name": "bot-session-1"
}
```

**Response (novo QR Code):**
```json
{
  "status": "qr_waiting",
  "qr_code": "base64_image_data",
  "session_name": "bot-session-1",
  "message": "Escaneie o QR Code com o WhatsApp"
}
```

**Response (ja conectado):**
```json
{
  "status": "connected",
  "phone_number": "+5511999999999",
  "bot_id": "uuid-do-bot",
  "message": "WhatsApp ja conectado"
}
```

### 4.2 Desconectar

```
POST /api/v1/whatsapp/disconnect
```

```json
{
  "bot_id": "uuid-do-bot"
}
```

### 4.3 Enviar Mensagem

```
POST /api/v1/whatsapp/send
```

```json
{
  "bot_id": "uuid-do-bot",
  "to": "5511999999999",
  "message": "Ola! Como posso ajudar?"
}
```

### 4.4 Status

```
GET /api/v1/whatsapp/status/{bot_id}
```

```json
{
  "bot_id": "uuid-do-bot",
  "state": "CONNECTED",
  "phone_number": "+5511999999999",
  "connected_at": "2026-05-26T10:30:00Z"
}
```

### 4.5 Atualizar QR Code

```
GET /api/v1/whatsapp/qr/{bot_id}
```

### 4.6 Listar Sessoes

```
GET /api/v1/whatsapp/sessions
```

```json
{
  "sessions": [
    {
      "bot_id": "uuid-1",
      "session_name": "bot-session-1",
      "state": "CONNECTED",
      "phone_number": "+5511999999999",
      "created_at": "2026-05-20T15:00:00Z",
      "last_active_at": "2026-05-26T10:30:00Z"
    },
    {
      "bot_id": "uuid-2",
      "session_name": "bot-session-2",
      "state": "DISCONNECTED",
      "created_at": "2026-05-18T09:00:00Z",
      "last_active_at": "2026-05-22T14:00:00Z"
    }
  ],
  "total": 2
}
```

### 4.7 Health Check

```
GET /api/v1/whatsapp/health
```

---

## 5. Servico WhatsApp (`services/whatsapp_service.py`)

```python
class WhatsAppService:
    _instance = None
    _sessions: dict[str, ConnectionState] = {}

    @classmethod
    async def get_instance(cls) -> "WhatsAppService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, bot_id: str, db: AsyncSession) -> dict:
        # 1. Verificar se ja existe sessao
        if bot_id in self._sessions:
            state = self._sessions[bot_id]
            if state == ConnectionState.CONNECTED:
                return {"status": "connected", ...}

        # 2. Solicitar novo QR Code ao connector
        qr_data = await self._request_qr(bot_id)
        self._sessions[bot_id] = ConnectionState.QR_WAITING
        return {"status": "qr_waiting", "qr_code": qr_data}

    async def send_message(self, bot_id: str, to: str, message: str) -> dict:
        # 1. Verificar conexao
        if self._sessions.get(bot_id) != ConnectionState.CONNECTED:
            raise HTTPException(400, "WhatsApp nao conectado")

        # 2. Enviar via connector
        result = await self._send_via_connector(bot_id, to, message)

        # 3. Registrar mensagem no banco
        await self._save_message(db, bot_id, to, message, direction="out")
        return result
```

---

## 6. Fluxo de Mensagem

### 6.1 Mensagem Saindo (Bot → Usuario)

```
Usuario pergunta → Bot processa → LLM/Rules gera resposta
                                          │
                                          ▼
                                   WhatsAppService.send_message()
                                          │
                                          ▼
                                   WPPConnect → WhatsApp Server
                                          │
                                          ▼
                                   Message salva no DB (direction=out)
```

### 6.2 Mensagem Entrando (Usuario → Bot)

```
Usuario envia msg → WhatsApp Server → WPPConnect webhook
                                           │
                                           ▼
                                    Backend recebe webhook
                                           │
                                    Message salva no DB (direction=in)
                                           │
                                    Bot processa (rules / LLM)
                                           │
                                    Envia resposta ao usuario
```

### 6.3 Tipos de Mensagem Suportados

| Tipo | Suporte |
|------|---------|
| Texto | ✅ Completo |
| Imagem | 📋 Planejado |
| Audio | 📋 Planejado |
| Video | 📋 Planejado |
| Documento | 📋 Planejado |
| Localizacao | 📋 Planejado |
| Contato | 📋 Planejado |
| Sticker | 📋 Planejado |
| Lista/Botoes | 📋 Planejado |

---

## 7. Seguranca WhatsApp

### 7.1 Whitelist de Numeros

```python
# Permitir que apenas numeros autorizados conversem com o bot
ALLOWED_NUMBERS = ["5511999999999", "5511888888888"]

async def is_allowed(phone: str) -> bool:
    if not settings.WHITELIST_ENABLED:
        return True
    return phone in ALLOWED_NUMBERS
```

### 7.2 Rate Limiting por Usuario

```python
# Limitar mensagens por usuario
MAX_MESSAGES_PER_MINUTE = 10
async def check_rate_limit(phone: str) -> bool:
    count = await redis.get(f"ratelimit:whatsapp:{phone}")
    if count and int(count) >= MAX_MESSAGES_PER_MINUTE:
        return False
    await redis.incr(f"ratelimit:whatsapp:{phone}")
    await redis.expire(f"ratelimit:whatsapp:{phone}", 60)
    return True
```

### 7.3 Auto-Disconnect

```python
# Desconectar automatico se WhatsApp detectar desconnecting
async def on_whatsapp_disconnect(bot_id: str, reason: str):
    logger.warning(f"WhatsApp disconnect: bot={bot_id}, reason={reason}")
    await whatsapp_service.update_session_state(bot_id, ConnectionState.LOGGED_OUT)
    await notify_admin(f"WhatsApp desconectado: {bot_id}")
```

---

## 8. Configuracao

```env
# WhatsApp
WHATSAPP_SESSION_DIR=./sessions
WHATSAPP_CONNECTOR_URL=http://localhost:3333
WHATSAPP_CONNECTOR_SECRET=your-connector-secret

# Rate limiting
WHITELIST_ENABLED=false
MAX_MESSAGES_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# Timeouts
WHATSAPP_CONNECT_TIMEOUT=30
WHATSAPP_QR_TIMEOUT=60
WHATSAPP_RECONNECT_ATTEMPTS=3
WHATSAPP_RECONNECT_DELAY=5
```

---

## 9. Problemas Conhecidos e Solucoes

| Problema | Solucao |
|----------|---------|
| QR Code expira (20s) | Regenerar automaticamente, fazer polling no app |
| Banimento do numero | Educar cliente a nao enviar spam, usar toneis |
| Sessao cai apos hibernacao | Auto-reconnect com backoff exponencial |
| Multiplos dispositivos | WPPConnect gerencia isso, sessao unica |
| Performance com muitas mensagens | Filas async (Celery/bull no futuro) |
| Webhook nao chega | Verificar firewall, proxy reverso |

---

## 10. Roadmap WhatsApp

| Funcao | Status |
|--------|--------|
| Conexao QR Code | ✅ |
| Envio de texto | ✅ |
| Recebimento de texto | ✅ |
| Persistencia de sessao | ✅ |
| Multiplas sessoes | ✅ |
| Health checks | ✅ |
| Imagem/Audio | 📋 |
| Grupos | 📋 |
| Listas/Botoes | 📋 |
| Status/Stories | 📋 |
| Business API | 📋 |
| Filas de mensagem | 📋 |
| Broadcast | 📋 |
