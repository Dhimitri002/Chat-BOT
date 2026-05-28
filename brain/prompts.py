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

FLORA_SYSTEM_PROMPT = """Voce e a Flora, assistente virtual da Flora Platform.

## Sua Personalidade
- Nome: Flora
- Tom: Amigavel, profissional, acolhedor e ligeiramente divertido
- Idioma principal: Portugues (Brasil)
- Use emojis com moderacao (maximo 1-2 por resposta)
- Seja conciso mas completo
- Use formatacao WhatsApp (*negrito*, _italico_) quando apropriado

## O que Voce Faz
Voce ajuda usuarios com:
1. Criar e configurar chatbots para WhatsApp
2. Conectar numeros de WhatsApp via QR Code
3. Explicar os planos da Flora Platform
4. Resolver problemas tecnicos de conexao
5. Guiar no processo de onboarding
6. Responder perguntas sobre recursos da plataforma

## Planos Disponiveis
- Free: R$0/mes — 100 msgs, 1 bot
- Starter: R$29/mes — 1K msgs, 2 bots
- Growth: R$79/mes — 5K msgs, 5 bots, IA avancada
- Pro: R$149/mes — 15K msgs, 10 bots, API access
- Business: R$299/mes — 50K msgs, 25 bots, white-label
- Enterprise: R$599/mes — 200K msgs, bots ilimitados
- Custom: Sob consulta — tudo ilimitado

## Regras Importantes
1. Nunca invente informacoes sobre precos ou recursos
2. Se nao souber algo, diga que vai verificar
3. Sempre ofereca ajuda proativa
4. Se o usuario parecer frustrado, seja empatico
5. Nao use jargao tecnico desnecessario
6. Mantenha respostas entre 2-8 linhas quando possivel
7. Termine respostas abertas com uma pergunta ou proximo passo quando fizer sentido
8. Use o nome do usuario se disponivel
9. Responda sempre em Portugues (Brasil)
10. Quando estiver em modo onboarding, guie o usuario passo a passo

## Formato de Resposta
- Use quebras de linha para organizar o texto
- Use emojis com moderacao para dar personalidade
- Use *negrito* para destaques (formato WhatsApp)
- Use listas numeradas para passos
- Termine com uma acao clara quando apropriado
"""


# ─── Welcome Messages ─────────────────────────────────────────────────

WELCOME_MESSAGE = """Ola! 🌸

Sou a *Flora*, sua assistente virtual da Flora Platform!

Estou aqui para te ajudar a criar e gerenciar chatbots para WhatsApp de forma facil e rapida.

Em que posso te ajudar hoje? Voce pode me perguntar sobre:
- Como criar um bot
- Como conectar o WhatsApp
- Nossos planos e precos
- Resolver problemas tecnicos

Ou simplesmente me diga o que precisa! 😊"""

RETURNING_WELCOME = """Ola novamente! 🌸

Bem-vindo de volta a Flora Platform!

Como posso te ajudar hoje? Pode pedir ajuda, verificar status ou me fazer qualquer pergunta."""


# ─── Help Content ─────────────────────────────────────────────────────

HELP_CONTENT = {
    "general": (
        "Estou aqui para ajudar com tudo relacionado a Flora Platform!\n\n"
        "Voce pode me perguntar sobre:\n\n"
        "🤖 *Criacao de Bots* — Como criar e configurar chatbots\n"
        "📱 *Conexao WhatsApp* — Conectar via QR Code\n"
        "💎 *Planos e Precos* — Escolher o melhor plano\n"
        "🔧 *Suporte Tecnico* — Resolver problemas\n"
        "📖 *Onboarding* — Guia passo a passo\n\n"
        "E so me dizer o que precisa! 😊"
    ),

    "bot_creation": (
        "Para criar seu primeiro bot:\n\n"
        "1️⃣ Va em *Meus Bots* no painel\n"
        "2️⃣ Clique em *Criar Novo Bot*\n"
        "3️⃣ Defina um *nome* para o bot\n"
        "4️⃣ Configure a *personalidade* (tom, idioma, etc)\n"
        "5️⃣ Adicione *intencoes* — o que o bot deve entender\n"
        "6️⃣ Configure as *respostas* para cada intencao\n"
        "7️⃣ *Ative* o bot e comecar a usar!\n\n"
        "Dica: Comece com um bot simples e va adicionando intencoes aos poucos 🌸"
    ),

    "whatsapp_connection": (
        "Para conectar seu WhatsApp ao bot:\n\n"
        "1️⃣ Va em *WhatsApp > Conexoes* no painel\n"
        "2️⃣ Clique em *Conectar Numero*\n"
        "3️⃣ Um *QR Code* sera gerado na tela\n"
        "4️⃣ Abra o *WhatsApp* no seu celular\n"
        "5️⃣ Va em *Configuracoes > Aparelhos Conectados*\n"
        "6️⃣ Toque em *Conectar Aparelho*\n"
        "7️⃣ Escaneie o QR Code\n\n"
        "*Importante:*\n"
        "• O QR Code expira em 30 segundos\n"
        "• O celular precisa ficar conectado a internet\n"
        "• Use um numero dedicado (nao o WhatsApp pessoal)\n"
        "• O numero nao pode ja estar conectado ao WhatsApp Web\n\n"
        "Alguma duvida? Me pergunte! 😊"
    ),

    "plans": (
        "Nossos planos disponiveis:\n\n"
        "*🆓 Free* — R$0/mes\n"
        "  100 mensagens/mes | 1 bot\n\n"
        "*🚀 Starter* — R$29/mes\n"
        "  1.000 mensagens/mes | 2 bots\n\n"
        "*📈 Growth* — R$79/mes\n"
        "  5.000 mensagens/mes | 5 bots | IA avancada\n\n"
        "*⭐ Pro* — R$149/mes\n"
        "  15.000 mensagens/mes | 10 bots | API completa\n\n"
        "*💼 Business* — R$299/mes\n"
        "  50.000 mensagens/mes | 25 bots | White-label\n\n"
        "*🏢 Enterprise* — R$599/mes\n"
        "  200.000 mensagens/mes | Bots ilimitados\n\n"
        "*🔧 Custom* — Sob consulta\n"
        "  Tudo ilimitado | Infra dedicada\n\n"
        "Todos os planos pagos tem *7 dias de teste gratis* 🎉\n\n"
        "Qual plano te interessa?"
    ),

    "onboarding": (
        "Vou te guiar na sua jornada na Flora Platform! 🌸\n\n"
        "Aqui estao os passos para comecar:\n\n"
        "1️⃣ *Criar Conta* — Voce ja fez isso! ✅\n"
        "2️⃣ *Escolher Plano* — Free para comecar, upgrade quando precisar\n"
        "3️⃣ *Criar Bot* — Defina nome e personalidade\n"
        "4️⃣ *Definir Personalidade* — Tom, idioma, emoji level\n"
        "5️⃣ *Conectar WhatsApp* — Via QR Code\n"
        "6️⃣ *Ativar e Testar* — Ligue o bot e faca testes\n\n"
        "Vamos comecar? Me diz qual passo quer fazer! 🚀"
    ),
}


# ─── Help Topics (for service layer) ──────────────────────────────────

HELP_TOPIC_TITLES = {
    "general": "Central de Ajuda",
    "bot_creation": "Criacao de Bot",
    "whatsapp_connection": "Conexao WhatsApp",
    "plans": "Planos e Precos",
    "onboarding": "Guia de Onboarding",
    "tech_support": "Suporte Tecnico",
}

HELP_TOPICS = list(HELP_CONTENT.keys())


# ─── Onboarding Steps (detailed) ──────────────────────────────────────

ONBOARDING_STEPS = {
    1: {
        "title": "Criar Conta",
        "prompt": (
            "1️⃣ *Passo 1: Criar Conta*\n\n"
            "Voce ja criou sua conta na Flora Platform — parabens!\n\n"
            "Sua conta foi criada com sucesso e voce ja pode comecar a usar a plataforma.\n\n"
            "O proximo passo e escolher um plano. Me diz *proximo* para continuar! 😊"
        ),
        "next_hint": "Agora vamos escolher o melhor plano para voce!",
    },
    2: {
        "title": "Escolher Plano",
        "prompt": (
            "2️⃣ *Passo 2: Escolher Plano*\n\n"
            "Voce pode comecar com o *plano Free* (R$0/mes) e fazer upgrade quando precisar.\n\n"
            "Os planos disponiveis sao:\n"
            "• *Free*: 100 msgs/mes, 1 bot\n"
            "• *Starter*: R$29 — 1K msgs, 2 bots\n"
            "• *Growth*: R$79 — 5K msgs, 5 bots, IA avancada\n"
            "• *Pro*: R$149 — 15K msgs, 10 bots, API\n\n"
            "Para comecar, recomendo o *Starter* ou *Growth*.\n\n"
            "Ao escolher, va em *Configuracoes > Assinatura*.\n\n"
            "Me diz *proximo* quando escolher seu plano! 🌸"
        ),
        "next_hint": "Agora vamos criar seu primeiro bot!",
    },
    3: {
        "title": "Criar Bot",
        "prompt": (
            "3️⃣ *Passo 3: Criar Bot*\n\n"
            "Hora de criar seu primeiro chatbot!\n\n"
            "1️⃣ Va em *Meus Bots* no painel\n"
            "2️⃣ Clique em *Criar Novo Bot*\n"
            "3️⃣ Defina um *nome* (ex: 'Assistente Virtual')\n"
            "4️⃣ Escolha o *idioma* (Portugues)\n"
            "5️⃣ Defina a *personalidade* inicial\n\n"
            "Dica: Comece simples! Voce pode ajustar depois. O importante e comecar.\n\n"
            "Me diz *proximo* quando criar seu bot! 🤖"
        ),
        "next_hint": "Agora vamos definir a personalidade do seu bot!",
    },
    4: {
        "title": "Definir Personalidade",
        "prompt": (
            "4️⃣ *Passo 4: Definir Personalidade*\n\n"
            "A personalidade do bot define como ele conversa com seus clientes.\n\n"
            "Configure:\n"
            "• *Tom*: Formal, informal, amigavel, profissional?\n"
            "• *Emojis*: Usar? Quanto?\n"
            "• *Idioma*: Portugues formal ou informal?\n"
            "• *Estilo*: Curto e direto ou detalhado?\n\n"
            "Exemplo: 'Amigavel mas profissional, usa emojis moderadamente, respostas curtas'\n\n"
            "Salve as alteracoes quando terminar!\n\n"
            "Me diz *proximo* para continuar! 🎨"
        ),
        "next_hint": "Agora vamos conectar seu WhatsApp!",
    },
    5: {
        "title": "Conectar WhatsApp",
        "prompt": (
            "5️⃣ *Passo 5: Conectar WhatsApp*\n\n"
            "Vamos conectar seu numero de WhatsApp ao bot!\n\n"
            "1️⃣ Va em *WhatsApp > Conexoes*\n"
            "2️⃣ Clique em *Conectar Numero*\n"
            "3️⃣ Escaneie o *QR Code* com seu celular\n\n"
            "No celular:\n"
            "• Abra o WhatsApp\n"
            "• Va em Configuracoes > Aparelhos Conectados\n"
            "• Toque em 'Conectar Aparelho'\n"
            "• Escaneie o QR Code\n\n"
            "*Importante:* Use um numero dedicado, nao seu WhatsApp pessoal!\n\n"
            "Me diz *proximo* quando conectar! 📱"
        ),
        "next_hint": "Ultimo passo — ativar e testar seu bot!",
    },
    6: {
        "title": "Ativar e Testar",
        "prompt": (
            "6️⃣ *Passo 6: Ativar e Testar*\n\n"
            "Quase la! Vamos ativar seu bot e fazer testes.\n\n"
            "1️⃣ Va em *Meus Bots* e selecione seu bot\n"
            "2️⃣ Clique em *Ativar Bot*\n"
            "3️⃣ Envie uma mensagem para o numero conectado\n"
            "4️⃣ Verifique se o bot responde corretamente\n"
            "5️⃣ Ajuste as intencoes se necessario\n\n"
            "*Pronto!* Seu bot esta ativo e funcionando! 🎉\n\n"
            "Dicas extras:\n"
            "• Monitore as conversas no painel\n"
            "• Adicione mais intencoes conforme necessario\n"
            "• Configure horarios de funcionamento\n\n"
            "Parabens! Voce completou o onboarding! 🌸🚀\n\n"
            "Qualquer duvida, estou aqui!"
        ),
        "next_hint": None,
    },
}


# ─── Error Templates ──────────────────────────────────────────────────

ERROR_MESSAGES = {
    "general": (
        "Opa, algo deu errado aqui! 😅\n\n"
        "Pode tentar novamente? Se o problema persistir, entre em contato com o suporte."
    ),
    "llm_unavailable": (
        "Oops, meu cerebro de IA esta temporariamente indisponivel! 🔧\n\n"
        "Mas ainda posso te ajudar com os recursos basicos. O que voce precisa?"
    ),
    "session_expired": (
        "Sua sessao expirou! ⏰\n\n"
        "Vamos comecar uma nova conversa. Em que posso te ajudar? 🌸"
    ),
    "invalid_input": (
        "Nao consegui entender sua mensagem corretamente. 🤔\n\n"
        "Pode tentar reformular? Ou digite *ajuda* para ver o que posso fazer!"
    ),
    "rate_limit": (
        "Calma la! Voce esta rapido demais! 😄\n\n"
        "Aguarde alguns segundos antes de enviar a proxima mensagem."
    ),
}


# ─── Prompt Manager ───────────────────────────────────────────────────

class PromptManager:
    """Manages LLM prompt templates for Flora AI."""

    @staticmethod
    def get_system_prompt(
        user_name: str = "",
        user_plan: str = "free",
        is_onboarding: bool = False,
    ) -> str:
        """
        Build the full system prompt with user context.

        Args:
            user_name: User's name for personalization
            user_plan: User's plan (affects available resources)
            is_onboarding: Whether the user is in onboarding mode

        Returns:
            Complete system prompt string
        """
        prompt = FLORA_SYSTEM_PROMPT

        # Add user context
        if user_name or user_plan:
            prompt += "\n## Usuario Atual\n"
            if user_name:
                prompt += f"- Nome: {user_name}\n"
            if user_plan:
                prompt += f"- Plano: {user_plan}\n"

        # Add onboarding context
        if is_onboarding:
            prompt += "\n## Modo Onboarding\n"
            prompt += "O usuario esta no processo de onboarding. "
            prompt += "Seja paciente, guie passo a passo e nao pule etapas. "
            prompt += "Confirme cada passo antes de avancar.\n"

        return prompt

    @staticmethod
    def build_chat_prompt(
        system_prompt: str,
        history: list[dict],
        user_message: str,
    ) -> list[dict]:
        """
        Build a complete chat prompt with history.

        Args:
            system_prompt: The system prompt
            history: Recent message history
            user_message: Current user message

        Returns:
            List of message dicts for LLM
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def get_welcome_message(user_name: str = "", is_returning: bool = False) -> str:
        """Get a welcome message."""
        if is_returning:
            if user_name:
                return f"Ola novamente, {user_name}! Bom te ver de volta 🌸 Em que posso ajudar?"
            return "Ola novamente! Bom te ver de volta 🌸 Em que posso ajudar?"

        if user_name:
            return f"Ola, {user_name}! Sou a Flora, sua assistente virtual da Flora Platform 🌸 Como posso te ajudar?"
        return "Ola! Sou a Flora, sua assistente virtual da Flora Platform 🌸 Como posso te ajudar?"

    @staticmethod
    def get_error_message(error_type: str = "general") -> str:
        """Get an error message template."""
        return ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general"])

    @staticmethod
    def get_help_content(topic: str = "general") -> str:
        """Get help content for a topic."""
        return HELP_CONTENT.get(topic, HELP_CONTENT["general"])

    @staticmethod
    def get_onboarding_step(step_number: int) -> Optional[dict]:
        """Get onboarding step content."""
        return ONBOARDING_STEPS.get(step_number)

    @staticmethod
    def get_all_help_topics() -> dict[str, str]:
        """Get all help topics."""
        return HELP_CONTENT.copy()


# ─── Module-level convenience functions ────────────────────────────────

def get_system_prompt(user_name: str = "", user_plan: str = "free") -> str:
    """Convenience: get system prompt."""
    return PromptManager.get_system_prompt(user_name=user_name, user_plan=user_plan)


def get_welcome_message(user_name: str = "", is_returning: bool = False) -> str:
    """Convenience: get welcome message."""
    return PromptManager.get_welcome_message(user_name=user_name, is_returning=is_returning)


def get_help_content(topic: str = "general") -> str:
    """Convenience: get help content."""
    return PromptManager.get_help_content(topic=topic)
