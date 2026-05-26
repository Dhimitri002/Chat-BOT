# 💰 API de Planos

> **Base URL:** `/api/v1/plans`

Gerenciamento dos 7 planos da plataforma Flora.

---

## Os 7 Planos

| Plan | Preco/mes | Preco/ano | Bots | Msgs/dia | LLM | Suporte |
|------|-----------|-----------|------|----------|-----|---------|
| **Starter** | R$ 27 | R$ 270 | 1 | 100 | Nao | Comunidade |
| **Basic** | R$ 47 | R$ 470 | 2 | 500 | Nao | Email |
| **Plus** | R$ 67 | R$ 670 | 3 | 1.000 | Nao | Email + Chat |
| **Pro** | R$ 97 | R$ 970 | 5 | 2.500 | Groq | Prioritario |
| **Master** | R$ 197 | R$ 1.970 | 15 | 10.000 | Groq+Gemini+OpenAI | Premium |
| **Elite** | R$ 397 | R$ 3.970 | 50 | 50.000 | Todos | VIP |
| **Enterprise** | Sob consulta | Sob consulta | Ilimitado | Ilimitado | Todos + Ollama | Dedicado |

---

## Modelo Plano

```json
{
  "id": "uuid",
  "name": "Pro",
  "slug": "pro",
  "description": "Para negocios em crescimento",
  "price_monthly": 97.00,
  "price_yearly": 970.00,
  "currency": "BRL",
  "max_bots": 5,
  "max_messages_per_day": 2500,
  "max_users": 1,
  "max_conversations": 500,
  "llm_enabled": true,
  "llm_provider": "groq",
  "llm_daily_limit": 500,
  "priority": 4,
  "is_popular": false,
  "is_active": true,
  "features": [
    "5 bots",
    "2.500 msgs/dia",
    "LLM Groq",
    "Suporte prioritario",
    "Analytics avancado"
  ]
}
```

---

## GET /plans

Listar todos os planos ativos (para pagina de precos).

**Query Parameters:**
| Param | Tipo | Descricao |
|-------|------|-----------|
| `active_only` | bool | Apenas planos ativos (default: true) |
| `include_inactive` | bool | Incluir inativos |

**Response (200 OK):**
```json
{
  "plans": [
    {
      "id": "uuid-1",
      "name": "Starter",
      "slug": "starter",
      "price_monthly": 27.00,
      "price_yearly": 270.00,
      "max_bots": 1,
      "max_messages_per_day": 100,
      "llm_enabled": false,
      "features": ["1 bot", "100 msgs/dia", "Suporte comunidade"],
      "is_popular": false
    },
    {
      "id": "uuid-4",
      "name": "Pro",
      "slug": "pro",
      "price_monthly": 97.00,
      "price_yearly": 970.00,
      "max_bots": 5,
      "max_messages_per_day": 2500,
      "llm_enabled": true,
      "llm_provider": "groq",
      "features": ["5 bots", "2.500 msgs/dia", "LLM Groq", "Suporte prioritario"],
      "is_popular": true
    }
  ],
  "total": 7
}
```

---

## GET /plans/{plan_id}

Detalhes de um plano.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Pro",
  "slug": "pro",
  "description": "Para negocios em crescimento",
  "price_monthly": 97.00,
  "price_yearly": 970.00,
  "currency": "BRL",
  "max_bots": 5,
  "max_messages_per_day": 2500,
  "max_users": 1,
  "max_conversations": 500,
  "llm_enabled": true,
  "llm_provider": "groq",
  "llm_daily_limit": 500,
  "priority": 4,
  "is_popular": true,
  "is_active": true,
  "features": [
    "5 bots ativos",
    "2.500 mensagens/dia",
    "LLM Groq (llama-3.1-70b)",
    "Suporte prioritario",
    "Analytics avancado",
    "3 transferencias de licenca"
  ],
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## Admin Endpoints

> Todos requerem `role: admin` ou `role: superadmin`

### POST /plans/admin/create

Criar novo plano.

**Request:**
```json
{
  "name": "Novo Plano",
  "slug": "novo-plano",
  "description": "Descricao do plano",
  "price_monthly": 147.00,
  "price_yearly": 1470.00,
  "max_bots": 10,
  "max_messages_per_day": 5000,
  "llm_enabled": true,
  "llm_provider": "groq",
  "llm_daily_limit": 1000,
  "is_popular": false,
  "features": ["Feature 1", "Feature 2"]
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Novo Plano",
  "slug": "novo-plano",
  "price_monthly": 147.00,
  "created_at": "2026-05-26T15:00:00Z"
}
```

### PUT /plans/admin/{plan_id}

Atualizar plano.

### DELETE /plans/admin/{plan_id}

Deletar plano.

### POST /plans/admin/{plan_id}/toggle

Ativar/desativar plano.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "is_active": false,
  "message": "Plano desativado"
}
```

---

## Comparacao de Planos

### GET /plans/compare

Endpoint especial para gerar tabela de comparacao de planos.

**Response (200 OK):**
```json
{
  "plans": [...],
  "features": [
    {
      "name": "Bots ativos",
      "values": {
        "starter": "1",
        "basic": "2",
        "plus": "3",
        "pro": "5",
        "master": "15",
        "elite": "50",
        "enterprise": "Ilimitado"
      }
    },
    {
      "name": "Mensagens/dia",
      "values": {
        "starter": "100",
        "basic": "500",
        ...
      }
    },
    {
      "name": "LLM",
      "values": {
        "starter": false,
        "basic": false,
        "plus": false,
        "pro": "groq",
        "master": "groq+gemini+openai",
        "elite": "all",
        "enterprise": "all+ollama"
      }
    }
  ]
}
```

---

## Exemplos cURL

```bash
# Listar planos
curl http://localhost:8000/api/v1/plans

# Ver plano especifico
curl http://localhost:8000/api/v1/plans/plan-uuid

# Comparar
curl http://localhost:8000/api/v1/plans/compare

# Admin: criar plano
curl -X POST http://localhost:8000/api/v1/plans/admin/create \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Custom","slug":"custom","price_monthly":147,"max_bots":10}'

# Admin: atualizar
curl -X PUT http://localhost:8000/api/v1/plans/admin/plan-uuid \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"price_monthly":157}'
```
