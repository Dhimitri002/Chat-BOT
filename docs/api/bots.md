# 🤖 API de Bots

> **Base URL:** `/api/v1/bots`

Gerenciamento de bots. Todos os endpoints requerem autenticacao (`Bearer <token>`).

---

## Modelo Bot

```json
{
  "id": "uuid",
  "name": "Bot Principal",
  "description": "Bot de atendimento",
  "personality": "friendly",
  "response_mode": "smart",
  "welcome_message": "Ola! Como posso ajudar?",
  "fallback_message": "Desculpe, nao entendi. Pode reformular?",
  "owner_id": "user-uuid",
  "status": "active",
  "is_active": true,
  "whatsapp_connected": false,
  "commands_count": 5,
  "intents_count": 12,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-05-26T15:00:00Z"
}
```

---

## GET /bots

Listar todos os bots do usuario.

**Query Parameters:**
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `page` | int | 1 | Pagina |
| `page_size` | int | 20 | Itens por pagina (max 100) |

**Response (200 OK):**
```json
{
  "bots": [
    {
      "id": "uuid-1",
      "name": "Bot Principal",
      "status": "active",
      "personality": "friendly",
      "whatsapp_connected": true,
      "created_at": "2026-01-15T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "name": "Bot Secundario",
      "status": "inactive",
      "personality": "professional",
      "whatsapp_connected": false,
      "created_at": "2026-02-20T14:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

## GET /bots/{bot_id}

Obter detalhes de um bot.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Bot Principal",
  "description": "Bot de atendimento ao cliente",
  "personality": "friendly",
  "response_mode": "smart",
  "welcome_message": "Ola! Bem-vindo! Como posso ajudar?",
  "fallback_message": "Desculpe, nao entendi. Pode reformular?",
  "owner_id": "user-uuid",
  "status": "active",
  "is_active": true,
  "whatsapp_connected": true,
  "commands_count": 5,
  "intents_count": 12,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-05-26T15:00:00Z"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 404 | Bot nao encontrado |
| 403 | Bot nao pertence ao usuario |

---

## POST /bots

Criar novo bot.

**Request:**
```json
{
  "name": "Bot Principal",
  "description": "Bot de atendimento",
  "personality": "friendly",
  "response_mode": "smart",
  "welcome_message": "Ola! Como posso ajudar?",
  "fallback_message": "Desculpe, nao entendi."
}
```

| Campo | Tipo | Obrigatorio | Regras |
|-------|------|-------------|--------|
| `name` | string | Sim | 1-100 chars |
| `description` | string | Nao | Max 500 chars |
| `personality` | string | Nao | `friendly`, `professional`, `casual`, `funny` |
| `response_mode` | string | Nao | `rules`, `smart`, `llm` |
| `welcome_message` | string | Nao | Max 1000 chars |
| `fallback_message` | string | Nao | Max 500 chars |

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Bot Principal",
  "personality": "friendly",
  "status": "active",
  "created_at": "2026-05-26T15:00:00Z"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 400 | Limite de bots atingido para o plano |
| 422 | Dados invalidos |

---

## PUT /bots/{bot_id}

Atualizar bot.

**Request:**
```json
{
  "name": "Bot Atualizado",
  "personality": "professional",
  "welcome_message": "Ola! Bem-vindo ao nosso atendimento!"
}
```

(Todos os campos sao opcionais — apenas os enviados sao atualizados)

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Bot Atualizado",
  "personality": "professional",
  "updated_at": "2026-05-26T16:00:00Z"
}
```

---

## DELETE /bots/{bot_id}

Deletar bot (e todos os dados associados).

**Response (200 OK):**
```json
{
  "message": "Bot deletado com sucesso"
}
```

---

## POST /bots/{bot_id}/activate

Ativar bot.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "status": "active",
  "message": "Bot ativado"
}
```

---

## POST /bots/{bot_id}/deactivate

Desativar bot.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "status": "inactive",
  "message": "Bot desativado"
}
```

---

## Comandos do Bot

### GET /bots/{bot_id}/commands

Listar comandos do bot.

**Response (200 OK):**
```json
{
  "commands": [
    {
      "id": "cmd-uuid",
      "trigger": "/ajuda",
      "response": "Aqui estao os comandos disponiveis...",
      "is_active": true
    },
    {
      "id": "cmd-uuid-2",
      "trigger": "/horario",
      "response": "Nosso horario: Seg-Sex 9h-18h",
      "is_active": true
    }
  ]
}
```

### POST /bots/{bot_id}/commands

Criar comando.

**Request:**
```json
{
  "trigger": "/ajuda",
  "response": "Aqui estao os comandos disponiveis: /ajuda, /horario, /contato"
}
```

### PUT /bots/{bot_id}/commands/{cmd_id}

Atualizar comando.

### DELETE /bots/{bot_id}/commands/{cmd_id}

Deletar comando.

---

## Intencoes do Bot

### GET /bots/{bot_id}/intents

Listar intencoes.

**Response (200 OK):**
```json
{
  "intents": [
    {
      "id": "intent-uuid",
      "name": "saudacao",
      "training_phrases": ["ola", "oi", "bom dia", "boa tarde"],
      "response": "Ola! Como posso ajudar?"
    },
    {
      "id": "intent-uuid-2",
      "name": "despedida",
      "training_phrases": ["tchau", "ate mais", "flw"],
      "response": "Tchau! Volte sempre! :)"
    }
  ]
}
```

### POST /bots/{bot_id}/intents

Criar intencao.

**Request:**
```json
{
  "name": "saudacao",
  "training_phrases": ["ola", "oi", "bom dia", "boa tarde", "eae"],
  "response": "Ola! Como posso ajudar?"
}
```

---

## Exemplos cURL

```bash
# Criar bot
curl -X POST http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Meu Bot","personality":"friendly"}'

# Listar bots
curl http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer <token>"

# Atualizar bot
curl -X PUT http://localhost:8000/api/v1/bots/{bot_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Novo Nome"}'

# Deletar bot
curl -X DELETE http://localhost:8000/api/v1/bots/{bot_id} \
  -H "Authorization: Bearer <token>"
```
