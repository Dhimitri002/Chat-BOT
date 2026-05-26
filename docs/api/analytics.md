# 📊 API de Analytics

> **Base URL:** `/api/v1/analytics`

Metricas, relatorios e dashboards. Todos os endpoints requerem autenticacao.

---

## GET /analytics/dashboard

Dashboard principal com metricas resumidas.

**Response (200 OK):**
```json
{
  "period": "last_30_days",
  "summary": {
    "total_messages": 12500,
    "messages_in": 6250,
    "messages_out": 6250,
    "active_conversations": 145,
    "active_bots": 3,
    "new_conversations": 85,
    "avg_response_time_seconds": 3.2,
    "success_rate": 0.97
  },
  "today": {
    "messages": 420,
    "conversations": 18,
    "errors": 3
  },
  "trends": {
    "messages_change_percent": 12.5,
    "conversations_change_percent": 8.3
  }
}
```

---

## GET /analytics/messages

Dados detalhados de mensagens.

**Query Parameters:**
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `period` | string | `7d` | `1d`, `7d`, `30d`, `90d`, `1y` |
| `bot_id` | string | (todos) | Filtrar por bot |
| `granularity` | string | `day` | `hour`, `day`, `week`, `month` |

**Response (200 OK):**
```json
{
  "period": "7d",
  "granularity": "day",
  "data": [
    {
      "date": "2026-05-20",
      "messages_in": 180,
      "messages_out": 175,
      "total": 355,
      "errors": 2
    },
    {
      "date": "2026-05-21",
      "messages_in": 210,
      "messages_out": 205,
      "total": 415,
      "errors": 1
    }
  ],
  "summary": {
    "inbound": 1250,
    "outbound": 1200,
    "total": 2450,
    "errors": 12
  }
}
```

---

## GET /analytics/conversations

Metricas de conversas.

**Response (200 OK):**
```json
{
  "total_conversations": 245,
  "active_conversations": 85,
  "new_conversations_today": 12,
  "avg_messages_per_conversation": 8.5,
  "median_response_time_seconds": 2.8,
  "top_conversations": [
    {
      "user_phone": "5511999999999",
      "bot_name": "Bot Principal",
      "message_count": 145,
      "last_message_at": "2026-05-26T15:30:00Z"
    }
  ],
  "distribution_by_day": [
    {"day": "seg", "count": 45},
    {"day": "ter", "count": 62},
    {"day": "qua", "count": 55},
    {"day": "qui", "count": 48},
    {"day": "sex", "count": 35}
  ]
}
```

---

## GET /analytics/bots

Metricas por bot.

**Response (200 OK):**
```json
{
  "bots": [
    {
      "bot_id": "uuid-1",
      "bot_name": "Bot Principal",
      "total_messages": 8500,
      "messages_today": 245,
      "active_conversations": 62,
      "success_rate": 0.98,
      "avg_response_time_seconds": 2.5,
      "llm_usage": {
        "total_tokens": 125000,
        "requests": 850,
        "cost_usd": 0.00
      }
    },
    {
      "bot_id": "uuid-2",
      "bot_name": "Bot Secundario",
      "total_messages": 4000,
      "messages_today": 120,
      "active_conversations": 23,
      "success_rate": 0.95,
      "avg_response_time_seconds": 4.2,
      "llm_usage": {
        "total_tokens": 45000,
        "requests": 320,
        "cost_usd": 0.00
      }
    }
  ]
}
```

---

## GET /analytics/llm

Uso de LLM detalhado.

**Response (200 OK):**
```json
{
  "total_tokens": 170000,
  "total_requests": 1170,
  "total_cost_usd": 0.00,
  "by_provider": {
    "groq": {
      "tokens": 120000,
      "requests": 850,
      "cost_usd": 0.00
    },
    "gemini": {
      "tokens": 35000,
      "requests": 220,
      "cost_usd": 0.00
    },
    "openai": {
      "tokens": 15000,
      "requests": 100,
      "cost_usd": 0.45
    }
  },
  "by_model": {
    "llama-3.1-70b-versatile": {
      "tokens": 120000,
      "requests": 850
    },
    "gemini-1.5-flash": {
      "tokens": 35000,
      "requests": 220
    },
    "gpt-4o-mini": {
      "tokens": 15000,
      "requests": 100
    }
  },
  "daily_usage": [
    {
      "date": "2026-05-26",
      "tokens": 8500,
      "requests": 62,
      "cost_usd": 0.00
    }
  ]
}
```

---

## GET /analytics/response-time

Analise de tempo de resposta.

**Response (200 OK):**
```json
{
  "avg_seconds": 3.2,
  "median_seconds": 2.8,
  "p95_seconds": 8.5,
  "p99_seconds": 15.2,
  "distribution": [
    {"range": "0-1s", "count": 450},
    {"range": "1-3s", "count": 1200},
    {"range": "3-5s", "count": 650},
    {"range": "5-10s", "count": 120},
    {"range": "10s+", "count": 30}
  ]
}
```

---

## Admin Analytics

> Requerem `role: admin` ou `role: superadmin`

### GET /analytics/admin/revenue

Metricas de receita.

**Response (200 OK):**
```json
{
  "total_revenue": 12500.00,
  "monthly_recurring_revenue": 4200.00,
  "annual_recurring_revenue": 50400.00,
  "revenue_by_plan": {
    "starter": 810.00,
    "basic": 1410.00,
    "plus": 1340.00,
    "pro": 4850.00,
    "master": 3940.00,
    "elite": 159.00
  },
  "monthly_growth_percent": 15.2,
  "churn_rate": 2.1
}
```

### GET /analytics/admin/users

Metricas de usuarios.

**Response (200 OK):**
```json
{
  "total_users": 152,
  "active_users": 128,
  "new_users_today": 5,
  "new_users_this_month": 42,
  "users_by_plan": {
    "starter": 45,
    "basic": 38,
    "plus": 25,
    "pro": 28,
    "master": 12,
    "elite": 4
  },
  "retention_rate": 0.89
}
```

### GET /analytics/admin/platform

Metricas gerais da plataforma.

**Response (200 OK):**
```json
{
  "total_bots": 245,
  "active_bots": 198,
  "total_messages_all_time": 1250000,
  "total_conversations": 12500,
  "total_licenses": 152,
  "active_licenses": 145,
  "revoked_licenses": 3,
  "expired_licenses": 4,
  "uptime_percent": 99.95
}
```

---

## Export

### GET /analytics/export

Exportar relatorio em CSV ou PDF.

**Query Parameters:**
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `type` | string | `csv` | `csv`, `pdf`, `json` |
| `report` | string | `messages` | `messages`, `conversations`, `revenue`, `llm` |
| `period` | string | `30d` | Periodo |

**Response:** Arquivo para download.

---

## Exemplos cURL

```bash
# Dashboard
curl http://localhost:8000/api/v1/analytics/dashboard \
  -H "Authorization: Bearer <token>"

# Mensagens (ultimos 30 dias)
curl "http://localhost:8000/api/v1/analytics/messages?period=30d&granularity=day" \
  -H "Authorization: Bearer <token>"

# LLM usage
curl http://localhost:8000/api/v1/analytics/llm \
  -H "Authorization: Bearer <token>"

# Admin: receita
curl http://localhost:8000/api/v1/analytics/admin/revenue \
  -H "Authorization: Bearer <admin_token>"

# Export CSV
curl "http://localhost:8000/api/v1/analytics/export?type=csv&report=messages&period=30d" \
  -H "Authorization: Bearer <token>" \
  -o report.csv
```
