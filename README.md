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

[![Versão](https://img.shields.io/badge/versão-1.0.0-red)](https://github.com/TiltzOff/flora-platform)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![KivyMD](https://img.shields.io/badge/KivyMD-1.2.0-009688)](https://kivymd.readthedocs.io)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![Status](https://img.shields.io/badge/status-Em%20Desenvolvimento-yellow)](#status)

[Instalação](#-instalação) |
[Configuração](#-configuração) |
[Execução](#-execução) |
[API](http://localhost:8000/docs) |
[Documentação](docs/) |
[Roadmap](docs/13-roadmap.md)

</div>

---

## 🌸 O Que É

A **Flora Platform** é uma fábrica de chatbots para WhatsApp baseada em assinatura (SaaS). Ela permite:

- **Administradores** criam, configuram e gerenciam bots profissionais
- **Clientes** adquirem licenças, conectam o WhatsApp via QR Code e têm um bot funcionando
- **Flora AI** — a assistente embutida que guia o cliente dentro do app, reduzindo churn e suporte

> De bots simples (baseados em regras) a bots inteligentes (com LLMs). Tudo em dois apps nativos bonitos com dark premium UI.

---

## ✨ Funcionalidades

### 🤖 Plataforma
| Função | Status |
|---|---|
| CRUD completo de bots (criar, editar, ativar, desativar) | ✅ Implementado |
| Sistema de licenças com assinatura digital (RSA) | ✅ Implementado |
| 7 planos de assinatura (Free → Enterprise) | ✅ Implementado |
| Conexão WhatsApp via QR Code | ✅ Implementado |
| LLM Router com multi-provider (OpenAI, Anthropic, Gemini, Groq) | ✅ Implementado |
| Flora AI — assistente virtual integrada | ✅ Implementado |
| Autenticação JWT + Refresh Token + 2FA | ✅ Implementado |
| Rate limiting e proteção anti-clone | ✅ Implementado |
| Sistema de intenções e comandos personalizados | ✅ Implementado |
| Analytics e métricas de uso | ✅ Implementado |
| Sistema de backup automático | ✅ Implementado |
| Templates de bot prontos | ✅ Implementado |
| Sistema de tickets de suporte | ✅ Implementado |
| Notificações em tempo real | ✅ Implementado |
| Webhooks (Stripe, MercadoPago) | 🔄 Em progresso |
| App Admin (KivyMD) | 🔄 Em progresso |
| App Cliente (KivyMD) | 🔄 Em progresso |
| Deploy automatizado (Docker) | ✅ Implementado |

### 🎨 Apps Nativos
| App | Tecnologia | Status |
|---|---|---|
| **App Admin** | KivyMD | 🔄 Em progresso |
| **App Cliente** | KivyMD | 🔄 Em progresso |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLORA PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   App Admin  │    │  App Cliente │    │   Webhook    │      │
│  │   (KivyMD)   │    │   (KivyMD)   │    │  (Stripe/MP) │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │   FastAPI API   │                          │
│                    │   (REST + JWT)  │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐        │
│  │   SQLite /  │    │    Redis    │    │  WhatsApp   │        │
│  │ PostgreSQL  │    │   (Cache)   │    │   Web API   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    🌸 Flora AI / LLM Router              │   │
│  │   OpenAI │ Anthropic │ Gemini │ Groq │ OpenRouter       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy async |
| **Banco de Dados** | SQLite (dev) / PostgreSQL (prod) |
| **Cache** | Redis |
| **Frontend** | KivyMD 1.2.0 (2 apps nativos) |
| **IA / LLM** | OpenAI, Anthropic, Gemini, Groq, OpenRouter |
| **WhatsApp** | QR Code (whatsapp-web.js via conector) |
| **Auth** | JWT + Refresh Token + 2FA (TOTP) |
| **Segurança** | RSA signatures, bcrypt, rate limiting, anti-clone |
| **Deploy** | Docker, Docker Compose |
| **Monitoramento** | Prometheus, Grafana (opcional) |

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- pip ou poetry
- Git
- (Opcional) Docker e Docker Compose
- (Opcional) Redis

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform

# 2. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 5. Execute o backend
python run.py
```

A API estará disponível em `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs` (Swagger UI)

### Com Docker

```bash
# 1. Clone e configure
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
cp .env.example .env

# 2. Suba os containers
docker compose up -d

# 3. Verifique os logs
docker compose logs -f backend
```

---

## 📁 Estrutura do Projeto

```
flora-platform/
│
├── README.md                 # Este arquivo
├── LICENSE                   # Licença
├── .env.example              # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt          # Dependências Python
├── pyproject.toml            # Configuração do projeto
├── setup.py                  # Setup para instalação
├── run.py                    # Entry point (desenvolvimento)
├── Dockerfile                # Imagem Docker (backend)
├── docker-compose.yml        # Orquestração de containers
├── pytest.ini                # Configuração de testes
│
├── backend/                  # FastAPI Backend
│   ├── __init__.py
│   ├── main.py               # Entry point da aplicação
│   ├── config.py             # Configurações (pydantic-settings)
│   ├── database.py           # Conexão DB + session
│   │
│   ├── api/
│   │   ├── deps.py           # Dependências (auth, db)
│   │   ├── router.py         # Router principal
│   │   ├── middleware/        # Middlewares (CORS, rate limit, audit)
│   │   └── v1/               # Endpoints da API v1
│   │
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas (validação)
│   ├── services/             # Lógica de negócio
│   └── security/             # Criptografia, licenças, anti-clone
│
├── app_admin/                # App Admin (KivyMD)
├── app_cliente/              # App Cliente (KivyMD)
│
├── brain/                    # Flora AI / LLM Router
├── whatsapp-connector/       # Conector WhatsApp
│
├── docs/                     # Documentação completa
│   ├── INDICE.md             # Índice da documentação
│   ├── 01-visao-geral.md     # Visão geral do projeto
│   ├── 02-arquitetura.md     # Arquitetura técnica
│   ├── 03-banco-de-dados.md  # Modelo de dados
│   ├── 04-fluxos.md          # Fluxos completos
│   ├── 05-llm-router.md      # LLM Router
│   ├── 06-telas-app-admin.md # Telas do App Admin
│   ├── 07-telas-app-cliente.md # Telas do App Cliente
│   ├── 08-design-visual.md   # Design system
│   ├── 09-flora-ai.md        # Flora AI
│   ├── 10-seguranca.md       # Segurança
│   ├── 11-api-endpoints.md   # Referência da API
│   ├── 12-estrutura-pastas.md # Estrutura de pastas
│   ├── 13-roadmap.md         # Roadmap
│   ├── 14-planos.md          # Planos e preços
│   ├── 15-instalacao.md      # Guia de instalação
│   ├── 16-ideias-expansao.md # Ideias de expansão
│   ├── contributing.md       # Guia de contribuição
│   ├── deploy.md             # Guia de deploy
│   ├── faq.md                # Perguntas frequentes
│   └── changelog.md          # Histórico de versões
│
├── tests/                    # Testes automatizados
├── data/                     # Dados estáticos
├── logs/                     # Logs da aplicação
├── backups/                  # Backups automáticos
├── keys/                     # Chaves criptográficas
└── monitoring/               # Configs Prometheus/Grafana
```

---

## 📚 Documentação

A documentação completa está na pasta [`docs/`](docs/). Comece pelo [índice](docs/INDICE.md).

| Documento | Descrição |
|---|---|
| [Visão Geral](docs/01-visao-geral.md) | O que é, para quem, por quê |
| [Arquitetura](docs/02-arquitetura.md) | Arquitetura técnica detalhada |
| [Banco de Dados](docs/03-banco-de-dados.md) | Modelo de dados e entidades |
| [Fluxos](docs/04-fluxos.md) | Fluxos completos do sistema |
| [LLM Router](docs/05-llm-router.md) | Roteamento inteligente de LLMs |
| [Flora AI](docs/09-flora-ai.md) | A assistente virtual |
| [Segurança](docs/10-seguranca.md) | Segurança e proteção |
| [API Endpoints](docs/11-api-endpoints.md) | Referência completa da API |
| [Estrutura de Pastas](docs/12-estrutura-pastas.md) | Organização do código |
| [Roadmap](docs/13-roadmap.md) | Roadmap de desenvolvimento |
| [Planos](docs/14-planos.md) | Planos e preços |
| [Instalação](docs/15-instalacao.md) | Guia de instalação completo |
| [Contributing](docs/contributing.md) | Guia de contribuição |
| [Deploy](docs/deploy.md) | Guia de deploy em produção |
| [FAQ](docs/faq.md) | Perguntas frequentes |
| [Changelog](docs/changelog.md) | Histórico de versões |

---

## 🔌 API

A API REST é documentada automaticamente via Swagger UI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Endpoints Principais

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/v1/auth/register` | Registrar novo usuário |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| POST | `/api/v1/auth/refresh` | Renovar access token |
| GET | `/api/v1/users/me` | Perfil do usuário logado |
| GET | `/api/v1/plans` | Listar planos disponíveis |
| POST | `/api/v1/bots` | Criar novo bot |
| GET | `/api/v1/bots` | Listar bots |
| POST | `/api/v1/whatsapp/connect` | Conectar WhatsApp (QR Code) |
| POST | `/api/v1/flora/chat` | Conversar com Flora AI |
| GET | `/api/v1/analytics/dashboard` | Dashboard de analytics |

Veja a [referência completa](docs/11-api-endpoints.md) para todos os endpoints.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja o [guia de contribuição](docs/contributing.md) para detalhes.

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 📋 Roadmap

| Fase | Status | Descrição |
|---|---|---|
| Fase 1 | ✅ Concluída | Backend core, models, auth, licenças |
| Fase 2 | ✅ Concluída | LLM Router, Flora AI, segurança |
| Fase 3 | 🔄 Em progresso | Apps KivyMD, WhatsApp connector |
| Fase 4 | 📋 Planejado | Billing, webhooks, analytics avançado |
| Fase 5 | 📋 Planejado | Deploy produção, monitoramento |

Veja o [roadmap completo](docs/13-roadmap.md) para detalhes.

---

## 📄 Licença

Este projeto é proprietário. Veja [LICENSE](LICENSE) para detalhes.

---

## 📬 Contato

**TiltzOff** — Desenvolvedor & Criador

- GitHub: [@TiltzOff](https://github.com/TiltzOff)
- Projeto: [github.com/TiltzOff/flora-platform](https://github.com/TiltzOff/flora-platform)

---

<div align="center">

🌸 **Flora Platform** — Transformando conversas em negócios.

Feito com ❤️ por TiltzOff

</div>
