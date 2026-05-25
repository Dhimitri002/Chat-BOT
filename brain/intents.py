"""
Intent Classification System — Flora Platform
=============================================
Classifies user messages into intent categories using
pattern matching and keyword analysis.

Intent Types:
    GREETING, FAREWELL, HELP, THANK_YOU, BOT_CONFIG,
    WHATSAPP_CONNECTION, PLANS, ONBOARDING, TECH_SUPPORT,
    ABOUT_FLORA, SUPPORT, COMPLAINT, COMPLIMENT, JOKE,
    STATUS, UNKNOWN
"""

from __future__ import annotations

import json
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Enumeration of all supported intent types."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    HELP = "help"
    THANK_YOU = "thank_you"
    BOT_CONFIG = "bot_config"
    WHATSAPP_CONNECTION = "whatsapp_connection"
    PLANS = "plans"
    ONBOARDING = "onboarding"
    TECH_SUPPORT = "tech_support"
    ABOUT_FLORA = "about_flora"
    SUPPORT = "support"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    JOKE = "joke"
    STATUS = "status"
    UNKNOWN = "unknown"


# ─── Keyword Patterns for Classification ───────────────────────────────

INTENT_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.GREETING: [
        "oi", "olá", "ola", "eae", "eai", "opa", "bom dia", "boa tarde",
        "boa noite", "fala aí", "fala ai", "salve", "hello", "hey", "hi",
        "bom dia", "boa noite", "e aí", "e ai",
    ],
    IntentType.FAREWELL: [
        "tchau", "flw", "falow", "até mais", "ate mais", "até logo",
        "ate logo", "vou sair", "bye", "até breve", "nos vemos", "falou",
    ],
    IntentType.HELP: [
        "ajuda", "help", "me ajuda", "me ajude", "socorro", "não entendi",
        "nao entendi", "como funciona", "o que você faz", "o que voce faz",
        "comandos", "menu", "opções", "opcoes", "o que fazer",
    ],
    IntentType.THANK_YOU: [
        "obrigado", "obrigada", "valeu", "thanks", "thank you", "agradeço",
        "agradeco", "mto obrigado", "muito obrigado", "show", "massa",
        "top", "perfeito",
    ],
    IntentType.BOT_CONFIG: [
        "configurar bot", "criar bot", "novo bot", "configuração",
        "configuracao", "setup", "iniciar bot", "bot não funciona",
        "bot parou", "meu bot", "configurar", "bot config",
    ],
    IntentType.WHATSAPP_CONNECTION: [
        "conectar whatsapp", "qr code", "qrcode", "escanear",
        "whatsapp não conecta", "nao conecta", "conexão falhou",
        "conexao falhou", "problema whatsapp", "whatsapp erro",
        "desconectou", "caiu whatsapp", "whatsapp",
    ],
    IntentType.PLANS: [
        "planos", "preços", "precos", "preço", "preco", "quanto custa",
        "assinatura", "plano gratuito", "plano pago", "upgrade",
        "plano free", "plano pro", "plano enterprise", "valores",
    ],
    IntentType.ONBOARDING: [
        "começar", "comecar", "iniciar", "primeiro uso", "primeira vez",
        "como começar", "como comecar", "tutorial", "guia", "passo a passo",
        "novo usuário", "novo usuario",
    ],
    IntentType.TECH_SUPPORT: [
        "erro", "bug", "não funciona", "nao funciona", "quebrou", "falha",
        "travou", "lento", "fora do ar", "indisponível", "indisponivel",
        "manutenção", "manutencao", "reportar",
    ],
    IntentType.ABOUT_FLORA: [
        "quem é você", "quem e voce", "seu nome", "como você se chama",
        "como voce se chama", "o que é flora", "o que e flora", "flora",
        "assistente", "robô", "robo",
    ],
    IntentType.SUPPORT: [
        "suporte", "atendimento", "falar com humano", "falar com pessoa",
        "chat suporte", "email suporte", "contato", "telefone",
        "whatsapp suporte",
    ],
    IntentType.COMPLAINT: [
        "ruim", "péssimo", "pessimo", "horrível", "horrivel", "odeio",
        "não gostei", "nao gostei", "insatisfeito", "frustrado",
        "decepcionado", "lixo", "inútil", "inutil",
    ],
    IntentType.COMPLIMENT: [
        "muito bom", "excelente", "incrível", "incrivel", "maravilhoso",
        "ótimo", "otimo", "fantástico", "fantastico", "amei", "adoro",
        "sensacional", "top demais", "muito bem",
    ],
    IntentType.JOKE: [
        "piada", "engraçado", "engraçada", "rir", "humor",
        "me faz rir", "conta uma piada", "tô triste", "to triste", "me anima",
    ],
    IntentType.STATUS: [
        "status", "conectado", "online", "funcionando", "bot ativo",
        "bot online", "verificar status", "tudo bem", "tudo certo",
        "como está", "como esta",
    ],
}


class IntentClassifier:
    """
    Classifies user messages into intent categories.

    Uses a combination of:
    1. Keyword matching (primary)
    2. Pattern matching from intents.json (fallback)
    3. Confidence scoring

    Usage:
        classifier = IntentClassifier()
        intent = classifier.classify("Oi, como vai?")
        # Returns: IntentType.GREETING
    """

    def __init__(self, intents_file: Optional[str] = None):
        self._intents_file = intents_file
        self._intents_data: dict = {}
        self._keyword_patterns: dict[IntentType, list[re.Pattern]] = {}

        self._compile_keywords()

        if intents_file:
            self._load_intents(intents_file)

    def _compile_keywords(self) -> None:
        """Pre-compile keyword patterns for faster matching."""
        for intent_type, keywords in INTENT_KEYWORDS.items():
            patterns = []
            for kw in keywords:
                # Use word boundary matching for short keywords
                if len(kw) <= 3:
                    pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
                else:
                    pattern = re.compile(re.escape(kw), re.IGNORECASE)
                patterns.append(pattern)
            self._keyword_patterns[intent_type] = patterns

    def _load_intents(self, filepath: str) -> None:
        """Load intents from JSON file for fallback matching."""
        try:
            path = Path(filepath)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._intents_data = json.load(f)
                logger.debug(f"Loaded intents from {filepath}")
            else:
                logger.warning(f"Intents file not found: {filepath}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load intents: {e}")

    def classify(self, message: str) -> IntentType:
        """
        Classify a message into an intent type.

        Args:
            message: User's message text

        Returns:
            IntentType enum value
        """
        if not message or not message.strip():
            return IntentType.UNKNOWN

        message_lower = message.lower().strip()

        # 1. Try keyword matching with confidence scoring
        scores: dict[IntentType, float] = {}

        for intent_type, patterns in self._keyword_patterns.items():
            score = 0.0
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    # Longer matches get higher scores
                    match_len = match.end() - match.start()
                    score += match_len / max(len(message_lower), 1)

            if score > 0:
                scores[intent_type] = score

        if scores:
            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]

            # Require minimum confidence
            if best_score > 0.01:
                logger.debug(
                    f"Classified as {best_intent.value} (score: {best_score:.3f})",
                    extra={"message": message[:50]}
                )
                return best_intent

        # 2. Fallback: match against intents.json patterns
        json_intent = self._match_json_intents(message_lower)
        if json_intent:
            return json_intent

        return IntentType.UNKNOWN

    def _match_json_intents(self, message_lower: str) -> Optional[IntentType]:
        """Match against intents.json patterns as fallback."""
        if not self._intents_data:
            return None

        tag_to_intent = {
            "saudacao": IntentType.GREETING,
            "despedida": IntentType.FAREWELL,
            "agradecimento": IntentType.THANK_YOU,
            "ajuda": IntentType.HELP,
            "bot_config": IntentType.BOT_CONFIG,
            "whatsapp_conexao": IntentType.WHATSAPP_CONNECTION,
            "planos": IntentType.PLANS,
            "onboarding": IntentType.ONBOARDING,
            "problema_tecnico": IntentType.TECH_SUPPORT,
            "personalidade": IntentType.ABOUT_FLORA,
            "suporte": IntentType.SUPPORT,
            "elogio": IntentType.COMPLIMENT,
            "reclamacao": IntentType.COMPLAINT,
            "piada": IntentType.JOKE,
            "status_conexao": IntentType.STATUS,
        }

        for intent in self._intents_data.get("intents", []):
            tag = intent.get("tag", "")
            for pattern in intent.get("patterns", []):
                if pattern.lower() in message_lower:
                    return tag_to_intent.get(tag)

        return None

    def classify_with_confidence(self, message: str) -> tuple[IntentType, float]:
        """
        Classify a message and return confidence score.

        Returns:
            (IntentType, confidence) tuple where confidence is 0.0-1.0
        """
        if not message or not message.strip():
            return IntentType.UNKNOWN, 0.0

        message_lower = message.lower().strip()
        scores: dict[IntentType, float] = {}

        for intent_type, patterns in self._keyword_patterns.items():
            score = 0.0
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    match_len = match.end() - match.start()
                    score += match_len / max(len(message_lower), 1)
            if score > 0:
                scores[intent_type] = score

        if scores:
            best_intent = max(scores, key=scores.get)
            best_score = min(scores[best_intent] * 5, 1.0)  # Normalize to 0-1
            return best_intent, best_score

        return IntentType.UNKNOWN, 0.0
