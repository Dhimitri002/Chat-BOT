# 🌸 FLORA PLATFORM — Arquitetura

> Arquitetura técnica detalhada: backend, frontend, IA, integrações e decisões de design.

---

## 🏗️ Visão Geral da Arquitetura

A Flora Platform segue uma arquitetura **multi-camadas** com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAMADA DE APRESENTAÇÃO                       │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐    │
│  │   App Admin  │   │  App Cliente │   │   Swagger UI /       │    │
│  │   (KivyMD)   │   │   (KivyMD)   │   │   ReDoc (API Docs)   │    │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘    │
│         │                  │                      │                 │
├─────────┴──────────────────┴──────────────────────┴─────────────────┤
│                        CAMADA DE API (HTTP)                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Router                            │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │   Auth     │ │   Bots     │ │   Plans    │ │  Admin   │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │ WhatsApp   │ │   Flora    │ │ Analytics  │ │ Webhooks │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    MIDDLEWARES                                │   │
│  │  CORS │ Rate Limit │ Audit Log │ Error Handler │ Auth JWT   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        CAMADA DE SERVIÇOS                            │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │   Auth     │ │  License   │ │  WhatsApp  │ │  Notification  │   │
│  │  Service   │ │  Service   │ │  Service   │ │   Service      │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │   LLM      │ │  Backup    │ │  Support   │ │   Webhook      │   │
│  │  Router    │ │  Service   │ │  Service   │ │   Service      │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        CAMADA DE SEGURANÇA                           │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │  Crypto    │ │  License   │ │  Anti-     │ │   bcrypt /     │   │
│  │  (AES/RSA) │ │  Manager   │ │  Clone     │ │   JWT          │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        CAMADA DE DADOS                               │
│                                                                     │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐  │
│  │   SQLAlchemy   │   │     Redis      │   │   Sistema de       │  │
│  │   ORM          │   │     (Cache)    │   │   Arquivos         │  │
│  │   (SQLite/PG)  │   │                │   │   (sessões WA)     │  │
│  └────────────────┘   └────────────────┘   └────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Backend — FastAPI

### Estrutura de Pastas

```
backend/
├── __init__.py
├── main.py               # Entry point (cria app FastAPI)
├── config.py             # Configurações via pydantic-settings
├── database.py           # Engine + Session factory (async)
│
├── api/
│   ├── deps.py           # Dependências injetáveis (get_db, get_current_user)
│   ├── router.py         # Router principal (agrega v1)
│   ├── middleware/
│   │   ├── cors.py       # CORS configuration
│   │   ├── rate_limit.py # Rate limiting por IP/user
│   │   ├── audit.py      # Audit logging
│   │   └── error_handler.py # Error handling global
│   └── v1/
│       ├── auth.py       # /auth/* (register, login, refresh, 2FA)
│       ├── users.py      # /users/* (CRUD usuários)
│       ├── plans.py      # /plans/* (listar planos)
│       ├── licenses.py   # /licenses/* (gerenciar licenças)
│       ├── bots.py       # /bots/* (CRUD bots)
│       ├── chat.py       # /chat/* (enviar/receber mensagens)
│       ├── flora.py      # /flora/* (chat com Flora AI)
│       ├── whatsapp.py   # /whatsapp/* (conectar, desconectar)
│       ├── commands.py   # /commands/* (comandos personalizados)
│       ├── intents.py    # /intents/* (intenções do bot)
│       ├── admin.py      # /admin/* (operações administrativas)
│       ├── analytics.py  # /analytics/* (métricas e dashboards)
│       ├── billing.py    # /billing/* (cobrança e assinaturas)
│       └── notifications.py # /notifications/*
│
├── models/               # SQLAlchemy models (18+ tabelas)
│   ├── base.py           # Base declarativa
│   ├── user.py           # User
│   ├── plan.py           # Plan
│   ├── subscription.py   # Subscription
│   ├── license.py        # License
│   ├── bot.py            # Bot
│   ├── command.py        # Command
│   ├── intent.py         # Intent
│   ├── memory.py         # Memory
│   ├── flora_session.py  # FloraSession
│   ├── whatsapp_session.py # WhatsAppSession
│   ├── llm_usage.py      # LLMUsage
│   ├── payment.py        # Payment
│   ├── audit_log.py      # AuditLog
│   ├── system_event.py   # SystemEvent
│   ├── notification.py   # Notification
│   ├── support_ticket.py # SupportTicket
│   ├── bot_template.py   # BotTemplate
│   └── webhook.py        # Webhook
│
├── schemas/              # Pydantic schemas (validação)
│   ├── auth.py
│   ├── user.py
│   ├── plan.py
│   ├── subscription.py
│   ├── license.py
│   ├── bot.py
│   ├── command.py
│   ├── intent.py
│   ├── chat.py
│   ├── whatsapp.py
│   ├── analytics.py
│   ├── system.py
│   ├── notification.py
│   └── common.py
│
├── services/             # Lógica de negócio
│   ├── auth_service.py
│   ├── license_service.py
│   ├── webhook_service.py
│   ├── support_service.py
│   ├── notification_service.py
│   └── backup_service.py
│
├── security/             # Segurança
│   ├── crypto.py         # Criptografia AES/RSA
│   ├── license_manager.py # Assinatura e validação de licenças
│   └── anti_clone.py     # Proteção anti-clone (hardware binding)
│
├── scripts/
│   └── seed_plans.py     # Seed de planos no banco
│
└── tests/
    ├── conftest.py
    └── test_security_phase1.py
```

### Padrões Utilizados

| Padrão | Onde | Descrição |
|---|---|---|
| **Repository** | Models + Services | Separação entre dados e lógica |
| **Dependency Injection** | `api/deps.py` | FastAPI Depends para auth, db |
| **Middleware Pipeline** | `api/middleware/` | CORS, rate limit, audit |
| **Schema Validation** | `schemas/` | Pydantic v2 para input/output |
| **Service Layer** | `services/` | Lógica de negócio isolada |
| **Async Everything** | Todo o backend | SQLAlchemy async + async/await |

---

## 📱 Frontend — KivyMD

### Dois Apps Nativos

```
app_admin/                  app_cliente/
├── main.py                 ├── main.py
├── screens/                ├── screens/
│   ├── login_screen.py     │   ├── login_screen.py
│   ├── dashboard_screen.py │   ├── home_screen.py
│   ├── bots_screen.py      │   ├── setup_screen.py
│   ├── licenses_screen.py  │   ├── chat_screen.py
│   ├── analytics_screen.py │   ├── config_screen.py
│   └── settings_screen.py  │   └── profile_screen.py
├── components/             ├── components/
│   ├── bot_card.py         │   ├── chat_bubble.py
│   ├── stats_card.py       │   ├── qr_viewer.py
│   └── nav_drawer.py       │   └── nav_bar.py
└── assets/                 └── assets/
    ├── fonts/                  ├── fonts/
    ├── images/                 └── images/
    └── themes/
        └── dark.py
```

### App Admin (Administrador)

| Tela | Funcionalidade |
|---|---|
| **Login** | Autenticação do admin |
| **Dashboard** | Visão geral: bots ativos, clientes, métricas |
| **Bots** | CRUD completo de bots |
| **Licenças** | Gerenciar licenças dos clientes |
| **Analytics** | Relatórios e gráficos |
| **Settings** | Configurações da plataforma |

### App Cliente (Cliente Final)

| Tela | Funcionalidade |
|---|---|
| **Login** | Login com licença |
| **Home** | Status do bot, métricas básicas |
| **Setup** | Configurar bot (prompt, personalidade) |
| **Chat** | Testar o bot via chat |
| **Config** | Ajustes e preferências |
| **Profile** | Dados da conta |

### Design System

- **Tema**: Dark premium
- **Cores primárias**: Roxo (#6C5CE7), Verde (#00B894), Rosa (#E84393)
- **Fonte**: Inter / Roboto
- **Ícones**: Material Design Icons
- **Efeitos**: Animações suaves, gradientes, glassmorphism

---

## 🧠 Flora AI + LLM Router

### Arquitetura do LLM Router

```
                    ┌─────────────────────┐
                    │   Entrada do User   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Classificador de  │
                    │   Tarefa            │
                    │   chat/summary/     │
                    │   intent/flora      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼────────┐ ┌────▼─────────┐ ┌───▼──────────┐
    │  Verificar Plano  │ │  Verificar   │ │  Verificar   │
    │  (quais LLMs      │ │  Budget      │ │  Latência    │
    │   estão liberados)│ │  Disponível  │ │  Necessária  │
    └─────────┬────────┘ └────┬─────────┘ └───┬──────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Selecionar Melhor │
                    │   Modelo            │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼────────┐ ┌────▼─────────┐ ┌───▼──────────┐
    │  Groq            │ │  Gemini      │ │  OpenAI      │
    │  (free, rápido)  │ │  (Google)    │ │  (GPT-4o)    │
    └──────────────────┘ └──────────────┘ └──────────────┘
              │                │                │
    ┌─────────▼────────┐ ┌────▼─────────┐
    │  Anthropic       │ │  OpenRouter  │
    │  (Claude)        │ │  (multi)     │
    └──────────────────┘ └──────────────┘
```

### Flora AI

A Flora AI é uma assistente virtual que vive **dentro do app cliente**:

- **Personalidade**: Amigável, prestativa, profissional
- **Contexto**: Sabe qual bot o cliente configurou, qual plano ele tem
- **Ações**: Guia, ensina, resolve problemas, reduz churn
- **Tecnologia**: Usa o LLM Router com prompt engineering especial

---

## 📡 Conexão WhatsApp

```
┌──────────────┐         ┌──────────────────┐        ┌──────────────┐
│  App Cliente │         │  Flora Backend   │        │  WhatsApp    │
│  (KivyMD)    │         │  (FastAPI)       │        │  Web API     │
│              │         │                  │        │              │
│  Escaneia    │ QR Code │  Gera QR Code    │        │              │
│  QR Code  ◄──────────  │  via whatsapp-   │        │              │
│              │         │  connector       │        │              │
│              │         │                  │        │              │
│              │  HTTP   │  Recebe          │  WA    │  WhatsApp    │
│  Recebe    ◄──────────  │  mensagens  ◄──────────  │  Messages    │
│  mensagens   │ WebSocket│  do WhatsApp    │  Web   │              │
│              │         │                  │        │              │
│              │  HTTP   │  Envia           │  WA    │  WhatsApp    │
│  Envia  ──────────────►  │  respostas ───────────►  │  Send        │
│  mensagens   │         │  do bot          │        │  Message     │
└──────────────┘         └──────────────────┘        └──────────────┘
```

### Fluxo de Conexão

1. Cliente abre o app e clica em "Conectar WhatsApp"
2. Backend gera QR Code via whatsapp-connector
3. App exibe o QR Code na tela
4. Cliente escanea com o celular
5. Sessão é estabelecida e salva
6. Bot começa a receber e responder mensagens

---

## 🗄️ Banco de Dados

### Dialeto

| Ambiente | Banco | Driver |
|---|---|---|
| Desenvolvimento | SQLite | aiosqlite |
| Produção | PostgreSQL | asyncpg |

### Migrations

Usamos **Alembic** para migrations:

```bash
# Criar migration
alembic revision --autogenerate -m "descricao"

# Aplicar
alembic upgrade head

# Reverter
alembic downgrade -1
```

### Entidades Principais

| Entidade | Descrição | Campos Chave |
|---|---|---|
| **User** | Usuários (admin + clientes) | email, password_hash, role, is_active |
| **Plan** | Planos de assinatura | name, slug, price, features, limits |
| **Subscription** | Assinaturas ativas | user_id, plan_id, status, expires_at |
| **License** | Licenças de uso | key_hash, signature, status, expires_at |
| **Bot** | Chatbots configurados | license_id, name, prompt, personality, is_active |
| **Command** | Comandos personalizados | bot_id, trigger, response, type |
| **Intent** | Intenções do bot | bot_id, name, training_phrases, response |
| **Memory** | Memória do bot | bot_id, key, value, ttl |
| **FloraSession** | Sessões da Flora AI | user_id, messages, context |
| **WhatsAppSession** | Sessões do WhatsApp | bot_id, session_data, status |
| **LLMUsage** | Uso de LLM (billing) | bot_id, provider, model, tokens, cost |
| **Payment** | Pagamentos | user_id, plan_id, amount, status |
| **AuditLog** | Log de auditoria | user_id, action, resource, timestamp |
| **Notification** | Notificações | user_id, type, title, body, read |
| **SupportTicket** | Tickets de suporte | user_id, subject, status, priority |
| **BotTemplate** | Templates de bot | name, category, config |
| **Webhook** | Webhooks configurados | url, events, secret |
| **SystemEvent** | Eventos do sistema | type, severity, details |

---

## 🔄 Fluxos de Dados

### Fluxo de Autenticação

```
Cliente ──POST /auth/login──► FastAPI
                                │
                    ┌───────────▼───────────┐
                    │  Verifica credenciais  │
                    │  (bcrypt + JWT)        │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Gera Access Token     │
                    │  + Refresh Token       │
                    └───────────┬───────────┘
                                │
Cliente ◄── {access, refresh} ──┘
```

### Fluxo de Chat (Bot)

```
WhatsApp ──mensagem──► WhatsApp Connector
                          │
                    ┌─────▼─────┐
                    │  Backend   │
                    │  recebe    │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  Processa  │
                    │  intenção  │
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────▼────┐ ┌───▼────┐ ┌───▼────┐
        │  Comando  │ │  LLM   │ │ Resposta│
        │  (regra)  │ │ Router │ │ padrão  │
        └─────┬────┘ └───┬────┘ └───┬────┘
              │           │           │
              └───────────┼───────────┘
                          │
                    ┌─────▼─────┐
                    │  Envia     │
                    │  resposta  │
                    └─────┬─────┘
                          │
WhatsApp ◄──resposta──────┘
```

---

## 🔗 Integrações Externas

| Serviço | Tipo | Uso |
|---|---|---|
| **OpenAI** | LLM | GPT-4o, GPT-4o-mini |
| **Anthropic** | LLM | Claude 3.5 Sonnet, Claude 3 Haiku |
| **Google AI** | LLM | Gemini 1.5 Flash, Gemini 1.5 Pro |
| **Groq** | LLM | Llama 3.1 (free, ultra-rápido) |
| **OpenRouter** | LLM | Multi-provider (auto-routing) |
| **Stripe** | Pagamento | Cobrança de assinaturas |
| **MercadoPago** | Pagamento | Cobrança em BRL |
| **WhatsApp Web** | Mensageria | Conexão via QR Code |
| **SMTP** | Email | Notificações por email |
| **Prometheus** | Monitoramento | Métricas e alertas |
| **Grafana** | Monitoramento | Dashboards visuais |
| **Sentry** | Monitoramento | Error tracking |

---

## 📐 Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| **Framework web** | FastAPI | Async nativo, auto-docs, type hints |
| **ORM** | SQLAlchemy 2.0 | Maduro, async, flexível |
| **Banco dev** | SQLite | Zero config, portátil |
| **Banco prod** | PostgreSQL | Robusto, escalável |
| **Frontend** | KivyMD | Cross-platform, Python, Material Design |
| **Auth** | JWT + Refresh | Stateless, escalável |
| **LLM** | Multi-provider | Redundância, otimização de custo |
| **Cache** | Redis | Rápido, pub/sub, TTL |
| **Deploy** | Docker | Reproduzível, isolado |

---

## 🔗 Próximos Passos

- [Banco de Dados](03-banco-de-dados.md) — Modelo de dados detalhado
- [Fluxos](04-fluxos.md) — Fluxos completos do sistema
- [LLM Router](05-llm-router.md) — Roteamento de LLMs
- [Flora AI](09-flora-ai.md) — A assistente virtual
- [Segurança](10-seguranca.md) — Segurança e proteção

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Visão Geral](01-visao-geral.md) | [Próximo: Banco de Dados](03-banco-de-dados.md)

</div>
