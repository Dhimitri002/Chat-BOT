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
        "oi", "ola", "eae", "eai", "opa", "bom dia", "boa tarde",
        "boa noite", "fala ai", "salve", "hello", "hey", "hi",
        "e ai", "e ae", "oie", "oii", "olá",
    ],
    IntentType.FAREWELL: [
        "tchau", "flw", "falow", "ate mais", "ate logo", "vou sair",
        "bye", "ate breve", "nos vemos", "falou", "valeu", "até",
        "até mais", "até logo",
    ],
    IntentType.HELP: [
        "ajuda", "help", "me ajuda", "me ajude", "socorro", "nao entendi",
        "como funciona", "o que voce faz", "o que fazes", "comandos",
        "menu", "opcoes", "duvida", "duvidas", "como fazer",
        "como usar", "tutorial", "guia", "instrucoes", "manual",
        "nao sei", "preciso de ajuda",
    ],
    IntentType.THANK_YOU: [
        "obrigado", "obrigada", "valeu", "thanks", "thank you",
        "agradeco", "mto obrigado", "muito obrigado", "show",
        "show de bola", "massa", "top", "perfeito", "otimo",
        "excelente", "maravilha", "amei", "adorei", "muito bom",
    ],
    IntentType.BOT_CONFIG: [
        "bot", "robot", "chatbot", "configurar bot", "criar bot",
        "novo bot", "meu bot", "personalidade", "tom do bot",
        "intencoes", "intencao", "respostas", "resposta",
        "configuracao", "configurar", "criar", "ativar bot",
        "desativar bot", "bot nao responde", "bot parado",
        "definir", "personalidade do bot", "nome do bot",
        "idioma do bot", "mensagem de boas vindas",
    ],
    IntentType.WHATSAPP_CONNECTION: [
        "whatsapp", "whats", "wa", "conectar", "conexao", "qr code",
        "qrcode", "escanear", "scan", "celular", "numero",
        "telefone", "desconectou", "caiu", "offline", "reconectar",
        "parear", "pareado", "aparelho", "whatsapp web",
        "multidevice", "multi-device",
    ],
    IntentType.PLANS: [
        "plano", "planos", "preco", "precos", "valor", "valores",
        "quanto custa", "assinatura", "assinar", "upgrade",
        "trocar plano", "mudar plano", "melhor plano",
        "free", "starter", "growth", "pro", "business",
        "enterprise", "custom", "gratis", "gratuito",
        "pago", "premium", "mensalidade", "anual",
        "desconto", "cupom", "promocao", "pix", "cartao",
        "boleto", "pagamento", "pagar",
    ],
    IntentType.ONBOARDING: [
        "onboarding", "comecar", "comeco", "primeiro passo",
        "como comecar", "iniciar", "primeira vez", "novato",
        "novo usuario", "guia", "passo a passo", "tutorial",
        "primeiros passos", "setup", "instalacao", "configuracao inicial",
    ],
    IntentType.TECH_SUPPORT: [
        "erro", "bug", "problema", "falha", "defeito", "nao funciona",
        "quebrou", "travou", "lento", "internet", "conexao",
        "servidor", "offline", "fora do ar", "indisponivel",
        "timeout", "crash", "bugado", "com erro", "com problema",
        "nao conecta", "nao carrega", "tela branca",
    ],
    IntentType.ABOUT_FLORA: [
        "quem e voce", "quem e vc", "o que e flora", "sobre voce",
        "sobre a flora", "sua historia", "seu nome", "seu proposito",
        "para que voce serve", "o que voce e", "inteligencia artificial",
        "ia", "ai", "voce e um bot", "voce e humana", "voce e real",
    ],
    IntentType.SUPPORT: [
        "suporte", "atendimento", "falar com alguem", "humano",
        "pessoa", "atendente", "sac", "reclamacao", "ouvidoria",
        "email", "contato", "telefone", "whatsapp suporte",
    ],
    IntentType.COMPLAINT: [
        "ruim", "pessimo", "horrivel", "detesto", "odeio",
        "insatisfeito", "insatisfeita", "frustrado", "frustrada",
        "raiva", "bravo", "brava", "puto", "irritado", "irritada",
        "nao gostei", "pessimo", "lixo", "merda", "inutil",
        "decepcionado", "decepcionada", "enganado", "enganada",
    ],
    IntentType.COMPLIMENT: [
        "otimo", "excelente", "incrivel", "fantastico", "sensacional",
        "adoro", "amei", "perfeito", "maravilhoso", "maravilhosa",
        "lindo", "linda", "bonito", "bonita", "legal", "bacana",
        "genial", "brilhante", "espetacular", "muito bom",
        "muito bem", "parabens", "trabalho bem feito",
    ],
    IntentType.JOKE: [
        "piada", "rir", "engracado", "humor", "brincadeira",
        "conta uma piada", "me faz rir", "me conta algo engra",
        "risada", "haha", "hehe", "kkkk", "joke",
    ],
    IntentType.STATUS: [
        "status", "funcionando", "online", "offline", "disponivel",
        "indisponivel", "manutencao", "sistema", "plataforma",
        "tudo bem", "tudo certo", "operacional", "estabilidade",
        "saude", "health", "uptime", "downtime",
    ],
}


class IntentClassifier:
    """
    Classifies user messages into intent categories.

    Uses keyword matching with confidence scoring.
    Can be extended with ML-based classification.
    """

    def __init__(self, intents_file: Optional[Path] = None):
        """
        Initialize the classifier.

        Args:
            intents_file: Optional path to intents.json for pattern matching
        """
        self.intents_file = intents_file or Path(__file__).parent / "intents.json"
        self._intents_data: Optional[dict] = None
        self._load_intents()

    def _load_intents(self) -> None:
        """Load intents from JSON file."""
        try:
            if self.intents_file.exists():
                with open(self.intents_file, "r", encoding="utf-8") as f:
                    self._intents_data = json.load(f)
            else:
                self._intents_data = {"intents": []}
                logger.warning("intents.json not found at %s", self.intents_file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load intents: %s", e)
            self._intents_data = {"intents": []}

    def classify(self, message: str) -> IntentType:
        """
        Classify a message into an intent type.

        Args:
            message: User message text

        Returns:
            The detected IntentType
        """
        intent, _ = self.classify_with_confidence(message)
        return intent

    def classify_with_confidence(self, message: str) -> tuple[IntentType, float]:
        """
        Classify a message and return confidence score.

        Args:
            message: User message text

        Returns:
            Tuple of (IntentType, confidence_score)
        """
        if not message or not message.strip():
            return IntentType.UNKNOWN, 0.0

        message_lower = message.strip().lower()

        # Score each intent type
        scores: dict[IntentType, float] = {}

        for intent_type, keywords in INTENT_KEYWORDS.items():
            score = self._calculate_score(message_lower, keywords)
            if score > 0:
                scores[intent_type] = score

        # Also check intents.json patterns
        json_score = self._check_json_intents(message_lower)
        for intent_tag, score in json_score.items():
            mapped = self._map_json_tag(intent_tag)
            if mapped:
                scores[mapped] = max(scores.get(mapped, 0), score)

        if not scores:
            return IntentType.UNKNOWN, 0.0

        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)  # type: ignore
        best_score = scores[best_intent]

        # Normalize confidence to 0-1 range
        confidence = min(best_score / 3.0, 1.0)

        return best_intent, confidence

    def _calculate_score(self, message: str, keywords: list[str]) -> float:
        """
        Calculate match score for a set of keywords.

        Exact phrase matches score higher than partial matches.
        """
        score = 0.0

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Exact phrase match (highest score)
            if keyword_lower in message:
                # Longer matches are more specific — score higher
                score += len(keyword_lower.split()) * 0.5

                # Bonus for exact word boundary match
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, message):
                    score += 0.3

        return score

    def _check_json_intents(self, message: str) -> dict[str, float]:
        """Check message against intents.json patterns."""
        scores: dict[str, float] = {}

        if not self._intents_data:
            return scores

        for intent in self._intents_data.get("intents", []):
            tag = intent.get("tag", "")
            patterns = intent.get("patterns", [])

            for pattern in patterns:
                if pattern.lower() in message:
                    scores[tag] = scores.get(tag, 0) + 1.0

        return scores

    @staticmethod
    def _map_json_tag(tag: str) -> Optional[IntentType]:
        """Map an intents.json tag to an IntentType enum."""
        tag_map = {
            "saudacao": IntentType.GREETING,
            "despedida": IntentType.FAREWELL,
            "agradecimento": IntentType.THANK_YOU,
            "ajuda": IntentType.HELP,
            "bot_config": IntentType.BOT_CONFIG,
            "whatsapp": IntentType.WHATSAPP_CONNECTION,
            "whatsapp_connect": IntentType.WHATSAPP_CONNECTION,
            "whatsapp_status": IntentType.WHATSAPP_CONNECTION,
            "planos": IntentType.PLANS,
            "plan_info": IntentType.PLANS,
            "plan_upgrade": IntentType.PLANS,
            "onboarding": IntentType.ONBOARDING,
            "suporte_tecnico": IntentType.TECH_SUPPORT,
            "tech_support": IntentType.TECH_SUPPORT,
            "sobre_flora": IntentType.ABOUT_FLORA,
            "about_flora": IntentType.ABOUT_FLORA,
            "suporte": IntentType.SUPPORT,
            "reclamacao": IntentType.COMPLAINT,
            "complaint": IntentType.COMPLAINT,
            "elogio": IntentType.COMPLIMENT,
            "compliment": IntentType.COMPLIMENT,
            "piada": IntentType.JOKE,
            "joke": IntentType.JOKE,
            "status": IntentType.STATUS,
            "license_info": IntentType.PLANS,
            "license_validate": IntentType.PLANS,
            "bot_create": IntentType.BOT_CONFIG,
            "intent_create": IntentType.BOT_CONFIG,
            "command_create": IntentType.BOT_CONFIG,
        }
        return tag_map.get(tag)

    def get_all_intents(self) -> list[IntentType]:
        """Return all available intent types."""
        return list(IntentType)

    def reload(self) -> None:
        """Reload intents from JSON file."""
        self._load_intents()
        logger.info("IntentClassifier reloaded with %d intents from JSON",
                     len(self._intents_data.get("intents", [])))
