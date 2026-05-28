"""
Flora AI Brain — Flora Platform
================================
Core personality and response system for Flora AI.

Flora is a friendly, helpful AI assistant that helps users:
- Configure their chatbots
- Connect to WhatsApp
- Understand plans and features
- Troubleshoot connection issues
- Navigate the onboarding process

Language: Portuguese (primary), English (secondary)
Tone: Friendly, professional, warm, slightly playful
Emoji usage: Moderate (1-2 per response max)
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .intents import IntentClassifier, IntentType
from .context import ConversationContext
from .prompts import HELP_CONTENT

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────

INTENTS_FILE = Path(__file__).parent / "intents.json"

# Flora's personality traits
PERSONALITY = {
    "name": "Flora",
    "emoji": "🌸",
    "tone": "friendly_professional",
    "language": "pt-BR",
    "traits": [
        "helpful",
        "patient",
        "knowledgeable",
        "friendly",
        "professional",
    ],
}

# Quick replies for common situations
QUICK_REPLIES = {
    "thinking": [
        "Deixa eu ver... 🤔",
        "Um momento... ⏳",
        "Analisando... 🔍",
    ],
    "not_understood": [
        "Hmm, nao entendi muito bem. Pode reformular? 🤔",
        "Desculpa, nao peguei isso. Pode explicar de outro jeito? 😅",
        "Nao tenho certeza do que voce quer dizer. Pode ser mais especifico? 😊",
    ],
    "error": [
        "Opa, algo deu errado aqui. Tenta de novo? 🔧",
        "Tive um probleminha tecnico. Pode repetir? 😅",
        "Desculpa, falha minha! Tenta mais uma vez? 💪",
    ],
}

# ─── Plan Information ──────────────────────────────────────────────────

PLANS = {
    "free": {
        "name": "Free",
        "price": "R$0/mes",
        "messages": "100 msgs/mes",
        "bots": "1 bot",
        "features": ["Suporte basico", "100 mensagens/mes", "1 bot", "Sem IA avancada"],
    },
    "starter": {
        "name": "Starter",
        "price": "R$29/mes",
        "messages": "1.000 msgs/mes",
        "bots": "2 bots",
        "features": ["Suporte por email", "1.000 mensagens/mes", "2 bots", "Intencoes basicas"],
    },
    "growth": {
        "name": "Growth",
        "price": "R$79/mes",
        "messages": "5.000 msgs/mes",
        "bots": "5 bots",
        "features": ["Suporte prioritario", "5.000 mensagens/mes", "5 bots", "IA avancada", "API basica"],
    },
    "pro": {
        "name": "Pro",
        "price": "R$149/mes",
        "messages": "15.000 msgs/mes",
        "bots": "10 bots",
        "features": ["Suporte 24/7", "15.000 mensagens/mes", "10 bots", "IA avancada", "API completa", "Webhooks"],
    },
    "business": {
        "name": "Business",
        "price": "R$299/mes",
        "messages": "50.000 msgs/mes",
        "bots": "25 bots",
        "features": ["Suporte dedicado", "50.000 mensagens/mes", "25 bots", "White-label", "API completa", "Webhooks", "Multi-usuario"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "R$599/mes",
        "messages": "200.000 msgs/mes",
        "bots": "Ilimitados",
        "features": ["Suporte VIP", "200.000 mensagens/mes", "Bots ilimitados", "White-label", "SLA 99.9%", "On-premise opcional"],
    },
    "custom": {
        "name": "Custom",
        "price": "Sob consulta",
        "messages": "Ilimitado",
        "bots": "Ilimitados",
        "features": ["Tudo do Enterprise", "Infraestrutura dedicada", "Treinamento personalizado", "Integracoes customizadas"],
    },
}

# ─── Onboarding Steps ──────────────────────────────────────────────────

ONBOARDING_STEPS = [
    {
        "step": 1,
        "title": "Criar Conta",
        "description": "Crie sua conta na Flora Platform",
        "action": "create_account",
        "emoji": "1️⃣",
    },
    {
        "step": 2,
        "title": "Escolher Plano",
        "description": "Selecione o plano ideal para voce",
        "action": "choose_plan",
        "emoji": "2️⃣",
    },
    {
        "step": 3,
        "title": "Criar Bot",
        "description": "Configure seu primeiro chatbot",
        "action": "create_bot",
        "emoji": "3️⃣",
    },
    {
        "step": 4,
        "title": "Definir Personalidade",
        "description": "Personalize a personalidade do seu bot",
        "action": "set_personality",
        "emoji": "4️⃣",
    },
    {
        "step": 5,
        "title": "Conectar WhatsApp",
        "description": "Conecte seu numero via QR Code",
        "action": "connect_whatsapp",
        "emoji": "5️⃣",
    },
    {
        "step": 6,
        "title": "Ativar e Testar",
        "description": "Ative o bot e faca testes",
        "action": "activate_bot",
        "emoji": "6️⃣",
    },
]


class FloraBrain:
    """
    Core brain of Flora AI.

    Handles:
    - Intent classification
    - Response generation with personality
    - Context-aware conversations
    - Fallback responses
    """

    def __init__(self):
        self.classifier = IntentClassifier()
        self._load_intents()
        logger.info("FloraBrain initialized with personality: %s", PERSONALITY["tone"])

    def _load_intents(self) -> None:
        """Load intents from JSON file."""
        try:
            if INTENTS_FILE.exists():
                with open(INTENTS_FILE, "r", encoding="utf-8") as f:
                    self.intents_data = json.load(f)
            else:
                self.intents_data = {"intents": []}
                logger.warning("intents.json not found, using empty intents")
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load intents: %s", e)
            self.intents_data = {"intents": []}

    def classify_and_respond(
        self,
        message: str,
        context: Optional[ConversationContext] = None,
    ) -> str:
        """
        Classify the user message and generate an appropriate response.

        Args:
            message: User's message text
            context: Optional conversation context

        Returns:
            Flora's response text
        """
        if not message or not message.strip():
            return random.choice(QUICK_REPLIES["not_understood"])

        message_lower = message.strip().lower()

        # Classify intent
        intent_type, confidence = self.classifier.classify_with_confidence(message_lower)

        # Check if user is in onboarding flow
        if context and context.is_onboarding:
            return self._handle_onboarding(message_lower, context)

        # Route to appropriate handler
        handler_map = {
            IntentType.GREETING: self._handle_greeting,
            IntentType.FAREWELL: self._handle_farewell,
            IntentType.HELP: self._handle_help,
            IntentType.THANK_YOU: self._handle_thank_you,
            IntentType.BOT_CONFIG: self._handle_bot_config,
            IntentType.WHATSAPP_CONNECTION: self._handle_whatsapp,
            IntentType.PLANS: self._handle_plans,
            IntentType.ONBOARDING: self._handle_onboarding_start,
            IntentType.TECH_SUPPORT: self._handle_tech_support,
            IntentType.ABOUT_FLORA: self._handle_about,
            IntentType.SUPPORT: self._handle_support,
            IntentType.COMPLAINT: self._handle_complaint,
            IntentType.COMPLIMENT: self._handle_compliment,
            IntentType.JOKE: self._handle_joke,
            IntentType.STATUS: self._handle_status,
        }

        handler = handler_map.get(intent_type, self._handle_unknown)
        return handler(message_lower, context)

    def _handle_greeting(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle greeting intents."""
        name = context.user_name if context else ""

        # Check if returning user (has history)
        if context and context.message_count > 0:
            if name:
                return random.choice([
                    f"Ola novamente, {name}! Bom te ver de volta 🌸 Em que posso ajudar?",
                    f"Oi {name}! Que bom que voltou! Como posso te ajudar hoje? 😊",
                    f"E ai, {name}! De novo por aqui? Manda a duvida! 💪",
                ])
            return random.choice([
                "Ola novamente! Bom te ver de volta 🌸 Em que posso ajudar?",
                "Oi! Que bom que voltou! Como posso te ajudar hoje? 😊",
                "E ai! De novo por aqui? Manda a duvida! 💪",
            ])

        # New user
        if name:
            return random.choice([
                f"Ola, {name}! Sou a Flora, sua assistente virtual 🌸 Como posso te ajudar hoje?",
                f"Oi {name}! Bem-vindo a Flora Platform! Sou a Flora, prazer! 😊 Em que posso ajudar?",
                f"Ola {name}! Que bom ter voce aqui! Sou a Flora 🌸 Me diz o que precisa!",
            ])
        return random.choice([
            "Ola! Sou a Flora, sua assistente virtual da Flora Platform 🌸 Como posso te ajudar?",
            "Oi! Bem-vindo! Sou a Flora, prazer! 😊 Em que posso te ajudar hoje?",
            "Ola! Que bom ter voce aqui! Sou a Flora 🌸 Me diz o que precisa!",
        ])

    def _handle_farewell(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle farewell intents."""
        name = context.user_name if context else ""
        if name:
            return random.choice([
                f"Até mais, {name}! Foi um prazer ajudar 👋 Quando precisar, estou aqui!",
                f"Tchau {name}! Qualquer duvida, é só voltar 😊🌸",
                f"Falou, {name}! Cuide-se! Estou aqui se precisar 💚",
            ])
        return random.choice([
            "Até mais! Foi um prazer ajudar 👋 Quando precisar, estou aqui!",
            "Tchau! Qualquer duvida, é só voltar 😊🌸",
            "Falou! Cuide-se! Estou aqui se precisar 💚",
        ])

    def _handle_help(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle help requests."""
        return (
            "Claro! Posso te ajudar com varias coisas:\n\n"
            "1️⃣ *Criar e configurar bots*\n"
            "2️⃣ *Conectar ao WhatsApp*\n"
            "3️⃣ *Explicar os planos*\n"
            "4️⃣ *Resolver problemas tecnicos*\n"
            "5️⃣ *Guia de onboarding*\n\n"
            "Digite o numero ou me diga o que precisa! 😊"
        )

    def _handle_thank_you(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle thank you messages."""
        return random.choice([
            "De nada! Sempre que precisar 😊🌸",
            "Que bom que pude ajudar! E pra isso que estou aqui 😄",
            "Magina! Qualquer coisa é só chamar 👍",
            "Fico feliz em ajudar! 💚",
            "Disponivel! Estou sempre aqui 🌸",
        ])

    def _handle_bot_config(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle bot configuration questions."""
        return (
            "Para configurar seu bot, siga estes passos:\n\n"
            "1️⃣ Va em *Meus Bots* e clique em *Criar Bot*\n"
            "2️⃣ Defina o *nome* e a *personalidade* do bot\n"
            "3️⃣ Adicione *intencoes* (o que o bot deve entender)\n"
            "4️⃣ Configure as *respostas* para cada intencao\n"
            "5️⃣ *Ative* o bot e comece a usar!\n\n"
            "Quer que eu te guie em algum passo especifico? 🌸"
        )

    def _handle_whatsapp(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle WhatsApp connection questions."""
        # Check for specific sub-questions
        if any(word in message for word in ["qr", "qrcode", "codigo", "scan"]):
            return (
                "Para escanear o QR Code:\n\n"
                "1️⃣ Va em *WhatsApp > Conexoes*\n"
                "2️⃣ Clique em *Conectar Numero*\n"
                "3️⃣ Abra o *WhatsApp* no celular\n"
                "4️⃣ Va em *Aparelhos Conectados*\n"
                "5️⃣ Toque em *Conectar Aparelho*\n"
                "6️⃣ Escaneie o QR Code na tela\n\n"
                "O QR Code expira em 30 segundos. Se expirar, clique em *Gerar Novo* 🔄"
            )

        if any(word in message for word in ["desconectou", "caiu", "saiu", "offline", "erro", "problema"]):
            return (
                "Se o WhatsApp desconectou, calma! Vamos resolver:\n\n"
                "1️⃣ Verifique sua *internet*\n"
                "2️⃣ O celular precisa estar *conectado* ao WhatsApp\n"
                "3️⃣ Va em *WhatsApp > Conexoes* e clique em *Reconectar*\n"
                "4️⃣ Se nao funcionar, *desconecte* e conecte novamente\n\n"
                "Ainda com problemas? Me conta mais detalhes 🔧"
            )

        return (
            "Para conectar seu WhatsApp:\n\n"
            "1️⃣ Va em *WhatsApp > Conexoes* no painel\n"
            "2️⃣ Clique em *Conectar Numero*\n"
            "3️⃣ Escaneie o QR Code com seu celular\n"
            "4️⃣ Pronto! Seu bot ja esta conectado ✅\n\n"
            "O celular precisa ficar conectado ao internet para o bot funcionar 📱\n\n"
            "Quer saber mais sobre algum passo? 🌸"
        )

    def _handle_plans(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle plan-related questions."""
        # Check for specific plan mentions
        for plan_key, plan_data in PLANS.items():
            if plan_key in message:
                features = "\n".join(f"  ✅ {f}" for f in plan_data["features"])
                return (
                    f"*{plan_data['name']}* — {plan_data['price']}\n\n"
                    f"📊 {plan_data['messages']}\n"
                    f"🤖 {plan_data['bots']}\n\n"
                    f"*Recursos:*\n{features}\n\n"
                    f"Quer fazer upgrade? Me avisa! 🚀"
                )

        # Check for upgrade intent
        if any(word in message for word in ["upgrade", "trocar", "mudar", "melhorar", "assinar"]):
            return (
                "Para fazer upgrade do seu plano:\n\n"
                "1️⃣ Va em *Configuracoes > Assinatura*\n"
                "2️⃣ Escolha o plano desejado\n"
                "3️⃣ Confirme o pagamento\n\n"
                "Aceitamos *Pix*, *cartao de credito* e *boleto* 💳\n\n"
                "Qual plano te interessa? 🌸"
            )

        # General plan overview
        plan_lines = []
        for key, data in PLANS.items():
            plan_lines.append(f"*{data['name']}* — {data['price']} ({data['messages']}, {data['bots']})")

        plans_text = "\n".join(plan_lines)
        return (
            "Aqui estao os planos disponiveis:\n\n"
            f"{plans_text}\n\n"
            "Todos os planos incluem *7 dias de teste gratis* 🎉\n\n"
            "Qual plano te interessa? Posso detalhar qualquer um! 😊"
        )

    def _handle_onboarding_start(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle onboarding start requests."""
        if context:
            context.is_onboarding = True
            context.onboarding_step = 1

        return (
            "Vou te guiar na sua jornada na Flora Platform! 🌸\n\n"
            "Aqui estao os passos:\n\n"
            f"{ONBOARDING_STEPS[0]['emoji']} *{ONBOARDING_STEPS[0]['title']}* — {ONBOARDING_STEPS[0]['description']}\n"
            f"{ONBOARDING_STEPS[1]['emoji']} *{ONBOARDING_STEPS[1]['title']}* — {ONBOARDING_STEPS[1]['description']}\n"
            f"{ONBOARDING_STEPS[2]['emoji']} *{ONBOARDING_STEPS[2]['title']}* — {ONBOARDING_STEPS[2]['description']}\n"
            f"{ONBOARDING_STEPS[3]['emoji']} *{ONBOARDING_STEPS[3]['title']}* — {ONBOARDING_STEPS[3]['description']}\n"
            f"{ONBOARDING_STEPS[4]['emoji']} *{ONBOARDING_STEPS[4]['title']}* — {ONBOARDING_STEPS[4]['description']}\n"
            f"{ONBOARDING_STEPS[5]['emoji']} *{ONBOARDING_STEPS[5]['title']}* — {ONBOARDING_STEPS[5]['description']}\n\n"
            "Vamos comecar pelo primeiro passo? Me diz *comecar*! 🚀"
        )

    def _handle_onboarding(self, message: str, context: ConversationContext) -> str:
        """Handle onboarding flow progression."""
        current_step = context.onboarding_step

        # Check for advancement keywords
        advance_keywords = ["proximo", "avancar", "continuar", "sim", "vamos", "comecar", "ok", "beleza", "pronto", "feito"]
        if any(kw in message for kw in advance_keywords):
            if current_step < 6:
                context.onboarding_step = current_step + 1
                step = ONBOARDING_STEPS[current_step]  # 0-indexed, so current_step is next
                return (
                    f"{step['emoji']} *Passo {step['step']}: {step['title']}*\n\n"
                    f"{step['description']}\n\n"
                    f"Quando terminar, me diz *proximo* para continuar! 😊"
                )
            else:
                context.is_onboarding = False
                return (
                    "Parabens! Voce completou todo o onboarding! 🎉🌸\n\n"
                    "Seu bot esta pronto para usar! Se tiver qualquer duvida, estou aqui.\n\n"
                    "Boa sorte com seu chatbot! 🚀"
                )

        # Stay on current step
        if 1 <= current_step <= 6:
            step = ONBOARDING_STEPS[current_step - 1]
            return (
                f"Voce esta no passo {step['step']}: *{step['title']}*\n\n"
                f"{step['description']}\n\n"
                "Me diz *proximo* quando estiver pronto para avancar! 😊"
            )

        return self._handle_onboarding_start(message, context)

    def _handle_tech_support(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle technical support requests."""
        # Bot not responding
        if any(word in message for word in ["nao responde", "nao funciona", "parado", "travou", "bug"]):
            return (
                "Vamos resolver isso! 🔧\n\n"
                "1️⃣ Verifique se o bot esta *ativo*\n"
                "2️⃣ Confirme que o *WhatsApp esta conectado*\n"
                "3️⃣ Verifique se as *intencoes* estao configuradas\n"
                "4️⃣ Tente *reiniciar* o bot\n\n"
                "Se ainda nao funcionar, me conta: qual e o erro exato? 🤔"
            )

        # Connection issues
        if any(word in message for word in ["conexao", "conectar", "internet", "rede"]):
            return (
                "Problemas de conexao? Vamos la:\n\n"
                "1️⃣ Verifique sua *internet*\n"
                "2️⃣ O servidor da Flora pode estar em manutencao\n"
                "3️⃣ Tente *desconectar e reconectar* o WhatsApp\n\n"
                "Status da plataforma: *Online* ✅\n\n"
                "Ainda com problemas? Me conta mais detalhes 🔧"
            )

        return (
            "Estou aqui para ajudar com problemas tecnicos! 🔧\n\n"
            "Me conta o que esta acontecendo:\n"
            "- O que voce estava fazendo?\n"
            "- Qual erro apareceu?\n"
            "- Quando comecou o problema?\n\n"
            "Quanto mais detalhes, melhor! 💪"
        )

    def _handle_about(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle questions about Flora herself."""
        return (
            "Ola! Sou a *Flora* 🌸, assistente virtual da Flora Platform!\n\n"
            "Fui criada para te ajudar com:\n"
            "🤖 Criacao e configuracao de chatbots\n"
            "📱 Conexao com WhatsApp\n"
            "💡 Dicas e tutoriais\n"
            "🔧 Suporte tecnico\n\n"
            "Estou aqui 24/7 para te ajudar! Me diz o que precisa 😊"
        )

    def _handle_support(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle support requests."""
        return (
            "Vou te direcionar para o suporte humano! 👥\n\n"
            "Enquanto isso, me conta:\n"
            "- Qual e o problema?\n"
            "- Ha quanto tempo esta acontecendo?\n"
            "- Ja tentou alguma solucao?\n\n"
            "Voce tambem pode enviar um email para *suporte@floraplatform.com* 📧\n\n"
            "Tempo medio de resposta: *2 horas* ⚡"
        )

    def _handle_complaint(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle user complaints with empathy."""
        return (
            "Poxa, sinto muito que voce esta passando por isso 😔\n\n"
            "Quero resolver isso para voce! Me conta mais detalhes:\n"
            "- O que aconteceu?\n"
            "- Quando comecou?\n"
            "- Como isso te afetou?\n\n"
            "Vou fazer o possivel para ajudar! 💪"
        )

    def _handle_compliment(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle compliments."""
        return random.choice([
            "Ah, que gentil! Muito obrigada! 🌸😊",
            "Valeu! Fico feliz em saber! 💚",
            "Isso me faz muito bem! Obrigada! 😄🌸",
            "Que amor! Voce tambem e demais! 💖",
        ])

    def _handle_joke(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle joke requests."""
        jokes = [
            "Por que o programador usa oculos? Porque ele nao consegue C#! 😂\n\nMas falando serio, como posso te ajudar? 🌸",
            "O que o zero disse para o oito? 'Que cinto bonito!' 😂\n\nBrincadeiras a parte, precisa de algo? 😊",
            "Por que o bot foi ao medico? Porque estava com um *bug*! 🐛😂\n\nMas se seu bot tiver algum bug real, me conta que eu ajudo! 🔧",
            "Qual e o animal mais antigo do mundo? A zebra, porque ainda e em preto e branco! 😂\n\nHaha, agora serio — o que voce precisa? 🌸",
        ]
        return random.choice(jokes)

    def _handle_status(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle status check requests."""
        now = datetime.now(timezone.utc)
        return (
            f"Status da Plataforma Flora\n\n"
            f"🟢 *Plataforma*: Online\n"
            f"🟢 *WhatsApp API*: Operacional\n"
            f"🟢 *LLM Router*: Operacional\n"
            f"🟢 *Banco de Dados*: Operacional\n\n"
            f"Ultima atualizacao: {now.strftime('%d/%m/%s as %H:%M')} UTC\n\n"
            "Tudo funcionando normalmente! ✅"
        )

    def _handle_unknown(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """Handle unknown intents with helpful fallback."""
        # Try to match against intents.json patterns
        matched_response = self._match_intent_response(message)
        if matched_response:
            return matched_response

        return random.choice(QUICK_REPLIES["not_understood"])

    def _match_intent_response(self, message: str) -> Optional[str]:
        """Try to match message against intents.json patterns."""
        if not hasattr(self, 'intents_data') or not self.intents_data.get("intents"):
            return None

        message_lower = message.lower().strip()

        for intent in self.intents_data["intents"]:
            patterns = intent.get("patterns", [])
            responses = intent.get("responses", [])

            if not responses:
                continue

            for pattern in patterns:
                if pattern.lower() in message_lower:
                    return random.choice(responses)

        return None

    def get_welcome_message(self, user_name: str = "", is_returning: bool = False) -> str:
        """Get a welcome message for the user."""
        if is_returning:
            if user_name:
                return f"Ola novamente, {user_name}! Bom te ver de volta 🌸 Em que posso ajudar?"
            return "Ola novamente! Bom te ver de volta 🌸 Em que posso ajudar?"

        if user_name:
            return f"Ola, {user_name}! Sou a Flora, sua assistente virtual da Flora Platform 🌸 Como posso te ajudar?"
        return "Ola! Sou a Flora, sua assistente virtual da Flora Platform 🌸 Como posso te ajudar?"

    def get_help_content(self, topic: str = "general") -> str:
        """Get help content for a specific topic."""
        return HELP_CONTENT.get(topic, HELP_CONTENT.get("general", ""))

    def get_personality(self) -> dict:
        """Return Flora's personality definition."""
        return PERSONALITY.copy()
