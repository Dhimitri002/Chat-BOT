# 🌸 FLORA PLATFORM — Visão Geral

> Entenda o que é a Flora Platform, para quem ela foi criada e por quê.

---

## 🌺 O Que É

A **Flora Platform** é uma plataforma SaaS (Software as a Service) completa para criação e gerenciamento de **chatbots para WhatsApp** com inteligência artificial integrada.

Ela funciona como uma **fábrica de chatbots**: você configura, personaliza e coloca um bot para funcionar no WhatsApp de um cliente — tudo a partir de uma interface bonita e intuitiva.

### Em Uma Frase

> **"De bots simples baseados em regras a bots inteligentes com LLM — tudo em dois apps nativos com dark premium UI."**

---

## 🎯 Para Quem

### 👨‍💼 Empreendedores Digitais
- Querem vender chatbots como serviço
- Precisam de uma plataforma white-label
- Buscam escalar sem equipe técnica grande

### 🏢 Agências de Marketing
- Oferecem chatbot como serviço adicional
- Gerenciam múltiplos clientes em um só lugar
- Precisam de relatórios e analytics

### 👨‍💻 Desenvolvedores
- Querem uma base sólida para projetos de chatbot
- Buscam arquitetura limpa e extensível
- Precisam de multi-tenancy e gestão de licenças

### 📞 Atendimento ao Cliente
- Empresas que querem automatizar o WhatsApp
- Precisam de bot + humano (handoff)
- Querem reduzir tempo de resposta

---

## 💡 Por Que Flora?

### O Problema

Criar e gerenciar chatbots para WhatsApp é **caro, complexo e fragmentado**:

- Ferramentas existentes são caras ou limitadas
- Integrar IA (LLMs) do zero dá muito trabalho
- Gerenciar múltiplos clientes e licenças é caótico
- Apps de controle são feios ou inexistentes

### A Solução

A Flora Platform resolve tudo isso em **uma única plataforma**:

| Problema | Solução Flora |
|---|---|
| Chatbot caro e complexo | Fábrica de bots com templates prontos |
| Integração com IA difícil | LLM Router com 5+ providers |
| Gestão de clientes caótica | Sistema de licenças com assinatura digital |
| Apps feios ou inexistentes | 2 apps KivyMD com dark premium UI |
| Sem analytics | Dashboard completo de métricas |
| Sem suporte integrado | Sistema de tickets + Flora AI |

---

## ✨ Diferenciais

### 🌸 Flora AI
Uma assistente virtual **embutida no app cliente** que:
- Guia o usuário na configuração do bot
- Responde dúvidas sobre a plataforma
- Reduz churn e necessidade de suporte humano
- Usa o mesmo LLM Router dos bots

### 🔀 LLM Router
Roteamento inteligente de modelos de linguagem:
- **5+ providers**: OpenAI, Anthropic, Gemini, Groq, OpenRouter
- **Fallback automático**: se um cai, usa o próximo
- **Otimização de custo**: escolhe o modelo mais barato para cada tarefa
- **Por plano**: cada plano tem acesso a modelos diferentes

### 📱 Apps Nativos (KivyMD)
Dois apps completos com design dark premium:
- **App Admin**: gerencie bots, licenças, clientes, analytics
- **App Cliente**: configure seu bot, conecte o WhatsApp, converse com a Flora

### 🔐 Segurança de Ponta a Ponta
- Licenças com **assinatura digital RSA**
- Autenticação **JWT + Refresh Token + 2FA**
- **Rate limiting** por endpoint
- **Anti-clone** (binding de hardware)
- **Criptografia** de dados sensíveis

---

## 📊 Números do Projeto

| Métrica | Valor |
|---|---|
| **Modelos de dados** | 18+ |
| **Endpoints REST** | 40+ |
| **Planos de assinatura** | 7 (Free → Enterprise) |
| **LLM Providers** | 5+ |
| **Apps nativos** | 2 (Admin + Cliente) |
| **Documentos** | 17+ |
| **Linhas de código** | ~15.000+ |

---

## 🗺️ Como se Encaixa no Ecossistema

```
                    ┌─────────────────┐
                    │   WhatsApp Web  │
                    │   (QR Code)     │
                    └────────┬────────┘
                             │
    ┌────────────┐    ┌──────▼──────┐    ┌────────────┐
    │  App Admin │    │   Flora     │    │  App       │
    │  (KivyMD)  │◄──►│   Platform  │◄──►│  Cliente   │
    │            │    │   (FastAPI) │    │  (KivyMD)  │
    └────────────┘    └──────┬──────┘    └────────────┘
                             │
                    ┌────────▼────────┐
                    │   Flora AI /    │
                    │   LLM Router    │
                    │   (5+ providers)│
                    └─────────────────┘
```

---

## 📋 Status Atual

| Componente | Status | Progresso |
|---|---|---|
| Backend (FastAPI) | ✅ Funcional | ~80% |
| Banco de Dados | ✅ Funcional | ~90% |
| Sistema de Licenças | ✅ Funcional | ~85% |
| LLM Router | ✅ Funcional | ~75% |
| Flora AI | ✅ Funcional | ~70% |
| App Admin (KivyMD) | 🔄 Em progresso | ~40% |
| App Cliente (KivyMD) | 🔄 Em progresso | ~40% |
| WhatsApp Connector | 🔄 Em progresso | ~50% |
| Billing/Payments | 📋 Planejado | ~10% |
| Analytics Avançado | 📋 Planejado | ~15% |

---

## 🔗 Próximos Passos

- [Arquitetura Técnica](02-arquitetura.md) — Entenda a arquitetura detalhada
- [Banco de Dados](03-banco-de-dados.md) — Modelo de dados e entidades
- [Fluxos](04-fluxos.md) — Fluxos completos do sistema
- [Instalação](15-instalacao.md) — Como instalar e rodar
- [Roadmap](13-roadmap.md) — O que vem por aí

---

<div align="center">

🌸 [Índice](INDICE.md) | [Próximo: Arquitetura](02-arquitetura.md)

</div>
