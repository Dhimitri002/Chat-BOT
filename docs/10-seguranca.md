# 🌸 FLORA PLATFORM — Segurança

> Documentação completa de segurança: criptografia, autenticação, licenças e proteção.

---

## 🔐 Visão Geral

A Flora Platform implementa segurança em múltiplas camadas:

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE REDE                            │
│  HTTPS │ WAF │ DDoS Protection │ Rate Limiting             │
├─────────────────────────────────────────────────────────────┤
│                    CAMADA DE API                             │
│  JWT │ CORS │ Input Validation │ CSRF Protection           │
├─────────────────────────────────────────────────────────────┤
│                    CAMADA DE APLICAÇÃO                       │
│  Auth │ RBAC │ Audit Log │ Anti-Clone                      │
├─────────────────────────────────────────────────────────────┤
│                    CAMADA DE DADOS                           │
│  Encryption │ Hashing │ Parameterized Queries │ Backups   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Criptografia

### Algoritmos Utilizados

| Uso | Algoritmo | Detalhes |
|---|---|---|
| **Senhas** | bcrypt | Custo 12, salt automático |
| **Assinatura de Licenças** | RSA-2048 | SHA-256, PKCS#1 v1.5 |
| **Dados Sensíveis** | AES-256 | Modo GCM, IV aleatório |
| **Tokens JWT** | HS256 | Chave simétrica (HMAC-SHA256) |
| **Comunicação** | TLS 1.3 | HTTPS obrigatório em produção |

### Chaves Criptográficas

```bash
# Gerar par de chaves RSA (licenças)
python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Salvar chave privada
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(b'senha-forte')
)
with open('keys/license_private.pem', 'wb') as f:
    f.write(pem_private)

# Salvar chave pública
public_key = private_key.public_key()
pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
with open('keys/license_public.pem', 'wb') as f:
    f.write(pem_public)

print('Chaves geradas com sucesso!')
"
```

### Gerenciamento de Chaves

| Chave | Onde | Rotação |
|---|---|---|
| `SECRET_KEY` | `.env` | A cada 90 dias |
| `JWT_SECRET` | `.env` | A cada 90 dias |
| `ENCRYPTION_KEY` | `.env` | A cada 180 dias |
| RSA Private Key | `keys/license_private.pem` | A cada 365 dias |
| RSA Public Key | `keys/license_public.pem` | A cada 365 dias |

---

## 🔐 Autenticação

### Fluxo JWT

```
┌────────┐                          ┌────────┐
│ Cliente│                          │ Servidor│
└───┬────┘                          └───┬────┘
    │  POST /auth/login                 │
    │  {email, password}                │
    │ ─────────────────────────────────▶│
    │                                   │
    │                           ┌───────▼───────┐
    │                           │ Verifica bcrypt│
    │                           │ Gera JWT       │
    │                           └───────┬───────┘
    │                                   │
    │  {access_token, refresh_token}    │
    │ ◀─────────────────────────────────│
    │                                   │
    │  GET /api/v1/bots                 │
    │  Authorization: Bearer {access}   │
    │ ─────────────────────────────────▶│
    │                                   │
    │                           ┌───────▼───────┐
    │                           │ Verifica JWT   │
    │                           │ Extrai user_id │
    │                           └───────┬───────┘
    │                                   │
    │  {bots: [...]}                    │
    │ ◀─────────────────────────────────│
```

### Access Token

| Atributo | Valor |
|---|---|
| **Algoritmo** | HS256 |
| **Expiração** | 30 minutos (configurável) |
| **Payload** | user_id, email, role, permissions |
| **Header** | Authorization: Bearer {token} |

### Refresh Token

| Atributo | Valor |
|---|---|
| **Expiração** | 7 dias (configurável) |
| **Armazenamento** | Banco de dados (hasheado) |
| **Rotação** | Novo refresh token a cada uso |
| **Revogação** | Possível via logout |

### 2FA (Autenticação de Dois Fatores)

```python
# Fluxo 2FA
# 1. Usuário habilita 2FA
POST /auth/2fa/setup
# Retorna: {secret, qr_code_uri}

# 2. Usuário verifica com app (Google Authenticator, Authy)
POST /auth/2fa/verify
Body: {code: "123456"}
# Retorna: {backup_codes: [...]}

# 3. Login com 2FA
POST /auth/login
Body: {email, password, totp_code: "123456"}
```

### Políticas de Senha

| Regra | Valor |
|---|---|
| **Tamanho mínimo** | 8 caracteres |
| **Tamanho máximo** | 128 caracteres |
| **Requer maiúscula** | Sim |
| **Requer minúscula** | Sim |
| **Requer número** | Sim |
| **Requer especial** | Sim |
| **Histórico** | Últimas 5 senhas não podem ser reutilizadas |
| **Expiração** | 90 dias (configurável) |
| **Bloqueio** | 5 tentativas falhas = 15 min bloqueio |

---

## 🛡️ Autorização (RBAC)

### Roles

| Role | Permissões |
|---|---|
| **admin** | Acesso total a tudo |
| **manager** | Gerenciar bots, licenças, clientes |
| **support** | Ver tickets, ajudar clientes |
| **client** | Gerenciar próprio bot |
| **viewer** | Somente leitura |

### Permissões por Endpoint

| Endpoint | Admin | Manager | Support | Client | Viewer |
|---|---|---|---|---|---|
| `/admin/*` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/licenses/*` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/bots/*` | ✅ | ✅ | ❌ | ✅ (own) | ❌ |
| `/support/*` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/analytics/*` | ✅ | ✅ | ❌ | ✅ (own) | ✅ |
| `/users/*` | ✅ | ✅ | ❌ | ✅ (own) | ❌ |

---

## 📜 Sistema de Licenças

### Geração de Licença

```python
# 1. Gerar par de chaves RSA (uma vez)
private_key, public_key = generate_rsa_keypair(2048)

# 2. Criar licença
license_data = {
    "user_id": "uuid-do-usuario",
    "plan_id": "uuid-do-plano",
    "expires_at": "2025-12-31T23:59:59Z",
    "max_devices": 1,
    "hardware_id": None  # preenchido no primeiro uso
}

# 3. Assinar digitalmente
signature = rsa_sign(
    data=json.dumps(license_data, sort_keys=True),
    private_key=private_key,
    hash_algorithm="SHA-256"
)

# 4. Gerar chave da licença
license_key = base64_encode(license_data + "." + signature)
```

### Validação de Licença

```
┌─────────────────────────────────────────────────────────────┐
│                  VALIDAÇÃO DE LICENÇA                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Decodificar licença (base64)                           │
│  2. Extrair dados e assinatura                              │
│  3. Verificar assinatura com chave pública RSA              │
│     └─ Inválida? → REJECT                                  │
│  4. Verificar expiração                                     │
│     └─ Expirada? → REJECT                                  │
│  5. Verificar se está revogada (DB lookup)                  │
│     └─ Revogada? → REJECT                                  │
│  6. Verificar hardware binding                              │
│     └─ Dispositivo diferente? → REJECT                     │
│  7. Verificar limites do plano                              │
│     └─ Excedido? → REJECT                                  │
│  8. ✅ LICENÇA VÁLIDA                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Status da Licença

| Status | Descrição |
|---|---|
| **active** | Licença válida e em uso |
| **expired** | Expirou a data de validade |
| **revoked** | Revogada pelo admin |
| **suspended** | Suspensa temporariamente |
| **pending** | Aguardando ativação |

---

## 🚫 Anti-Clone

O sistema anti-clone impede que uma licença seja usada em múltiplos dispositivos:

```python
# Fluxo Anti-Clone
def validate_device(license_key, hardware_id):
    license = get_license(license_key)

    if license.hardware_id is None:
        # Primeiro uso: vincular dispositivo
        license.hardware_id = hardware_id
        save(license)
        return True

    if license.hardware_id != hardware_id:
        # Dispositivo diferente: bloquear
        log_security_event("CLONE_ATTEMPT", license_key, hardware_id)
        return False

    return True
```

### Hardware ID

O hardware ID é gerado a partir de:
- CPU serial number
- MAC address
- Disk serial number
- Machine name

---

## 🚦 Rate Limiting

### Limites por Endpoint

| Endpoint | Limite | Janela |
|---|---|---|
| `/auth/login` | 5 req | 1 minuto |
| `/auth/register` | 3 req | 10 minutos |
| `/api/v1/*` (auth) | 100 req | 1 minuto |
| `/api/v1/*` (admin) | 200 req | 1 minuto |
| `/flora/chat` | 30 req | 1 minuto |
| `/whatsapp/*` | 50 req | 1 minuto |

### Headers de Rate Limit

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1719000000
```

---

## 📋 Audit Log

Todas as ações importantes são registradas:

```python
{
    "id": "uuid",
    "user_id": "uuid-do-usuario",
    "action": "bot.create",
    "resource": "bot",
    "resource_id": "uuid-do-bot",
    "details": {"name": "Bot de Vendas"},
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2025-06-21T10:30:00Z"
}
```

### Eventos Auditados

| Evento | Severidade |
|---|---|
| Login (sucesso/falha) | Info / Warning |
| Criação de bot | Info |
| Exclusão de bot | Warning |
| Geração de licença | Info |
| Revogação de licença | Critical |
| Tentativa de clone | Critical |
| Alteração de plano | Info |
| Exportação de dados | Warning |
| Alteração de senha | Info |
| Habilitação de 2FA | Info |

---

## 🔒 Headers de Segurança

```python
# Headers aplicados em todas as respostas
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## 🛡️ Proteção contra Ataques Comuns

| Ataque | Proteção |
|---|---|
| **SQL Injection** | SQLAlchemy ORM (parameterized queries) |
| **XSS** | Pydantic validation + CSP headers |
| **CSRF** | JWT (stateless) + SameSite cookies |
| **Brute Force** | Rate limiting + account lockout |
| **Session Hijacking** | JWT com expiração curta + refresh rotation |
| **Man-in-the-Middle** | TLS 1.3 obrigatório |
| **Replay Attack** | JWT jti claim + nonce |
| **IDOR** | RBAC + resource ownership checks |
| **Mass Assignment** | Pydantic schemas (explicit fields) |

---

## 🔗 Próximos Passos

- [Instalação](15-instalacao.md) — Configurar o ambiente
- [Deploy](deploy.md) — Segurança em produção
- [API Endpoints](11-api-endpoints.md) — Endpoints e autenticação
- [FAQ](faq.md) — Perguntas frequentes sobre segurança

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Flora AI](09-flora-ai.md) | [Próximo: API Endpoints](11-api-endpoints.md)

</div>
