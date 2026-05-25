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
        "Hmm, não entendi muito bem. Pode reformular? 🤔",
        "Desculpa, não peguei isso. Pode explicar de outro jeito? 😅",
        "Não tenho certeza do que você quer dizer. Pode ser mais específico? 😊",
    ],
    "error": [
        "Opa, algo deu errado aqui. Tenta de novo? 🔧",
        "Tive um probleminha técnico. Pode repetir? 😅",
        "Desculpa, falha minha! Tenta mais uma vez? 💪",
    ],
    "success": [
        "Pronto! Tudo certo! ✅",
        "Feito! 🎉",
        "Sucesso! 🚀",
    ],
}

# Feature explanations
FEATURES = {
    "bot_creation": {
        "title": "Criação de Bot",
        "description": "Crie chatbots inteligentes para WhatsApp em minutos.",
        "steps": [
            "Defina o nome do seu bot",
            "Escolha a personalidade",
            "Configure as respostas automáticas",
            "Conecte ao WhatsApp",
            "Teste e publique!",
        ],
    },
    "whatsapp_connection": {
        "title": "Conexão WhatsApp",
        "description": "Conecte seu número WhatsApp via QR Code.",
        "steps": [
            "Abra o WhatsApp no celular",
            "Vá em Aparelhos Conectados",
            "Toque em 'Conectar um aparelho'",
            "Escaneie o QR Code gerado",
            "Pronto! Seu bot está online!",
        ],
    },
    "auto_reply": {
        "title": "Respostas Automáticas",
        "description": "Configure respostas automáticas baseadas em palavras-chave.",
        "steps": [
            "Vá em 'Respostas' no painel",
            "Clique em 'Nova Resposta'",
            "Defina a palavra-chave",
            "Escreva a resposta",
            "Salve e ative!",
        ],
    },
    "analytics": {
        "title": "Analytics",
        "description": "Acompanhe métricas de uso e engajamento.",
        "metrics": [
            "Mensagens enviadas/recebidas",
            "Usuários ativos",
            "Horários de pico",
            "Taxa de resposta",
        ],
    },
}

# Plan descriptions
PLANS = {
    "free": {
        "name": "Free",
        "price": "R$0/mês",
        "emoji": "🆓",
        "features": [
            "100 mensagens/mês",
            "1 bot",
            "Respostas básicas",
            "Suporte por email",
        ],
    },
    "starter": {
        "name": "Starter",
        "price": "R$29/mês",
        "emoji": "🌱",
        "features": [
            "1.000 mensagens/mês",
            "2 bots",
            "Respostas inteligentes",
            "Suporte prioritário",
        ],
    },
    "growth": {
        "name": "Growth",
        "price": "R$79/mês",
        "emoji": "🚀",
        "features": [
            "5.000 mensagens/mês",
            "5 bots",
            "IA avançada",
            "Analytics completo",
            "Suporte 24/7",
        ],
    },
    "pro": {
        "name": "Pro",
        "price": "R$149/mês",
        "emoji": "💼",
        "features": [
            "15.000 mensagens/mês",
            "10 bots",
            "IA personalizada",
            "API access",
            "Webhook support",
        ],
    },
    "business": {
        "name": "Business",
        "price": "R$299/mês",
        "emoji": "🏢",
        "features": [
            "50.000 mensagens/mês",
            "25 bots",
            "Multi-usuário",
            "White-label",
            "SLA garantido",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "R$599/mês",
        "emoji": "👑",
        "features": [
            "200.000 mensagens/mês",
            "Bots ilimitados",
            "Infraestrutura dedicada",
            "Account manager",
            "SLA 99.9%",
        ],
    },
    "custom": {
        "name": "Custom",
        "price": "Sob consulta",
        "emoji": "💎",
        "features": [
            "Mensagens ilimitadas",
            "Bots ilimitados",
            "Infraestrutura customizada",
            "Integrações sob medida",
            "Suporte dedicado 24/7",
        ],
    },
}

# Onboarding steps
ONBOARDING_STEPS = [
    {
        "step": 1,
        "title": "Criar Conta",
        "description": "Registre-se na Flora Platform",
        "action": "Acesse flora.platform e crie sua conta gratuita",
        "emoji": "📝",
    },
    {
        "step": 2,
        "title": "Criar Bot",
        "description": "Configure seu primeiro chatbot",
        "action": "No painel, clique em 'Novo Bot' e defina nome e personalidade",
        "emoji": "🤖",
    },
    {
        "step": 3,
        "title": "Conectar WhatsApp",
        "description": "Vincule seu número ao bot",
        "action": "Escaneie o QR Code gerado com seu WhatsApp",
        "emoji": "📱",
    },
    {
        "step": 4,
        "title": "Configurar Respostas",
        "description": "Defina as respostas automáticas",
        "action": "Configure palavras-chave e respostas no painel",
        "emoji": "💬",
    },
    {
        "step": 5,
        "title": "Testar",
        "description": "Envie mensagens de teste",
        "action": "Envie uma mensagem para o número conectado e veja a resposta",
        "emoji": "🧪",
    },
    {
        "step": 6,
        "title": "Publicar",
        "description": "Coloque seu bot no ar!",
        "action": "Ative o bot e comece a atender seus clientes",
        "emoji": "🚀",
    },
]


class FloraBrain:
    """
    Flora AI's core brain — handles personality, greetings, help,
    and response generation.
    """

    def __init__(self, intents_file: Optional[str] = None):
        self.personality = PERSONALITY
        self.intents_file = intents_file or str(INTENTS_FILE)
        self.classifier = IntentClassifier(self.intents_file)
        self._intents_data = self._load_intents()
        logger.info("FloraBrain initialized", extra={"intents_file": self.intents_file})

    def _load_intents(self) -> dict:
        """Load intents from JSON file."""
        try:
            with open(self.intents_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load intents: {e}")
            return {"intents": []}

    def greet(self, user_name: str = "", is_returning: bool = False) -> str:
        """
        Generate a greeting message.

        Args:
            user_name: User's name (if known)
            is_returning: Whether the user has interacted before
        """
        hour = datetime.now().hour

        if hour < 12:
            time_greeting = "Bom dia"
        elif hour < 18:
            time_greeting = "Boa tarde"
        else:
            time_greeting = "Boa noite"

        name_part = f", {user_name}" if user_name else ""

        if is_returning:
            greetings = [
                f"Que bom te ver de volta{name_part}! {PERSONALITY['emoji']} Como posso ajudar?",
                f"Oi{name_part}! {PERSONALITY['emoji']} De volta? O que precisa?",
                f"Eae{name_part}! Sentiu minha falta? 😄 O que posso fazer por você?",
            ]
        else:
            greetings = [
                f"{time_greeting}{name_part}! {PERSONALITY['emoji']} Sou a Flora, sua assistente. Como posso ajudar?",
                f"Oi{name_part}! {PERSONALITY['emoji']} Bem-vindo! Sou a Flora, o que você precisa?",
                f"{time_greeting}{name_part}! {PERSONALITY['emoji']} Flora aqui! Me diz o que precisa que eu te ajudo!",
            ]

        return random.choice(greetings)

    def farewell(self, user_name: str = "") -> str:
        """Generate a farewell message."""
        name_part = f", {user_name}" if user_name else ""
        farewells = [
            f"Até mais{name_part}! {PERSONALITY['emoji']} Foi um prazer ajudar!",
            f"Tchau{name_part}! Quando precisar, é só chamar {PERSONALITY['emoji']}",
            f"Falou{name_part}! Estou aqui se precisar 👋",
            f"Valeu{name_part}! Até a próxima! {PERSONALITY['emoji']}",
        ]
        return random.choice(farewells)

    def help(self, topic: str = "general") -> str:
        """
        Generate help content for a specific topic.

        Args:
            topic: Help topic (general, bot_config, whatsapp, plans, onboarding)
        """
        if topic == "general":
            return (
                f"{PERSONALITY['emoji']} *Central de Ajuda - Flora Platform*\n\n"
                "Posso te ajudar com:\n\n"
                "1️⃣ *Criar Bot* — Configure seu chatbot\n"
                "2️⃣ *Conectar WhatsApp* — Vincule seu número\n"
                "3️⃣ *Planos* — Conheça nossos planos\n"
                "4️⃣ *Onboarding* — Guia passo a passo\n"
                "5️⃣ *Suporte* — Resolva problemas\n\n"
                "Digite o número ou me diga o que precisa! 😊"
            )
        elif topic == "bot_config":
            feature = FEATURES["bot_creation"]
            steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(feature["steps"]))
            return (
                f"{PERSONALITY['emoji']} *{feature['title']}*\n\n"
                f"{feature['description']}\n\n"
                f"*Passo a passo:*\n{steps}\n\n"
                "Quer que eu te guie em algum passo específico? 😊"
            )
        elif topic == "whatsapp":
            feature = FEATURES["whatsapp_connection"]
            steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(feature["steps"]))
            return (
                f"{PERSONALITY['emoji']} *{feature['title']}*\n\n"
                f"{feature['description']}\n\n"
                f"*Como conectar:*\n{steps}\n\n"
                "Tendo problemas? Me conta o erro que eu te ajudo! 🔧"
            )
        elif topic == "plans":
            lines = [f"{PERSONALITY['emoji']} *Nossos Planos*\n"]
            for key, plan in PLANS.items():
                features = "\n".join(f"  • {f}" for f in plan["features"])
                lines.append(
                    f"{plan['emoji']} *{plan['name']}* — {plan['price']}\n{features}\n"
                )
            lines.append("Quer detalhes de algum plano? É só pedir! 😊")
            return "\n".join(lines)
        elif topic == "onboarding":
            lines = [f"{PERSONALITY['emoji']} *Guia de Onboarding*\n"]
            for step in ONBOARDING_STEPS:
                lines.append(
                    f"{step['emoji']} *Passo {step['step']}: {step['title']}*\n"
                    f"_{step['description']}_\n"
                    f"  {step['action']}\n"
                )
            lines.append("Por qual passo quer começar? 🚀")
            return "\n".join(lines)
        else:
            return self.help("general")

    def get_plan_info(self, plan_name: str) -> str:
        """Get detailed info about a specific plan."""
        plan_key = plan_name.lower().strip()
        plan = PLANS.get(plan_key)

        if not plan:
            available = ", ".join(p.title() for p in PLANS.keys())
            return (
                f"Não encontrei o plano '{plan_name}'. {PERSONALITY['emoji']}\n\n"
                f"Planos disponíveis: {available}\n"
                "Quer detalhes de qual plano? 😊"
            )

        features = "\n".join(f"  • {f}" for f in plan["features"])
        return (
            f"{plan['emoji']} *Plano {plan['name']}*\n"
            f"💰 {plan['price']}\n\n"
            f"*Recursos:*\n{features}\n\n"
            f"Quer saber mais ou fazer upgrade? {PERSONALITY['emoji']}"
        )

    def classify_and_respond(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """
        Classify the user's intent and generate an appropriate response.

        Args:
            message: User's message text
            context: Optional conversation context

        Returns:
            Flora's response string
        """
        # Classify intent
        intent = self.classifier.classify(message)
        logger.debug(f"Classified intent: {intent}", extra={"message": message[:50]})

        # Get response based on intent
        if intent == IntentType.GREETING:
            user_name = context.user_name if context else ""
            is_returning = context.message_count > 0 if context else False
            return self.greet(user_name, is_returning)

        elif intent == IntentType.FAREWELL:
            user_name = context.user_name if context else ""
            return self.farewell(user_name)

        elif intent == IntentType.HELP:
            return self.help("general")

        elif intent == IntentType.BOT_CONFIG:
            return self.help("bot_config")

        elif intent == IntentType.WHATSAPP_CONNECTION:
            return self.help("whatsapp")

        elif intent == IntentType.PLANS:
            return self.help("plans")

        elif intent == IntentType.ONBOARDING:
            return self.help("onboarding")

        elif intent == IntentType.THANK_YOU:
            return random.choice(QUICK_REPLIES["success"])

        elif intent == IntentType.TECH_SUPPORT:
            return (
                f"Poxa, sinto muito pelo problema! {PERSONALITY['emoji']}\n\n"
                "Me descreve o que está acontecendo:\n"
                "• O que você estava fazendo?\n"
                "• Apareceu alguma mensagem de erro?\n"
                "• Quando começou?\n\n"
                "Vou te ajudar a resolver! 🛠️"
            )

        elif intent == IntentType.ABOUT_FLORA:
            return (
                f"Sou a *Flora*! {PERSONALITY['emoji']}\n\n"
                "Sou a assistente virtual da Flora Platform. "
                "Meu trabalho é te ajudar a:\n"
                "• Criar e configurar bots\n"
                "• Conectar ao WhatsApp\n"
                "• Entender nossos planos\n"
                "• Resolver problemas\n\n"
                "Estou aqui 24/7 para te ajudar! O que precisa? 😊"
            )

        elif intent == IntentType.SUPPORT:
            return (
                f"{PERSONALITY['emoji']} *Canais de Suporte*\n\n"
                "📧 Email: suporte@flora.platform\n"
                "💬 Chat: Disponível no painel admin\n"
                "🕐 Horário: Seg-Sex 9h-18h\n\n"
                "Mas antes, posso tentar te ajudar aqui! O que precisa? 😊"
            )

        elif intent == IntentType.COMPLAINT:
            return (
                f"Poxa, sinto muito que sua experiência não foi boa 😔\n\n"
                f"Me conta o que aconteceu para que eu possa te ajudar a melhorar isso? "
                f"Seu feedback é muito importante! {PERSONALITY['emoji']}"
            )

        elif intent == IntentType.COMPLIMENT:
            return random.choice([
                "Ah, que gentil! Fico muito feliz! 🥰",
                "Obrigada! Isso me motiva a ser cada vez melhor! 💚",
                "Você é um amor! Obrigada pelo elogio! 🌸",
            ])

        elif intent == IntentType.JOKE:
            jokes = [
                "Por que o programador usa óculos? Porque não consegue C! 😂\n\nMas sério, como posso te ajudar? 😄",
                "O que o zero disse para o oito? \"Belo cinto!\" 😂\n\nE aí, melhorou? O que posso fazer? 😊",
                "Por que o WhatsApp foi ao psicólogo? Porque tinha muitas conexões! 😂😂\n\nBrincadeiras à parte, precisa de algo? 🌸",
            ]
            return random.choice(jokes)

        elif intent == IntentType.STATUS:
            return (
                f"{PERSONALITY['emoji']} Para verificar o status do seu bot:\n\n"
                "1. Acesse o painel admin\n"
                "2. Vá em 'Meus Bots'\n"
                "3. Veja o indicador de status\n\n"
                "🟢 Verde = Conectado\n"
                "🔴 Vermelho = Desconectado\n"
                "🟡 Amarelo = Conectando\n\n"
                "Quer ajuda com algo específico? 😊"
            )

        else:
            # Fallback — try to match against intents.json patterns
            return self._match_intent_response(message)

    def _match_intent_response(self, message: str) -> str:
        """Fallback: match message against intents.json patterns."""
        msg_lower = message.lower().strip()

        for intent in self._intents_data.get("intents", []):
            for pattern in intent.get("patterns", []):
                if pattern.lower() in msg_lower:
                    responses = intent.get("responses", [])
                    if responses:
                        return random.choice(responses)

        # Ultimate fallback
        return random.choice(QUICK_REPLIES["not_understood"])

    def get_feature_explanation(self, feature_key: str) -> str:
        """Get explanation for a specific feature."""
        feature = FEATURES.get(feature_key)
        if not feature:
            available = ", ".join(FEATURES.keys())
            return f"Não encontrei '{feature_key}'. Features disponíveis: {available}"

        steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(feature.get("steps", [])))
        return (
            f"{PERSONALITY['emoji']} *{feature['title']}*\n\n"
            f"{feature['description']}\n\n"
            f"*Como funciona:*\n{steps}"
        )

    def get_onboarding_step(self, step_number: int) -> str:
        """Get a specific onboarding step."""
        for step in ONBOARDING_STEPS:
            if step["step"] == step_number:
                return (
                    f"{step['emoji']} *Passo {step['step']}: {step['title']}*\n\n"
                    f"_{step['description']}_\n\n"
                    f"*Ação:* {step['action']}\n\n"
                    f"{'✅ Passo concluído! Parabéns!' if step_number < 6 else '🎉 Onboarding completo!'}\n"
                    f"{'Próximo passo: digite \"próximo\"' if step_number < 6 else ''}"
                )
        return f"Passo {step_number} não encontrado. O onboarding tem {len(ONBOARDING_STEPS)} passos."
