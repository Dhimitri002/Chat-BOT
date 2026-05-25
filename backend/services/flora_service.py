"""
Flora AI Service
=================
Serviço principal da Flora AI — integra o brain da Flora com o LLM Router
para fornecer respostas inteligentes e contextuais.

Responsabilidades:
  - Gerenciar sessões de conversa (criar, carregar, persistir)
  - Integrar FloraBrain com LLMRouter para respostas via LLM
  - Fornecer fallback inteligente quando LLM não está disponível
  - Expor endpoints para chat, histórico, onboarding e ajuda
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime, timezone

from backend.core.llm_router import LLMRouter
from backend.config import settings

from brain.flora import FloraBrain
from brain.prompts import (
    get_system_prompt,
    get_welcome_message,
    get_help_content,
    ONBOARDING_STEPS,
    HELP_TOPICS,
)
from brain.intents import IntentClassifier, Intent
from brain.context import ConversationContext

logger = logging.getLogger(__name__)


class FloraService:
    """
    Serviço da Flora AI.

    Gerencia o ciclo completo de conversa:
    1. Recebe mensagem do usuário
    2. Carrega/cria contexto da sessão
    3. Classifica intenção
    4. Gera resposta via LLM (com fallback)
    5. Persiste contexto atualizado
    """

    def __init__(self):
        self.llm_router = LLMRouter(
            provider=getattr(settings, "LLM_PROVIDER", "groq"),
        )
        self.classifier = IntentClassifier()
        self._sessions: dict[str, ConversationContext] = {}

    def _get_or_create_context(
        self,
        session_id: Optional[str],
        user_id: str,
        user_name: str = "",
        user_plan: str = "free",
    ) -> tuple[ConversationContext, bool]:
        """
        Obtém ou cria um contexto de conversa.

        Returns:
            (context, is_new) — o contexto e se é uma sessão nova
        """
        if session_id and session_id in self._sessions:
            return self._sessions[session_id], False

        ctx = ConversationContext(
            system_prompt=get_system_prompt(user_name),
            user_name=user_name,
            user_plan=user_plan,
        )
        self._sessions[ctx.session_id] = ctx
        return ctx, True

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
        user_name: str = "",
        user_plan: str = "free",
    ) -> dict[str, Any]:
        """
        Processa uma mensagem do usuário e retorna a resposta da Flora.

        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (opcional, cria nova se não existir)
            user_id: ID do usuário
            user_name: Nome do usuário (para personalização)
            user_plan: Plano do usuário (determina provedores LLM disponíveis)

        Returns:
            dict com response, session_id, intent, tools_used, etc.
        """
        if not message or not message.strip():
            return {
                "response": "🌸 Olá! Não recebi sua mensagem. Pode tentar novamente?",
                "session_id": session_id or "",
                "intent": "unknown",
                "confidence": 0.0,
                "tools_used": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # 1. Obter ou criar contexto
        ctx, is_new = self._get_or_create_context(
            session_id, user_id, user_name, user_plan
        )

        # 2. Classificar intenção
        intent_result = self.classifier.classify_with_fallback(message)
        ctx.update_state(last_intent=intent_result.intent.value)

        # 3. Adicionar mensagem do usuário
        ctx.add_user_message(
            message,
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
        )

        # 4. Gerar resposta
        response_text = await self._generate_response(
            ctx, message, intent_result, user_plan
        )

        # 5. Adicionar resposta ao contexto
        ctx.add_assistant_message(
            response_text,
            intent=intent_result.intent.value,
        )

        return {
            "response": response_text,
            "session_id": ctx.session_id,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "tools_used": [],
            "is_new_session": is_new,
            "message_count": ctx.total_user_messages,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_response(
        self,
        ctx: ConversationContext,
        message: str,
        intent_result,
        user_plan: str,
    ) -> str:
        """Gera resposta usando LLM ou fallback."""

        # Tentar via LLM primeiro
        try:
            llm_response = await self._call_llm(ctx, user_plan)
            if llm_response and llm_response.strip():
                return llm_response
        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {e}")

        # Fallback: resposta baseada em intenção
        return self._fallback_response(intent_result, message, ctx.state.user_name)

    async def _call_llm(self, ctx: ConversationContext, user_plan: str) -> str:
        """Chama o LLM via LLMRouter."""
        messages = ctx.get_messages_for_llm()

        if not messages:
            return ""

        result = await self.llm_router.chat(
            messages=messages,
            plan=user_plan,
            temperature=0.7,
            max_tokens=1024,
        )

        content = result.get("content", "")
        tokens = result.get("usage", {}).get("total_tokens", 0)
        ctx.total_tokens += tokens

        return content

    def _fallback_response(
        self,
        intent_result,
        message: str,
        user_name: str = "",
    ) -> str:
        """Gera resposta fallback baseada na intenção."""
        name = user_name or "amigo(a)"

        # Greetings
        if intent_result.intent == Intent.GREETINGS:
            return get_welcome_message(name)

        # Farewell
        if intent_result.intent == Intent.FAREWELL:
            return (
                f"Foi um prazer conversar com você, {name}! 😊 "
                f"Se precisar de qualquer coisa, é só me chamar. "
                f"Tenha um ótimo dia! 🌸"
            )

        # Unknown
        if intent_result.intent == Intent.UNKNOWN:
            return (
                f"🤔 Hmm, não entendi muito bem o que você quis dizer.\n\n"
                f"Posso te ajudar com:\n"
                f"- 🤖 **Criar bots** — Como criar e configurar\n"
                f"- 📱 **WhatsApp** — Como conectar\n"
                f"- 💳 **Planos** — Preços e upgrade\n"
                f"- 🔧 **Suporte** — Resolver problemas\n\n"
                f"O que você precisa, {name}?"
            )

        # Mapear intenção para tópico de ajuda
        help_topic_map = {
            Intent.ONBOARDING: "onboarding",
            Intent.BOT_CONFIG: "create_bot",
            Intent.WHATSAPP: "connect_whatsapp",
            Intent.BILLING: "billing",
            Intent.TECHNICAL: "troubleshooting",
            Intent.HELP: "onboarding",
            Intent.GENERAL: "onboarding",
        }

        topic = help_topic_map.get(intent_result.intent)
        if topic:
            help_content = get_help_content(topic)
            return f"**{help_content['title']}**\n\n{help_content['content']}"

        return (
            f"🌸 Obrigada por sua mensagem, {name}! "
            f"Estou aqui para te ajudar com a Flora Platform. "
            f"Pode me perguntar sobre bots, WhatsApp, planos ou qualquer dúvida!"
        )

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """
        Retorna o histórico de uma sessão.

        Args:
            session_id: ID da sessão

        Returns:
            Lista de mensagens com role, content e timestamp
        """
        if session_id not in self._sessions:
            return []

        ctx = self._sessions[session_id]
        return ctx.get_recent_history()

    def clear_history(self, session_id: str) -> bool:
        """
        Limpa o histórico de uma sessão.

        Args:
            session_id: ID da sessão

        Returns:
            True se a sessão foi encontrada e limpa, False caso contrário
        """
        if session_id not in self._sessions:
            return False

        self._sessions[session_id].clear_history()
        return True

    def delete_session(self, session_id: str) -> bool:
        """Remove completamente uma sessão."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def get_onboarding_steps(self) -> list[dict[str, Any]]:
        """Retorna os passos do onboarding."""
        return ONBOARDING_STEPS

    def get_help_topic(self, topic: str) -> dict[str, Any]:
        """
        Retorna conteúdo de ajuda para um tópico específico.

        Args:
            topic: Nome do tópico (onboarding, create_bot, connect_whatsapp, etc.)

        Returns:
            dict com title, content e related topics
        """
        return get_help_content(topic)

    def get_all_help_topics(self) -> dict[str, dict[str, Any]]:
        """Retorna todos os tópicos de ajuda disponíveis."""
        return HELP_TOPICS

    def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retorna informações sobre uma sessão."""
        if session_id not in self._sessions:
            return None

        ctx = self._sessions[session_id]
        return {
            "session_id": ctx.session_id,
            "message_count": ctx.total_user_messages,
            "total_tokens": ctx.total_tokens,
            "state": ctx.state.to_dict(),
            "created_at": ctx.created_at,
            "updated_at": ctx.updated_at,
        }

    def get_suggestions(self, session_id: Optional[str] = None) -> list[str]:
        """
        Retorna sugestões contextuais para o usuário.
        Baseado no estado atual da conversa.
        """
        if session_id and session_id in self._sessions:
            ctx = self._sessions[session_id]
            intent = ctx.state.last_intent

            suggestions_map = {
                "onboarding": [
                    "Como criar meu primeiro bot?",
                    "Como conectar o WhatsApp?",
                    "Quais planos estão disponíveis?",
                ],
                "bot_config": [
                    "Como definir a personalidade do bot?",
                    "Como adicionar intenções?",
                    "Como ativar meu bot?",
                ],
                "whatsapp": [
                    "Como escanear o QR Code?",
                    "Meu WhatsApp desconectou, o que fazer?",
                    "Posso conectar mais de um número?",
                ],
                "billing": [
                    "Qual o melhor plano para mim?",
                    "Como fazer upgrade?",
                    "Vocês aceitam Pix?",
                ],
                "technical": [
                    "Bot não está respondendo",
                    "Erro ao conectar WhatsApp",
                    "Como ver logs do bot?",
                ],
            }

            return suggestions_map.get(intent, self._default_suggestions())

        return self._default_suggestions()

    @staticmethod
    def _default_suggestions() -> list[str]:
        return [
            "Como criar um bot?",
            "Ver meus planos",
            "Conectar WhatsApp",
            "Ver tutorial",
        ]


# ── Singleton ────────────────────────────────────────────────────────────────

_flora_service: Optional[FloraService] = None


def get_flora_service() -> FloraService:
    """Retorna a instância singleton do FloraService."""
    global _flora_service
    if _flora_service is None:
        _flora_service = FloraService()
    return _flora_service
