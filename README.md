# 🌸 Flora Platform - Fábrica de Chatbots WhatsApp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![KivyMD](https://img.shields.io/badge/KivyMD-1.2.0-009688.svg)](https://kivymd.readthedocs.io/)

> **Plataforma SaaS completa para criação, gerenciamento e monetização de chatbots profissionais para WhatsApp**

## 📋 Visão Geral

A **Flora Platform** é uma solução completa (white-label) para empreendedores criarem e venderem chatbots inteligentes para WhatsApp. Combine o poder dos LLMs modernos com uma experiência do usuário premium para criar bots que realmente convertem e geram valor.

### 🎯 Para Quem é Esta Plataforma?

- **Empreendedores digitais** que querem um negócio recorrente
- **Agências de marketing** que desejam oferecer chatbots como serviço
- **Desenvolvedores freelancers** que querem escalar seus serviços
- **Empresas** que precisam automatizar atendimento e vendas no WhatsApp

## 🚀 Status Atual

> **Em desenvolvimento ativo** - Funcionalidades principais implementadas, frontend em fase inicial

✅ **Backend Core**: 90% concluído  
✅ **Documentação Técnica**: Completa  
✅ **Arquitetura**: Definida e estruturada  
🔄 **Frontend Apps**: 5% concluído (necessário completar telas)  
🔄 **WhatsApp Integration**: Parcial (requer implementação completa)  
❌ **Testes Automatizados**: Pendente  
❌ **Deploy/DevOps**: Pendente  

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FLORA PLATFORM                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐    │
│  │  App Admin   │◀──▶│   Backend    │◀──▶│  App Cliente │    │
│  │ (KivyMD)     │    │ (FastAPI)    │    │ (KivyMD)     │    │
│  └──────────────┘    └──────┬───────┘    └────────────┘    │
│                             │                           │
│                     ┌───────▼───────┐ ┌─────────────┐   │
│                     │  PostgreSQL   │ │   Redis     │   │
│                     │   + Timescale │ │   (Cache)   │   │
│                     └───────┬───────┘ └─────────────┘   │
│                             │                           │
│               ┌─────────────▼─────────────┐             │
│               │     LLM Router            │             │
│               │ (Groq/Gemini/OpenAI/      │             │
│               │  Anthropic/Ollama)        │             │
│               └─────────────┬─────────────┘             │
│                             │                           │
│               ┌─────────────▼─────────────┐             │
│               │   WhatsApp Manager        │             │
│               │ (WPPConnect + Webhooks)   │             │
│               └───────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 💎 Funcionalidades Principais

### 👑 Para Administradores (App Admin)
- **Dashboard Executivo**: Métricas em tempo real (receita, churn, LTV)
- **Gestão de Bots**: Criar, editar, clonar e excluir bots ilimitados
- **Gerenciamento de Clientes**: CRUD completo com segmentação
- **Controle de Planos**: Criar edições personalizadas com limites específicos
- **Licenciamento**: Geração, validação e revogação de licenças seguras
- **Analytics Avançado**: Relatórios personalizáveis com exportação
- **Logs & Auditoria**: Rastreamento completo de todas as ações
- **Backup & Restore**: Agendamento automático e recuperação sob demanda
- **Suporte Integrado**: Sistema de tickets dentro da plataforma
- **Marketplace de Templates**: Biblioteca de prompts prontos por nicho
- **White-label Completo**: Personalização total da marca

### 📱 Para Clientes (App Cliente)
- **Onboarding Guiado**: 3-step tour interativo de boas-vindas
- **Validação de Licença**: Input manual ou QR Code para ativação instantânea
- **Dashboard do Bot**: Status de conexão, métricas básicas e alertas
- **Conexão WhatsApp**: Pareamento seguro via QR Code (como WhatsApp Web)
- **Flora AI Chat**: Assistente pessoal para ajudar na configuração
- **Teste em Tempo Real**: Converse com seu bot antes de publicar
- **Configuração Avançada**: Prompt, personalidade, comandos customizados
- **Meu Plano**: Visualização de uso, limites e opções de upgrade
- **Relatórios Simples**: Métricas de engajamento e performance
- **Central de Notificações**: Alertas importantes e atualizações do sistema
- **Suporte Direto**: Chat com equipe de suporte ou comunidade

### ⚙️ Backend (Powered by FastAPI)
- **LLM Router Inteligente**: Seleção automática do melhor modelo por tarefa e plano
- **Sistema de Comandos**: Crie automações poderosas com linguagem natural
- **Memória Contextual**: Lembra conversas importantes por plano
- **Webhook Receber/Enviar**: Integração com sistemas externos (CRM, ERP, etc.)
- **Rate Limiting Inteligente**: Proteção contra abuso por plano e IP
- **Segurança de nível empresarial**: Auth2, criptografia AES-256, assinaturas digitais
- **Arquitetura Escalável**: Stateless, pronta para Kubernetes e auto-scaling
- **Monitoramento Completo**: Métricas Prometheus, logs estruturados, health checks

## 🔗 Integração com WhatsApp

A Flora Platform oferece integração nativa e segura com WhatsApp através de:

1. **QR Code Pairing**: Experiência familiar como WhatsApp Web/Desktop
2. **Gerenciamento de Sessão**: Persistência automática e reconexão inteligente
3. **Webhook Recebendo**: Processamento em tempo real de mensagens recebidas
4. **Envio de Mensagens**: Suporte a texto, imagem, vídeo, documento, localização e contatos
5. **Templates Aprovados**: Envio de mensagens template para notificações
6. **Gerenciamento de Grupos**: Criação, participação e moderação de grupos
7. **Status e Presence**: Visualização de online/offline e digitação
8. **Marcadores de Leitura**: Confirmação de entrega e leitura
9. **Webhook de Status**: Notificações de conexão, desconexão e erros
10. **Gerenciamento de Perfil**: Atualização de nome, foto e status do bot

## 🧠 Flora AI - Sua Assistente Pessoal

A Flora AI está integrada em todos os pontos de contato da plataforma para:

- **Reduzir o churn** através de orientação proativa
- **Diminuir tickets de suporte** respondendo perguntas comuns
- **Guiar onboarding** de novos clientes de forma pessoal
- **Sugerir melhorias** baseado no uso e plano do cliente
- **Explicar recursos complexos** em linguagem simples
- **Oferecer suporte 24/7** em múltiplos idiomas
- **Aprender com interações** para ficar cada vez mais útil

## 🔒 Segurança e Privacidade

- **Autenticação**: JWT com refresh tokens e rotação automática
- **Autorização**: Controle de acesso baseado em papéis (RBAC) granular
- **Criptografia**: AES-256 para dados em repouso, TLS 1.3+ em trânsito
- **Assinatura Digital**: Licenças protegidas contra falsificação
- **Privacidade**: Isolamento rigoroso de dados entre clientes
- **Compliance**: LGPD pronto, GDPR-ready com direito ao esquecimento
- **Auditoria**: Log imutável de todas as ações críticas
- **Rate Limiting**: Proteção contra DDoS e abuso de APIs
- **Input Validation**: Sanitização rigorosa de todas as entradas
- **Dependency Scanning**: Verificação automática de vulnerabilidades

## 💰 Modelo de Monetização

### Planos Disponíveis
| Plano       | Preço       | Bots | Mensagens/mês | LLMs Acessíveis | Recursos |
|-------------|-------------|------|---------------|-----------------|----------|
| **Starter** | R$ 49,90    | 1    | 1.000         | Groq Free       | Básico   |
| **Growth**  | R$ 149,90   | 5    | 10.000        | Groq + Gemini   | Médio    |
| **Pro**     | R$ 399,90   | 20   | 50.000        | Todos + Ollama  | Avançado |
| **Enterprise** | Custom   | Ilimitado | Ilimitado   | Todos + SLA     | Total    |

### Add-ons Disponíveis
- **+10.000 mensagens**: R$ 29,90
- **Bot extra**: R$ 19,90/mês
- **WhatsApp Business API**: R$ 99,90/mês
- **Consultoria de implementação**: R$ 499,90/sessão
- **Templaes premium**: A partir de R$ 49,90 cada

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno e assíncrono
- **SQLAlchemy 2.0**: ORM poderoso com suporte a PostgreSQL
- **Pydantic**: Validação de dados e settings modernos
- **Python-Jose**: Autenticação JWT segura
- **Passlib**: Hash de senhas moderno (Argon2id, bcrypt)
- **Cryptography**: Assinaturas digitais e criptografia avançada
- **Redis**: Cache, filas e pub/sub
- **Celery**: Processamento assíncrono de tarefas
- **WPPConnect**: Ponte para WhatsApp Web
- **Groq/Gemini/OpenAI/Anthropic**: Acesso a LLMs de ponta
- **Ollama**: Suporte a modelos locais para empresas

### Frontend (Apps)
- **Python 3.11+**: Linguagem única para todo o stack
- **Kivy**: Framework cross-platform nativos
- **KivyMD**: Implementação Material Design 3
- **KV Language**: Declaração declarativa de UI
- **Pillow**: Manipulação avançada de imagens
- **Matplotlib**: Gráficos e visualizações
- **QRCode**: Geração de códigos para pareamento WhatsApp
- **Requests/Aiohttp**: Cliente HTTP síncrono e assíncrono
- **Python-SocketIO**: Comunicação em tempo real

### DevOps & Infra
- **Docker**: Containerização de todos os serviços
- **Docker-Compose**: Orquestração local de desenvolvimento
- **GitHub Actions**: CI/CD automatizado
- **Prometheus/Grafana**: Monitoramento e alertas
- **ELK Stack**: Logs centralizados e análise
- **Backup Automático**: Snapshots diários do banco
- **SSL/TLS**: Certificados automáticos com Let's Encrypt

## 📦 Instalação e Setup

### Pré-requisitos
- Python 3.11 ou superior
- PostgreSQL 15+ (ou SQLite para desenvolvimento)
- Redis 7+
- Node.js 18+ (para WhatsApp connector opcional)
- Docker e Docker-Compose (para deploy completo)
- Git

### Desenvolvimento Local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/flora-platform.git
cd flora-platform

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 5. Inicialize o banco de dados
alembic upgrade head

# 6. Execute os serviços
# Em terminais separados:
python -m uvicorn backend.main:app --reload  # Backend API
python run_admin.py                           # App Admin
python run_cliente.py                         # App Cliente
```

### Produção com Docker

```bash
# 1. Configure ambiente de produção
cp .env.production.example .env
# Edite .env com suas configurações de produção

# 2. Construa e execute os containers
docker-compose -f docker-compose.prod.yml up -d

# 3. Execute migrações
docker-compose exec backend alembic upgrade head

# 4. Acesse:
# - Admin: http://seudominio/admin
# - Cliente: http://seudominio/cliente
# - API Docs: http://seudominio/docs
```

## 📚 Documentação

Documentação completa disponível na pasta `/docs`:

- [🌸 Visão Geral do Produto](docs/01-visao-geral.md)
- [🏗️ Arquitetura Completa](docs/02-arquitetura.md)
- [💾 Banco de Dados Detalhado](docs/03-banco-de-dados.md)
- [🔄 Fluxos de Negócio](docs/04-fluxos.md)
- [⚙️ LLM Router Inteligente](docs/05-llm-router.md)
- [📱 Telas do App Admin](docs/06-telas-app-admin.md)
- [📲 Telas do App Cliente](docs/07-telas-app-cliente.md)
- [�� Design Visual e Theme](docs/08-design-visual.md)
- [🤖 Flora AI - Assistente Integrada](docs/09-flora-ai.md)
- [🔐 Segurança e Privacidade](docs/10-seguranca.md)
- [💰 Modelo de Monetização](docs/11-monetizacao.md)
- [🚀 Guia de Deploy](docs/12-deploy.md)
- [🧪 Testes e Qualidade](docs/13-testes.md)
- [📈 Roadmap e Futuro](docs/14-roadmap.md)

## 🧪 Testes

Executa a suíte de testes:

```bash
# Testes unitários
pytest

# Testes com cobertura
pytest --cov=backend --cov-report=html

# Testes específicos
pytest tests/test_auth.py
pytest tests/test_whatsapp.py -v

# Testes de carga (exemplo)
locust -f locustfile.py --host=http://localhost:8000
```

## 👥 Contribuindo

Quer contribuir? Ótimo! Siga estas diretrizes:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Faça suas alterações
4. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
5. Push para a branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

Leia nosso [Guia de Contribuição](CONTRIBUTING.md) para detalhes.

### Código de Conduta
Por favor, leia nosso [Código de Conduta](CODE_OF_CONDUCT.md) para manter um ambiente respeitoso e produtivo.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Comunidade Kivy/KivyMD** pelo excelente framework cross-platform
- **Equipe do FastAPI** pelo framework web moderno e performático
- **Provedores de LLM** (Groq, Gemini, OpenAI, Anthropic) pelo acesso a modelos de ponta
- **Projeto WPPConnect** pela ponte para WhatsApp Web
- **Todos os contribuidores open-source** que tornam isso possível

## 📞 Suporte e Contato

- **Documentação**: /docs ou [docs.seudominio.com](https://docs.seudominio.com)
- **Suporte Técnico**: support@floraplatform.com
- **Vendas e Parcerias**: sales@floraplatform.com
- **Relatar Bugs**: issues no GitHub
- **Feature Requests**: discussions no GitHub
- **Comunidade**: discord.gg/floraplatform
- **Twitter**: @FloraPlatform
- **LinkedIn**: company/flora-platform

---

<div align="center">
  <sub>Construído com ❤️ por empreendedores, para empreendedores</sub><br>
  <sub>Versão 1.0.0 • © 2026 Flora Platform</sub>
</div>