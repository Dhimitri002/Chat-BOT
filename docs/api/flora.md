# 🌸 API Flora AI

> **Base URL:** `/api/v1/flora`

Endpoints da Flora AI — a assistente inteligente da plataforma.

---

## POST /flora/chat

Enviar mensagem para a Flora AI.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "message": "Como eu conecto meu WhatsApp?",
  "session_id": "uuid-da-sessao-opcional"
}
```

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `message` | string | Sim | Mensagem do usuario |
| `session_id` | string | Nao | ID da sessao existente (cria nova se omitido) |

**Response (200 OK):**
```json
{
  "response": "Para conectar seu WhatsApp, va na tela 'Conexao' e clique em 'Escanear QR Code'. Abra o WhatsApp no seu celular, va em 'Dispositivos Conectados' e escaneie o codigo exibido. :)",
  "session_id": "flora-session-uuid",
  "intent": "whatsapp_connect",
  "confidence": 0.95,
  "tools_used": [],
  "is_new_session": false,
  "message_count": 5,
  "timestamp": "2026-05-26T15:30:00Z"
}
```

**Campos da Response:**
| Campo | Tipo | Descricao |
|-------|------|-----------|
| `response` | string | Resposta da Flora |
| `session_id` | string | ID da sessao (usar nas proximas mensagens) |
| `intent` | string | Intencao detectada |
| `confidence` | float | Confianca da deteccao (0-1) |
| `tools_used` | array | Ferramentas utilizadas (planejado) |
| `is_new_session` | bool | Se e uma nova sessao |
| `message_count` | int | Total de mensagens na sessao |

**Erros:**
| Status | Descricao |
|--------|-----------|
| 400 | Mensagem vazia ou muito longa |
| 429 | Limite de mensagens atingido |
| 503 | LLM indisponivel (usando fallback) |

---

## GET /flora/sessions

Listar sessoes Flora do usuario.

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "id": "flora-session-uuid",
      "message_count": 12,
      "is_active": true,
      "created_at": "2026-05-26T10:00:00Z",
      "last_active_at": "2026-05-26T15:30:00Z",
      "last_message": "Como conecto o WhatsApp?"
    }
  ],
  "total": 1
}
```

---

## GET /flora/history/{session_id}

Obter historico de uma sessao Flora.

**Query Parameters:**
| Param | Tipo | Default |
|-------|------|---------|
| `page` | int | 1 |
| `page_size` | int | 50 |

**Response (200 OK):**
```json
{
  "session_id": "flora-session-uuid",
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "Ola, como funciona?",
      "created_at": "2026-05-26T15:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Ola! A plataforma Flora permite criar chatbots para WhatsApp...",
      "created_at": "2026-05-26T15:00:02Z"
    }
  ],
  "total": 12
}
```

---

## DELETE /flora/session/{session_id}

Deletar uma sessao Flora.

**Response (200 OK):**
```json
{
  "message": "Sessao deletada com sucesso"
}
```

---

## GET /flora/onboarding

Obter passos do onboarding guiado.

**Response (200 OK):**
```json
{
  "steps": [
    {
      "id": "welcome",
      "title": "Bem-vindo a Flora!",
      "description": "Vamos configurar seu bot em 5 minutos",
      "icon": "hand-wave",
      "action": null,
      "completed": false
    },
    {
      "id": "license",
      "title": "Validar Licenca",
      "description": "Insira sua chave de licenca para comecar",
      "icon": "key",
      "action": "license_validation",
      "completed": false
    },
    {
      "id": "bot_name",
      "title": "Nome do Bot",
      "description": "Como voce quer chamar seu bot?",
      "icon": "robot",
      "action": "bot_config",
      "completed": false
    },
    {
      "id": "whatsapp",
      "title": "Conectar WhatsApp",
      "description": "Escaneie o QR Code com seu celular",
      "icon": "qrcode",
      "action": "whatsapp_connect",
      "completed": false
    },
    {
      "id": "test",
      "title": "Testar o Bot",
      "description": "Envie uma mensagem de teste",
      "icon": "message",
      "action": "chat_test",
      "completed": false
    },
    {
      "id": "done",
      "title": "Tudo Pronto!",
      "description": "Seu bot esta funcionando. A Flora esta aqui se precisar!",
      "icon": "check-circle",
      "action": null,
      "completed": false
    }
  ]
}
```

---

## POST /flora/help

Obter ajuda sobre um topico especifico.

**Request:**
```json
{
  "topic": "whatsapp",
  "question": "Como funciona o QR Code?"
}
```

**Response (200 OK):**
```json
{
  "topic": "whatsapp",
  "answer": "O QR Code e a forma de conectar seu WhatsApp ao bot. Funciona assim:\n\n1. Va na tela 'Conexao'\n2. Clique em 'Escanear QR Code'\n3. Abra o WhatsApp no celular\n4. Va em 'Dispositivos Conectados'\n5. Escaneie o codigo exibido\n\nO QR Code expira em 20 segundos. Se expirar, clique em 'Atualizar QR'.",
  "related_topics": ["whatsapp_connect", "whatsapp_problem"],
  "suggested_actions": [
    {
      "label": "Ir para Conexao",
      "action": "navigate:whatsapp_connect"
    }
  ]
}
```

**Topicos disponiveis:**
| Topico | Descricao |
|--------|-----------|
| `whatsApp` | Conexao e problemas WhatsApp |
| `bot_config` | Configuracao do bot |
| `bot_personality` | Personalidade do bot |
| `plans` | Planos e precos |
| `license` | Licencas e ativacao |
| `payment` | Pagamento e cobranca |
| `analytics` | Metricas e relatorios |
| `general` | Ajuda geral |

---

## GET /flora/suggestions

Obter sugestoes de perguntas/acoes baseadas no contexto do usuario.

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "text": "Como mudar a personalidade do bot?",
      "icon": "emotion",
      "action": "flora_chat",
      "payload": "personality_change"
    },
    {
      "text": "Como ver mensagens recebidas?",
      "icon": "inbox",
      "action": "navigate:chat_history"
    },
    {
      "text": "Como fazer upgrade do plano?",
      "icon": "arrow-up",
      "action": "navigate:plan_details"
    },
    {
      "text": "Quantas mensagens enviei hoje?",
      "icon": "chart",
      "action": "flora_chat",
      "payload": "stats_today"
    }
  ]
}
```

---

## GET /flora/status

Status do servico Flora AI.

**Response (200 OK):**
```json
{
  "status": "online",
  "llm_available": true,
  "active_providers": ["groq", "gemini"],
  "active_sessions": 45,
  "avg_response_time_ms": 1200,
  "version": "1.0.0"
}
```

---

## Limites por Plano

| Plano | Msgs Flora/dia | Historico | LLM |
|-------|----------------|-----------|-----|
| Starter | 10 | 7 dias | Nao |
| Basic | 25 | 14 dias | Nao |
| Plus | 50 | 30 dias | Nao |
| Pro | 100 | 60 dias | Groq |
| Master | 250 | 90 dias | Todos |
| Elite | 500 | 180 dias | Todos |
| Enterprise | Ilimitado | 365 dias | Todos |

---

## Exemplos cURL

```bash
# Chat com Flora
curl -X POST http://localhost:8000/api/v1/flora/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Como conecto o WhatsApp?"}'

# Com sessao existente
curl -X POST http://localhost:8000/api/v1/flora/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"E se o QR Code expirar?","session_id":"flora-session-uuid"}'

# Ver historico
curl http://localhost:8000/api/v1/flora/history/flora-session-uuid \
  -H "Authorization: Bearer <token>"

# Onboarding
curl http://localhost:8000/api/v1/flora/onboarding \
  -H "Authorization: Bearer <token>"

# Ajuda
curl -X POST http://localhost:8000/api/v1/flora/help \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"topic":"whatsapp","question":"Como funciona?"}'

# Sugestoes
curl http://localhost:8000/api/v1/flora/suggestions \
  -H "Authorization: Bearer <token>"

# Deletar sessao
curl -X DELETE http://localhost:8000/api/v1/flora/session/flora-session-uuid \
  -H "Authorization: Bearer <token>"
```
