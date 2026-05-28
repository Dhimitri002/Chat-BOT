# 🌸 FLORA PLATFORM — API Endpoints

> Referência completa dos endpoints REST da Flora Platform.

---

## 📋 Base URL

| Ambiente | URL |
|---|---|
| **Desenvolvimento** | `http://localhost:8000` |
| **Produção** | `https://api.flora.com.br` |

Todos os endpoints são prefixados com `/api/v1/`.

---

## 🔐 Autenticação

### Registrar Usuário

```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "email": "usuario@exemplo.com",
    "password": "Senha@123456",
    "name": "Nome do Usuário"
}
```

**Resposta (201):**
```json
{
    "id": "uuid",
    "email": "usuario@exemplo.com",
    "name": "Nome do Usuário",
    "role": "client",
    "is_active": true,
    "created_at": "2025-06-21T10:00:00Z"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "usuario@exemplo.com",
    "password": "Senha@123456",
    "totp_code": "123456"
}
```

**Resposta (200):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Resposta (200):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

**Resposta (204):** No Content

### Setup 2FA

```http
POST /api/v1/auth/2fa/setup
Authorization: Bearer {access_token}
```

**Resposta (200):**
```json
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code_uri": "otpauth://totp/Flora:usuario@exemplo.com?secret=JBSWY3DPEHPK3PXP&issuer=Flora"
}
```

### Verificar 2FA

```http
POST /api/v1/auth/2fa/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "code": "123456"
}
```

**Resposta (200):**
```json
{
    "verified": true,
    "backup_codes": ["ABC123", "DEF456", "GHI789"]
}
```

---

## 👤 Usuários

### Perfil do Usuário

```http
GET /api/v1/users/me
Authorization: Bearer {access_token}
```

**Resposta (200):**
```json
{
    "id": "uuid",
    "email": "usuario@exemplo.com",
    "name": "Nome do Usuário",
    "role": "client",
    "is_active": true,
    "two_factor_enabled": false,
    "created_at": "2025-06-21T10:00:00Z",
    "subscription": {
        "plan": "Pro",
        "status": "active",
        "expires_at": "2025-07-21T10:00:00Z"
    }
}
```

### Atualizar Perfil

```http
PATCH /api/v1/users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "Novo Nome"
}
```

### Alterar Senha

```http
POST /api/v1/users/me/password
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "current_password": "Senha@123456",
    "new_password": "NovaSenha@789"
}
```

---

## 📦 Planos

### Listar Planos

```http
GET /api/v1/plans
```

**Resposta (200):**
```json
{
    "plans": [
        {
            "id": "uuid",
            "name": "Free",
            "slug": "free",
            "price": 0,
            "currency": "BRL",
            "interval": "month",
            "features": {
                "messages_limit": 100,
                "bots_limit": 1,
                "commands_limit": 5,
                "intents_limit": 5,
                "llm_providers": ["groq"],
                "flora_ai": false,
                "support": "community"
            }
        },
        {
            "id": "uuid",
            "name": "Pro",
            "slug": "pro",
            "price": 149,
            "currency": "BRL",
            "interval": "month",
            "features": {
                "messages_limit": 20000,
                "bots_limit": 5,
                "commands_limit": 200,
                "intents_limit": 500,
                "llm_providers": ["groq", "gemini", "openai", "anthropic"],
                "flora_ai": true,
                "support": "chat"
            }
        }
    ]
}
```

### Detalhes do Plano

```http
GET /api/v1/plans/{plan_id}
```

---

## 📜 Licenças

### Listar Licenças (Admin)

```http
GET /api/v1/licenses
Authorization: Bearer {admin_token}
```

**Query Params:**
| Param | Tipo | Descrição |
|---|---|---|
| `status` | string | Filtrar por status |
| `user_id` | uuid | Filtrar por usuário |
| `page` | int | Página (default: 1) |
| `limit` | int | Itens por página (default: 20) |

### Criar Licença (Admin)

```http
POST /api/v1/licenses
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "user_id": "uuid-do-usuario",
    "plan_id": "uuid-do-plano",
    "duration_days": 30,
    "max_devices": 1
}
```

**Resposta (201):**
```json
{
    "id": "uuid",
    "key_hash": "sha256-hash-da-licenca",
    "signature": "rsa-signature",
    "status": "active",
    "expires_at": "2025-07-21T10:00:00Z",
    "created_at": "2025-06-21T10:00:00Z"
}
```

### Validar Licença

```http
POST /api/v1/licenses/validate
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "license_key": "FLORA-XXXX-XXXX-XXXX",
    "hardware_id": "hw-id-do-dispositivo"
}
```

**Resposta (200):**
```json
{
    "valid": true,
    "plan": "Pro",
    "expires_at": "2025-07-21T10:00:00Z",
    "features": {...}
}
```

### Revogar Licença (Admin)

```http
DELETE /api/v1/licenses/{license_id}
Authorization: Bearer {admin_token}
```

---

## 🤖 Bots

### Listar Bots

```http
GET /api/v1/bots
Authorization: Bearer {access_token}
```

**Resposta (200):**
```json
{
    "bots": [
        {
            "id": "uuid",
            "name": "Bot de Vendas",
            "personality": "profissional",
            "is_active": true,
            "whatsapp_connected": true,
            "messages_count": 1250,
            "created_at": "2025-06-01T10:00:00Z"
        }
    ],
    "total": 1,
    "page": 1
}
```

### Criar Bot

```http
POST /api/v1/bots
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "Bot de Vendas",
    "personality": "profissional",
    "language": "pt-BR",
    "prompt": "Você é um assistente de vendas...",
    "welcome_message": "Olá! Como posso ajudar?",
    "farewell_message": "Obrigado! Volte sempre!",
    "template_id": "uuid-do-template (opcional)"
}
```

### Detalhes do Bot

```http
GET /api/v1/bots/{bot_id}
Authorization: Bearer {access_token}
```

### Atualizar Bot

```http
PATCH /api/v1/bots/{bot_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "Novo Nome",
    "is_active": false
}
```

### Excluir Bot

```http
DELETE /api/v1/bots/{bot_id}
Authorization: Bearer {access_token}
```

### Duplicar Bot

```http
POST /api/v1/bots/{bot_id}/duplicate
Authorization: Bearer {access_token}
```

---

## 💬 Chat

### Enviar Mensagem (Teste)

```http
POST /api/v1/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "bot_id": "uuid-do-bot",
    "message": "Olá, quero saber sobre preços"
}
```

**Resposta (200):**
```json
{
    "response": "Temos os seguintes planos...",
    "intent_matched": "consultar_precos",
    "confidence": 0.95,
    "provider": "groq",
    "model": "llama-3.1-8b-instant",
    "tokens_used": 150,
    "response_time_ms": 350
}
```

### Histórico de Mensagens

```http
GET /api/v1/chat/history?bot_id={bot_id}&limit=50
Authorization: Bearer {access_token}
```

---

## 🌸 Flora AI

### Enviar Mensagem

```http
POST /api/v1/flora/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "message": "Como conecto o WhatsApp?",
    "session_id": "uuid-da-sessão"
}
```

**Resposta (200):**
```json
{
    "response": "Para conectar seu WhatsApp...",
    "session_id": "uuid",
    "tokens_used": 245,
    "model": "llama-3.1-8b-instant",
    "provider": "groq"
}
```

### Histórico da Sessão

```http
GET /api/v1/flora/sessions/{session_id}
Authorization: Bearer {access_token}
```

### Limpar Sessão

```http
DELETE /api/v1/flora/sessions/{session_id}
Authorization: Bearer {access_token}
```

---

## 📱 WhatsApp

### Conectar (Gerar QR Code)

```http
POST /api/v1/whatsapp/connect
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "bot_id": "uuid-do-bot"
}
```

**Resposta (200):**
```json
{
    "qr_code": "base64-encoded-qr-image",
    "expires_in": 30,
    "session_id": "uuid"
}
```

### Status da Conexão

```http
GET /api/v1/whatsapp/status?bot_id={bot_id}
Authorization: Bearer {access_token}
```

**Resposta (200):**
```json
{
    "status": "connected",
    "phone_number": "+5511999999999",
    "connected_at": "2025-06-21T10:00:00Z",
    "battery_level": 85,
    "platform": "android"
}
```

### Desconectar

```http
POST /api/v1/whatsapp/disconnect
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "bot_id": "uuid-do-bot"
}
```

---

## ⚡ Comandos

### Listar Comandos

```http
GET /api/v1/commands?bot_id={bot_id}
Authorization: Bearer {access_token}
```

### Criar Comando

```http
POST /api/v1/commands
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "bot_id": "uuid-do-bot",
    "trigger": "/preços",
    "type": "keyword",
    "response": "Nossos preços são...",
    "is_active": true
}
```

### Atualizar Comando

```http
PATCH /api/v1/commands/{command_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "response": "Novo texto de resposta"
}
```

### Excluir Comando

```http
DELETE /api/v1/commands/{command_id}
Authorization: Bearer {access_token}
```

---

## 🎯 Intenções

### Listar Intenções

```http
GET /api/v1/intents?bot_id={bot_id}
Authorization: Bearer {access_token}
```

### Criar Intenção

```http
POST /api/v1/intents
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "bot_id": "uuid-do-bot",
    "name": "consultar_horario",
    "training_phrases": [
        "Qual o horário?",
        "Que horas abre?",
        "Funciona quando?",
        "Horário de funcionamento"
    ],
    "response": "Funcionamos de seg a sex, 9h às 18h!",
    "is_active": true
}
```

### Atualizar Intenção

```http
PATCH /api/v1/intents/{intent_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "training_phrases": ["novas", "frases", "aqui"]
}
```

### Excluir Intenção

```http
DELETE /api/v1/intents/{intent_id}
Authorization: Bearer {access_token}
```

---

## 📊 Analytics

### Dashboard

```http
GET /api/v1/analytics/dashboard
Authorization: Bearer {access_token}
```

**Resposta (200):**
```json
{
    "period": "30d",
    "messages": {
        "total": 12500,
        "received": 6250,
        "sent": 6250,
        "daily_average": 417
    },
    "users": {
        "active": 150,
        "new": 25,
        "churned": 3
    },
    "llm": {
        "tokens_used": 2500000,
        "cost": 12.50,
        "by_provider": {
            "groq": 1800000,
            "openai": 700000
        }
    },
    "response_time": {
        "average_ms": 350,
        "p95_ms": 800,
        "p99_ms": 1200
    }
}
```

### Métricas do Bot

```http
GET /api/v1/analytics/bots/{bot_id}
Authorization: Bearer {access_token}
```

### Uso de LLM

```http
GET /api/v1/analytics/llm-usage?bot_id={bot_id}&period=7d
Authorization: Bearer {access_token}
```

---

## 🔔 Notificações

### Listar Notificações

```http
GET /api/v1/notifications?unread_only=true
Authorization: Bearer {access_token}
```

### Marcar como Lida

```http
PATCH /api/v1/notifications/{notification_id}/read
Authorization: Bearer {access_token}
```

### Marcar Todas como Lidas

```http
POST /api/v1/notifications/read-all
Authorization: Bearer {access_token}
```

---

## 🎫 Suporte

### Listar Tickets

```http
GET /api/v1/support/tickets
Authorization: Bearer {access_token}
```

### Criar Ticket

```http
POST /api/v1/support/tickets
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "subject": "Bot não responde",
    "description": "Meu bot parou de responder ontem...",
    "priority": "high"
}
```

### Responder Ticket

```http
POST /api/v1/support/tickets/{ticket_id}/reply
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "message": "Aqui está mais informações..."
}
```

---

## 🛠️ Admin

### Listar Usuários

```http
GET /api/v1/admin/users?page=1&limit=20
Authorization: Bearer {admin_token}
```

### Atualizar Usuário

```http
PATCH /api/v1/admin/users/{user_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "role": "manager",
    "is_active": false
}
```

### Estatísticas do Sistema

```http
GET /api/v1/admin/stats
Authorization: Bearer {admin_token}
```

### Logs de Auditoria

```http
GET /api/v1/admin/audit-logs?user_id={user_id}&action=login
Authorization: Bearer {admin_token}
```

---

## 🔌 Webhooks

### Webhook WhatsApp

```http
POST /api/v1/webhooks/whatsapp
X-Webhook-Signature: {hmac_signature}
Content-Type: application/json

{
    "event": "message.received",
    "data": {
        "from": "5511999999999",
        "message_id": "msg-uuid",
        "text": "Olá!",
        "timestamp": "2025-06-21T10:00:00Z"
    }
}
```

### Webhook Stripe

```http
POST /api/v1/webhooks/stripe
Stripe-Signature: {stripe_signature}
Content-Type: application/json
```

---

## ❌ Códigos de Erro

| Código | Descrição | HTTP |
|---|---|---|
| `INVALID_CREDENTIALS` | Email ou senha incorretos | 401 |
| `TOKEN_EXPIRED` | Token JWT expirado | 401 |
| `INSUFFICIENT_PERMISSIONS` | Sem permissão para o recurso | 403 |
| `RESOURCE_NOT_FOUND` | Recurso não encontrado | 404 |
| `VALIDATION_ERROR` | Erro de validação nos dados | 422 |
| `RATE_LIMITED` | Muitas requisições | 429 |
| `LICENSE_EXPIRED` | Licença expirada | 403 |
| `LICENSE_REVOKED` | Licença revogada | 403 |
| `PLAN_LIMIT_EXCEEDED` | Limite do plano excedido | 403 |
| `INTERNAL_ERROR` | Erro interno do servidor | 500 |

### Formato de Erro

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Dados inválidos",
        "details": [
            {
                "field": "email",
                "message": "Email inválido"
            }
        ]
    }
}
```

---

## 🔗 Próximos Passos

- [Segurança](10-seguranca.md) — Autenticação e segurança
- [Flora AI](09-flora-ai.md) — Chat com a Flora
- [Instalação](15-instalacao.md) — Como instalar
- [FAQ](faq.md) — Perguntas frequentes

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Segurança](10-seguranca.md) | [Próximo: Estrutura de Pastas](12-estrutura-pastas.md)

</div>
