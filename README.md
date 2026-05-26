```
  ███████╗██╗      ██████╗ ██████╗  █████╗
  ██╔════╝██║     ██╔═══██╗██╔══██╗██╔══██╗
  █████╗  ██║     ██║   ██║██████╔╝███████║
  ██╔══╝  ██║     ██║   ██║██╔══██╗██╔══██║
  ██║     ███████╗╚██████╔╝██║  ██║██║  ██║
  ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
       🌸 Plataforma SaaS de Chatbots WhatsApp com IA
```

<div align="center">

[![Versao](https://img.shields.io/badge/versao-1.0.0-red)](https://github.com/TiltzOff/flora-platform)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![KivyMD](https://img.shields.io/badge/KivyMD-1.2.0-009688)](https://kivymd.readthedocs.io)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![Status](https://img.shields.io/badge/status-Em%20Desenvolvimento-yellow)](#status)

[Instalacao](#-instalacao) |
[Configuracao](#-configuração) |
[Execucao](#-execução) |
[API](http://localhost:8000/docs) |
[Documentacao](docs/) |
[Roadmap](docs/13-roadmap.md)

</div>

---

## 🌸 O Que E

A **Flora Platform** e uma fabrica de chatbots para WhatsApp baseada em assinatura (SaaS). Ela permite:

- **Administradores** criam, configuram e gerenciam bots profissionais
- **Clientes** adquirem licencas, conectam o WhatsApp via QR Code e tem um bot funcionando
- **Flora AI** — a assistente embutida que guia o cliente dentro do app, reduzindo churn e suporte

> **GPT (Generative Pre-trained Transformer)**: De bots simples (baseados em regras) a bots inteligentes (com LLMs). Tudo em dois apps nativos bonitos com dark premium UI.

---

## ✨ Funcionalidades

### 🤖 Plataforma
| Funcao | Status |
|---|---|
| CRUD completo de bots (criar, editar, ativar, desativar) | ✅ Implementado |
| Sistema de licencas com assinatura digital (RSA) | ✅ Implementado |
| 7 planos configuraveis (Starter a Enterprise) | ✅ Implementado |
| Autenticacao JWT (access + refresh tokens) | ✅ Implementado |
| CRUD de usuarios e RBAC (roles/permissoes) | ✅ Implementado |
| Health checks (liveness, readiness, detailed) | ✅ Implementado |
| Rate limiting anti-brute force | ✅ Implementado |
| Criptografia AES-256-GCM para dados sensiveis | ✅ Implementado |
| Integracao WhatsApp via API (QR Code) | ✅ Implementado |
| Envio/recebimento de mensagens WhatsApp | ✅ Implementado |
| Flora AI — chat inteligente no app | ✅ Implementado |
| Analytics dashboard (mensagens, bots, usuarios, receita) | ✅ Implementado |
| Chat history (listagem e busca) | ✅ Implementado |
| Multi-LLM Router (Groq, Gemini, OpenAI, Anthropic) | 📋 Planejado |
| Webhooks Stripe/MercadoPago | 📋 Planejado |
| Sistema de templates de bots | 📋 Planejado |
| 2FA/TOTP para admins | 📋 Planejado |
| App Admin (KivyMD) — 15 telas | 🔄 Em progresso |
| App Cliente (KivyMD) — 13 telas | 🔄 Em progresso |
| Testes automatizados (pytest) | 🔄 Em progresso |
| Docker Compose (producao) | 📋 Planejado |
| CI/CD pipeline | 📋 Planejado |

### 📱 App Administrador
- Dashboard com metricas em tempo real
- Editor de bot wizard (8 etapas)
- Gerenciamento de licencas e clientes
- Gerenciamento de planos
- Analytics avancados com graficos
- Logs e auditoria
- Backup/restore
- Sandbox de teste de bot

### 📱 App Cliente
- Onboarding em 3 slides
- Validacao de licenca
- Dashboard do bot
- Conexao WhatsApp (QR Code)
- Chat de teste com o bot
- Flora AI integrada
- Gestao do plano
- Metricas basicas

---

## 🛠️ Stack Tecnica

### Backend
| Tecnologia | Uso |
|---|---|
| [Python 3.11+](https://python.org) | Linguagem base |
| [FastAPI 0.115](https://fastapi.tiangolo.com) | Framework web async |
| [SQLAlchemy 2.0](https://sqlalchemy.org) | ORM |
| [Pydantic 2.9](https://pydantic.dev) | Validacao de dados |
| [SQLite](https://sqlite.org) (dev) / [PostgreSQL 15](https://postgresql.org) (prod) | Banco de dados |
| [Redis 7](https://redis.io) | Cache / Rate limiting |
| python-jose | JWT tokens |
| passlib [bcrypt] | Hash de senhas |
| cryptography | AES-256-GCM, RSA |
| loguru | Logging estruturado |
| httpx / aiohttp | HTTP async clients |
| psutil | Monitoramento do sistema |

### Frontend (Apps Desktop)
| Tecnologia | Uso |
|---|---|
| [Kivy 2.3](https://kivy.org) | Framework UI cross-platform |
| [KivyMD 1.2](https://kivymd.readthedocs.io) | Material Design components |
| Pillow | Processamento de imagens |
| qrcode | Geracao de QR Code |
| matplotlib | Graficos |
| requests | HTTP client |

### Suporte LLM
| Provider | Modelos |
|---|---|
| **Groq** | llama-3.1-8b-instant, llama-3.1-70b-versatile |
| **Gemini** | gemini-1.5-flash, gemini-1.5-pro |
| **OpenAI** | gpt-4o-mini, gpt-4o |
| **Anthropic** | claude-3-haiku, claude-3-5-sonnet |

### Qualidade
| Ferramenta | Uso |
|---|---|
| pytest + pytest-asyncio | Testes |
| black | Formatacao |
| ruff | Linter |
| mypy | Type checking |

---

## 📋 Pre-requisitos

| Software | Versao | Obrigatorio |
|---|---|---|
| Python | 3.11+ | ✅ |
| pip | 23+ | ✅ |
| Git | 2.40+ | ✅ |
| PostgreSQL | 15+ | Apenas producao |
| Redis | 7+ | Apenas producao |

### Opcional
| Software | Uso |
|---|---|
| Docker + Docker Compose | Deploy em conteineres |
| Node.js 20+ | WhatsApp WPPConnect connector |
| make | Atalhos de comando |

---

## 🚀 Instalacao

### Passo a Passo

```bash
# 1. Clone o repositorio
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform

# 2. Ambiente virtual
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuracao
cp .env.example .env
# Edite .env com suas configuracoes (veja secao abaixo)

# 5. Setup inicial
python run.py setup

# 6. Execucao
python run.py backend
```

### Instalacao com Docker

```bash
# Tudo incluido (backend + PostgreSQL + Redis)
docker compose up -d

# Verificar
docker compose ps
docker compose logs -f backend
```

---

## ⚙️ Configuracao

Copie `.env.example` para `.env` e configure as variaveis essenciais:

### Variaveis de Seguranca (OBRIGATORIAS — geracao no startup falhara se invalidas)

| Variavel | Descricao | Exemplo |
|---|---|---|
| `SECRET_KEY` | Chave secreta para sessoes (min 32 chars) | `a1b2c3d4e5f6...` |
| `FLORA_MASTER_KEY` | Chave mestra do sistema (min 32 chars) | `x9y8z7w6v5...` |
| `LICENSE_SIGNING_KEY` | Chave para assinar licencas (min 32 chars) | `k1l2m3n4o5...` |

### Banco de Dados

| Variavel | Descricao | Padrao |
|---|---|---|
| `DATABASE_URL` | URL de conexao | `sqlite+aiosqlite:///./flora.db` |

**Desenvolvimento (SQLite):**
```
DATABASE_URL=sqlite+aiosqlite:///./flora.db
```

**Producao (PostgreSQL):**
```
DATABASE_URL=postgresql+asyncpg://flora:password@localhost:5432/flora_platform
```

### Redis

| Variavel | Descricao | Padrao |
|---|---|---|
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |

### JWT / Autenticacao

| Variavel | Descricao | Padrao |
|---|---|---|
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiracao do access token (minutos) | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiracao do refresh token (dias) | `7` |

### LLM / IA (opcional em dev)

| Variavel | Provider |
|---|---|
| `GROQ_API_KEY` | Groq |
| `GEMINI_API_KEY` | Google Gemini |
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |

### WhatsApp

| Variavel | Descricao | Padrao |
|---|---|---|
| `WHATSAPP_CONNECTOR_URL` | URL do servico WPPConnect | `http://localhost:3333` |
| `WHATSAPP_SESSION_DIR` | Diretorio de sessoes WhatsApp | `./sessions` |

### Admin

| Variavel | Descricao | Padrao |
|---|---|---|
| `ADMIN_EMAIL` | Email do admin padrao | `admin@flora.com` |
| `ADMIN_PASSWORD` | Senha do admin padrao | `Admin@123456` |
| `ADMIN_NAME` | Nome do admin padrao | `Administrador` |

### Completo `.env` minimo para dev:

```env
APP_NAME=Flora Platform
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

SECRET_KEY=dev-secret-key-change-me-please-32chars!!
FLORA_MASTER_KEY=flora-master-key-change-please-32chars!!
LICENSE_SIGNING_KEY=license-key-change-please-32chars!!

DATABASE_URL=sqlite+aiosqlite:///./flora.db
REDIS_URL=redis://localhost:6379/0

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

ADMIN_EMAIL=admin@flora.com
ADMIN_PASSWORD=Admin@123456
ADMIN_NAME=Administrador

WHATSAPP_SESSION_DIR=./sessions
WHATSAPP_CONNECTOR_URL=http://localhost:3333

LOG_LEVEL=INFO
```

---

## ▶️ Execucao

### Via `run.py`

```bash
# Backend (FastAPI - http://localhost:8000)
python run.py backend

# App Admin (KivyMD desktop)
python run.py admin

# App Cliente (KivyMD desktop)
python run.py client

# Setup inicial
python run.py setup

# Testes
python run.py test

# Tudo (backend + apps)
python run.py all
```

### Via Uvicorn (direto)

```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Rotas Uteis

| URL | Descricao |
|---|---|
| `http://localhost:8000/` | Info da API |
| `http://localhost:8000/docs` | Swagger UI (documentacao interativa) |
| `http://localhost:8000/redoc` | ReDoc (documentacao alternativa) |
| `http://localhost:8000/api/v1/health` | Health check |
| `http://localhost:8000/api/v1/health/detailed` | Health check detalhado |
| `http://localhost:8000/api/v1/health/ready` | Readiness probe (K8s) |
| `http://localhost:8000/api/v1/health/live` | Liveness probe (K8s) |

---

## 📖 API — Endpoints Principais

A documentacao completa da API esta em [`docs/API/`](docs/API/).

### Resumo dos Recursos

```
/api/v1/
├── /auth              # Autenticacao (register, login, refresh, logout, me)
├── /users             # Gestao de usuarios
├── /bots              # CRUD de bots
├── /licenses          # Gestao de licencas
├── /plans             # Gestao de planos
├── /chat              # Historico e envio de mensagens
├── /commands          # Comandos personalizados
├── /intents           # Intencoes do bot
├── /whatsapp          # Conexao e mensagens WhatsApp
├── /flora             # Flora AI (chat, help, suggestions, onboarding)
├── /analytics         # Metricas e relatorios
├── /admin             # Operacoes administrativas
├── /webhooks          # Webhooks (Stripe, MercadoPago)
├── /billing           # Faturamento
├── /notifications     # Notificacoes
└── /health            # Health checks
```

### Autenticacao

Todas as rotas (exceto `/auth/*` e `/health/*`) requerem autenticacao:

```
Authorization: Bearer <access_token>
```

### Exemplo de Uso

```bash
# Registro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Senha@123","name":"Usuario"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Senha@123"}'

# Criar bot (com token)
curl -X POST http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bot Principal","personality":"friendly"}'
```

---

## 📊 Roadmap

| Fase | Nome | Status |
|---|---|---|
| 0 | Fundacao (estrutura, DB, models) | ✅ Completa |
| 1 | Autenticacao e Seguranca (JWT, RBAC, criptografia) | ✅ Completa |
| 2 | Sistema de Licencas (RSA, validacao, revogacao) | ✅ Completa |
| 3 | Backend de Bots (CRUD, commands, intents) | ✅ Completa |
| 4 | WhatsApp Connector (QR Code, sessoes, mensagens) | ✅ Completa |
| 5 | Flora AI (chat, help, onboarding, suggestions) | ✅ Completa |
| 6 | Analytics e Relatorios | ✅ Completa |
| 7 | App Admin (KivyMD) | 🔄 Em progresso |
| 8 | App Cliente (KivyMD) | 🔄 Em progresso |
| 9 | Testes e Qualidade | 🔄 Em progresso |
| 10 | Docker e CI/CD | 📋 Planejado |
| 11 | Producao e Deploy | 📋 Planejado |

Detalhes: [`docs/13-roadmap.md`](docs/13-roadmap.md)

---

## 📁 Estrutura do Projeto

```
flora-platform/
├── README.md                       # Voce esta aqui
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .env.example                    # Template de configuracao
├── requirements.txt                # Dependencias Python
├── run.py                          # Script de execucao
├── Dockerfile
├── docker-compose.yml
│
├── backend/                        # FastAPI Backend
│   ├── main.py                     # Entry point
│   ├── config.py                   # Configuracoes (Pydantic Settings)
│   ├── database.py                 # Conexao DB + sessions
│   │
│   ├── api/                        # Camada de API
│   │   ├── router.py               # Router principal
│   │   ├── deps.py                 # Dependencias (auth, db)
│   │   ├── middleware/             # CORS, rate limit, audit, errors
│   │   └── v1/                     # Endpoints v1
│   │       ├── auth.py             # /auth
│   │       ├── users.py            # /users
│   │       ├── bots.py             # /bots
│   │       ├── licenses.py         # /licenses
│   │       ├── plans.py            # /plans
│   │       ├── chat.py             # /chat
│   │       ├── commands.py         # /commands
│   │       ├── intents.py          # /intents
│   │       ├── whatsapp.py         # /whatsapp
│   │       ├── flora.py            # /flora
│   │       ├── analytics.py        # /analytics
│   │       ├── admin.py            # /admin
│   │       ├── webhooks.py         # /webhooks
│   │       ├── billing.py          # /billing
│   │       ├── notifications.py    # /notifications
│   │       └── health.py           # /health
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── user.py, bot.py, license.py, plan.py
│   │   ├── message.py, whatsapp_session.py, payment.py
│   │   ├── llm_usage.py, audit_log.py, flora_session.py ...
│   │
│   ├── schemas/                    # Pydantic schemas
│   │   ├── auth.py, bot.py, license.py, plan.py
│   │   ├── chat.py, whatsapi.py, user.py ...
│   │
│   ├── services/                   # Logica de negocio
│   │   ├── auth_service.py
│   │   ├── license_service.py
│   │   ├── whatsapp_service.py
│   │   ├── flora_service.py
│   │   ├── chat_service.py
│   │   ├── analytics_service.py
│   │   └── ...
│   │
│   ├── core/                       # Nucleo do sistema
│   │   ├── security.py             # JWT, criptografia
│   │   ├── license_manager.py      # RSA signing
│   │   ├── llm_router.py           # Multi-LLM routing
│   │   └── ...
│   │
│   └── utils/                      # Utilitarios
│
├── app_admin/                      # App Administrador (KivyMD)
│   ├── main.py
│   ├── screens/                    # Telas
│   ├── components/                 # Componentes reutilizaveis
│   └── services/                   # Comunicacao com API
│
├── app_cliente/                    # App Cliente (KivyMD)
│   ├── main.py
│   ├── screens/                    # Telas
│   ├── components/                 # Componentes reutilizaveis
│   └── services/                   # Comunicacao com API
│
├── tests/                          # Testes (pytest)
│   ├── test_auth.py
│   ├── test_bots.py
│   ├── test_licenses.py
│   └── ...
│
├── docs/                           # Documentacao completa
│   ├── arquitetura/                # Documentos de arquitetura
│   │   ├── visao-geral.md
│   │   ├── backend.md
│   │   ├── client-app.md
│   │   ├── admin-app.md
│   │   ├── whatsapp-integration.md
│   │   └── flora-ai.md
│   ├── API/                        # Referencia da API
│   │   ├── auth.md
│   │   ├── bots.md
│   │   ├── licenses.md
│   │   ├── whatsapp.md
│   │   ├── chat.md
│   │   ├── plans.md
│   │   ├── analytics.md
│   │   └── flora.md
│   ├── guides/                     # Guias praticos
│   │   ├── instalacao.md
│   │   ├── configuracao.md
│   │   ├── execucao.md
│   │   ├── desenvolvimento.md
│   │   └── deploy.md
│   ├── 13-roadmap.md               # Roadmap detalhado
│   ├── 14-planos.md                # Planos e precos
│   ├── 08-design-visual.md         # Design system
│   └── ...
│
├── logs/                           # Logs da aplicacao
├── sessions/                       # Sessoes WhatsApp
├── uploads/                        # Arquivos enviados
└── backups/                        # Backups
```

---

## 📚 Documentacao

Toda a documentacao esta na pasta [`docs/`](docs/):

### Arquitetura
- [Visao Geral](docs/arquitetura/visao-geral.md) — Arquitetura de alto nivel
- [Backend](docs/arquitetura/backend.md) — FastAPI, models, services
- [App Cliente](docs/arquitetura/client-app.md) — KivyMD, telas, fluxos
- [App Admin](docs/arquitetura/admin-app.md) — KivyMD, telas, fluxos
- [WhatsApp](docs/arquitetura/whatsapp-integration.md) — Integracao WhatsApp
- [Flora AI](docs/arquitetura/flora-ai.md) — Sistema Flora AI

### API Reference
- [Autenticacao](docs/API/auth.md) — JWT, registro, login
- [Bots](docs/API/bots.md) — CRUD de bots
- [Licencas](docs/API/licenses.md) — Sistema de licencas
- [WhatsApp](docs/API/whatsapp.md) — Conexao e mensagens
- [Chat](docs/API/chat.md) — Historico e envio
- [Planos](docs/API/plans.md) — Gestao de planos
- [Analytics](docs/API/analytics.md) — Metricas
- [Flora AI](docs/API/flora.md) — Endpoints da Flora

### Guias
- [Instalacao](docs/guides/instalacao.md) — Guia de instalacao
- [Configuracao](docs/guides/configuracao.md) — Variaveis de ambiente
- [Execucao](docs/guides/execucao.md) — Como executar
- [Desenvolvimento](docs/guides/desenvolvimento.md) — Guia do desenvolvedor
- [Deploy](docs/guides/deploy.md) — Guia de producao

### Outros
- [Roadmap](docs/13-roadmap.md) — Fases do projeto
- [Planos e Precos](docs/14-planos.md) — 7 planos detalhados
- [Design Visual](docs/08-design-visual.md) — Paleta, tipografia, componentes
- [Seguranca](docs/10-seguranca.md) — 6 camadas de seguranca
- [Banco de Dados](docs/03-banco-de-dados.md) — Diagrama ER, SQL

---

## 🤝 Contribuindo

Leia o [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes de contribuicao.

Resumo:
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudancas (`git commit -m "Adiciona feature X"`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para o historico de versoes.

---

## 📄 Licenca

Este projeto e proprietario. Todos os direitos reservados.
Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 📞 Contato

- **Autor:** TiltzOff
- **GitHub:** [@TiltzOff](https://github.com/TiltzOff)
- **Email:** suporte@flora.bot

---

<div align="center">

**Feito com Python, FastAPI, KivyMD e muito cafe**

🌸 *Flora Platform — Chatbots WhatsApp com IA*

</div>
