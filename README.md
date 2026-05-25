<div align="center">

# 🌸 Flora Platform

**Plataforma Completa de Chatbots WhatsApp com Licenciamento**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![KivyMD](https://img.shields.io/badge/KivyMD-3DDB86?style=for-the-badge&logo=kivy&logoColor=white)](https://kivymd.readthedocs.io)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-v1.0.0-success?style=for-the-badge)](.)

*Dois apps nativos • Flora AI integrada • Licenciamento digital • 7 planos*

[Visão Geral](#-visão-geral) • [Instalação](#-instalação) • [Execução](#-execução) • [Arquitetura](#-arquitetura) • [Planos](#-planos) • [API](#-api) • [Documentação](#-documentação)

---

</div>

## 🌸 Visão Geral

A **Flora Platform** é uma fábrica completa de chatbots para WhatsApp baseada em assinatura. Você cria, configura e gerencia bots profissionais. Seus clientes compram licenças, conectam o WhatsApp por QR Code e têm um bot funcionando — de simples (regras) a inteligente (LLMs).

A **Flora AI** 🌸 é a assistente virtual embutida que guia o cliente dentro do app, reduzindo churn e suporte.

### Modelo de Negócio

```
Receita = Σ (clientes_ativos × preço_plano) - custo_LLM - infra

Margem saudável porque:
✅ Planos sem LLM = custo quase zero
✅ Planos com LLM = markup de 3-10x sobre custo real
✅ Enterprise = preço premium com custo marginal baixo
✅ Revenda = você lucra, revendedor lucra
```

### Diferenciais

| # | Diferencial | Descrição |
|---|---|---|
| 1 | 📱 **Dois apps nativos** | KivyMD desktop — dark theme premium |
| 2 | 🌸 **Flora AI integrada** | Assistente que reduz churn e suporte |
| 3 | 🧠 **LLM Router inteligente** | Custo otimizado por plano |
| 4 | 🔐 **Licença com assinatura digital** | Anti-pirataria real |
| 5 | 🏷️ **White-label nativo** | Revendedores têm marca própria |
| 6 | 📴 **Modo offline** | Ollama local para enterprise |
| 7 | 📷 **QR Code pairing** | Zero configuração técnica |

---

## 🚀 Instalação

### Pré-requisitos

- **Python 3.11+**
- **pip** (gerenciador de pacotes)
- **Git**
- **SQLite** (padrão) ou **PostgreSQL 15+** (produção)
- **Node.js 20+** (conector WhatsApp — opcional)

### Passo a Passo

```bash
# 1. Clone o repositório
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform

# 2. Crie o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure o ambiente
python run.py setup
# Edite .env com suas configurações

# 5. Inicie o backend
python run.py backend

# 6. Inicie o app Admin (outro terminal)
python run.py admin

# 7. Inicie o app Cliente (outro terminal)
python run.py client
```

### Docker

```bash
docker compose up -d
docker compose ps
docker compose logs -f backend
```

---

## ▶️ Execução Rápida

```bash
# Configuração inicial (cria .env, instala deps, cria pastas)
python run.py setup

# Backend FastAPI (API + docs Swagger)
python run.py backend
# → http://localhost:8000/docs

# App Admin (Dashboard KivyMD — dark premium)
python run.py admin

# App Cliente (KivyMD — dark cute)
python run.py client

# Testes
python run.py test

# Tudo junto
python run.py all
```

---

## 🏗️ Arquitetura

```
flora-platform/
├── 📁 backend/                    # FastAPI REST API
│   ├── main.py                    # Entry point + startup
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── database.py                # Async SQLAlchemy + session
│   ├── seed_plans.py              # Seed de planos padrão
│   ├── 📁 api/
│   │   ├── deps.py                # Auth + DB dependencies
│   │   ├── middleware/             # Rate limiter, security
│   │   ├── 📁 v1/                 # API Version 1
│   │   │   ├── auth.py           # Login, register, refresh, me
│   │   │   ├── admin.py          # Dashboard, gestão admin
│   │   │   ├── bots.py           # CRUD de bots
│   │   │   ├── chat.py           # Chat/mensagens
│   │   │   ├── commands.py       # Comandos personalizados
│   │   │   ├── flora.py          # Flora AI endpoints
│   │   │   ├── intents.py        # Intenções/NLU
│   │   │   ├── licenses.py       # Licenças (validate, activate)
│   │   │   ├── plans.py          # Planos
│   │   │   ├── users.py          # Perfil do usuário
│   │   │   ├── webhooks.py       # WhatsApp webhooks
│   │   │   └── health.py         # Health check
│   │   └── router.py              # Router aggregation
│   ├── 📁 core/
│   │   ├── security.py           # JWT + password hashing
│   │   ├── llm_router.py          # LLM routing engine
│   │   ├── chat_engine.py         # Message processing pipeline
│   │   ├── command_engine.py      # Command parsing
│   │   ├── flora_engine.py        # Flora AI engine
│   │   ├── license_manager.py     # License validation
│   │   └── whatsapp_manager.py    # WhatsApp session manager
│   ├── 📁 models/                 # SQLAlchemy ORM (18 models)
│   │   ├── base.py               # Base model (UUID + timestamps)
│   │   ├── user.py               # User (name, email, role)
│   │   ├── bot.py                # Bot (owner_id, config, status)
│   │   ├── plan.py               # Plan (slug, price, features)
│   │   ├── license.py            # License (license_key, key_hash)
│   │   ├── subscription.py       # Subscription
│   │   ├── whatsapp_session.py   # WhatsApp session
│   │   ├── intent.py             # Intent
│   │   ├── command.py            # Command (trigger, response)
│   │   ├── memory.py             # Conversation memory
│   │   ├── message.py            # Message (user_phone, direction)
│   │   ├── llm_usage.py          # LLM usage tracking
│   │   ├── audit_log.py          # Audit log
│   │   ├── system_event.py       # System events
│   │   ├── notification.py       # Notifications
│   │   ├── flora_session.py      # Flora sessions
│   │   ├── support_ticket.py     # Support tickets
│   │   ├── webhook.py            # Webhook config
│   │   ├── payment.py            # Payment records
│   │   └── bot_template.py       # Bot templates
│   ├── 📁 services/               # Business logic (12 services)
│   │   ├── auth_service.py       # Auth + 2FA + rate limiting
│   │   ├── bot_service.py        # Bot management
│   │   ├── license_service.py    # License lifecycle + hardware binding
│   │   ├── whatsapp_service.py   # WhatsApp operations
│   │   ├── flora_service.py      # Flora AI logic
│   │   ├── chat_service.py       # Message pipeline
│   │   ├── billing_service.py    # Subscriptions/billing
│   │   ├── notification_service.py
│   │   ├── analytics_service.py
│   │   ├── support_service.py
│   │   ├── webhook_service.py
│   │   └── backup_service.py
│   ├── 📁 schemas/                # Pydantic validation (14 schemas)
│   │   ├── auth.py, bot.py, chat.py, command.py
│   │   ├── common.py, license.py, plan.py, user.py
│   │   ├── whatsapp.py, intent.py, analytics.py
│   │   ├── system.py, subscription.py, notification.py
│   │   └── __init__.py
│   └── 📁 security/               # Security modules
│       ├── crypto.py             # AES + RSA encryption
│       ├── license_manager.py    # Offline license validation
│       ├── rate_limiter.py       # Rate limiting
│       ├── middleware.py          # Security middleware
│       ├── audit.py              # Audit logging
│       └── anti_clone.py         # Hardware fingerprinting
│
├── 📁 app_admin/                  # App Administrador (KivyMD)
│   ├── main.py                    # Entry point
│   ├── 📁 screens/                # 10 telas
│   │   ├── login_screen.py       # Login administrativo
│   │   ├── dashboard_screen.py   # Dashboard com stats
│   │   ├── bots_screen.py        # Gestão de bots
│   │   ├── bot_create_screen.py  # Criação de bot
│   │   ├── licenses_screen.py    # Gestão de licenças
│   │   ├── users_screen.py       # Gestão de usuários
│   │   ├── plans_screen.py       # Gestão de planos
│   │   ├── analytics_screen.py   # Analytics e métricas
│   │   ├── settings_screen.py    # Configurações
│   │   └── __init__.py
│   ├── 📁 components/             # Componentes reutilizáveis
│   │   ├── sidebar.py            # Navegação lateral
│   │   └── top_bar.py            # Barra superior
│   ├── 📁 services/
│   │   └── api_client.py          # Cliente API
│   ├── 📁 styles/
│   │   └── theme.py               # Tema dark premium
│   └── 📁 utils/
│       └── constants.py
│
├── 📁 app_cliente/                # App Cliente (KivyMD)
│   ├── main.py                    # Entry point
│   ├── 📁 screens/                # 15 telas
│   │   ├── splash_screen.py      # Splash screen
│   │   ├── login_screen.py       # Login por licença
│   │   ├── register_screen.py    # Registro
│   │   ├── onboarding_screen.py  # Onboarding inicial
│   │   ├── home_screen.py        # Painel principal
│   │   ├── bot_create_screen.py  # Criação de bot
│   │   ├── bot_panel_screen.py   # Painel do bot
│   │   ├── chat_screen.py        # Chat de teste
│   │   ├── commands_screen.py    # Comandos personalizados
│   │   ├── whatsapp_screen.py    # Conexão WhatsApp (QR Code)
│   │   ├── flora_chat_screen.py  # Chat com Flora AI
│   │   ├── plans_screen.py       # Planos e upgrade
│   │   ├── support_screen.py     # Suporte
│   │   ├── settings_screen.py    # Configurações
│   │   └── __init__.py
│   ├── 📁 widgets/                # Widgets reutilizáveis
│   │   └── __init__.py
│   ├── 📁 services/
│   │   ├── api_client.py
│   │   └── websocket_client.py
│   └── 📁 utils/
│       └── constants.py
│
├── 📁 brain/                      # Flora AI Brain
│   ├── flora.py                   # Core Flora module
│   ├── prompts.py                 # System prompts
│   ├── tools.py                   # Tool definitions
│   ├── context.py                 # Conversation context
│   ├── intents.py                 # Intent classification
│   └── intents.json               # Intent definitions
│
├── 📁 whatsapp-connector/         # WhatsApp Connection Module
│   ├── 📁 src/                    # Node.js connector
│   │   └── index.js
│   ├── 📁 python_bridge/          # Python bridge
│   │   ├── bridge.py
│   │   ├── config.py
│   │   └── __main__.py
│   └── package.json
│
├── 📁 docs/                       # Documentação completa (14 docs)
│   ├── 01-visao-geral.md
│   ├── 02-arquitetura.md
│   ├── 03-banco-de-dados.md
│   ├── 04-fluxos.md
│   ├── 05-llm-router.md
│   ├── 06-telas-app-admin.md
│   ├── 07-telas-app-cliente.md
│   ├── 08-design-visual.md
│   ├── 09-flora-ai.md
│   ├── 10-seguranca.md
│   ├── 11-api-endpoints.md
│   ├── 12-estrutura-pastas.md
│   ├── 13-roadmap.md
│   └── 14-planos.md
│
├── 📁 tests/                      # Testes
│   ├── conftest.py
│   ├── 📁 backend/                # 8 test files
│   ├── 📁 services/               # 6 test files
│   └── 📁 integration/            # 3 test files
│
├── .env.example                   # Template de variáveis de ambiente
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py                         # Script de execução rápida
└── README.md                      # Este arquivo
```

---

## 💰 Planos

| Plano | Preço/mês | Mensagem/dia | Bots | LLM | Suporte |
|---|---|---|---|---|---|
| 🆓 Gratuito | R$ 0 | 50 | 1 | ❌ | ❌ |
| 🌱 Starter | R$ 49,90 | 500 | 1 | ✅ | Email |
| 🌿 Pro | R$ 99,90 | 2.000 | 3 | ✅ | Prioritário |
| 🌳 Business | R$ 199,90 | 10.000 | 5 | ✅ | Prioritário |
| 🌸 Enterprise | R$ 499,90 | 50.000 | 20 | ✅+Local | Dedicado |
| 💎 Reseller | R$ 799,90 | 100.000 | 50 | ✅+Local | Dedicado |
| 🏢 Custom | Sob consulta | Custom | Custom | Custom | Custom |

---

## 🔌 API

### Endpoints Principais

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Registro | ❌ |
| POST | `/api/v1/auth/login` | Login | ❌ |
| POST | `/api/v1/auth/refresh` | Refresh token | ❌ |
| GET | `/api/v1/auth/me` | Perfil atual | ✅ |
| POST | `/api/v1/auth/logout` | Logout | ✅ |
| GET | `/api/v1/health` | Health check | ❌ |
| GET | `/api/v1/bots` | Listar bots | ✅ |
| POST | `/api/v1/bots` | Criar bot | ✅ |
| GET | `/api/v1/bots/{id}` | Detalhes do bot | ✅ |
| PUT | `/api/v1/bots/{id}` | Atualizar bot | ✅ |
| DELETE | `/api/v1/bots/{id}` | Deletar bot | ✅ |
| GET | `/api/v1/chat/conversations` | Lista conversas | ✅ |
| GET | `/api/v1/chat/history` | Histórico de chat | ✅ |
| POST | `/api/v1/chat/send` | Enviar mensagem | ✅ |
| GET | `/api/v1/commands` | Listar comandos | ✅ |
| POST | `/api/v1/commands` | Criar comando | ✅ |
| PUT | `/api/v1/commands/{id}` | Atualizar comando | ✅ |
| DELETE | `/api/v1/commands/{id}` | Deletar comando | ✅ |
| POST | `/api/v1/flora/chat` | Chat com Flora | ✅ |
| GET | `/api/v1/flora/history` | Histórico Flora | ✅ |
| GET | `/api/v1/flora/onboarding` | Passos onboarding | ✅ |
| POST | `/api/v1/flora/help` | Ajuda por tópico | ✅ |
| GET | `/api/v1/whatsapp/status` | Status WhatsApp | ✅ |
| POST | `/api/v1/whatsapp/connect` | Conectar WhatsApp | ✅ |
| POST | `/api/v1/whatsapp/disconnect` | Desconectar | ✅ |
| GET | `/api/v1/licenses` | Minhas licenças | ✅ |
| POST | `/api/v1/licenses/validate` | Validar licença | ❌ |
| POST | `/api/v1/licenses/activate` | Ativar licença | ✅ |
| GET | `/api/v1/plans` | Listar planos | ✅ |
| GET | `/api/v1/users/profile` | Meu perfil | ✅ |
| PUT | `/api/v1/users/profile` | Atualizar perfil | ✅ |
| GET | `/api/v1/admin/dashboard` | Dashboard admin | Admin |
| GET | `/api/v1/admin/users` | Listar usuários | Admin |
| GET | `/api/v1/admin/bots` | Listar todos bots | Admin |
| GET | `/api/v1/admin/licenses` | Listar todas licenças | Admin |
| GET | `/api/v1/admin/events` | Eventos do sistema | Admin |
| GET | `/api/v1/admin/audit-logs` | Logs de auditoria | Admin |

Documentação completa: **http://localhost:8000/docs** (Swagger)

---

## 🔐 Segurança

- **JWT** com refresh tokens e expiração
- **Bcrypt** para hashing de senhas
- **AES-256** para criptografia de licenças
- **HMAC** para assinatura de licenças
- **Hardware fingerprinting** anti-clonagem
- **Rate limiting** por IP e usuário
- **2FA** (TOTP) opcional
- **Audit logging** de todas as ações
- **CORS** configurado
- **Validação de entrada** em todos os endpoints
- **IP lockout** após tentativas falhas
- **Token blacklist** para logout

---

## 🧪 Testes

```bash
# Executar todos os testes
python run.py test

# Com pytest diretamente
pytest tests/ -v --tb=short

# Com cobertura
pytest --cov=backend --cov-report=html

# Testes específicos
pytest tests/backend/test_auth.py -v
pytest tests/services/test_license_service.py -v
```

---

## 🗺️ Roadmap

| Fase | Status | Descrição |
|---|---|---|
| Fase 1 | ✅ | Arquitetura base + models + schemas |
| Fase 2 | ✅ | Backend API + Auth + Licenças |
| Fase 3 | ✅ | App Admin + App Cliente |
| Fase 4 | ✅ | WhatsApp Connector + QR Code |
| Fase 5 | ✅ | Flora AI + LLM Router |
| Fase 6 | ✅ | Segurança + Anti-pirataria |
| Fase 7 | ✅ | Testes + Polimento + Deploy |
| Fase 8 | 🔄 | Analytics avançado + Métricas |
| Fase 9 | ⬜ | White-label + Revenda |
| Fase 10 | ⬜ | App Mobile (Android/iOS) |
| Fase 11 | ⬜ | Marketplace de templates |

---

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.
Licenças de uso são gerenciadas pela própria plataforma Flora.

---

<div align="center">

**Feito com 🌸 por TiltzOff**

© 2026 Flora Platform. Todos os direitos reservados.

</div>
