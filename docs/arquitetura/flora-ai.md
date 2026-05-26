# 🌸 Flora AI — Sistema de IA

> **Versao:** 1.0.0 | **Data:** 2026-05-26 | **Status:** Implementado (~70%)

---

## 1. Visao Geral

Flora AI e a assistente inteligente embutida na plataforma Flora. Ela ajuda o cliente a configurar, entender e aproveitar a plataforma — reduzindo churn e necessidade de suporte.

```
┌─────────────────────────────────────────────────┐
│                  FLORA AI                        │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │          System Prompt                      │ │
│  │  "Voce e Flora, assistente da plataforma    │ │
│    │   Flora. Voce ajuda clientes a...        │ │
│  │    Tom: simpatica, profissional, direta"   │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────────┐    │
│  │ Context │  │ Intent  │  │   LLM        │    │
│  │Injector │  │Detector │  │   Router     │    │
│  │         │  │         │  │              │    │
│  │ Plano   │  │ help    │  │ Groq (free)  │    │
│  │ Licenca │  │ config  │  │ Gemini (free)│    │
│  │ Bot     │  │ bot     │  │ OpenAI ($)   │    │
│  │ Uso     │  │ plano   │  │ Claude ($)   │    │
│  └─────────┘  └─────────┘  └──────────────┘    │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │          FloraSession (Historia)            │ │
│  │  → Mantem contexto da conversa              │ │
│  │  → Max 50 mensagens por sessao              │ │
│  │  → Reset apos 30min de inatividade          │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 2. Funcionalidades da Flora

| Funcao | Descricao | Status |
|--------|-----------|--------|
| **Chat** | Conversar em linguagem natural sobre a plataforma | ✅ |
| **Onboarding** | Guiar novos clientes passo a passo | ✅ |
| **Ajuda** | Explicar features, planos, configuracoes | ✅ |
| **Sugestoes** | Sugerir proximas acoes baseadas no contexto | ✅ |
| **Config Ajuda** | Ajudar a configurar o bot step-by-step | 📋 |
| **Analytics** | Explicar metricas em linguagem simples | 📋 |
| **Troubleshooting** | Diagnosticar problemas comuns | 📋 |

---

## 3. Endpoints da API

### 3.1 Chat Principal

```
POST /api/v1/flora/chat
```

**Request:**
```json
{
  "message": "Como eu conecto meu WhatsApp?",
  "session_id": "uuid-da-sessao-opcional"
}
```

**Response:**
```json
{
  "response": "Para conectar seu WhatsApp, va na tela 'Conexao' e clique em 'Escanear QR Code'. Abra o WhatsApp no seu celular, va em 'Dispositivos Conectados' e escaneie o codigo exibido. :)",
  "session_id": "uuid-da-sessao",
  "intent": "whatsapp_connect",
  "confidence": 0.95,
  "tools_used": [],
  "is_new_session": false,
  "message_count": 5,
  "timestamp": "2026-05-26T15:30:00Z"
}
```

### 3.2 Listar Sessoes

```
GET /api/v1/flora/sessions
```

### 3.3 Historico

```
GET /api/v1/flora/history/{session_id}
```

### 3.4 Limpar Sessao

```
DELETE /api/v1/flora/session/{session_id}
```

### 3.5 Onboarding

```
GET /api/v1/flora/onboarding
```

```json
{
  "steps": [
    {
      "id": "welcome",
      "title": "Bem-vindo!",
      "description": "Vamos configurar seu bot em 5 minutos",
      "icon": "hand-wave",
      "action": null
    },
    {
      "id": "license",
      "title": "Validar Licenca",
      "description": "Insira sua chave de licenca",
      "icon": "key",
      "action": "license_validation"
    },
    {
      "id": "bot_name",
      "title": "Nome do Bot",
      "description": "Como voce quer chamar seu bot?",
      "icon": "robot",
      "action": "bot_config"
    },
    {
      "id": "whatsapp",
      "title": "Conectar WhatsApp",
      "description": "Escaneie o QR Code",
      "icon": "qrcode",
      "action": "whatsapp_connect"
    },
    {
      "id": "test",
      "title": "Testar",
      "description": "Envie uma mensagem de teste",
      "icon": "message",
      "action": "chat_test"
    }
  ]
}
```

### 3.6 Ajuda por Topico

```
POST /api/v1/flora/help
```

```json
{
  "topic": "whatsapp",
  "question": "Como funciona o QR Code?"
}
```

### 3.7 Sugestoes

```
GET /api/v1/flora/suggestions
```

```json
{
  "suggestions": [
    "Como mudar a personalidade do bot?",
    "Como ver mensagens recebidas?",
    "Como fazer upgrade do plano?"
  ]
}
```

---

## 4. Servico Flora (`services/flora_service.py`)

```python
class FloraService:
    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        # 1. Obter ou criar sessao
        session = await self._get_or_create_session(db, user_id, session_id)

        # 2. Detectar intencao
        intent = await self._detect_intent(message)

        # 3. Injetar contexto
        context = await self._inject_context(db, user_id, intent)

        # 4. Construir prompt
        system_prompt = self._build_system_prompt(context, intent)

        # 5. Chamar LLM Router
        response = await self.llm_router.chat(
            system_prompt=system_prompt,
            user_message=message,
            history=session.get_recent_messages(limit=10),
        )

        # 6. Salvar mensagens
        await self._save_message(db, session.id, "user", message)
        await self._save_message(db, session.id, "assistant", response)

        return {
            "response": response,
            "session_id": session.id,
            "intent": intent.name,
            "confidence": intent.confidence,
        }

    def _build_system_prompt(self, context: dict, intent: Intent) -> str:
        return f"""Voce e Flora, assistente da plataforma Flora.
Ajuda clientes a configurar e usar chatbots WhatsApp.

CONTEXTO DO USUARIO:
- Plano: {context['plan_name']}
- Licenca: {"Ativa" if context['license_active'] else "Expirada"}
- Bot: {context.get('bot_name', "Nao configurado")}
- WhatsApp: {"Conectado" if context['whatsapp_connected'] else "Desconectado"}

REGRAS:
1. Seja simpatica, profissao e direta
2. Responda em portugues brasileiro
3. Use emojis com moderacao
4. Se nao sabe, diga honestamente
5. Sugira proximos passos quando possivel
6. Max 3 paragrafos por resposta
"""
```

---

## 5. Intencoes Detectadas

| Intencao | Descricao | Exemplo |
|----------|-----------|---------|
| `help_geral` | Ajuda geral sobre a plataforma | "Como funciona?" |
| `whatsapp_connect` | Conectar WhatsApp | "Como conecto o WhatsApp?" |
| `whatsapp_problem` | Problemas com WhatsApp | "QR Code nao aparece" |
| `bot_config` | Configurar bot | "Como mudo a personalidade?" |
| `bot_personality` | Personalidade do bot | "Bot esta muito formal" |
| `plan_info` | Informacoes sobre plano | "O que inclui o plano Pro?" |
| `plan_upgrade` | Upgrade de plano | "Quero fazer upgrade" |
| `license_issue` | Problemas com licenca | "Licenca expirou" |
| `payment` | Pagamento e cobranca | "Quando vence minha assinatura?" |
| `analytics` | Metricas e relatorios | "Quantas mensagens enviei?" |
| `greeting` | Saudacao | "Ola!" |
| `farewell` | Despedida | "Tchau, obrigado!" |
| `feature_request` | Pedido de funcao | "Podiam adicionar..." |
| `bug_report` | Report de bug | "Encontrei um erro" |

---

## 6. LLM Router

### 6.1 Selecao por Plano

| Plano | Provider Prioritario | Fallback |
|-------|---------------------|----------|
| Starter, Basic, Plus | Regras (sem LLM) | — |
| Pro | Groq (llama 70b) | Regras |
| Master | Groq | Gemini | OpenAI |
| Elite | OpenAI (gpt-4o) | Groq | Claude |
| Enterprise | Configuravel | Todos |
| Free/Trial | Groq (rate limitado) | — |

### 6.2 Fallback em Cadeia

```
1. Tenta Groq (gratis, rapido)
   → Se falha:
2. Tenta Gemini (gratis, medio)
   → Se falha:
3. Tenta OpenAI (pago, lento)
   → Se falha:
4. Usa respostas pre-definidas (regras)
```

### 6.3 Estimativa de Custos

| Provider | Modelo | Custo/1M tokens | Limite gratuito |
|----------|--------|-----------------|-----------------|
| Groq | llama-3.1-70b | $0.00 | Sim (rate limit) |
| Gemini | 1.5-flash | $0.00 | Sim (15req/min) |
| OpenAI | gpt-4o-mini | $0.15 in / $0.60 out | Nao |
| OpenAI | gpt-4o | $2.50 in / $10.00 out | Nao |
| Claude | 3-haiku | $0.25 in / $1.25 out | Nao |

---

## 7. Sessao Flora

```python
class FloraSession(Base):
    __tablename__ = "flora_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    relationship("FloraMessage", back_populates="session")
```

**Limpeza automatica:**
- Sessoes inativas por 30 dias sao marcadas como inativas
- Mensagens com mais de 90 dias sao arquivadas
- Max 50 mensagens por sessao em memoria

---

## 8. Analytics de Uso da Flora

```
GET /api/v1/analytics/flora
```

```json
{
  "total_sessions": 1523,
  "total_messages": 8456,
  "avg_messages_per_session": 5.5,
  "intents_distribution": {
    "help_geral": 35,
    "whatsapp_connect": 22,
    "bot_config": 18,
    "plan_upgrade": 12,
    "other": 13
  },
  "llm_usage": {
    "groq": 6500,
    "gemini": 1200,
    "openai": 756
  },
  "avg_response_time_ms": 1200,
  "satisfaction_rate": 0.89
}
```

---

## 9. Futuro da Flora AI

| Ideia | Descricao | Prioridade |
|-------|-----------|------------|
| **Proactive Help** | Antecipar problemas antes que o cliente perceba | Alta |
| **A/B Testing** | Testar diferentes responses para otimizar | Media |
| **Multi-language** | Suporte a espanhol e ingles | Media |
| **Training Monitor** | Sugerir training phrases baseado em perguntas reais | Alta |
| **Voice Input** | Aceitar mensagens de voz | Baixa |
| **Screen Sharing** | Identificar onde o cliente esta travado | Baixa |
| **Bot Personality Generator** | Gerar personalidade automaticamente | Baixa |
