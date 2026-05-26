# 💬 API de Chat

> **Base URL:** `/api/v1/chat`

Gerenciamento de historico de conversas e envio de mensagens.

---

## Modelo Mensagem

```json
{
  "id": "uuid",
  "bot_id": "bot-uuid",
  "user_phone": "5511999999999",
  "direction": "in",
  "content": "Ola, quero informacoes!",
  "content_type": "text",
  "status": "delivered",
  "is_read": false,
  "created_at": "2026-05-26T15:30:00Z"
}
```

**Campos:**
| Campo | Tipo | Descricao |
|-------|------|-----------|
| `direction` | string | `in` (recebida) ou `out` (enviada) |
| `content_type` | string | `text`, `image`, `audio`, `video` |
| `status` | string | `sent`, `delivered`, `read`, `failed` |

---

## GET /chat/conversations

Listar todas as conversas dos bots do usuario.

**Query Parameters:**
| Param | Tipo | Default |
|-------|------|---------|
| `page` | int | 1 |
| `page_size` | int | 20 |
| `bot_id` | string | (todos) |
| `search` | string | (fone ou nome) |

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "bot_id": "bot-uuid",
      "bot_name": "Bot Principal",
      "user_phone": "5511999999999",
      "last_message": "Ola, quero informacoes!",
      "last_message_at": "2026-05-26T15:30:00Z",
      "message_count": 25,
      "unread_count": 3
    },
    {
      "bot_id": "bot-uuid-2",
      "bot_name": "Bot Secundario",
      "user_phone": "5511888888888",
      "last_message": "Obrigado!",
      "last_message_at": "2026-05-26T14:00:00Z",
      "message_count": 8,
      "unread_count": 0
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

## GET /chat/history

Obter historico de mensagens de uma conversa.

**Query Parameters:**
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `bot_id` | string | Obrigatorio | ID do bot |
| `user_phone` | string | Obrigatorio | Telefone do usuario |
| `page` | int | 1 | Pagina |
| `page_size` | int | 50 | Max 100 |
| `before` | string | - | ISO timestamp (mensagens antes de) |
| `after` | string | - | ISO timestamp (mensagens depois de) |

**Response (200 OK):**
```json
{
  "messages": [
    {
      "id": "msg-uuid-1",
      "direction": "in",
      "content": "Ola, quero informacoes!",
      "content_type": "text",
      "status": "delivered",
      "is_read": true,
      "created_at": "2026-05-26T15:30:00Z"
    },
    {
      "id": "msg-uuid-2",
      "direction": "out",
      "content": "Ola! Claro, qual informacao voce precisa?",
      "content_type": "text",
      "status": "delivered",
      "is_read": true,
      "created_at": "2026-05-26T15:30:05Z"
    },
    {
      "id": "msg-uuid-3",
      "direction": "in",
      "content": "Quero saber sobre precos",
      "content_type": "text",
      "status": "delivered",
      "is_read": true,
      "created_at": "2026-05-26T15:31:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 50
}
```

---

## POST /chat/send

Enviar mensagem para um numero (chat manual).

**Request:**
```json
{
  "bot_id": "bot-uuid",
  "to": "5511999999999",
  "content": "Ola! Obrigado por entrar em contato!",
  "content_type": "text"
}
```

**Response (200 OK):**
```json
{
  "id": "msg-uuid",
  "bot_id": "bot-uuid",
  "to": "5511999999999",
  "content": "Ola! Obrigado por entrar em contato!",
  "direction": "out",
  "status": "sent",
  "created_at": "2026-05-26T16:00:00Z"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 400 | WhatsApp nao conectado |
| 404 | Bot nao encontrado |
| 429 | Rate limit atingido |

---

## POST /chat/mark-read

Marcar mensagens como lidas.

**Request:**
```json
{
  "bot_id": "bot-uuid",
  "user_phone": "5511999999999",
  "message_ids": ["msg-uuid-1", "msg-uuid-2"]
}
```

**Response (200 OK):**
```json
{
  "marked_count": 2,
  "message": "Mensagens marcadas como lidas"
}
```

---

## DELETE /chat/history

Deletar historico de uma conversa.

**Request:**
```json
{
  "bot_id": "bot-uuid",
  "user_phone": "5511999999999"
}
```

**Response (200 OK):**
```json
{
  "message": "Historico deletado"
}
```

---

## GET /chat/search

Buscar mensagens noshistoricos.

**Query Parameters:**
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `q` | string | Obrigatorio | Texto a buscar |
| `bot_id` | string | - | Filtrar por bot |
| `user_phone` | string | - | Filtrar por telefone |
| `limit` | int | 20 | Max 50 |

**Response (200 OK):**
```json
{
  "results": [
    {
      "id": "msg-uuid",
      "bot_id": "bot-uuid",
      "user_phone": "5511999999999",
      "content": "Ola, quero informacoes sobre planos!",
      "direction": "in",
      "created_at": "2026-05-26T15:30:00Z",
      "match_context": "...quero informacoes sobre planos!"
    }
  ],
  "total": 5,
  "query": "planos"
}
```

---

## Estatisticas

### GET /chat/stats

Estatisticas de chat do usuario.

**Response (200 OK):**
```json
{
  "total_messages": 1250,
  "messages_in": 625,
  "messages_out": 625,
  "total_conversations": 45,
  "active_conversations": 12,
  "unread_messages": 8,
  "avg_response_time_seconds": 3.5,
  "messages_today": 52,
  "messages_this_week": 310,
  "messages_this_month": 1250
}
```

---

## Exemplos cURL

```bash
# Listar conversas
curl "http://localhost:8000/api/v1/chat/conversations?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# Ver historico
curl "http://localhost:8000/api/v1/chat/history?bot_id=bot-uuid&user_phone=5511999999999" \
  -H "Authorization: Bearer <token>"

# Enviar mensagem
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"bot-uuid","to":"5511999999999","content":"Ola!"}'

# Buscar
curl "http://localhost:8000/api/v1/chat/search?q=planos&limit=10" \
  -H "Authorization: Bearer <token>"

# Stats
curl http://localhost:8000/api/v1/chat/stats \
  -H "Authorization: Bearer <token>"
```
