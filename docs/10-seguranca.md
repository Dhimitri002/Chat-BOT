# 🌸 FLORA PLATFORM — Segurança

## Princípio Fundamental

> **O app do cliente NUNCA deve conter a chave mastra do sistema.**
> Toda validação crítica acontece no backend. O cliente é "burro" por design.

## Camada 1: Transporte

```
• HTTPS/TLS 1.3 em toda comunicação
• Certificate pinning nos apps (Kivy)
• HSTS headers no backend
• Cipher suites fortes apenas
• Desabilitar TLS 1.0, 1.1
```

## Camada 2: Autenticação

### Senhas
```python
# Argon2id — vencedor do Password Hashing Competition
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # iterações
    memory_cost=65536,   # 64MB de RAM
    parallelism=4,       # threads
    hash_len=32,         # tamanho do hash
    salt_len=16          # tamanho do salt
)

# Hash
hash = ph.hash(password)

# Verify
ph.verify(hash, password)
```

### JWT (JSON Web Tokens)
```python
import jwt
from datetime import datetime, timedelta

# Access token — curto (15 min)
access_token = jwt.encode({
    "sub": user.id,
    "role": user.role,
    "exp": datetime.utcnow() + timedelta(minutes=15),
    "iat": datetime.utcnow(),
    "jti": str(uuid4()),  # unique token ID para revogação
}, PRIVATE_KEY, algorithm="RS256")

# Refresh token — mais longo (7 dias)
refresh_token = jwt.encode({
    "sub": user.id,
    "exp": datetime.utcnow() + timedelta(days=7),
    "type": "refresh",
    "jti": str(uuid4()),
}, PRIVATE_KEY, algorithm="RS256")
```

### 2FA (TOTP)
```python
import pyotp

# Gerar secret
secret = pyotp.random_base32()

# Gerar QR Code para Google Authenticator
uri = pyotp.totp.TOTP(secret).provisioning_uri(
    name=user.email,
    issuer_name="Flora Platform"
)

# Verificar código
totp = pyotp.TOTP(secret)
is_valid = totp.verify(user_provided_code, valid_window=1)
```

### Rate Limiting
```python
# Por IP: 100 req/min
# Por usuário: 200 req/min
# Login: 5 tentativas / 15 min → bloqueio 30 min
# Validação de licença: 10 tentativas / hora

from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/15minute")
async def login(request: Request, credentials: LoginSchema):
    ...
```

### Proteção Brute Force
```python
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=30)

async def check_login_attempts(user):
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(423, "Conta bloqueada. Tente novamente em 30 min.")
    
    if user.login_attempts >= MAX_ATTEMPTS:
        user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
        user.login_attempts = 0
        raise HTTPException(423, "Muitas tentativas. Conta bloqueada.")
```

## Camada 3: Autorização (RBAC)

```
Roles:
  superadmin  → Acesso total a tudo
  admin       → Gerencia bots, clientes, licenças (não pode deletar superadmin)
  reseller    → Gerencia seus próprios clientes, gera licenças
  client      → Acesso apenas ao seu próprio bot e dados

Permissões por role:
  superadmin: [*:create, *:read, *:update, *:delete]
  admin: [bots:*, clients:read, clients:update, licenses:*, analytics:read]
  reseller: [clients:create, clients:read (own), licenses:create (own)]
  client: [bot:read (own), bot:update (own), analytics:read (own)]
```

## Camada 4: Criptografia de Dados

### AES-256-GCM para dados sensíveis
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class EncryptionService:
    def __init__(self):
        # Chave de 256 bits — armazenada em variável de ambiente
        self.key = bytes.fromhex(os.environ["ENCRYPTION_KEY"])
        self.aesgcm = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self.aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            None  # additional authenticated data
        )
        # Retorna nonce + ciphertext em base64
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
```

### Dados que DEVEM ser criptografados em repouso:
- Chaves de API das LLMs
- Secrets de webhooks
- TOTP secrets dos usuários
- Tokens de refresh (opcional, recomendado)
- Dados de pagamento (tokens, não números de cartão)

### HMAC para integridade
```python
import hmac
import hashlib

def generate_hmac(data: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_hmac(data: str, secret: str, expected_hmac: str) -> bool:
    return hmac.compare_digest(generate_hmac(data, secret), expected_hmac)
```

## Camada 5: Licenças

### Geração do Par de Chaves
```python
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives import serialization

# RSA-2048 (ou ECC P-256 para melhor performance)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

public_key = private_key.public_key()

# Serializar para armazenar
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(MASTER_PASSWORD)
)

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
```

### Assinatura da Licença
```python
from cryptography.hazmat.primitives.asymmetric import padding

def sign_license(license_key: str, private_key) -> str:
    signature = private_key.sign(
        license_key.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()
```

### Fingerprint do Dispositivo
```python
import hashlib
import platform

def get_device_fingerprint() -> str:
    """Gera fingerprint único do dispositivo"""
    components = [
        platform.node(),           # hostname
        platform.machine(),        # arquitetura
        platform.processor(),      # processador
        os.environ.get("COMPUTERNAME", ""),
        # Adicionar mais identificadores conforme necessário
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()
```

### Anti-Replay
```python
import time
import redis

def check_anti_replay(token_jti: str, redis_client) -> bool:
    """Verifica se o token já foi usado (replay attack)"""
    key = f"token:{token_jti}"
    if redis_client.exists(key):
        return False  # Token já usado — replay!
    
    # Registra token com expiração
    redis_client.setex(key, 900, "used")  # 15 min
    return True
```

## Camada 6: Auditoria

```python
async def audit_log(
    db,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID,
    old_value: dict = None,
    new_value: dict = None,
    request: Request = None
):
    """Registra toda ação sensível"""
    await db.execute(
        insert(AuditLog).values(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    )
```

### Ações que DEVEM ser auditadas:
- Login (sucesso e falha)
- Criação/revogação de licença
- Ativação/desativação de bot
- Alteração de plano
- Alteração de configuração sensível
- Exportação de dados
- Tentativa de acesso negado
- Validação de licença (falha)
- Alteração de senha
- Habilitação/desabilitação de 2FA

## Checklist de Segurança

```
✅ Senhas com Argon2id
✅ JWT com RS256 (assimétrico)
✅ Access token curto (15 min)
✅ Refresh token rotativo
✅ 2FA/TOTP para admins
✅ Rate limiting em todos os endpoints
✅ Criptografia AES-256-GCM para segredos
✅ Assinatura digital RSA para licenças
✅ Fingerprint de dispositivo
✅ Anti-replay tokens
✅ HTTPS obrigatório
✅ CORS configurado
✅ Input validation (Pydantic)
✅ SQL injection prevention (SQLAlchemy ORM)
✅ XSS prevention (sem HTML rendering)
✅ CSRF tokens (onde aplicável)
✅ Logs de auditoria completos
✅ Bloqueio por brute force
✅ Chaves nunca no código cliente
✅ Feature flags server-side
✅ Validação de licença online
✅ Revogação remota
✅ Backups criptografados
✅ Variáveis de ambiente para segredos
✅ Segregação de dados por tenant
✅ Princípio de menor privilégio
```
