# 🛠️ Arquitetura do App Admin

> **Versao:** 1.0.0 | **Data:** 2026-05-26 | **Status:** Em Progresso (~30%)

---

## 1. Visao Geral

O App Admin e o painel de controle da plataforma Flora. Usado pelo **dono da plataforma** ou **equipe de suporte** para gerenciar clientes, licencas, bots e visualizar metricas.

```
┌─────────────────────────────────────────────┐
│              APP ADMIN                       │
│                                              │
│  ┌──────────────┐   ┌────────────────────┐  │
│  │   KivyMD     │   │   Kivy Core        │  │
│  │   Screens    │   │   (Events, Clock,  │  │
│  │   Widgets    │   │    Properties)     │  │
│  └──────┬───────┘   └────────┬───────────┘  │
│         │                    │               │
│  ┌──────┴────────────────────┴───────────┐  │
│  │            Services Layer              │  │
│  │  (API calls, Analytics, Licenses)      │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│  ┌──────────────────┴────────────────────┐  │
│  │          Local Storage                │  │
│  │  (JSON config, Auth token, Cache)     │  │
│  └───────────────────────────────────────┘  │
└──────────────────────────┬───────────────────┘
                           │
                    HTTP / HTTPS
                           │
                   ┌───────┴───────┐
                   │  BACKEND API  │
                   │  (FastAPI)    │
                   └───────────────┘
```

---

## 2. Estrutura de Pastas

```
app_admin/
├── main.py                     # App KivyMD entry point (admin version)
├── assets/
│   ├── images/                 # Icones, logos, backgrounds
│   └── fonts/                  # Fontes customizadas
├── screens/
│   ├── admin_login.py          # Login admin (diferente do cliente)
│   ├── admin_dashboard.py     # Dashboard com metricas gerais
│   ├── client_list.py          # Lista de clientes
│   ├── client_detail.py        # Detalhes de um cliente
│   ├── license_management.py   # CRUD de licencas
│   ├── license_generator.py    # Gerar nova licenca
│   ├── plan_management.py      # CRUD de planos
│   ├── plan_editor.py          # Editor de plano
│   ├── bot_templates.py        # Templates de bots
│   ├── bot_editor.py           # Editor de bot (wizard 8 etaps)
│   ├── analytics_dashboard.py # Analytics avancados
│   ├── llm_usage.py            # Uso de LLM por cliente
│   ├── user_management.py      # CRUD de usuarios
│   ├── audit_logs.py           # Logs de auditoria
│   ├── settings_admin.py       # Configuracoes da plataforma
│   ├── backup_restore.py       # Backup e restore
│   └── sandbox.py              # Sandbox de teste de bot
├── components/
│   ├── nav_drawer.py           # Menu de navegacao lateral
│   ├── charts.py               # Graficos (matplotlib)
│   ├── data_tables.py          # Tabelas de dados
│   └── edit_forms.py           # Formularios de edicao
├── services/
│   ├── api_service.py          # Client HTTP para o backend (admin endpoints)
│   ├── analytics_service.py    # Agregacao de metricas
│   └── export_service.py       # Export CSV/PDF
└── utils/
    ├── constants.py
    ├── helpers.py
    └── validators.py
```

---

## 3. Telas (15+ Telas)

| # | Tela | Arquivo | Status |
|---|------|---------|--------|
| 1 | **Login Admin** | `admin_login.py` | ✅ |
| 2 | **Dashboard** | `admin_dashboard.py` | 🔄 |
| 3 | **Lista de Clientes** | `client_list.py` | 🔄 |
| 4 | **Detalhe do Cliente** | `client_detail.py` | 🔄 |
| 5 | **Gestao de Licencas** | `license_management.py` | 🔄 |
| 6 | **Gerador de Licenca** | `license_generator.py` | 🔄 |
| 7 | **Gestao de Planos** | `plan_management.py` | 📋 |
| 8 | **Editor de Plano** | `plan_editor.py` | 📋 |
| 9 | **Templates de Bots** | `bot_templates.py` | 📋 |
| 10 | **Editor de Bot (Wizard)** | `bot_editor.py` | 📋 |
| 11 | **Analytics** | `analytics_dashboard.py` | 📋 |
| 12 | **Uso de LLM** | `llm_usage.py` | 📋 |
| 13 | **Gestao de Usuarios** | `user_management.py` | 📋 |
| 14 | **Logs de Auditoria** | `audit_logs.py` | 📋 |
| 15 | **Configuracoes** | `settings_admin.py` | 📋 |
| 16 | **Backup/Restore** | `backup_restore.py` | 📋 |
| 17 | **Sandbox** | `sandbox.py` | 📋 |

---

## 4. Fluxo Principal

```
┌────────────┐    ┌─────────────┐
│ Admin Login│───>│  Dashboard  │
└────────────┘    └──────┬──────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌──────────┐  ┌──────────────────┐  ┌──────────────┐
│ Clientes │  │  Licencas        │  │  Analytics   │
│          │  │  (CRUD, gera,    │  │  (metricas,  │
│ Lista    │  │   valida, revoga)│  │   graficos,  │
│ Detalhe  │  │                  │  │   relatorios)│
└──────────┘  └──────────────────┘  └──────────────┘
    │                    │                    │
    ▼                    ▼                    ▼
┌──────────┐  ┌──────────────────┐  ┌──────────────┐
│ Planos   │  │  Bots            │  │  Auditoria   │
│ (CRUD)   │  │  (templates,     │  │              │
│          │  │   wizard editor) │  │  Logs        │
└──────────┘  └──────────────────┘  │  Backups     │
                                     └──────────────┘
```

---

## 5. Tema Visual

O App Admin compartilha a mesma paleta dark do App Cliente, mas com variacoes sutis para diferenciar os contextos:

```python
# Cores do Admin (levemente diferentes)
ADMIN_PRIMARY = "#7C4DFF"        # Roxo para diferenciar
ADMIN_PRIMARY_DARK = "#651FFF"
ADMIN_SURFACE = "#1A1A2E"        # Superficie mais azulada
ADMIN_CARD = "#252540"
ADMIN_NAV_BG = "#0F0F1A"         # Nav escuro

# Mesmo accent e status colors
ACCENT = "#00BCD4"
SUCCESS = "#4CAF50"
WARNING = "#FFC107"
ERROR = "#F44336"
```

---

## 6. Dashboard do Admin

O dashboard apresenta metricas-chave em cards:

```
┌─────────────────────────────────────────────────┐
│  FLORA ADMIN DASHBOARD                          │
│                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │  152   │ │  43    │ │  8.5k  │ │ R$12k  │   │
│  │Clientes│ │  Bots  │ │Mensag. │ │Receita │   │
│  │Ativos  │ │Ativos  │ │  Hoje  │ │ Mensal │   │
│  └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                  │
│  ┌────────────────────┐ ┌────────────────────┐  │
│  │  Grafico Mensagens │ │  Grafico Receita   │  │
│  │  (ultimos 7 dias)  │ │  (ultimos 12 mes)  │  │
│  │                    │ │                    │  │
│  │    /\    /\        │ │    ████████        │  │
│  │   /  \  /  \  /\   │ │    ██████████      │  │
│  │  /    \/    \/  \  │ │    ████████████    │  │
│  └────────────────────┘ └────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Atividade Recente                        │  │
│  │  • Cliente X conectou WhatsApp (2min)     │  │
│  │  • Nova licenca gerada para Y (15min)     │  │
│  │  • Bot Z atingiu limite LLM (1h)          │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 7. Editor de Bot (Wizard 8 Etapas)

O editor de bot e um wizard multi-etapas:

| Etapa | Nome | Descricao |
|-------|------|-----------|
| 1 | **Identidade** | Nome, avatar, descricao do bot |
| 2 | **Personalidade** | Tom (friendly, professional, casual, funny) |
| 3 | **Comportamento** | Regras de resposta, limites, fallback |
| 4 | **Perguntas** | FAQ / perguntas frequentes |
| 5 | **Comandos** | Comandos personalizados (/ajuda, /info) |
| 6 | **Intencoes** | Training phrases para cada intencao |
| 7 | **Integracoes** | WhatsApp, webhooks, APIs externas |
| 8 | **Revisao** | Preview, testar, publicar |

---

## 8. Gestao de Licencas

```python
# screens/license_generator.py
class LicenseGeneratorScreen(MDScreen):
    def generate_license(self):
        # 1. Selecionar cliente
        client_id = self.ids.client_spinner.text
        # 2. Selecionar plano
        plan_id = self.ids.plan_spinner.text
        # 3. Duracao
        duration = self.ids.duration_slider.value  # meses
        # 4. Gerar via API
        result = await api_service.generate_license(
            client_id=client_id,
            plan_id=plan_id,
            duration_months=duration
        )
        # 5. Exibir chave de licenca
        self.ids.license_key.text = result["license_key"]
        # 6. Opcao de exportar arquivo .floralicense
        self.export_license_file(result)
```

**Operacoes de licenca:**
- Criar nova licenca
- Validar licenca existente
- Revogar licenca
- Renovar licenca
- Transferir licenca (trocar maquina)
- Ver historico de uso

---

## 9. Analytics Avancados

```python
# screens/analytics_dashboard.py
class AnalyticsDashboardScreen(MDScreen):
    def on_enter(self):
        self.load_metrics()

    async def load_metrics(self):
        # Metricas gerais
        metrics = await api_service.get_admin_analytics()
        self.ids.total_clients.text = str(metrics["total_clients"])
        self.ids.active_bots.text = str(metrics["active_bots"])
        self.ids.total_messages.text = str(metrics["total_messages"])
        self.ids.monthly_revenue.text = f"R$ {metrics['monthly_revenue']:.2f}"

        # Graficos
        self.render_message_chart(metrics["messages_by_day"])
        self.render_revenue_chart(metrics["revenue_by_month"])
        self.render_plan_distribution(metrics["clients_by_plan"])
        self.render_llm_usage_chart(metrics["llm_usage_by_provider"])
```

---

## 10. Sandbox de Teste

Permite testar um bot antes de publicar:

```python
# screens/sandbox.py
class SandboxScreen(MDScreen):
    def send_test_message(self, text: str):
        # Enviar mensagem para o bot em modo sandbox
        response = await api_service.sandbox_chat(
            bot_id=self.bot_id,
            message=text
        )
        # Mostrar resposta + debug info
        self.add_message(text, is_user=True)
        self.add_message(response["response"], is_user=False)
        self.show_debug_info({
            "intent": response["intent"],
            "confidence": response["confidence"],
            "llm_used": response.get("llm_used", "rules"),
            "response_time_ms": response["response_time_ms"]
        })
```

---

## 11. Desenvolvimento

### Execucao

```bash
cd app_admin

# Executar app
python main.py

# Com debug
FLORA_DEBUG=true python main.py
```

### Build

```bash
# Windows
pyinstaller --name "Flora Admin" --onefile --windowed \
    --icon assets/images/admin_icon.png main.py
```

---

## 12. Diferencas para o App Cliente

| Aspecto | App Admin | App Cliente |
|---------|-----------|-------------|
| **Publico** | Dono da plataforma | Cliente final |
| **Cor primaria** | Roxo (#7C4DFF) | Rosa (#E91E63) |
| **Login** | Admin (role=admin) | Cliente (role=user) |
| **Escopo** | Toda a plataforma | Apenas seu bot |
| **Analytics** | Globais (todos clientes) | Individuais (so seu bot) |
| **Licencas** | Cria/Revoga/Valida | Apenas valida a sua |
| **Bots** | Templates + Editor | Configuracao do proprio |
| **Telas** | 15+ | 13 |
