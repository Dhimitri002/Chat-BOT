# 🔧 Arquitetura do Backend

> **Versao:** 1.0.0 | **Data:** 2026-05-26

---

## 1. Visao Geral

O backend e uma API REST construida com **FastAPI** usando Python assincrono. Segue uma arquitetura de 4 camadas com separacao clara de responsabilidades.

```
Request  → API Layer → Services Layer → Models Layer → Database
Response ← Schemas   ← Business Logic  ← SQLAlchemy   ← SQLite/PG
```

---

## 2. Estrutura de Pastas

```
backend/
├── main.py                     # App FastAPI, startup/shutdown, CORS
├── config.py                   # Settings (Pydantic), carrega .env
├── database.py                 # Engine, session maker, health check
│
├── api/
│   ├── router.py               # Router principal (agrega todos v1)
│   ├── deps.py                 # Dependencies: get_db, get_current_user, get_current_admin
│   ├── middleware/
│   │   ├── cors.py             # CORS configuration
│   │   ├── audit.py            # Audit logging middleware
│   │   ├── rate_limit.py       # Rate limiting (Redis-based)
│   │   └── error_handler.py    # Global error handling
│   └── v1/
│       ├── auth.py             # POST /register, /login, /refresh, /logout, GET /me
│       ├── users.py            # CRUD /users
│       ├── bots.py             # CRUD /bots
│       ├── licenses.py         # CRUD /licenses, POST /validate, POST /activate
│       ├── plans.py            # CRUD /plans
│       ├── chat.py             # GET /conversations, GET /history, POST /send
│       ├── commands.py         # CRUD /bots/{id}/commands
│       ├── intents.py          # CRUD /bots/{id}/intents
│       ├── whatsapp.py         # POST /connect, /disconnect, /send, /qr, /status
│       ├── flora.py            # POST /chat, GET /history, /help, /suggestions, /onboarding
│       ├── analytics.py        # GET /dashboard, /messages, /users, /revenue
│       ├── admin.py            # Admin-only operations
│       ├── webhooks.py         # Webhooks Stripe/MercadoPago
│       ├── billing.py          # Billing operations
│       ├── notifications.py    # Notifications
│       └── health.py           # Health checks (live, ready, detailed)
│
├── models/                     # SQLAlchemy ORM models
│   ├── user.py
│   ├── bot.py
│   ├── license.py
│   ├── plan.py
│   ├── message.py
│   ├── whatsapp_session.py
│   ├── payment.py
│   ├── audit_log.py
│   ├── flora_session.py
│   ├── llm_usage.py
│   ├── intent.py
│   ├── command.py
│   └── notification.py
│
├── schemas/                    # Pydantic validation schemas
│   ├── auth.py                 # LoginRequest, LoginResponse, RegisterRequest, RefreshRequest
│   ├── bot.py                  # BotCreateRequest, BotUpdate, BotResponse
│   ├── license.py              # LicenseCreate, LicenseResponse, LicenseValidateRequest
│   ├── plan.py                 # PlanCreate, PlanUpdate, PlanResponse
│   ├── chat.py                 # SendMessageRequest, ChatHistoryResponse
│   ├── whatsapp.py             # ConnectRequest, SendMessageRequest, StatusResponse
│   └── user.py                 # UserResponse, UserUpdate
│
├── services/                   # Business logic layer
│   ├── auth_service.py         # Register, login, password verification
│   ├── license_service.py      # Create, validate, activate, revoke licenses
│   ├── whatsapp_service.py     # Connect, disconnect, send, session management
│   ├── flora_service.py        # Chat with Flora, help, suggestions
│   ├── chat_service.py         # Message history, conversation management
│   ├── analytics_service.py    # Metrics aggregation
│   ├── bot_service.py          # Bot business logic
│   ├── user_service.py         # User management
│   └── notification_service.py # Notifications
│
├── core/                       # Core utilities
│   ├── security.py             # JWT creation/verification, password hashing, encryption
│   ├── license_manager.py      # RSA signing, license generation
│   ├── llm_router.py           # Multi-LLM provider routing
│   └── crypto.py               # AES-256-GCM encryption/decryption
│
└── utils/                      # Utilidades auxiliares
    ├── helpers.py
    └── validators.py
```

---

## 3. Entry Point (`main.py`)

```python
from fastapi import FastAPI
from backend.api.router import api_router
from backend.config import settings

app = FastAPI(
    title="Flora Platform API",
    description="API da Plataforma Flora — Chatbots WhatsApp com IA",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

app.add_middleware(CORSMiddleware, ...)

app.include_router(api_router)  # All /api/v1/* routes

@app.on_event("startup")
async def startup():
    await create_all_tables()   # Auto-create tables
    await check_db_connection() # Verify DB health
```

**Rotas fora de `/api/v1/`:**
```
GET /          → Info da API
GET /docs      → Swagger UI
GET /redoc     → ReDoc
```

---

## 4. Configuracao (`config.py`)

Carrega todas as variaveis de ambiente com validacao via Pydantic:

```python
class Settings(BaseSettings):
    # Seguranca (obrigatorio, min 32 chars)
    SECRET_KEY: str
    FLORA_MASTER_KEY: str
    LICENSE_SIGNING_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./flora.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin
    ADMIN_EMAIL: str = "admin@flora.com"
    ADMIN_PASSWORD: str = "Admin@123456"

    # WhatsApp
    WHATSAPP_SESSION_DIR: str = "./sessions"
    WHATSAPP_CONNECTOR_URL: str = "http://localhost:3333"
```

**Validdores customizados** garantem que chaves de seguranca tenham comprimento minimo e nao usem valores padrao inseguros.

---

## 5. Sistema de Camadas

### 5.1 Rota (API Layer)

Responsabilidade: receber request, chamar service, retornar response.

```python
@router.post("/bots", response_model=BotResponse, status_code=201)
async def create_bot(
    body: BotCreateRequest,           # Validação automática via Pydantic
    current_user: User = Depends(get_current_user),  # Auth via JWT
    db: AsyncSession = Depends(get_db),              # DB session
):
    bot = await BotService.create_bot(db, body, current_user.id)
    await db.commit()
    return BotResponse.model_validate(bot)
```

### 5.2 Service (Business Logic)

Responsabilidade: logica de negocio, validacoes, orquestracao.

```python
class LicenseService:
    async def create_license(self, db, plan_id, user_id, duration_days=30):
        # Verificar plano
        # Gerar chave de licenca
        # Assinar digitalmente (RSA)
        # Persistir no banco
        return license

    async def validate_license(self, db, key, device_fingerprint):
        # Verificar assinatura
        # Verificar expiracao
        # Verificar device binding
        # Verificar revogacao
        return result
```

### 5.3 Model (ORM Layer)

Responsabilidade: mapeamento objeto-relacional.

```python
class Bot(Base):
    __tablename__ = "bots"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")
    relationship("Message", back_populates="bot")
```

### 5.4 Schema (Validation Layer)

Responsabilidade: validacao de entrada/saida de dados.

```python
class BotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    personality: str = Field(default="friendly")
    response_mode: Field(default="smart")
```

---

## 6. Sistema de Autenticacao

```
┌─────────────────────────────────────────────────┐
│                FLUXO JWT                        │
│                                                  │
│  Cliente ──POST /auth/login──> Backend           │
│    │                             │               │
│    │                        Verifica senha       │
│    │                        (Argon2/BCrypt)      │
│    │                             │               │
│    │<── {access_token,          │               │
│    │      refresh_token} ───────┘               │
│    │                                              │
│    │  Requisicoes subsequentes:                  │
│    │  Authorization: Bearer {access_token}       │
│    │                                              │
│    │  Quando access expira:                      │
│    │  POST /auth/refresh {refresh_token}         │
│    │  ──> {new_access_token, new_refresh_token}  │
│    │                                              │
│    │  Logout:                                    │
│    │  POST /auth/logout ──> blacklist token      │
└─────────────────────────────────────────────────┘
```

**Implementacao em `core/security.py`:**
```python
def create_access_token(data: dict, expires_delta: timedelta) -> str:
    # JWT com expiracao, issuer, audience
    payload = {
        **data,
        "exp": now + expires_delta,
        "iss": settings.TOKEN_ISSUER,
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)  # Argon2id ou BCrypt

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

---

## 7. Dependencies (`api/deps.py`)

```python
async def get_db() -> AsyncSession:
    """Yield async DB session por request."""
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decodifica JWT, retorna usuario autenticado."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await db.execute(select(User).where(User.id == payload["sub"]))
    return user.scalar_one()

async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifica se usuario e admin."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(403, "Acesso negado")
    return current_user
```

---

## 8. Health Checks (`api/v1/health.py`)

| Endpoint | Descricao | Uso |
|----------|-----------|-----|
| `GET /api/v1/health` | Status geral | Monitoramento |
| `GET /api/v1/health/detailed` | DB + sistema + uptime | Debug |
| `GET /api/v1/health/live` | Liveness probe | Kubernetes |
| `GET /api/v1/health/ready` | Readiness probe | Kubernetes |

**Response exemplo:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "database": "connected",
  "redis": "connected",
  "system": {
    "cpu_percent": 5.2,
    "memory_rss_mb": 128.5,
    "python_version": "3.11.9"
  }
}
```

---

## 9. Banco de Dados

### 9.1 Desenvolvimento (SQLite)

```python
DATABASE_URL = "sqlite+aiosqlite:///./flora.db"
engine = create_async_engine(DATABASE_URL)
```

### 9.2 Producao (PostgreSQL)

```python
DATABASE_URL = "postgresql+asyncpg://flora:password@localhost:5432/flora_platform"
```

### 9.3 Migrations (Alembic)

```bash
# Gerar migration
alembic revision --autogenerate -m "descricao"

# Aplicar
alembic upgrade head
```

---

## 10. Logging

```python
# Usa loguru para logging estruturado
from loguru import logger

logger.add("logs/flora_{time}.log", rotation="500 MB", retention="30 days")
logger.info("Usuario logado", user_id=user.id)
```

**Niveis de log:**
- `DEBUG` — detalhado (env=development)
- `INFO` — operacoes normais
- `WARNING` — erros recuperaveis
- `ERROR` — erros criticos
- `CRITICAL` — falhas fatais

---

## 11. Error Handling

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "status": exc.status_code},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Erro interno do servidor"},
    )
```

**Padrao de resposta de erro:**
```json
{
  "error": true,
  "message": "Credenciais invalidas",
  "status": 401
}
```

---

## 12. Performance

| Tecnica | Implementacao |
|---------|---------------|
| Conexao async | `async/await` em toda a stack |
| Connection pool | SQLAlchemy pool (10 conexoes, max 20) |
| Cache | Redis para rate limit e token blacklist |
| Serializacao rapida | Pydantic v2 (core em Rust) |
| Docs auto | Swagger UI gerado automaticamente |
| Health checks | Leitura direta sem overhead |

---

## 13. Variaveis de Ambiente (Referencia Rapida)

| Variavel | Tipo | Obrigatoria |
|----------|------|-------------|
| `SECRET_KEY` | str (32+) | ✅ Sim |
| `FLORA_MASTER_KEY` | str (32+) | ✅ Sim |
| `LICENSE_SIGNING_KEY` | str (32+) | ✅ Sim |
| `DATABASE_URL` | str | ✅ (default SQLite) |
| `REDIS_URL` | str | ✅ (default local) |
| `JWT_ALGORITHM` | str | ✅ (default HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | ✅ (default 30) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | ✅ (default 7) |
| `ADMIN_EMAIL` | str | ✅ (default admin@flora.com) |
| `ADMIN_PASSWORD` | str | ✅ (default Admin@123456) |
| `WHATSAPP_SESSION_DIR` | str | ✅ (default ./sessions) |
| `WHATSAPP_CONNECTOR_URL` | str | ✅ (default localhost:3333) |
| `GROQ_API_KEY` | str | ❌ (dev use mocks) |
| `OPENAI_API_KEY` | str | ❌ |
| `GEMINI_API_KEY` | str | ❌ |
| `ANTHROPIC_API_KEY` | str | ❌ |
