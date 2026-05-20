# 🌸 FLORA PLATFORM — Estrutura de Pastas

```
flora-platform/
│
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── Dockerfile
│
├── backend/                              # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                           # Entry point
│   ├── config.py                         # Configurações (pydantic-settings)
│   ├── database.py                       # Conexão DB + session
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                       # Dependências (auth, db)
│   │   ├── router.py                     # Router principal
│   │   │
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── licenses.py
│   │   │   ├── plans.py
│   │   │   ├── subscriptions.py
│   │   │   ├── bots.py
│   │   │   ├── whatsapp.py
│   │   │   ├── intents.py
│   │   │   ├── commands.py
│   │   │   ├── chat.py
│   │   │   ├── analytics.py
│   │   │   ├── billing.py
│   │   │   ├── support.py
│   │   │   ├── backup.py
│   │   │   ├── templates.py
│   │   │   ├── webhooks.py
│   │   │   └── system.py
│   │   │
│   │   └── webhooks/
│   │       ├── __init__.py
│   │       ├── stripe.py
│   │       └── mercadopago.py
│   │
│   ├── models/                           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── license.py
│   │   ├── plan.py
│   │   ├── subscription.py
│   │   ├── bot.py
│   │   ├── whatsapp_session.py
│   │   ├── intent.py
│   │   ├── command.py
│   │   ├── memory.py
│   │   ├── message.py
│   │   ├── llm_usage.py
│   │   ├── audit_log.py
│   │   ├── system_event.py
│   │   ├── backup.py
│   │   ├── webhook.py
│   │   ├── support_ticket.py
│   │   ├── bot_template.py
│   │   └── reseller.py
│   │
│   ├── schemas/                          # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── license.py
│   │   ├── plan.py
│   │   ├── bot.py
│   │   ├── chat.py
│   │   ├── analytics.py
│   │   └── common.py
│   │
│   ├── services/                         # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── license_service.py
│   │   ├── bot_service.py
│   │   ├── whatsapp_service.py
│   │   ├── chat_service.py
│   │   ├── billing_service.py
│   │   ├── analytics_service.py
│   │   ├── backup_service.py
│   │   ├── notification_service.py
│   │   └── support_service.py
│   │
│   ├── core/                             # Core do sistema
│   │   ├── __init__.py
│   │   ├── security.py                   # Criptografia, JWT, hash
│   │   ├── llm_router.py                 # Roteador de LLMs
│   │   ├── llm_providers/                # Implementações por provider
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── groq.py
│   │   │   ├── gemini.py
│   │   │   ├── openai.py
│   │   │   ├── anthropic.py
│   │   │   ├── ollama.py
│   │   │   └── deepseek.py
│   │   ├── flora_ai.py                   # Lógica da Flora
│   │   ├── command_engine.py             # Motor de comandos
│   │   ├── intent_matcher.py             # Matching de intents
│   │   ├── audit.py                      # Auditoria
│   │   └── exceptions.py                 # Exceções customizadas
│   │
│   ├── tasks/                            # Tarefas agendadas
│   │   ├── __init__.py
│   │   ├── scheduler.py
│   │   ├── license_check.py
│   │   ├── backup_task.py
│   │   ├── cleanup_task.py
│   │   └── notification_task.py
│   │
│   ├── migrations/                       # Alembic
│   │   ├── env.py
│   │   ├── alembic.ini
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_licenses.py
│   │   ├── test_bots.py
│   │   ├── test_chat.py
│   │   ├── test_llm_router.py
│   │   ├── test_security.py
│   │   └── test_commands.py
│   │
│   └── scripts/
│       ├── seed_plans.py
│       ├── generate_keys.py
│       └── init_db.py
│
├── app-admin/                            # App Administrador (KivyMD)
│   ├── main.py
│   ├── buildozer.spec
│   │
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── splash_screen.py
│   │   ├── login_screen.py
│   │   ├── dashboard_screen.py
│   │   ├── bot_list_screen.py
│   │   ├── bot_editor_screen.py
│   │   ├── license_manager_screen.py
│   │   ├── client_manager_screen.py
│   │   ├── plan_manager_screen.py
│   │   ├── analytics_screen.py
│   │   ├── logs_screen.py
│   │   ├── backup_screen.py
│   │   ├── template_screen.py
│   │   ├── support_screen.py
│   │   ├── settings_screen.py
│   │   └── sandbox_screen.py
│   │
│   ├── components/                       # Componentes reutilizáveis
│   │   ├── __init__.py
│   │   ├── cards.py
│   │   ├── charts.py
│   │   ├── dialogs.py
│   │   ├── navigation.py
│   │   ├── forms.py
│   │   └── loading.py
│   │
│   ├── services/                         # Cliente da API
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── auth_manager.py
│   │   └── websocket_client.py
│   │
│   ├── themes/
│   │   ├── __init__.py
│   │   ├── colors.py
│   │   ├── typography.py
│   │   └── theme.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── helpers.py
│   │
│   ├── assets/
│   │   ├── images/
│   │   │   ├── logo.png
│   │   │   ├── logo_splash.png
│   │   │   ├── flora_avatar.png
│   │   │   └── empty_states/
│   │   ├── fonts/
│   │   │   ├── Inter-Regular.ttf
│   │   │   ├── Inter-Bold.ttf
│   │   │   └── JetBrainsMono-Regular.ttf
│   │   └── icons/
│   │
│   └── views/                            # Arquivos .kv
│       ├── splash.kv
│       ├── login.kv
│       ├── dashboard.kv
│       └── ...
│
├── app-cliente/                          # App do Cliente (KivyMD)
│   ├── main.py
│   ├── buildozer.spec
│   │
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── splash_screen.py
│   │   ├── welcome_screen.py
│   │   ├── license_screen.py
│   │   ├── dashboard_screen.py
│   │   ├── whatsapp_connect_screen.py
│   │   ├── chat_screen.py
│   │   ├── flora_chat_screen.py
│   │   ├── plan_screen.py
│   │   ├── reports_screen.py
│   │   ├── bot_settings_screen.py
│   │   ├── support_screen.py
│   │   ├── account_screen.py
│   │   └── notifications_screen.py
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── qr_display.py
│   │   ├── chat_bubble.py
│   │   ├── plan_card.py
│   │   └── status_indicator.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── license_manager.py
│   │   └── websocket_client.py
│   │
│   ├── themes/
│   │   ├── colors.py
│   │   └── theme.py
│   │
│   ├── assets/
│   │   ├── images/
│   │   └── fonts/
│   │
│   └── views/
│       └── ...
│
├── whatsapp-connector/                   # Serviço de conexão WhatsApp
│   ├── main.py
│   ├── session_manager.py
│   ├── message_handler.py
│   ├── qr_generator.py
│   └── config.py
│
├── docs/                                 # Documentação
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
│   ├── 14-planos.md
│   └── 15-ideias-expansao.md
│
├── scripts/                              # Scripts utilitários
│   ├── setup.sh
│   ├── run_dev.sh
│   ├── run_prod.sh
│   └── backup.sh
│
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.connector
    └── nginx.conf
```
