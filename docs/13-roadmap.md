# 🌸 FLORA PLATFORM — Roadmap

> Roadmap de desenvolvimento: o que foi feito, o que está em progresso e o que vem por aí.

---

## 📊 Visão Geral

| Fase | Nome | Status | Progresso |
|---|---|---|---|
| **Fase 1** | Fundação | ✅ Concluída | 100% |
| **Fase 2** | Inteligência | ✅ Concluída | 100% |
| **Fase 3** | Interface | 🔄 Em progresso | ~45% |
| **Fase 4** | Monetização | 📋 Planejado | ~15% |
| **Fase 5** | Produção | 📋 Planejado | ~5% |
| **Fase 6** | Expansão | 📋 Planejado | ~0% |

---

## ✅ Fase 1 — Fundação (Concluída)

> Backend core, banco de dados, autenticação e segurança básica.

### Backend Core

- [x] Estrutura do projeto FastAPI
- [x] Configuração (pydantic-settings)
- [x] Banco de dados (SQLite dev / PostgreSQL prod)
- [x] SQLAlchemy async ORM
- [x] Sistema de migrations (Alembic)
- [x] Health check endpoint
- [x] Error handling global
- [x] CORS middleware

### Modelos de Dados

- [x] 18+ modelos SQLAlchemy
- [x] Relacionamentos (FK, many-to-many)
- [x] Timestamps automáticos (created_at, updated_at)
- [x] UUID como chave primária
- [x] Soft delete (is_active, deleted_at)

### Autenticação

- [x] Registro de usuários
- [x] Login com JWT
- [x] Refresh Token
- [x] 2FA (TOTP)
- [x] Perfil do usuário (CRUD)
- [x] Roles (admin, client)

### Sistema de Licenças

- [x] Geração de licenças com assinatura RSA
- [x] Validação de assinatura digital
- [x] Expiração e renovação
- [x] Revogação de licenas
- [x] Binding de dispositivo (anti-clone)

### Segurança

- [x] Criptografia AES/RSA
- [x] Hash de senhas (bcrypt)
- [x] Rate limiting
- [x] Audit logging
- [x] Anti-clone (hardware binding)

### Planos

- [x] 7 planos (Free → Enterprise)
- [x] CRUD de planos
- [x] Limites por plano
- [x] Acesso a LLMs por plano

---

## ✅ Fase 2 — Inteligência (Concluída)

> LLM Router, Flora AI, comandos e intenções.

### LLM Router

- [x] Arquitetura multi-provider
- [x] Integração OpenAI (GPT-4o, GPT-4o-mini)
- [x] Integração Anthropic (Claude 3.5 Sonnet, Haiku)
- [x] Integração Google (Gemini 1.5 Flash, Pro)
- [x] Integração Groq (Llama 3.1)
- [x] Integração OpenRouter
- [x] Fallback automático entre providers
- [x] Seleção por complexidade da tarefa
- [x] Otimização de custo por plano
- [x] Tracking de uso (tokens, custo)
- [x] Rate limiting por provider

### Flora AI

- [x] Definição de personalidade
- [x] System prompt engineering
- [x] Integração com LLM Router
- [x] Gestão de sessões de chat
- [x] Memória contextual
- [x] Guia de onboarding do cliente
- [x] Resolução de problemas
- [x] Redução de churn

### Comandos e Intenções

- [x] Sistema de comandos personalizados
- [x] Comandos por regex
- [x] Comandos por keyword
- [x] Sistema de intenções (intent matching)
- [x] Training phrases por intenção
- [x] Respostas dinâmicas
- [x] CRUD via API

### Templates de Bot

- [x] BotTemplates model
- [x] Templates por categoria
- [x] Criação de bot a partir de template
- [x] Templates padrão (atendimento, vendas, suporte)
- [x] Seed de templates no banco

---

## 🔄 Fase 3 — Interface (Em Progresso)

> Apps KivyMD, WhatsApp connector, analytics básico.

### App Admin (KivyMD) — 40%

- [x] Estrutura do projeto KivyMD
- [x] Design system (dark premium theme)
- [x] Tela de Login
- [x] Tela de Dashboard
- [x] Componentes base (cards, nav drawer)
- [ ] Tela de Bots (CRUD) — Em progresso
- [ ] Tela de Licenças — Em progresso
- [ ] Tela de Analytics — Pendente
- [ ] Tela de Configurações — Pendente
- [ ] Notificações push — Pendente
- [ ] Tema claro/escuro toggle — Pendente

### App Cliente (KivyMD) — 40%

- [x] Estrutura do projeto KivyMD
- [x] Design system (dark premium theme)
- [x] Tela de Login
- [x] Tela Home
- [x] Componentes base
- [ ] Tela de Setup do Bot — Em progresso
- [ ] Tela de Chat (teste) — Em progresso
- [ ] Tela de Configurações — Pendente
- [ ] Tela de Perfil — Pendente
- [ ] Integração QR Code — Pendente

### WhatsApp Connector — 50%

- [x] Estrutura do connector
- [x] Geração de QR Code
- [x] Recebimento de mensagens
- [x] Envio de mensagens
- [ ] Sessões persistentes — Em progresso
- [ ] Reconexão automática — Em progresso
- [ ] Suporte a mídias (imagens, áudio) — Pendente
- [ ] Suporte a grupos — Pendente
- [ ] Status de conexão em tempo real — Pendente

### Analytics Básico — 30%

- [x] Modelo de dados para métricas
- [x] Endpoint de dashboard
- [x] Contagem de mensagens
- [ ] Gráficos de uso — Em progresso
- [ ] Relatórios por período — Pendente
- [ ] Exportação (CSV, PDF) — Pendente
- [ ] Analytics por bot — Pendente

### Notificações — 60%

- [x] Modelo de notificações
- [x] CRUD via API
- [x] Marcar como lida
- [ ] Notificação em tempo real (WebSocket) — Em progresso
- [ ] Notificações por email — Pendente
- [ ] Push notifications — Pendente

### Sistema de Suporte — 50%

- [x] Modelo de tickets
- [x] CRUD de tickets via API
- [x] Status e prioridade
- [ ] Interface de tickets no app — Em progresso
- [ ] Notificações de novos tickets — Pendente
- [ ] SLA e escalação — Pendente

---

## 📋 Fase 4 — Monetização (Planejado)

> Billing, webhooks de pagamento, analytics avançado.

### Sistema de Pagamentos

- [ ] Integração Stripe
- [ ] Integração MercadoPago
- [ ] Gestão de assinaturas
- [ ] Cobrança recorrente
- [ ] Histórico de pagamentos
- [ ] Receipts e invoices

### Webhooks de Pagamento

- [ ] Webhook Stripe (succeso, falha, cancelamento)
- [ ] Webhook MercadoPago
- [ ] Processamento assíncrono
- [ ] Retry logic

### Analytics Avançado

- [ ] Funil de conversão
- [ ] Taxa de retenção
- [ ] LTV (Lifetime Value)
- [ ] Churn prediction
- [ ] A/B testing de prompts
- [ ] Heatmap de uso

### Sistema de Backup

- [ ] Backup automático do banco
- [ ] Restauração via API
- [ ] Backup incremental
- [ ] Retenção configurável

---

## 📋 Fase 5 — Produção (Planejado)

> Deploy, monitoramento, performance, segurança avançada.

### Deploy e Infraestrutura

- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Blue-green deployment
- [ ] Auto-scaling
- [ ] Load balancing
- [ ] CDN para assets

### Monitoramento

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Sentry error tracking
- [ ] Uptime monitoring
- [ ] Alertas por email/Slack

### Performance

- [ ] Cache Redis otimizado
- [ ] Query optimization
- [ ] Connection pooling
- [ ] CDN para mídia
- [ ] Lazy loading nos apps

### Segurança Avançada

- [ ] WAF (Web Application Firewall)
- [ ] DDoS protection
- [ ] Penetration testing
- [ ] Security headers
- [ ] Rate limiting distribuído

---

## 📋 Fase 6 — Expansão (Planejado)

> Novos canais, features avançadas e mercado.

### Novos Canais

- [ ] Telegram bot
- [ ] Instagram DM
- [ ] Facebook Messenger
- [ ] SMS
- [ ] Email automation
- [ ] Web Widget (chat embutido)

### Features Avançadas

- [ ] Multi-tenancy completo
- [ ] White-label (subdomínios customizados)
- [ ] API pública para integrações
- [ ] Marketplace de templates
- [ ] Builder visual de fluxos (drag-and-drop)
- [ ] Analytics com ML (predições)
- [ ] Sentiment analysis
- [ ] Voice bot (speech-to-text + text-to-speech)

### Mercado

- [ ] Landing page
- [ ] Programa de afiliados
- [ ] Documentação pública da API
- [ ] SDK para desenvolvedores
- [ ] Comunidade Discord

---

## 📈 Métricas de Progresso

| Componente | Progresso |
|---|---|
| Backend (FastAPI) | ████████████░░░░ 80% |
| Banco de Dados | ██████████████░░ 90% |
| Sistema de Licenças | █████████████░░░ 85% |
| LLM Router | ██████████░░░░░░ 75% |
| Flora AI | ██████████░░░░░░ 70% |
| App Admin | █████░░░░░░░░░░░ 40% |
| App Cliente | █████░░░░░░░░░░░ 40% |
| WhatsApp Connector | ██████░░░░░░░░░░ 50% |
| Analytics | ████░░░░░░░░░░░░ 30% |
| Billing | █░░░░░░░░░░░░░░░ 10% |
| Monitoramento | ██░░░░░░░░░░░░░░ 15% |

**Progresso geral: ~45%**

---

## 🔗 Próximos Passos

- [Visão Geral](01-visao-geral.md) — Entenda o projeto
- [Instalação](15-instalacao.md) — Como instalar
- [Segurança](10-seguranca.md) — Segurança da plataforma
- [Deploy](deploy.md) — Guia de deploy em produção

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Estrutura de Pastas](12-estrutura-pastas.md) | [Próximo: Planos](14-planos.md)

</div>
