# 🌸 Visao Geral da Arquitetura

> **Versao:** 1.0.0 | **Data:** 2026-05-26 | **Status:** Em Desenvolvimento

---

## 1. Visao de Alto Nivel

A Flora Platform e uma fabrica de chatbots para WhatsApp baseada em SaaS. Possui tres componentes principais:

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLORA PLATFORM                              │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  APP ADMIN   │    │   BACKEND    │    │ APP CLIENTE  │       │
│  │   (KivyMD)   │    │  (FastAPI)   │    │  (KivyMD)    │       │
│  │              │    │              │    │              │       │
│  │ Dashboard    │◄──►│ API REST     │◄──►│ Dashboard    │       │
│  │ Editor Bot   │    │ JWT Auth     │    │ Licenca      │       │
│  │ Licencas     │    │ CRUD Bots    │    │ QR Code      │       │
│  │ Analytics    │    │ WhatsApp     │    │ Flora AI     │       │
│  │ Clientes     │    │ Flora AI     │    │ Chat Teste   │       │
│  │ Planos       │    │ Analytics    │    │ Planos       │       │
│  └──────────────┘    └──────┬───────┘    └──────────────┘       │
│                             │                                    │
│                    ┌────────┼────────┐                          │
│                    │        │        │                           │
│                    ▼        ▼        ▼                           │
│              ┌────────┐ ┌───────┐ ┌──────────┐                 │
│              │SQLite/ │ │ Redis │ │ WPPConn. │                 │
│              │ PgSQL  │ │       │ │ WhatsApp │                 │
│              └────────┘ └───────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Os Dois Apps

### 2.1 App Administrador (`app_admin/`)

O painel de controle da plataforma. Usado pelo **dono da plataforma** ou **equipe de suporte**.

**Escopo:**
- Dashboard com metricas de toda a plataforma
- Gerenciamento de clientes e licencas
- CRUD de planos
- Editor completo de bots (wizard 8 etapas)
- Analytics avancados (receita, LLM usage, usuarios)
- Logs de auditoria
- Backup/restore
- Sandbox de teste

**Fluxo principal:**
```
Login Admin → Dashboard → [Bots / Clientes / Planos / Analytics / Config]
```

### 2.2 App Cliente (`app_cliente/`)

O app que o **cliente final** usa para configurar e monitorar seu bot.

**Escopo:**
- Validacao de licenca (ou geracao nova + pagamento)
- Dashboard do bot personalizado
- Conexao WhatsApp (QR Code)
- Chat de teste com o bot
- Flora AI integrada (assistente)
- Visualizacao do plano e upgrade
- Metricas basicas de uso

**Fluxo principal:**
```
Onboarding → Validacao Licenca → Dashboard → [Bot / Conexao / Flora / Plano]
```

---

## 3. Backend (`api/`)

O coracao da plataforma. FastAPI async com separacao de camadas:

**Camadas:**
```
api/v1/          → Endpoints (rotas, request/response)
   ↓
services/        → Logica de negocio
   ↓
models/          → SQLAlchemy models (tabelas)
   ↓
schemas/         → Pydantic schemas (validacao)
   ↓
core/            → Seguranca, crypto, LLM router
   ↓
database/        → Conexao DB + sessions
```

**Recursos implementados:**

| Recurso | Status | Arquivo |
|---------|--------|---------|
| Auth (JWT, register, login) | ✅ | `api/v1/auth.py` |
| Users (CRUD, RBAC) | ✅ | `api/v1/users.py` |
| Bots (CRUD) | ✅ | `api/v1/bots.py` |
| Licenses (CRUD, validate, activate) | ✅ | `api/v1/licenses.py` |
| Plans (CRUD) | ✅ | `api/v1/plans.py` |
| Chat (history, send, conversations) | ✅ | `api/v1/chat.py` |
| Commands (CRUD) | ✅ | `api/v1/commands.py` |
| Intents (CRUD) | ✅ | `api/v1/intents.py` |
| WhatsApp (connect, disconnect, send, QR) | ✅ | `api/v1/whatsapp.py` |
| Flora AI (chat, help, suggestions) | ✅ | `api/v1/flora.py` |
| Analytics (dashboard, messages, users, revenue) | ✅ | `api/v1/analytics.py` |
| Admin (operations) | ✅ | `api/v1/admin.py` |
| Health checks | ✅ | `api/v1/health.py` |
| Webhooks | 📋 | `api/v1/webhooks.py` |
| Billing | 📋 | `api/v1/billing.py` |
| Notifications | 📋 | `api/v1/notifications.py` |

---

## 4. Seguranca

Principio fundamental: **O app do cliente nunca deve conter a chave mestra. Toda validacao critica acontece no backend.**

```
Camada 1: Transporte     → HTTPS/TLS 1.3, certificate pinning
Camada 2: Autenticacao   → JWT (access 15min + refresh 7dias), Argon2id/BCrypt, 2FA
Camada 3: Autorizacao    → RBAC (roles: user, admin, superadmin)
Camada 4: Criptografia   → AES-256-GCM (dados), RSA (licencas), SHA-256
Camada 5: Rate Limiting  → Redis-based, por usuario/IP
Camada 6: Auditoria      → AuditLog em todas as operacoes criticas
```

---

## 5. Modelo de Dados (Simplificado)

```
┌─────────┐     ┌───────────┐     ┌─────────┐
│  Users  │────<│  Licenses │>────│  Plans  │
└────┬────┘     └───────────┘     └─────────┘
     │
     │  1:N
     ▼
┌─────────┐     ┌───────────┐     ┌──────────┐
│   Bots  │────<│ WhatsApp  │     │  Intents │
└────┬────┘     │ Sessions  │     └──────────┘
     │          └───────────┘
     │  1:N
     ▼
┌─────────┐     ┌───────────┐
│ Messages│     │  Commands │
└─────────┘     └───────────┘

┌──────────────┐  ┌──────────┐  ┌──────────────┐
│ FloraSession │  │ Payments │  │  AuditLogs   │
└──────────────┘  └──────────┘  └──────────────┘
```

Diagrama ER completo: [`../03-banco-de-dados.md`](../03-banco-de-dados.md)

---

## 6. Integracao WhatsApp

```
App Cliente → Backend API → WhatsAppService → WPPConnect → WhatsApp
                                  │
                                  ├── SessionStore (arquivo/local)
                                  ├── ConnectionState machine
                                  ├── QR Code generation
                                  └── Message routing
```

**Estados de conexao:**
```
DISCONNECTED → CONNECTING → QR_WAITING → CONNECTED
                    ↑                          │
                    └──── RECONNECTING ←──────┘
                                        ↓
                                   LOGGED_OUT / ERROR
```

Detalhes: [`whatsapp-integration.md`](whatsapp-integration.md)

---

## 7. Flora AI

```
Cliente → /api/v1/flora/chat → FloraService → LLM Router → Provider (Groq, Gemini, OpenAI...)
                │
                ├── System Prompt (personalidade, regras)
                ├── Context Injection (plano, licenca, bot status)
                ├── Intent Detection
                └── History Management (FloraSession)
```

Detalhes: [`flora-ai.md`](flora-ai.md)

---

## 8. Multi-LLM Router

O sistema suporta multiplos provedores de LLM com politica por plano:

| Planos | Provideres Liberados | Modelo Principal |
|--------|---------------------|-----------------|
| Starter, Basic | Nenhum (regras apenas) | — |
| Plus | Nenhum (regras apenas) | — |
| Pro | Groq | llama-3.1-70b |
| Master | Groq, Gemini, OpenAI | gpt-4o |
| Elite | Todos | gpt-4o |
| Enterprise | Todos + Ollama | Configuravel |

Detalhes: [`../05-llm-router.md`](../05-llm-router.md)

---

## 9. Fluxo de Licenca

```
1. Admin cria licenca no App Admin
   → LicenseService.create_license()
   → RSA signature = sign(plan_id + user_id + expiry + machine_id)
   → AES-256-GCM encriptacao do arquivo de licenca

2. Cliente ativa licenca no App Cliente
   → POST /licenses/validate {key, device_fingerprint}
   → LicenseService.verify_signature()
   → Verifica: expiry, device binding, revoked status

3. A cada abertura do app
   → LicenseService.validate_license(local_file)
   → Compara device fingerprint
   → Grace period de 7 dias se expirado
```

---

## 10. Plano de Deploy (Producao)

```
                    ┌─────────────┐
                    │  Nginx      │
                    │  (reverse   │
                    │   proxy,    │
                    │   TLS)      │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  FastAPI    │
                    │  (Uvicorn)  │
                    │  x3 workers │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │ WPPConnect│
        │   15+    │ │   7+     │ │  Node.js  │
        └──────────┘ └──────────┘ └──────────┘
```

---

## 11. Status da Implementacao

| Componente | Status | Progresso |
|-----------|--------|-----------|
| Backend API (FastAPI) | ✅ Implementado | ~90% |
| Models + Schemas | ✅ Implementado | ~95% |
| Auth + Seguranca | ✅ Implementado | ~85% |
| WhatsApp Connector | ✅ Implementado | ~75% |
| Flora AI | ✅ Implementado | ~70% |
| Analytics | ✅ Implementado | ~65% |
| App Admin (KivyMD) | 🔄 Em progresso | ~30% |
| App Cliente (KivyMD) | 🔄 Em progresso | ~40% |
| Testes | 🔄 Em progresso | ~15% |
| Docker + CI/CD | 📋 Planejado | ~10% |
| Deploy Producao | 📋 Planejado | ~5% |

Detalhes: [`../STATUS.md`](../STATUS.md) | [`../13-roadmap.md`](../13-roadmap.md)

---

## 12. Navegacao da Documentacao

### Arquitetura
- [Backend](backend.md) — Detalhes da API FastAPI
- [App Cliente](client-app.md) — Arquitetura do app cliente
- [App Admin](admin-app.md) — Arquitetura do app admin
- [WhatsApp](whatsapp-integration.md) — Integracao WhatsApp
- [Flora AI](flora-ai.md) — Sistema Flora AI

### API Reference
- [Auth](../API/auth.md) — Autenticacao
- [Bots](../API/bots.md) — CRUD de bots
- [Licenses](../API/licenses.md) — Sistema de licencas
- [WhatsApp](../API/whatsapp.md) — Conexao e mensagens
- [Chat](../API/chat.md) — Historico
- [Plans](../API/plans.md) — Planos
- [Analytics](../API/analytics.md) — Metricas
- [Flora](../API/flora.md) — Flora AI

### Guias
- [Instalacao](../guides/instalacao.md) — Como instalar
- [Configuracao](../guides/configuracao.md) — Variaveis de ambiente
- [Execucao](../guides/execucao.md) — Como executar
- [Desenvolvimento](../guides/desenvolvimento.md) — Guia do dev
- [Deploy](../guides/deploy.md) — Deploy em producao
