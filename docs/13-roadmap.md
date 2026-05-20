# 🌸 FLORA PLATFORM — Roadmap por Fases

## Fase 0: Fundação (Semanas 1-2)
**Objeto:** Estrutura base do projeto

- [ ] Criar estrutura de pastas completa
- [ ] Configurar ambiente Python (.venv, requirements.txt)
- [ ] Configurar .env.example com todas as variáveis
- [ ] Setup do banco SQLite com SQLAlchemy + Alembic
- [ ] Criar models principais (users, licenses, plans, bots)
- [ ] Criar schemas Pydantic
- [ ] Setup do FastAPI com router base
- [ ] Endpoint de health check
- [ ] Configurar Loguru
- [ ] README.md completo

## Fase 1: Autenticação e Segurança (Semanas 3-4)
**Objeto:** Sistema de auth completo

- [ ] Registro de usuários
- [ ] Login com JWT (access + refresh)
- [ ] Hash de senhas com Argon2id
- [ ] 2FA/TOTP para admins
- [ ] Rate limiting
- [ ] Proteção brute force
- [ ] RBAC (roles e permissões)
- [ ] Criptografia AES-256-GCM
- [ ] Geração de par de chaves RSA para licenças
- [ ] Logs de auditoria
- [ ] Middleware de segurança

## Fase 2: Sistema de Licenças (Semanas 5-6)
**Objeto:** Geração e validação de licenças

- [ ] CRUD de planos
- [ ] Geração de licenças com assinatura digital
- [ ] Validação de licença (endpoint)
- [ ] Fingerprint de dispositivo
- [ ] Anti-replay
- [ ] Revogação remota
- [ ] Renovação
- [ ] Expiração automática
- [ ] Seed de planos padrão (Starter → Enterprise)

## Fase 3: Backend de Bots (Semanas 7-8)
**Objeto:** CRUD e configuração de bots

- [ ] CRUD de bots
- [ ] CRUD de intents
- [ ] CRUD de comandos
- [ ] Motor de comandos (command engine)
- [ ] Intent matcher
- [ ] CRUD de templates
- [ ] Aplicar template em bot
- [ ] Versionamento de configuração
- [ ] Backup/restore de bot

## Fase 4: WhatsApp Connector (Semanas 9-10)
**Objeto:** Conexão WhatsApp funcionando

- [ ] Integração WPPConnect
- [ ] Geração de QR Code
- [ ] Gerenciamento de sessões
- [ ] Recebimento de mensagens
- [ ] Envio de mensagens
- [ ] Processamento de mensagem (intent → resposta)
- [ ] Fallback para LLM
- [ ] Status da conexão
- [ ] Reconexão automática
- [ ] Envio de mídia (básico)

## Fase 5: LLM Router (Semanas 11-12)
**Objeto:** Roteamento inteligente de LLMs

- [ ] Implementar base do LLM Router
- [ ] Provider: Groq
- [ ] Provider: Gemini
- [ ] Provider: OpenAI
- [ ] Provider: Anthropic
- [ ] Provider: Ollama (local)
- [ ] Fallback chain
- [ ] Rate limiting por plano
- [ ] Controle de custos
- [ ] Métricas de uso (tokens, custo, latência)
- [ ] Registro de uso no banco

## Fase 6: Flora AI (Semanas 13-14)
**Objeto:** Assistente Flora funcionando

- [ ] System prompt da Flora
- [ ] Endpoint /chat/flora
- [ ] Integração com LLM Router
- [ ] Memória de conversa (sessão)
- [ ] Sugestões rápidas (chips)
- [ ] Streaming de resposta
- [ ] Contexto do cliente no prompt
- [ ] Limites e regras da Flora

## Fase 7: App do Cliente - KivyMD (Semanas 15-18)
**Objeto:** App do cliente funcional

- [ ] Setup KivyMD com tema dark premium
- [ ] Splash screen
- [ ] Onboarding (3 slides)
- [ ] Tela de validação de licença
- [ ] Dashboard do bot
- [ ] Tela de conexão WhatsApp (QR Code)
- [ ] Chat de teste
- [ ] Chat com Flora
- [ ] Tela do plano
- [ ] Relatórios simples
- [ ] Configurações do bot
- [ ] Suporte
- [ ] Conta
- [ ] Notificações
- [ ] Bottom navigation
- [ ] Componentes reutilizáveis
- [ ] API client
- [ ] WebSocket client (tempo real)

## Fase 8: App Administrador - KivyMD (Semanas 19-22)
**Objeto:** App admin funcional

- [ ] Setup KivyMD com tema dark premium
- [ ] Login + 2FA
- [ ] Dashboard com cards e gráficos
- [ ] Lista de bots
- [ ] Editor de bot (wizard 8 etapas)
- [ ] Gerenciador de licenças
- [ ] Gerenciador de clientes
- [ ] Gerenciador de planos
- [ ] Analytics com gráficos
- [ ] Logs e auditoria
- [ ] Backup/restore
- [ ] Templates
- [ ] Suporte (tickets)
- [ ] Configurações
- [ ] Sandbox de teste
- [ ] Sidebar navigation
- [ ] Componentes reutilizáveis

## Fase 9: Analytics e Billing (Semanas 23-24)
**Objeto:** Métricas e pagamentos

- [ ] Dashboard de analytics completo
- [ ] Métricas de mensagens
- [ ] Métricas de LLM (custo, tokens, latência)
- [ ] Relatórios por bot/cliente
- [ ] Exportação Excel/PDF
- [ ] Integração Stripe (checkout)
- [ ] Integração MercadoPago
- [ ] Webhook de pagamento
- [ ] Cobrança recorrente
- [ ] Notificação de vencimento
- [ ] Grace period

## Fase 10: Polimento e Produção (Semanas 25-26)
**Objeto:** Produto pronto para vender

- [ ] Testes unitários (pytest)
- [ ] Testes de integração
- [ ] Correção de bugs
- [ ] Otimização de performance
- [ ] Build com PyInstaller
- [ ] Docker setup
- [ ] Deploy em VPS
- [ ] PostgreSQL (migrar de SQLite)
- [ ] Redis (cache + sessões)
- [ ] Nginx reverse proxy
- [ ] SSL/HTTPS
- [ ] Monitoramento (logs, alertas)
- [ ] Documentação final
- [ ] Vídeo de demo

## Fase 11: Expansão (Semanas 27+)
**Objeto:** Crescimento contínuo

- [ ] Mais provedores LLM (DeepSeek, Cohere, Together)
- [ ] Mais templates de bot
- [ ] Sistema de revenda
- [ ] White-label
- [ ] API pública para clientes Enterprise
- [ ] Webhooks outbound
- [ ] Integração CRM
- [ ] Campanhas de marketing
- [ ] App mobile (Android via Buildozer)
- [ ] Versão web (opcional)
- [ ] Multi-idioma (EN, ES)
- [ ] Marketplace de templates
- [ ] Programa de afiliados
- [ ] Suporte humano integrado
