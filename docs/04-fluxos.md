# 🌸 FLORA PLATFORM — Fluxos Completos

## 1. Fluxo da Licença

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  ADMIN   │     │ BACKEND  │     │  CLIENTE │     │ BACKEND  │
│ cria     │     │ gera     │     │ digita   │     │ valida   │
│ licença  │────▶│ chave +  │────▶│ licença  │────▶│ assinatura│
│          │     │ assinatura│     │ no app   │     │ digital   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                       │                  │
                                       │            ┌─────┴─────┐
                                       │            │ Válida?    │
                                       │            │ • Assinat. │
                                       │            │ • Expirou? │
                                       │            │ • Revogada?│
                                       │            │ • Disposit.│
                                       │            └─────┬─────┘
                                       │           Sim │  │ Não
                                       │          ┌────┘  └────┐
                                       │          ▼            ▼
                                       │    Libera bot    Mostra erro
                                       │    + token JWT   específico
                                       │          │
                                       ▼          ▼
                                  ┌─────────────────┐
                                  │  App conectado  │
                                  │  sessão ativa   │
                                  │  refresh token  │
                                  └─────────────────┘
```

### Geração de Licença (código)

```python
import secrets
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization

def generate_license_key() -> str:
    """Gera chave legível: FLORA-XXXX-XXXX-XXXX-XXXX"""
    parts = [secrets.token_hex(2).upper() for _ in range(4)]
    return f"FLORA-{'-'.join(parts)}"

def sign_license(license_key: str, private_key) -> str:
    """Assina digitalmente a licença com RSA-PSS"""
    signature = private_key.sign(
        license_key.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()

def validate_license(license_key: str, device_fingerprint: str, db, public_key) -> dict:
    """Valida todos os aspectos da licença"""
    # 1. Busca no banco
    license = db.licenses.find_by_key_hash(hashlib.sha256(license_key.encode()).hexdigest())
    if not license:
        return {"valid": False, "reason": "not_found"}

    # 2. Verifica assinatura digital
    try:
        public_key.verify(
            base64.b64decode(license.signature),
            license_key.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except Exception:
        return {"valid": False, "reason": "invalid_signature"}

    # 3. Verifica status
    if license.status != "active":
        return {"valid": False, "reason": f"license_{license.status}"}

    # 4. Verifica expiração
    if license.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "reason": "expired"}

    # 5. Verifica dispositivo (anti-clonagem)
    if license.device_fingerprint and license.device_fingerprint != device_fingerprint:
        return {"valid": False, "reason": "device_mismatch"}

    # 6. Verifica rate de validações
    if license.validation_count >= license.max_validations:
        return {"valid": False, "reason": "validation_limit"}

    # 7. Tudo OK — registra validação
    db.licenses.increment_validation(license.id, device_fingerprint)

    return {
        "valid": True,
        "plan": license.subscription.plan,
        "expires_at": license.expires_at,
        "features": license.subscription.plan.features
    }
```

## 2. Fluxo do QR Code WhatsApp

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  CLIENTE │     │ APP      │     │ BACKEND  │     │WPPConnect│
│ clica    │────▶│ pede QR  │────▶│ inicia   │────▶│ gera QR  │
│ "Conectar"│    │          │     │ sessão   │     │ Code     │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                       │                  │
                                       │◀─────────────────┘
                                       │    QR Code base64
                                       │
                                  ┌────┴─────┐
                                  │ App      │
                                  │ exibe QR │
                                  │ em tela  │
                                  └────┬─────┘
                                       │
                                  ┌────┴─────┐
                                  │ Cliente  │
                                  │ escaneia │
                                  │ com cel  │
                                  └────┬─────┘
                                       │
                                  ┌────┴─────┐
                                  │ WPPConn  │
                                  │ conecta  │
                                  │ → status │
                                  │ connected│
                                  └──────────┘
```

## 3. Fluxo da Flora AI

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  CLIENTE │     │ APP      │     │ BACKEND  │     │ LLM      │
│ pergunta │────▶│ envia    │────▶│ monta    │────▶│ Router   │
│ à Flora  │     │ contexto │     │ prompt   │     │ escolhe  │
│          │     │          │     │ + históri│     │ modelo   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                         │
                                                    ┌────┴────┐
                                                    │ Groq?   │
                                                    │ Gemini? │
                                                    │ Ollama? │
                                                    │ (por    │
                                                    │  plano) │
                                                    └────┬────┘
                                                         │
┌──────────┐     ┌──────────┐     ┌──────────┐          │
│  CLIENTE │◀────│ APP      │◀────│ BACKEND  │◀─────────┘
│ vê       │     │ mostra   │     │ retorna  │
│ resposta │     │ resposta │     │ streaming│
└──────────┘     └──────────┘     └──────────┘
```

## 4. Fluxo de Mensagem do WhatsApp

```
[WhatsApp User envia msg]
        │
        ▼
[WPPConnect recebe]
        │
        ▼
[Envia para Backend via webhook/internal]
        │
        ▼
[Backend processa]
  ├─ Salva mensagem (inbound)
  ├─ Busca bot configurado
  ├─ Verifica horário (business hours?)
  │   ├─ Dentro → processa
  │   └─ Fora → away message (se configurada)
  ├─ Tenta match de intents
  │   ├─ Match encontrado → responde com intent response
  │   └─ Sem match → verifica LLM
  │       ├─ Plano tem LLM → chama LLM Router
  │       │   ├─ Monta prompt (system + history + context)
  │       │   ├─ Chama provider (Groq, Gemini, etc.)
  │       │   ├─ Fallback se falhar
  │       │   └─ Salva métricas (tokens, custo, latência)
  │       └─ Plano sem LLM → fallback message
  ├─ Salva resposta (outbound)
  ├─ Envia via WPPConnect
  └─ Atualiza memória do contato
```

## 5. Fluxo de Comandos Personalizados

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  ADMIN   │     │ BACKEND  │     │ SANDBOX  │     │ PRODUÇÃO │
│ cria     │────▶│ valida   │────▶│ testa    │────▶│ aprova   │
│ comando  │     │ sintaxe  │     │ conflitos│     │ publica  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘

Pipeline de validação:
1. Sintaxe válida? (JSON schema)
2. Conflito com comandos existentes?
3. Padrão perigoso? (regex injection, etc.)
4. Dentro dos limites do plano?
5. Teste em sandbox → OK?
6. Aprovação do admin
7. Versionamento (v1, v2, ...)
8. Deploy com rollback disponível
```

## 6. Fluxo de Segurança

```
┌──────────────────────────────────────────────────────────────┐
│                    CAMADAS DE SEGURANÇA                       │
│                                                                │
│  Camada 1: TRANSPORTE                                         │
│  • HTTPS/TLS 1.3 em toda comunicação                         │
│  • Certificate pinning nos apps                              │
│  • HSTS headers                                               │
│                                                                │
│  Camada 2: AUTENTICAÇÃO                                      │
│  • Argon2id para hash de senhas                              │
│  • JWT com expiração curta (15 min)                          │
│  • Refresh token rotativo (7 dias)                            │
│  • 2FA/TOTP para admins                                      │
│  • Rate limit por IP e por usuário                           │
│  • Bloqueio após 5 tentativas falhas                         │
│                                                                │
│  Camada 3: AUTORIZAÇÃO                                       │
│  • RBAC (role-based access control)                          │
│  • Feature flags por plano (server-side)                     │
│  • Validação de permissão em cada endpoint                   │
│                                                                │
│  Camada 4: DADOS                                              │
│  • AES-256-GCM para dados sensíveis em repouso              │
│  • Chaves em variáveis de ambiente / vault                   │
│  • Segregação de dados por tenant                            │
│  • Backups criptografados                                    │
│                                                                │
│  Camada 5: LICENÇAS                                          │
│  • Assinatura digital RSA-2048/ECC                           │
│  • Fingerprint de dispositivo                                │
│  • Validação online obrigatória                              │
│  • Revogação remota                                          │
│  • Anti-replay tokens                                        │
│                                                                │
│  Camada 6: AUDITORIA                                         │
│  • Log de toda ação sensível                                │
│  • Alerta de comportamento anômalo                           │
│  • Retenção de logs configurável                             │
│  • Exportação para SIEM                                      │
└──────────────────────────────────────────────────────────────┘
```

## 7. Fluxo de Pagamento/Assinatura

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  CLIENTE │     │ BACKEND  │     │ PAYMENT  │     │ BACKEND  │
│ escolhe  │────▶│ cria     │────▶│ PROVIDER │────▶│ recebe   │
│ plano    │     │ checkout │     │ (Stripe/ │     │ webhook  │
│          │     │ session  │     │  MP/Pix) │     │ confirma │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                         │
                                                    ┌────┴────┐
                                                    │ Ativa   │
                                                    │ assinat.│
                                                    │ + gera  │
                                                    │ licença │
                                                    └─────────┘

Ciclo de renovação:
1. APScheduler verifica assinaturas expirando (diário)
2. Tenta cobrança automática via provider
3. Sucesso → renova + nova licença
4. Falha → notifica cliente + grace period (3 dias)
5. Grace expirou → suspende bot + licença
6. 30 dias suspenso → cancela + arquiva
```
