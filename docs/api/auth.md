# 🔐 API de Autenticacao

> **Base URL:** `/api/v1/auth`

Todos os endpoints de autenticacao. Nenhum requer autenticacao previa (exceto `me` e `logout`).

---

## POST /register

Registrar novo usuario.

**Request:**
```json
{
  "email": "usuario@example.com",
  "password": "SenhaForte@123",
  "name": "Nome Usuario"
}
```

| Campo | Tipo | Obrigatorio | Regras |
|-------|------|-------------|--------|
| `email` | string | Sim | Email valido, unico |
| `password` | string | Sim | Min 8 chars, 1 maiuscula, 1 numero |
| `name` | string | Nao | Max 100 chars |

**Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "usuario@example.com",
  "name": "Nome Usuario",
  "role": "user",
  "is_active": true,
  "is_2fa_enabled": false,
  "created_at": "2026-05-26T15:00:00Z"
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 409 | Email ja cadastrado |
| 422 | Dados invalidos |

---

## POST /login

Autenticar usuario e receber tokens.

**Request:**
```json
{
  "email": "usuario@example.com",
  "password": "SenhaForte@123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "usuario@example.com",
    "name": "Nome Usuario",
    "role": "user"
  }
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 401 | Credenciais invalidas |
| 403 | Conta desativada |
| 429 | Muitas tentativas (rate limit) |

---

## POST /refresh

Renovar access token usando refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Erros:**
| Status | Descricao |
|--------|-----------|
| 401 | Refresh token invalido ou expirado |

---

## GET /me

Obter dados do usuario autenticado.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "usuario@example.com",
  "name": "Nome Usuario",
  "role": "user",
  "is_active": true,
  "is_2fa_enabled": false,
  "created_at": "2026-01-15T10:00:00Z"
}
```

---

## POST /logout

Invalidar token atual (blacklist).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

---

## POST /forgot-password

Solicitar recuperacao de senha.

**Request:**
```json
{
  "email": "usuario@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Se o email existir, um link de recuperacao foi enviado"
}
```

---

## POST /reset-password

Redefinir senha com token de recuperacao.

**Request:**
```json
{
  "token": "reset-token-uuid",
  "new_password": "NovaSenha@456"
}
```

**Response (200 OK):**
```json
{
  "message": "Senha alterada com sucesso"
}
```

---

## 2FA (Planejado)

### POST /2fa/setup
Configurar autenticador TOTP.

### POST /2fa/verify
Verificar codigo TOTP.

### POST /2fa/disable
Desabilitar 2FA.

---

## Protecao contra Brute Force

| Regra | Valor |
|-------|-------|
| Max tentativas de login | 5 por minuto |
| Tempo de bloqueio | 15 minutos |
| Rate limit geral | 100 req/min |

---

## Exemplo Completo (cURL)

```bash
# Registro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"Senha@123","name":"Usuario"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"Senha@123"}'

# Usar token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```
