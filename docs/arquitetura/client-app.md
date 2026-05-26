# 📱 Arquitetura do App Cliente

> **Versao:** 1.0.0 | **Data:** 2026-05-26 | **Status:** Em Progresso (~40%)

---

## 1. Visao Geral

O App Cliente e um aplicativo desktop construido com **KivyMD** (Material Design para Kivy). E o app usado pelo **cliente final** — a pessoa que comprou uma licenca e quer configurar seu bot de WhatsApp.

```
┌─────────────────────────────────────────────┐
│              APP CLIENTE                     │
│                                              │
│  ┌──────────────┐   ┌────────────────────┐  │
│  │   KivyMD     │   │   Kivy Core        │  │
│  │   Screens    │   │   (Events, Clock,  │  │
│  │   Widgets    │   │    Properties)     │  │
│  └──────┬───────┘   └────────┬───────────┘  │
│         │                    │               │
│  ┌──────┴────────────────────┴───────────┐  │
│  │            Services Layer              │  │
│  │  (API calls, License, WhatsApp)        │  │
│  └──────────────────┬────────────────────┘  │
│                     │                        │
│  ┌──────────────────┴────────────────────┐  │
│  │          Local Storage                │  │
│  │  (JSON config, License file, Cache)   │  │
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
app_cliente/
├── main.py                     # App KivyMD entry point
├── assets/
│   ├── images/                 # Icones, logos, backgrounds
│   └── fonts/                  # Fontes customizadas
├── screens/
│   ├── splash_screen.py        # Splash com logo Flora
│   ├── onboarding.py           # 3 slides de introducao
│   ├── login.py                # Login com email/senha
│   ├── license_validation.py   # Validacao de licenca
│   ├── dashboard.py            # Dashboard principal
│   ├── bot_config.py           # Configuracao do bot
│   ├── bot_editor.py           # Editor de regras/perguntas
│   ├── bot_personality.py      # Personalidade do bot
│   ├── whatsapp_connect.py     # Conexao QR Code
│   ├── chat_test.py            # Chat de teste com o bot
│   ├── flora_ai.py             # Tela da Flora AI
│   ├── plan_details.py         # Detalhes do plano
│   ├── help.py                 # Ajuda / FAQ
│   └── settings.py             # Configuracoes do app
├── components/
│   ├── custom_widgets.py       # Widgets reutilizaveis
│   ├── bot_preview.py          # Preview do bot em tempo real
│   └── charts.py               # Graficos simples
├── services/
│   ├── api_service.py          # Client HTTP para o backend
│   ├── license_service.py      # Validacao local de licenca
│   ├── whatsapp_service.py     # Comunicacao com WhatsApp local
│   └── storage_service.py      # Persistencia local (JSON)
└── utils/
    ├── constants.py            # Constantes do app
    ├── helpers.py              # Funcoes auxiliares
    └── validators.py           # Validadores de input
```

---

## 3. Telas (13 Telas)

| # | Tela | Arquivo | Status |
|---|------|---------|--------|
| 1 | **Splash** | `splash_screen.py` | ✅ |
| 2 | **Onboarding** (3 slides) | `onboarding.py` | ✅ |
| 3 | **Login** | `login.py` | ✅ |
| 4 | **Validacao de Licenca** | `license_validation.py` | ✅ |
| 5 | **Dashboard** | `dashboard.py` | 🔄 |
| 6 | **Configuracao do Bot** | `bot_config.py` | 🔄 |
| 7 | **Editor de Perguntas** | `bot_editor.py` | 🔄 |
| 8 | **Personalidade do Bot** | `bot_personality.py` | 🔄 |
| 9 | **Conexao WhatsApp** | `whatsapp_connect.py` | 🔄 |
| 10 | **Chat de Teste** | `chat_test.py` | 🔄 |
| 11 | **Flora AI** | `flora_ai.py` | 🔄 |
| 12 | **Plano** | `plan_details.py` | 📋 |
| 13 | **Configuracoes** | `settings.py` | 📋 |

---

## 4. Fluxo Principal

```
┌───────┐    ┌────────────┐    ┌──────┐    ┌────────────┐
│ Splash│───>│ Onboarding │───>│ Login│───>│  Validacao │
│       │    │  (3 slides)│    │      │    │  Licenca   │
└───────┘    └────────────┘    └──────┘    └─────┬──────┘
                                                  │
                    ┌─────────────────────────────┘
                    ▼
              ┌──────────┐
              │Dashboard │<──────────────────────┐
              └────┬─────┘                       │
                   │                              │
    ┌──────────────┼──────────────┬───────────┐  │
    ▼              ▼              ▼           ▼  │
┌────────┐  ┌───────────┐  ┌──────────┐  ┌─────┴──────┐
│  Bot   │  │ WhatsApp  │  │  Flora   │  │   Plano    │
│ Config │  │  Connect  │  │    AI    │  │  Details   │
└────────┘  └───────────┘  └──────────┘  └────────────┘
```

---

## 5. Tema Visual

O app usa **dark premium UI** com a paleta Flora:

```python
# Cores principais
PRIMARY = "#E91E63"          # Rosa principal
PRIMARY_DARK = "#AD1457"     # Rosa escuro
ACCENT = "#00BCD4"           # Cyan accent
BACKGROUND = "#121212"       # Fundo escuro
SURFACE = "#1E1E2E"          # Superficie
CARD = "#2A2A3A"             # Cards
TEXT_PRIMARY = "#FFFFFF"     # Texto principal
TEXT_SECONDARY = "#B0BEC5"   # Texto secundario
SUCCESS = "#4CAF50"          # Verde
WARNING = "#FFC107"          # Amarelo
ERROR = "#F44336"            # Vermelho
```

**Fontes:**
- Titulos: **Roboto Bold**
- Corpo: **Roboto Regular**
- Destaques: **Roboto Light**

**Componentes KivyMD Usados:**
- `MDTopAppBar` — Barra superior
- `MDNavigationDrawer` — Menu lateral
- `MDCard` — Cards elevados
- `MDTextField` — Campos de texto
- `MDRaisedButton` — Botoes
- `MDSwitch` — Toggles
- `MDChip` — Tags
- `MDProgressBar` — Barra de progresso
- `MDDialog` — Dialogos
- `MDTabs` — Abas

---

## 6. Comunicacao com o Backend

```python
# services/api_service.py
import httpx

class APIService:
    BASE_URL = "http://localhost:8000/api/v1"

    async def login(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            data = response.json()
            self.token = data["access_token"]
            return data

    async def get_bots(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/bots",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            return response.json()["bots"]
```

---

## 7. Validacao de Licenca (Local)

```python
# services/license_service.py
import json
from pathlib import Path

LICENSE_FILE = Path.home() / ".flora" / "license.json"

class LicenseService:
    @staticmethod
    def save_license(license_data: dict):
        LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LICENSE_FILE, "w") as f:
            json.dump(license_data, f)

    @staticmethod
    def load_license() -> dict | None:
        if LICENSE_FILE.exists():
            with open(LICENSE_FILE) as f:
                return json.load(f)
        return None

    @staticmethod
    def is_valid() -> bool:
        lic = LicenseService.load_license()
        if not lic:
            return False
        # Verificar expiracao localmente
        from datetime import datetime
        expiry = datetime.fromisoformat(lic["expires_at"])
        return datetime.now() < expiry
```

---

## 8. Conexao WhatsApp

A tela de conexao WhatsApp exibe o QR Code e monitora o status:

```python
# screens/whatsapp_connect.py
class WhatsAppConnectScreen(MDScreen):
    def on_enter(self):
        self.start_qr_check()

    async def start_qr_check(self):
        # 1. Solicitar QR Code do backend
        qr_data = await api_service.get_whatsapp_qr()
        # 2. Exibir QR Code na tela
        self.ids.qr_image.source = generate_qr_image(qr_data)
        # 3. Polling de status a cada 2 segundos
        while not self.connected:
            status = await api_service.get_whatsapp_status()
            if status["state"] == "CONNECTED":
                self.connected = True
                self.show_success()
            await asyncio.sleep(2)
```

---

## 9. Flora AI no App Cliente

A Flora AI e integrada diretamente na tela dedicada:

```python
# screens/flora_ai.py
class FloraAIScreen(MDScreen):
    def send_message(self, text: str):
        # Adicionar mensagem do usuario ao chat
        self.add_chat_bubble(text, is_user=True)
        # Enviar para o backend
        response = await api_service.flora_chat(text)
        # Exibir resposta da Flora
        self.add_chat_bubble(response["response"], is_user=False)
```

---

## 10. Telas em Detalhe

### Tela: Dashboard
Visao geral do bot conectado:
- Status da conexao WhatApp (conectado/desconctado)
- Mensagens enviadas/recebidas (hoje, semana)
- Grafico de uso de LLM
- Acoes rapidas (Testar bot, Conectar WhatsApp, Ver plano)

### Tela: Configuracao do Bot
- Nome do bot
- Personalidade (friendly, professional, casual, funny)
- Mensagem de boas-vindas
- Resposta padrao quando nao sabe
- Custom commands
- Training phrases (intencoes)

### Tela: Conexao WhatsApp
- QR Code grande e visivel
- Status da conexao com indicador visual
- Botao para desconectar
- Informacoes da sessao (numero, nome)

### Tela: Chat de Teste
- Interface de chat real com o bot
- Mostra nome e avatar do bot
- Envia mensagem e recebe resposta em tempo real
- Mostra fallback when bot nao sabe responder

---

## 11. Desenvolvimento

### Execucao

```bash
cd app_cliente

# Executar app
python main.py

# Com debug
FLORA_DEBUG=true python main.py
```

### Build (gerar executavel)

```bash
# Usando PyInstaller
pip install pyinstaller

# Windows
pyinstaller --name "Flora Cliente" --onefile --windowed \
    --icon assets/images/icon.png main.py

# Mac
pyinstaller --name "Flora Cliente" --onefile --windowed \
    --icon assets/images/icon.icns main.py
```

---

## 12. Problemas Conhecidos

| Problema | Status |
|----------|--------|
| KivyMD 1.2 incompativel com Kivy 2.3 em alguns widgets | 🔍 Investigando |
| QR Code renderizacao lenta em CPUs fracas | 📋 Planejado: otimizacao |
| Sessao WhatsApp cai apos hibernacao do SO | 📋 Planejado: auto-reconnect |
| High DPI scaling no Windows | 🔄 WIP |
