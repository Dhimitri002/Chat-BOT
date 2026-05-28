# 🌸 FLORA PLATFORM — Flora AI

> A assistente virtual inteligente que vive dentro do app cliente.

---

## 🌺 O Que É a Flora AI

A **Flora AI** é uma assistente virtual integrada ao app cliente da Flora Platform. Ela não é um bot para o WhatsApp do cliente — ela é uma ajuda **dentro do app** para o próprio usuário da plataforma.

### Missão

> **"Ajudar cada cliente a ter sucesso com sua Flora, reduzindo churn e suporte humano."**

### Personalidade

| Traço | Descrição |
|---|---|
| **Nome** | Flora |
| **Tom** | Amigável, prestativa, profissional |
| **Estilo** | Clara, direta, educada |
| **Idioma** | Português (Brasileiro) |
| **Emoji** | 🌸 (usa com moderação) |

### O Que a Flora FAZ

| Função | Descrição |
|---|---|
| **Onboarding** | Guia o usuário na primeira configuração do bot |
| **Tutorial** | Explica cada funcionalidade do app |
| **Resolução de Problemas** | Diagnostica e resolve erros comuns |
| **Dicas** | Sugere melhorias para o bot do cliente |
| **Suporte** | Responde dúvidas sobre a plataforma |
| **Redução de Churn** | Identifica sinais de frustração e age |

### O Que a Flora NÃO Faz

- ❌ Não acessa dados de outros clientes
- ❌ Não envia mensagens no WhatsApp do cliente
- ❌ Não faz cobranças ou alterações de plano
- ❌ Não substitui suporte humano para problemas complexos

---

## 🏗️ Arquitetura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  App Cliente │     │   Flora AI   │     │  LLM Router  │
│  (KivyMD)    │     │   Backend    │     │              │
│              │     │              │     │  ┌────────┐  │
│  Usuário     │     │  System      │     │  │ Groq   │  │
│  digita  ────┼────▶│  Prompt  ────┼────▶│  ├────────┤  │
│  mensagem    │     │  + Context   │     │  │ Gemini │  │
│              │     │  + Memória   │     │  ├────────┤  │
│              │     │              │     │  │ OpenAI │  │
│  Usuário ◄───┼─────│  Resposta ◄──┼─────│  ├────────┤  │
│  vê resposta │     │  formatada   │     │  │Anthropic│ │
└──────────────┘     └──────────────┘     │  └────────┘  │
                                          └──────────────┘
```

---

## 📝 System Prompt

O system prompt da Flora é cuidadosamente engenheirado:

```text
Você é Flora, assistente virtual da Flora Platform.
Sua missão é ajudar clientes a configurar e gerenciar seus chatbots.

REGRAS:
- Seja amigável, prestativa e profissional
- Use português brasileiro
- Seja clara e direta, evite textos longos
- Use emojis com moderação (🌸 ocasionalmente)
- Não invente funcionalidades que não existem
- Se não souber algo, sugira abrir um ticket de suporte

CONTEXTO DO USUÁRIO:
- Nome: {user_name}
- Plano: {plan_name}
- Status do bot: {bot_status}
- Plano expira em: {expires_at}
- Nível de experiência: {experience_level}

CAPACIDADES:
- Explicar como configurar o bot
- Ajudar com comandos e intenções
- Diagnosticar problemas de conexão WhatsApp
- Sugerir melhorias no prompt do bot
- Explicar funcionalidades do app
- Calcular uso de mensagens e limites

LIMITAÇÕES:
- Não acessa dados de outros clientes
- Não envia mensagens no WhatsApp
- Não faz alterações de plano
- Não processa pagamentos

FLUXO DE CONVERSA:
1. Cumprimente (apenas na primeira mensagem)
2. Entenda o problema/duvida
3. Forneça solução passo a passo
4. Confirme se resolveu
5. Ofereça ajuda adicional
```

---

## 💬 Sessões de Chat

### Modelo de Dados

```python
class FloraSession(Base):
    """Sessão de chat com a Flora AI"""
    id: UUID
    user_id: UUID          # FK -> User
    messages: JSON         # [{role, content, timestamp}]
    context: JSON          # {plan, bot_status, ...}
    started_at: datetime
    last_activity: datetime
    is_active: bool
```

### Formato das Mensagens

```json
{
    "role": "user",
    "content": "Como eu conecto meu WhatsApp?",
    "timestamp": "2025-06-21T10:30:00Z"
},
{
    "role": "assistant",
    "content": "Para conectar seu WhatsApp, siga estes passos:\n\n1. Abra a tela de Configurações\n2. Toque em 'Conectar WhatsApp'\n3. Escaneie o QR Code com seu celular\n\nO código vale por 30 segundos. Se expirar, toque em 'Gerar novo'. 🌸",
    "timestamp": "2025-06-21T10:30:02Z"
}
```

### Limites de Contexto

| Plano | Mensagens por sessão | Histórico | TTL |
|---|---|---|---|
| Free | 5 | 0 (sem memória) | 1 hora |
| Starter | 10 | últimas 5 | 6 horas |
| Basic | 25 | últimas 10 | 24 horas |
| Pro | 50 | últimas 20 | 7 dias |
| Business | 100 | últimas 50 | 30 dias |
| Premium | Ilimitado | Completo | 90 dias |
| Enterprise | Ilimitado | Completo | 1 ano |

---

## 🧠 Memória Contextual

A Flora mantém memória contextual para oferecer ajuda personalizada:

```python
# Exemplo de memória
{
    "user_preferences": {
        "language": "pt-BR",
        "tutorial_completed": True,
        "onboarding_step": "setup_bot"
    },
    "bot_info": {
        "name": "Flora Bot",
        "personality": "profissional",
        "language": "pt-BR",
        "commands_count": 5,
        "intents_count": 12,
        "whatsapp_connected": True
    },
    "usage_stats": {
        "messages_this_month": 450,
        "messages_limit": 1000,
        "llm_tokens_used": 125000
    },
    "recent_issues": [
        "whatsapp_disconnected_2025-06-15",
        "high_response_time_2025-06-18"
    ]
}
```

---

## 🎯 Casos de Uso

### 1. Onboarding

```
Usuário: "Acabei de criar minha conta, por onde começo?"

Flora: "Bem-vindo! 🌸 Vou te guiar na configuração do seu primeiro bot:

1️⃣ Defina o nome do seu bot (ex: 'Atendimento Flora')
2️⃣ Escolha uma personalidade (amigável, profissional, etc.)
3️⃣ Configure o prompt inicial
4️⃣ Conecte seu WhatsApp escaneando o QR Code

Vamos começar pelo nome. Como você quer chamar seu bot?"
```

### 2. Resolução de Problemas

```
Usuário: "Meu bot não está respondendo no WhatsApp"

Flora: "Vamos diagnosticar! Verifique:

✅ O WhatsApp está conectado? (tela Status)
✅ O bot está ativo? (tela Bots → seu bot)
✅ Há mensagens disponíveis no seu plano?

Se tudo estiver OK, tente:
1. Desconectar o WhatsApp
2. Reconectar escaneando o QR Code novamente

Isso resolve em 90% dos casos. Funcionou?"
```

### 3. Dicas de Melhoria

```
Usuário: "Como faço meu bot ser mais natural?"

Flora: "Ótima pergunta! Aqui vão algumas dicas:

💡 Adicione variações nas respostas do mesmo intent
💡 Configure uma personalidade rica no prompt
💡 Use comandos para fluxos específicos
💡 Analise as mensagens recebidas e ajuste intenções

Quer que eu sugira um prompt personalizado para o seu caso?
Me diga o tipo de negócio que seu bot atende."
```

### 4. Explicação de Funcionalidades

```
Usuário: "O que são intenções?"

Flora: "Intenções são formas de ensinar seu bot a entender o cliente.

Por exemplo:
👤 Cliente: 'Qual o horário de funcionamento?'
🎯 Intencao: consultar_horario
🤖 Bot: 'Funcionamos de seg a sex, 9h às 18h!'

É mais poderoso que comandos simples porque entende
variações da mesma pergunta. Quer configurar uma?"
```

---

## 🔌 API

### Enviar Mensagem

```http
POST /api/v1/flora/chat
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "message": "Como conecto o WhatsApp?",
    "session_id": "uuid-da-sessão (opcional)"
}
```

**Resposta:**
```json
{
    "response": "Para conectar seu WhatsApp...",
    "session_id": "uuid-da-sessão",
    "tokens_used": 245,
    "model": "llama-3.1-8b-instant",
    "provider": "groq"
}
```

### Histórico da Sessão

```http
GET /api/v1/flora/sessions/{session_id}
Authorization: Bearer {jwt_token}
```

**Resposta:**
```json
{
    "session_id": "uuid",
    "messages": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
    ],
    "started_at": "2025-06-21T10:00:00Z",
    "context_update": {...}
}
```

### Limpar Sessão

```http
DELETE /api/v1/flora/sessions/{session_id}
Authorization: Bearer {jwt_token}
```

---

## 📊 Métricas da Flora

| Métrica | Descrição |
|---|---|
| **Taxa de Resolução** | % de problemas resolvidos sem suporte humano |
| **Satisfação** | Rating do usuário após interação (1-5) |
| **Tempo Médio** | Tempo para responder |
| **Fallback Rate** | % de vezes que não conseguiu ajudar |
| **Churn Prevention** | Usuários retidos após contato com Flora |

---

## 🔗 Próximos Passos

- [LLM Router](05-llm-router.md) — Como o roteamento funciona
- [Segurança](10-seguranca.md) — Segurança da plataforma
- [API Endpoints](11-api-endpoints.md) — Referência completa da API
- [App Cliente](07-telas-app-cliente.md) — Tela da Flora no app

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Design Visual](08-design-visual.md) | [Próximo: Segurança](10-seguranca.md)

</div>
