"""
Flora AI Service
=================
Servico principal da Flora AI — integra o brain da Flora com o LLM Router
para fornecer respostas inteligentes e contextuais.

Responsabilidades:
  - Gerenciar sessoes de conversa (criar, carregar, persistir)
  - Integrar FloraBrain com LLMRouter para respostas via LLM
  - Fornecer fallback inteligente quando LLM nao esta disponivel
  - Expor endpoints para chat, historico, onboarding e ajuda
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from brain.flora import FloraBrain, PLANS, ONBOARDING_STEPS, PERSONALITY
from brain.prompts import (
    FLORA_SYSTEM_PROMPT,
    WELCOME_MESSAGE,
    RETURNING_WELCOME,
    HELP_CONTENT,
    ONBOARDING_STEPS as ONBOARDING_PROMPTS,
    PromptManager,
)
from brain.intents import IntentClassifier, IntentType
from brain.context import ConversationContext, ContextManager

logger = logging.getLogger(__name__)

# Try to import LLMRouter — service works without it (rule-based fallback)
try:
    from backend.core.llm_router import LLMRouter, LLMError
    from backend.config import settings
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    logger.warning("LLM Router not available — Flora will use rule-based responses only")


class FloraService:
    """
    Servico da Flora AI.

    Gerencia o ciclo completo de conversa:
    1. Recebe mensagem do usuario
    2. Carrega/cria contexto da sessao
    3. Classifica intencao
    4. Gera resposta via LLM (com fallback)
    5. Persiste contexto atualizado
    """

    def __init__(self):
        self.brain = FloraBrain()
        self.classifier = IntentClassifier()
        self.prompt_manager = PromptManager()
        self.context_manager = ContextManager()

        # Initialize LLM router if available
        self.llm_router: Optional[Any] = None
        if _LLM_AVAILABLE:
            try:
                self.llm_router = LLMRouter(
                    provider=getattr(settings, "LLM_PROVIDER", "groq"),
                )
                logger.info("FloraService: LLM Router initialized")
            except Exception as e:
                logger.warning(f"FloraService: LLM Router init failed: {e}")

    def _get_or_create_context(
        self,
        session_id: Optional[str],
        user_id: str,
        user_name: str = "",
        user_plan: str = "free",
    ) -> tuple[ConversationContext, bool]:
        """
        Obtem ou cria um contexto de conversa.

        Returns:
            (context, is_new) — o contexto e se e uma sessao nova
        """
        if session_id:
            existing = self.context_manager.get(session_id)
            if existing:
                return existing, False

        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        ctx = self.context_manager.get_or_create(
            session_id=new_session_id,
            user_id=user_id,
            user_name=user_name,
            user_plan=user_plan,
        )
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
        Processa uma mensagem do usuario e retorna a resposta da Flora.

        Args:
            message: Mensagem do usuario
            session_id: ID da sessao (opcional, cria nova se nao existir)
            user_id: ID do usuario
            user_name: Nome do usuario (para personalizacao)
            user_plan: Plano do usuario (determina provedores LLM disponiveis)

        Returns:
            dict com response, session_id, intent, tools_used, etc.
        """
        if not message or not message.strip():
            return {
                "response": "Ola! Nao recebi sua mensagem. Pode tentar novamente? " + PERSONALITY["emoji"],
                "session_id": session_id or "",
                "intent": "unknown",
                "confidence": 0.0,
                "tools_used": [],
                "is_new_session": False,
                "message_count": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # 1. Get or create context
        ctx, is_new = self._get_or_create_context(
            session_id, user_id, user_name, user_plan
        )

        # 2. Classify intent
        intent_type, confidence = self.classifier.classify_with_confidence(message)
        ctx.last_intent = intent_type.value

        # 3. Add user message to context
        ctx.add_message(
            role="user",
            content=message,
            metadata={"intent": intent_type.value, "confidence": confidence},
        )

        # 4. Generate response
        response_text = await self._generate_response(
            ctx, message, intent_type, confidence, user_name, user_plan
        )

        # 5. Add assistant response to context
        ctx.add_message(
            role="assistant",
            content=response_text,
            metadata={"intent": intent_type.value},
        )

        return {
            "response": response_text,
            "session_id": ctx.session_id,
            "intent": intent_type.value,
            "confidence": confidence,
            "tools_used": [],
            "is_new_session": is_new,
            "message_count": ctx.message_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_response(
        self,
        ctx: ConversationContext,
        message: str,
        intent_type: IntentType,
        confidence: float,
        user_name: str,
        user_plan: str,
    ) -> str:
        """Generates response using LLM or fallback."""

        # Try LLM first if available and confidence is not high enough for rule-based
        if self.llm_router:
            try:
                llm_response = await self._call_llm(ctx, user_plan)
                if llm_response and llm_response.strip():
                    return llm_response
            except Exception as e:
                logger.warning(f"LLM call failed, using fallback: {e}")

        # Fallback: rule-based response via FloraBrain
        return self._fallback_response(intent_type, confidence, message, ctx)

    async def _call_llm(self, ctx: ConversationContext, user_plan: str) -> str:
        """Calls the LLM via LLMRouter."""
        context_messages = ctx.get_recent_context(n=10)

        if not context_messages:
            return ""

        # Build system prompt with user context
        system_prompt = FLORA_SYSTEM_PROMPT
        if ctx.user_name:
            system_prompt += f"\n\n## Usuario Atual\nNome: {ctx.user_name}"
        if ctx.user_plan:
            system_prompt += f"\nPlano: {ctx.user_plan}"

        messages = [{"role": "system", "content": system_prompt}] + context_messages

        result = await self.llm_router.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        content = result.content if hasattr(result, 'content') else result.get("content", "")
        tokens = result.total_tokens if hasattr(result, 'total_tokens') else result.get("usage", {}).get("total_tokens", 0)
        ctx.metadata["total_tokens"] = ctx.metadata.get("total_tokens", 0) + tokens

        return content

    def _fallback_response(
        self,
        intent_type: IntentType,
        confidence: float,
        message: str,
        ctx: ConversationContext,
    ) -> str:
        """Generates rule-based fallback response via FloraBrain."""
        user_name = ctx.user_name

        # If confidence is high enough, use FloraBrain's classify_and_respond
        if confidence > 0.05:
            return self.brain.classify_and_respond(message, ctx)

        # Very low confidence — use brain's fallback
        return self.brain._match_intent_response(message)

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """
        Retorna o historico de uma sessao.

        Args:
            session_id: ID da sessao

        Returns:
            Lista de mensagens com role, content e timestamp
        """
        ctx = self.context_manager.get(session_id)
        if not ctx:
            return []

        return [msg.to_dict() for msg in ctx.history]

    def clear_history(self, session_id: str) -> bool:
        """
        Limpa o historico de uma sessao (keeps session, clears messages).

        Args:
            session_id: ID da sessao

        Returns:
            True se a sessao foi encontrada e limpa
        """
        ctx = self.context_manager.get(session_id)
        if not ctx:
            return False

        # Clear messages but keep session
        ctx._history.clear()
        ctx.message_count = 0
        ctx.last_activity = datetime.now(timezone.utc).isoformat()
        return True

    def delete_session(self, session_id: str) -> bool:
        """Remove completamente uma sessao."""
        return self.context_manager.delete(session_id)

    def get_onboarding_steps(self) -> list[dict[str, Any]]:
        """Retorna os passos do onboarding."""
        return ONBOARDING_STEPS

    def get_onboarding_step(self, step_number: int) -> Optional[dict[str, Any]]:
        """Retorna um passo especifico do onboarding com conteudo completo."""
        if 1 <= step_number <= 6:
            step_data = ONBOARDING_PROMPTS.get(step_number, {})
            return {
                "step": step_number,
                "title": step_data.get("title", ""),
                "content": step_data.get("prompt", ""),
                "emoji": ONBOARDING_STEPS[step_number - 1]["emoji"],
                "next_hint": step_data.get("next_hint"),
                "is_last_step": step_number == 6,
            }
        return None

    def get_help_topic(self, topic: str) -> Optional[dict[str, Any]]:
        """
        Retorna conteudo de ajuda para um topico especifico.

        Args:
            topic: Nome do topico (general, bot_creation, whatsapp_connection, plans, onboarding)

        Returns:
            dict com title, content e related topics
        """
        content = HELP_CONTENT.get(topic)
        if not content:
            return None

        # Determine title from topic
        topic_titles = {
            "general": "Central de Ajuda",
            "bot_creation": "Criacao de Bot",
            "whatsapp_connection": "Conexao WhatsApp",
            "plans": "Planos",
            "onboarding": "Guia de Onboarding",
        }

        related_map = {
            "general": ["bot_creation", "whatsapp_connection", "plans", "onboarding"],
            "bot_creation": ["general", "whatsapp_connection"],
            "whatsapp_connection": ["general", "bot_creation"],
            "plans": ["general", "onboarding"],
            "onboarding": ["general", "bot_creation", "whatsapp_connection"],
        }

        return {
            "topic": topic,
            "title": topic_titles.get(topic, topic),
            "content": content,
            "related": related_map.get(topic, []),
        }

    def get_all_help_topics(self) -> dict[str, dict[str, Any]]:
        """Retorna todos os topicos de ajuda disponiveis."""
        result = {}
        for topic_key in HELP_CONTENT:
            topic_data = self.get_help_topic(topic_key)
            if topic_data:
                result[topic_key] = topic_data
        return result

    def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retorna informacoes sobre uma sessao."""
        ctx = self.context_manager.get(session_id)
        if not ctx:
            return None

        return {
            "session_id": ctx.session_id,
            "user_id": ctx.user_id,
            "user_name": ctx.user_name,
            "user_plan": ctx.user_plan,
            "message_count": ctx.message_count,
            "total_tokens": ctx.metadata.get("total_tokens", 0),
            "is_onboarding": ctx.is_onboarding,
            "onboarding_step": ctx.onboarding_step,
            "last_intent": ctx.last_intent,
            "created_at": ctx.created_at,
            "updated_at": ctx.last_activity,
            "is_expired": ctx.is_expired,
        }

    def get_suggestions(self, session_id: Optional[str] = None) -> list[str]:
        """
        Retorna sugestoes contextuais para o usuario.
        Baseado no estado atual da conversa.
        """
        if session_id:
            ctx = self.context_manager.get(session_id)
            if ctx:
                intent = ctx.last_intent

                suggestions_map = {
                    "onboarding": [
                        "Como criar meu primeiro bot?",
                        "Como conectar o WhatsApp?",
                        "Quais planos estao disponiveis?",
                    ],
                    "bot_config": [
                        "Como definir a personalidade do bot?",
                        "Como adicionar intencoes?",
                        "Como ativar meu bot?",
                    ],
                    "whatsapp_connection": [
                        "Como escanear o QR Code?",
                        "Meu WhatsApp desconectou, o que fazer?",
                        "Posso conectar mais de um numero?",
                    ],
                    "plans": [
                        "Qual o melhor plano para mim?",
                        "Como fazer upgrade?",
                        "Voces aceitam Pix?",
                    ],
                    "tech_support": [
                        "Bot nao esta respondendo",
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


# ─── Singleton ─────────────────────────────────────────────────────────

_flora_service: Optional[FloraService] = None


def get_flora_service() -> FloraService:
    """Retorna a instancia singleton do FloraService."""
    global _flora_service
    if _flora_service is None:
        _flora_service = FloraService()
    return _flora_service
