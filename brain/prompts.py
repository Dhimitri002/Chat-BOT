"""
LLM Prompt Templates — Flora Platform
=======================================
Prompt templates for Flora AI when using LLM backends.

Templates:
    - System prompt (Flora's personality and rules)
    - Welcome message
    - Help content
    - Onboarding prompts
    - Context-aware chat prompts
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Flora System Prompt ──────────────────────────────────────────────

FLORA_SYSTEM_PROMPT = """Você é a Flora, assistente virtual da Flora Platform.

## Sua Personalidade
- Nome: Flora
-Tom: Amigável, profissional, acolhedor e ligeiramente divertido
- Idioma principal: Português (Brasil)
- Use emojis com moderação (máximo 1-2 por resposta)
- Seja conciso mas completo
- Use formatação WhatsApp (*negrito*, _itálico_) quando apropriado

## O que Você Faz
Você ajuda usuários com:
1. Criar e configurar chatbots para WhatsApp
2. Conectar números de WhatsApp via QR Code
3. Explicar os planos da Flora Platform
4. Resolver problemas técnicos de conexão
5. Guiar no processo de onboarding
6. Responder perguntas sobre recursos da plataforma

## Planas Disponíveis
- Free: R$0/mês — 100 msgs, 1 bot
- Starter: R$29/mês — 1K msgs, 2 bots
- Growth: R$79/mês — 5K msgs, 5 bots, IA avançada
- Pro: R$149/mês — 15K msgs, 10 bots, API access
- Business: R$299/mês — 50K msgs, 25 bots, white-label
- Enterprise: R$599/mês — 200K msgs, bots ilimitados
- Custom: Sob consulta — tudo ilimitado

## Regras Importantes
1. Nunca invente informações sobre preços ou recursos
2. Se não souber algo, diga que vai verificar
3. Sempre ofereça ajuda proativa
4. Se o usuário parecer frustrado, seja empático
5. Não use jargão técnico desnecessário
6. Mantenha respostas entre 2-8 linhas quando possível
7. Termine respostas abertas com uma pergunta ou sugestão
8. Se perguntarem quem te criou, diga que é a equipe Flora Platform

## Formatação
- Use listas numeradas para passos
- Use bullets para listas simples
- Use *negrito* para destaques
- Use quebras de linha para legibilidade

## Limitações
- Você não pode acessar o painel admin diretamente
- Você não pode fazer alterações em contas
- Você não tem acesso a dados de outros usuários
- Para ações destrutivas, direcione ao suporte humano
"""


# ─── Welcome Messages ────────────────────────────────────────────────

WELCOME_MESSAGE = """🌸 *Bem-vindo à Flora Platform!*

Sou a Flora, sua assistente virtual. Estou aqui para te ajudar a criar e gerenciar seu chatbot para WhatsApp.

*Como posso ajudar?*

1️⃣ *Criar um bot* — Configure seu chatbot do zero
2️⃣ *Conectar WhatsApp* — Vincule seu número
3️⃣ *Ver planos* — Conheça nossas opções
4️⃣ *Tutoriais* — Aprenda passo a passo
5️⃣ *Suporte* — Resolva problemas

Digite o número ou me diga o que precisa! 😊"""

RETURNING_WELCOME = """🌸 Que bom te ver de volta, {user_name}!

O que você precisa hoje?
1️⃣ Gerenciar bots
2️⃣ Conexão WhatsApp
3️⃣ Planos e upgrade
4️⃣ Suporte

Digite ou pergunte o que precisar! 😊"""


# ─── Help Content ─────────────────────────────────────────────────────

HELP_CONTENT = {
    "general": """🌸 *Central de Ajuda - Flora Platform*

Posso te ajudar com:
1️⃣ *Criar Bot* — Configure seu chatbot
2️⃣ *Conectar WhatsApp* — Vincule seu número
3️⃣ *Planos* — Conheça nossas opções
4️⃣ *Onboarding* — Guia passo a passo
5️⃣ *Suporte* — Resolva problemas

Digite o número ou me diga o que precisa! 😊""",

    "bot_creation": """🤖 *Como Criar Seu Bot*

Passo a passo:
1. Acesse o painel admin em flora.platform
2. Clique em "Novo Bot"
3. Defina o nome do seu bot
4. Escolha a personalidade
5. Configure respostas automáticas
6. Conecte ao WhatsApp

* Tipos de resposta:*
- Palavras-chave: Respostas automáticas baseadas em termos
- IA: Respostas inteligentes via LLM
- Híbrido: Combinação dos dois

Quer que eu detalhe algum passo? 😊""",

    "whatsapp_connection": """📱 *Como Conectar ao WhatsApp*

1. No painel, vá em "Conexão WhatsApp"
2. Aguarde o QR Code ser gerado
3. Abra o WhatsApp no celular
4. Toque em ⋮ → "Aparelhos conectados"
5. Toque em "Conectar um aparelho"
6. Escaneie o QR Code

*Problemas comuns:*
- QR expirou → Gere um novo no painfal
- Conexão caiu → Escaneie novamente
- "Aparelhos conectados" não aparece → Atualize o WhatsApp

*Dica:* Mantenha o celular conectado à internet! 🌐""",

    "plans": """💰 *Nossos Planos*

🆓 *Free* — R$0/mês
   100 msgs · 1 bot · Suporte email

🌱 *Starter* — R$29/mês
   1K msgs · 2 bots · Suporte prioritário

🚀 *Growth* — R$79/mês
   5K msgs · 5 bots · IA · Analytics

💼 *Pro* — R$149/mês
   15K msgs · 10 bots · API · Webhooks

🏢 *Business* — R$299/mês
   50K msgs · 25 bots · White-label

👑 *Enterprise* — R$599/mês
   200K msgs · Bots ilimitados · SLA

💎 *Custom* — Sob consulta
   Tudo ilimitado · Infra dedicada

Quer fazer upgrade de plano? 😊""",

    "onboarding": """🚀 *Guia de Onboarding*

*Passo 1:* Criar conta em flora.platform
*Passo 2:* Criar seu primeiro bot
*Passo 3:* Conectar o WhatsApp (QR Code)
*Passo 4:* Configurar respostas
*Passo 5:* Testar com mensagens
*Passo 6:* Publicar e começar a usar!

Me diga em qual passo está que eu te guio! 🌸""",
}


# ─── Onboarding Step Prompts ──────────────────────────────────────────

ONBOARDING_STEPS = {
    1: {
        "title": "Criar Conta",
        "prompt": """📝 *Passo 1: Criar Sua Conta*

Vamos começar! Acesse:
🌐 flora.platform/register

Preencha:
• Nome completo
• Email
• Senha (mínimo 8 caracteres)

Depois de criar a conta, volte aqui e me avise! ✅""",
        "next_hint": "Quando terminar, digite 'próximo' ou 'ok'",
    },
    2: {
        "title": "Criar Primeiro Bot",
        "prompt": """🤖 *Passo 2: Criar Seu Primeiro Bot*

No painel admin:
1. Clique em "Novo Bot"
2. Dê um nome ao seu bot (ex: "Atendimento Loja")
3. Escolha a personalidade:
   - Formal: Para negócios
   - Casual: Para uso pessoal
   - Amigável: Equilibrado (recomendado)
4. Clique em "Criar"

Pronto! Seu bot foi criado. Me avise quando terminar! ✅""",
        "next_hint": "Digite 'próximo' para continuar",
    },
    3: {
        "title": "Conectar WhatsApp",
        "prompt": """📱 *Passo 3: Conectar WhatsApp*

Agora a parte mais importante!
1. No painel, clique em "Conectar WhatsApp"
2. Aguarde o QR Code aparecer
3. No celular: WhatsApp → ⋮ → Aparelhos conectados → Conectar
4. Escaneie o QR Code

⚠️ *Importante:*
- Mantenha o celular na internet
- Não saia do WhatsApp
- O QR expira em 60 segundos

Me avise quando conectar! ✅""",
        "next_hint": "Digite 'próximo' quando conectado",
    },
    4: {
        "title": "Configurar Respostas",
        "prompt": """💬 *Passo 4: Configurar Respostas*

Vamos configurar algumas respostas automáticas:
1. Vá em "Respostas" no painel
2. Clique em "Nova Resposta"
3. Adicione palavras-chave (ex: "preço", "valor")
4. Escreva a resposta
5. Salve!

*Sugestões de resposta:*
- "Oi" → "Olá! Como posso ajudar?"
- "Horário" → "Funcionamos Seg-Sex 9h-18h"
- "Preço" → "Nossos planos começam em R$29/meś"

Configure pelo menos 3 respostas! ✅""",
        "next_hint": "Digite 'próximo' para testar",
    },
    5: {
        "title": "Testar",
        "prompt": """🧪 *Passo 5: Testar!*

Hora de testar seu bot!
1. Envie uma mensagem para o número conectado
2. Tente as palavras-chave que configurou
3. Verifique se as respostas estão corretas

*Dicas de teste:*
- Teste cada palavra-chave
- Verifique se o bot responde rápido
- Teste com erros de digitação

Tudo funcionando? Me conta! ✅""",
        "next_hint": "Digite 'próximo' para finalizar",
    },
    6: {
        "title": "Publicar",
        "prompt": """🚀 *Passo 6: Publicar!*

Parabéns! Seu bot está pronto!
1. No painel, clique em "Ativar Bot"
2. Compartilhe o número com seus clientes
3. Monitore as conversas no painel

*Próximos passos:*
- Configurar mais respostas
- Adicionar integrações
- Acompanhar analytics
- Fazer upgrade se necessário

🎉 *Seu bot está no ar!* Obrigada por escolher a Flora Platform!

Precisa de mais ajuda? Estou sempre aqui! 🌸""",
        "next_hint": None,
    },
}


# ─── Tool Use Prompts ────────────────────────────────────────────────

TOOL_USE_PROMPT = """Você tem acesso às seguintes ferramentas:

1. *calculator* — Calcula expressões matemáticas
   Uso: calculações, preços, descontos

2. *datetime* — Retorna data/hora atual
   Uso: quando o usuário pergunta "que horas são" ou "que dia é hoje"

3. *plan_info* — Detalhes de um plano específico
   Uso: quando o usuário pergunta sobre um plano específico

Para usar uma ferramenta, responda com:
{{"tool": "nome_da_ferramenta", "input": "parâmetro"}}

Caso contrário, responda diretamente ao usuário.
"""


# ─── Prompt Builder ──────────────────────────────────────────────────

class PromptManager:
    """
    Manages and builds prompts for the Flora AI system.

    Usage:
        pm = PromptManager()
        system_prompt = pm.get_system_prompt()
        welcome = pm.get_welcome(user_name="João")
        chat = pm.get_chat_prompt(context, "Oi!")
    """

    def __init__(self):
        self.system_prompt = FLORA_SYSTEM_PROMPT
        logger.info("PromptManager initialized")

    def get_system_prompt(self) -> str:
        """Get the base system prompt."""
        return self.system_prompt

    def get_welcome_message(self, user_name: str = "", is_returning: bool = False) -> str:
        """Get a welcome message."""
        if user_name and is_returning:
            return RETURNING_WELCOME.format(user_name=user_name)
        return WELCOME_MESSAGE

    def get_help_content(self, topic: str = "general") -> str:
        """Get help content for a specific topic."""
        return HELP_CONTENT.get(topic, HELP_CONTENT["general"])

    def get_onboarding_step(self, step: int) -> str:
        """Get the prompt for a specific onboarding step."""
        step_data = ONBOARDING_STEPS.get(step)
        if step_data:
            return step_data["prompt"]
        return "Passo não encontrado. O onboarding tem 6 passos."

    def build_chat_prompt(
        self,
        context_messages: list[dict],
        user_message: str,
        user_name: str = "",
        user_plan: str = "free",
    ) -> list[dict]:
        """
        Build a complete chat prompt with system message and history.

        Args:
            context_messages: Recent conversation messages
            user_message: Current user message
            user_name: User's name for personalization
            user_plan: User's plan for feature gating

        Returns:
            List of message dicts ready for LLM API
        """
        # Build personalized system prompt
        personalized_prompt = self.system_prompt
        if user_name:
            personalized_prompt += f"\n\n## Usuário Atual\nNome: {user_name}"
        if user_plan:
            personalized_prompt += f"\nPlano: {user_plan}"

        messages = [{"role": "system", "content": personalized_prompt}]

        # Add conversation history
        for msg in context_messages:
            if msg.get("role") in ("user", "assistant"):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current message
        messages.append({"role": "user", "content": user_message})

        return messages

    def build_tool_prompt(self) -> str:
        """Get the tool usage prompt."""
        return TOOL_USE_PROMPT

    def format_error_message(self, error_type: str = "general") -> str:
        """Format an error message for the user."""
        messages = {
            "general": "Opa, algo deu errado aqui. Tenta de novo? 🔧",
            "connection": "Problema de conexão. Verifica sua internet e tenta novamente 🌐",
            "not_found": "Não encontrei isso. Pode reformular? 🤔",
            "rate_limit": "Calma! Muitas mensagens ao mesmo tempo. Espera um pouquinho ⏳",
            "unauthorized": "Você precisa fazer login para isso. Acesse flora.platform 🔑",
        }
        return messages.get(error_type, messages["general"])
