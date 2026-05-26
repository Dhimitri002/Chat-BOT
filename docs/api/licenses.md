# 🔑 API de Licencas

> **Base URL:** `/api/v1/licenses`

Sistema de licencas com assinatura digital RSA e criptografia AES-256-GCM.

---

## Modelo Licenca

```json
{
  "id": "uuid",
  "license_key": "FLORA-XXXX-XXXX-XXXX-XXXX",
  "plan_id": "plan-uuid",
  "user_id": "user-uuid",
  "status": "active",
  "device_fingerprint": "sha256-hash",
  "machine_id": "machine-uuid",
  "max_machines": 1,
  "transfers_used": 0,
  "max_transfers": 3,
  "activated_at": "2026-01-15T10:00:00Z",
  "expires_at": "2026-07-15T10:00:00Z",
  "grace_period_ends_at": "2026-07-22T10:00:00Z",
  "created_at": "2026-01-15T09:00:00Z"
}
```

**Status possiveis:** `active`, `expired`, `revoked`, `suspended`, `pending`

---

## POST /licenses/validate

Validar uma chave de licenca. **Nao requer autenticacao** (usado pelo app cliente na ativacao).

**Request:**
```json
{
  "license_key": "FLORA-XXXX-XXXX-XXXX-XXXX",
  "device_fingerprint": "sha256-do-device"
}
```

**Response (200 OK) — Valida:**
```json
{
  "valid": true,
  "plan": {
    "id": "plan-uuid",
    "name": "Pro",
    "features": {
      "max_bots": 3,
      "max_messages_per_day": 1000,
      "llm_enabled": true,
      "llm_provider": "groq"
    }
  },
  "expires_at": "2026-07-15T10:00:00Z",
  "days_remaining": 50,
  "features": {
    "max_bots": 3,
    "max_messages_per_day": 1000,
    "llm_enabled": true
  }
}
```

**Response (200 OK) — Invalida:**
```json
{
  "valid": false,
  "reason": "Licenca expirada"
}
```

**Razoes de invalidacao:**
| Razao | Descricao |
|-------|-----------|
| `invalid_key` | Chave nao encontrada |
| `expired` | Licenca expirada (fora do grace period) |
| `revoked` | Licenca revogada pelo admin |
| `device_mismatch` | Device fingerprint diferente |
| `max_machines` | Limite de maquinas atingido |
| `invalid_signature` | Assinatura digital invalida |

---

## POST /licenses/activate

Ativar licenca para o usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "license_key": "FLORA-XXXX-XXXX-XXXX-XXXX",
  "device_fingerprint": "sha256-do-device"
}
```

**Response (200 OK):**
```json
{
  "message": "Licenca ativada com sucesso",
  "license": {
    "id": "uuid",
    "plan_name": "Pro",
    "expires_at": "2026-07-15T10:00:00Z",
    "days_remaining": 50
  }
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 400 | Licenca invalida ou expirada |
| 409 | Licenca ja ativada por outro usuario |
| 403 | Limite de maquinas atingido |

---

## GET /licenses

Listar licencas do usuario autenticado.

**Response (200 OK):**
```json
{
  "licenses": [
    {
      "id": "uuid",
      "license_key": "FLORA-XXXX-XXXX-XXXX",
      "plan_name": "Pro",
      "status": "active",
      "expires_at": "2026-07-15T10:00:00Z",
      "days_remaining": 50
    }
  ],
  "total": 1
}
```

---

## GET /licenses/{license_id}

Obter detalhes de uma licenca.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "license_key": "FLORA-XXXX-XXXX-XXXX-XXXX",
  "plan": {
    "id": "plan-uuid",
    "name": "Pro",
    "price_monthly": 97.00
  },
  "status": "active",
  "device_fingerprint": "sha256-hash",
  "activated_at": "2026-01-15T10:00:00Z",
  "expires_at": "2026-07-15T10:00:00Z",
  "grace_period_ends_at": "2026-07-22T10:00:00Z",
  "days_remaining": 50,
  "max_machines": 1,
  "transfers_used": 0,
  "max_transfers": 3
}
```

---

## POST /licenses/{license_id}/transfer

Transferir licenca para outro device.

**Request:**
```json
{
  "new_device_fingerprint": "sha256-novo-device"
}
```

**Response (200 OK):**
```json
{
  "message": "Licenca transferida com sucesso",
  "transfers_remaining": 2
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 403 | Limite de transferencias atingido |

---

## Admin Endpoints

> Requerem `role: admin` ou `role: superadmin`

### POST /licenses/admin/create

Criar nova licenca (admin).

**Request:**
```json
{
  "plan_id": "plan-uuid",
  "user_id": "user-uuid",
  "duration_months": 6,
  "max_machines": 1
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "license_key": "FLORA-A1B2-C3D4-E5F6-G7H8",
  "plan_name": "Pro",
  "expires_at": "2026-11-26T10:00:00Z"
}
```

### POST /licenses/admin/{license_id}/revoke

Revogar licenca.

**Response (200 OK):**
```json
{
  "message": "Licenca revogada com sucesso"
}
```

### GET /licenses/admin/all

Listar todas as licencas (admin).

**Query Parameters:** `page`, `page_size`, `status`, `plan_id`, `user_id`

---

## Seguranca da Licenca

```
┌─────────────────────────────────────────────────┐
│           CADEIA DE SEGURANCA                    │
│                                                  │
│  1. RSA Signature                                │
│     sign(plan_id + user_id + expiry + machine)   │
│     → Impossivel falsificar sem private key      │
│                                                  │
│  2. AES-256-GCM Encryption                       │
│     encrypt(license_data, key)                   │
│     → Conteudo ilegivel sem key                  │
│                                                  │
│  3. Device Binding                               │
│     fingerprint = hash(hw_id + os + mac)         │
│     → Licenca so funciona na maquina autorizada  │
│                                                  │
│  4. Grace Period                                 │
│     7 dias apos expiracao                        │
│     → Cliente nao perde acesso imediatamente     │
│                                                  │
│  5. Transfer Limit                               │
│     Max 3 transferencias                         │
│     → Previne compartilhamento abusivo           │
└─────────────────────────────────────────────────┘
```

---

## Exemplos cURL

```bash
# Validar licenca
curl -X POST http://localhost:8000/api/v1/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"FLORA-XXXX-XXXX-XXXX","device_fingerprint":"abc123"}'

# Ativar licenca
curl -X POST http://localhost:8000/api/v1/licenses/activate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"license_key":"FLORA-XXXX-XXXX-XXXX","device_fingerprint":"abc123"}'

# Listar minhas licencas
curl http://localhost:8000/api/v1/licenses \
  -H "Authorization: Bearer <token>"

# Admin: criar licenca
curl -X POST http://localhost:8000/api/v1/licenses/admin/create \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"plan-uuid","user_id":"user-uuid","duration_months":12}'
```
