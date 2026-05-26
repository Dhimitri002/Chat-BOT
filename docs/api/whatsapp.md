# 📲 API de WhatsApp

> **Base URL:** `/api/v1/whatsApp`

Gerenciamento de conexoes WhatsApp e envio de mensagens. Todos os endpoints requerem autenticacao.

---

## POST /whatsapp/connect

Conectar uma sessao WhatsApp para um bot. Retorna QR Code se necessario.

**Request:**
```json
{
  "bot_id": "bot-uuid"
}
```

**Response (Novo QR Code):**
```json
{
  "status": "qr_waiting",
  "qr_code": "base64_image_data",
  "session_name": "bot-session-1",
  "message": "Escaneie o QR Code com o WhatsApp"
}
```

**Response (Ja conectado):**
```json
{
  "status": "connected",
  "phone_number": "+5511999999999",
  "bot_id": "bot-uuid",
  "message": "WhatsApp ja conectado"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 404 | Bot nao encontrado |
| 400 | Bot nao pertence ao usuario |
| 422 | Ja existe sessao conectada |

---

## POST /whatsapp/desconnect

Desconectar sessao WhatsApp.

**Request:**
```json
{
  "bot_id": "bot-uuid"
}
```

**Response (200 OK):**
```json
{
  "status": "disconnected",
  "message": "Sessao WhatsApp desconectada"
}
```

---

## POST /whatsapp/send

Enviar mensagem de texto.

**Request:**
```json
{
  "bot_id": "bot-uuid",
  "to": "5511999999999",
  "message": "Ola! Como posso ajudar?"
}
```

| Campo | Tipo | Obrigatorio | Regras |
|-------|------|-------------|--------|
| `bot_id` | string | Sim | UUID valido |
| `to` | string | Sim | Numero com codigo pais (ex: 5511999999999) |
| `message` | string | Sim | Max 4096 chars |

**Response (200 OK):**
```json
{
  "status": "sent",
  "message_id": "msg-uuid",
  "to": "5511999999999",
  "timestamp": "2026-05-26T15:30:00Z"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 400 | WhatsApp nao conectado |
| 404 | Bot nao encontrado |
| 429 | Rate limit atingido |

---

## GET /whatsapp/status/{bot_id}

Obter status da conexao WhatsApp.

**Response (200 OK):**
```json
{
  "bot_id": "bot-uuid",
  "state": "CONNECTED",
  "phone_number": "+5511999999999",
  "connected_at": "2026-05-20T15:00:00Z",
  "session_name": "bot-session-1"
}
```

**Estados possiveis:**
| Estado | Descricao |
|--------|-----------|
| `DISCONNECTED` | Nao conectado |
| `CONNECTING` | Conectando |
| `QR_WAITING` | Aguardando scan do QR Code |
| `CONNECTED` | Conectado e funcionando |
| `LOGGED_OUT` | Desconectado pelo usuario |
| `ERROR` | Erro na conexao |

---

## GET /whatsapp/qr/{bot_id}

Obter QR Code atualizado (se expirou).

**Response (200 OK):**
```json
{
  "qr_code": "base64_image_data",
  "expires_in_seconds": 15
}
```

---

## GET /whatsapp/sessions

Listar todas as sessoes WhatsApp do usuario.

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "bot_id": "uuid-1",
      "bot_name": "Bot Principal",
      "session_name": "bot-session-1",
      "state": "CONNECTED",
      "phone_number": "+5511999999999",
      "created_at": "2026-05-20T15:00:00Z",
      "last_active_at": "2026-05-26T15:30:00Z"
    },
    {
      "bot_id": "uuid-2",
      "bot_name": "Bot Secundario",
      "session_name": "bot-session-2",
      "state": "DISCONNECTED",
      "created_at": "2026-05-18T09:00:00Z",
      "last_active_at": "2026-05-22T14:00:00Z"
    }
  ],
  "total": 2
}
```

---

## GET /whatsapp/health

Health check do servico WhatsApp.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "connector_url": "http://localhost:3333",
  "active_sessions": 5,
  "total_sessions": 12
}
```

---

## Webhooks (Receiving)

### POST /webhooks/whatsapp

Endpoint para receber mensagens do WPPConnect connector.

**Request (webhook payload):**
```json
{
  "event": "message",
  "session": "bot-session-1",
  "data": {
    "from": "5511999999999@s.whatsapp.net",
    "to": "5511888888888@s.whatsapp.net",
    "body": "Ola, quero informacoes!",
    "type": "chat",
    "timestamp": 1716736200,
    "id": "msg-abc123"
  }
}
```

**Eventos suportados:**
| Evento | Descricao |
|--------|-----------|
| `message` | Mensagem recebida |
| `message_ack` | Confirmacao de entrega |
| `qrcode` | Novo QR Code |
| `connected` | Conexao estabelecida |
| `disconnected` | Conexao perdida |
| `error` | Erro na sessao |

---

## Rate Limiting

| Regra | Valor |
|-------|-------|
| Envio por numero | 10 msg/min |
| Envio global | 100 msg/min por bot |
| Conexoes simultaneas | Conforme plano |

---

## Fluxo Completo

```
1. Cliente clica "Conectar WhatsApp"
   → POST /whatsapp/connect { bot_id }
   → Retorna QR Code

2. Cliente escaneia QR Code com celular
   → WPPConnect detecta conexao
   → POST /webhooks/whatsapp { event: "connected" }

3. Usuario envia mensagem no WhatsApp
   → WPPConnect recebe
   → POST /webhooks/whatsapp { event: "message", ... }

4. Backend processa mensagem
   → Salva no DB
   → Bot gera resposta (rules ou LLM)
   → POST /whatsapp/send { to, message }
```

---

## Exemplos cURL

```bash
# Conectar
curl -X POST http://localhost:8000/api/v1/whatsapp/connect \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"bot-uuid"}'

# Enviar mensagem
curl -X POST http://localhost:8000/api/v1/whatsapp/send \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"bot-uuid","to":"5511999999999","message":"Ola!"}'

# Ver status
curl http://localhost:8000/api/v1/whatsapp/status/bot-uuid \
  -H "Authorization: Bearer <token>"

# Desconectar
curl -X POST http://localhost:8000/api/v1/whatsapp/disconnect \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"bot-uuid"}'
```
