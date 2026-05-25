"""
Flora Platform — Flora AI Engine
=================================
The main Flora AI assistant logic.
Handles personality, context awareness, memory integration,
and multi-turn conversations.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class FloraPersonality:
    """Flora AI personality configuration."""
    name: str = "Flora"
    tone: str = "friendly"  # friendly, professional, casual, formal
    language: str = "pt-BR"
    emoji_usage: bool = True
    max_response_length: int = 2000
    creativity: float = 0.7  # 0.0 = conservative, 1.0 = creative

    # Response style
    use_bullet_points: bool = True
    ask_followup_questions: bool = True
    acknowledge_emotions: bool = True


@dataclass
class FloraMemory:
    """Short-term memory for a Flora conversation."""
    session_id: str
    user_facts: dict = field(default_factory=dict)
    conversation_topics: list = field(default_factory=list)
    last_intent: str = ""
    message_count: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class FloraEngine:
    """
    Flora AI assistant engine.

    Features:
    - Personality-driven responses
    - Context awareness across conversation
    - Memory of user preferences and facts
    - Emotion detection and empathetic responses
    - Multi-language support
    """

    def __init__(
        self,
        llm_router=None,
        personality: Optional[FloraPersonality] = None,
        max_memory_sessions: int = 1000,
    ):
        self._router = llm_router
        self._personality = personality or FloraPersonality()
        self._memories: dict[str, FloraMemory] = {}
        self._max_sessions = max_memory_sessions

        logger.info(f"FloraEngine initialized: name={self._personality.name}")

    async def generate(
        self,
        message: str,
        context: Any = None,
        history: Optional[list[dict]] = None,
    ) -> str:
        """
        Generate a Flora AI response.

        Args:
            message: User's message
            context: Chat context (bot_id, user_id, etc.)
            history: Previous messages in the conversation

        Returns:
            Flora's response string
        """
        start = time.time()

        try:
            session_id = getattr(context, "session_id", "default") if context else "default"
            memory = self._get_memory(session_id)

            # Build system prompt with personality and memory
            system_prompt = self._build_system_prompt(memory, context)

            # Assemble messages
            messages = []
            if history:
                # Use recent history (last 10 messages)
                messages.extend(history[-10:])
            else:
                messages.append({"role": "user", "content": message})

            # Generate response
            if self._router:
                response = await self._router.chat(
                    messages=messages,
                    system=system_prompt,
                    temperature=self._personality.creativity,
                    max_tokens=self._personality.max_response_length,
                )
                result = response.content
            else:
                result = self._fallback_response(message)

            # Update memory
            memory.message_count += 1
            self._extract_facts(message, result, memory)

            elapsed = time.time() - start
            logger.debug(f"Flora response generated in {elapsed:.2f}s")

            return result

        except Exception as e:
            logger.error(f"FloraEngine error: {e}", exc_info=True)
            return self._error_response()

    def _build_system_prompt(self, memory: FloraMemory, context: Any = None) -> str:
        """Build a system prompt incorporating personality and memory."""
        p = self._personality

        prompt_parts = [
            f"Você é {p.name}, uma assistente virtual inteligente e prestativa.",
        ]

        # Tone
        tone_map = {
            "friendly": "Seja amigável, calorosa e acessível.",
            "professional": "Mantenha um tom profissional e objetivo.",
            "casual": "Seja descontraída e use linguagem informal.",
            "formal": "Use linguagem formal e educada.",
        }
        prompt_parts.append(tone_map.get(p.tone, tone_map["friendly"]))

        # Language
        if p.language == "pt-BR":
            prompt_parts.append("Responda sempre em português brasileiro.")
        elif p.language == "en-US":
            prompt_parts.append("Always respond in English.")

        # Emoji
        if p.emoji_usage:
            prompt_parts.append("Use emojis com moderação para tornar a conversa mais expressiva.")

        # Emotion acknowledgment
        if p.acknowledge_emotions:
            prompt_parts.append("Reconheça as emoções do usuário e responda com empatia.")

        # Memory facts
        if memory.user_facts:
            prompt_parts.append("\nSobre o usuário:")
            for key, value in memory.user_facts.items():
                prompt_parts.append(f"- {key}: {value}")

        # Context
        if context:
            if hasattr(context, "user_name") and context.user_name:
                prompt_parts.append(f"\nO usuário se chama {context.user_name}.")
            if hasattr(context, "metadata") and context.metadata.get("bot_name"):
                prompt_parts.append(f"Você está operando como {context.metadata['bot_name']}.")

        # Response guidelines
        prompt_parts.append("\nDiretrizes:")
        prompt_parts.append("- Seja concisa mas completa")
        prompt_parts.append("- Faça perguntas de acompanhamento quando apropriado")
        prompt_parts.append("- Se não souber algo, seja honesta")
        prompt_parts.append("- Nunca invente informações factuais")

        return "\n".join(prompt_parts)

    def _get_memory(self, session_id: str) -> FloraMemory:
        """Get or create memory for a session."""
        if session_id not in self._memories:
            # Evict oldest if at capacity
            if len(self._memories) >= self._max_sessions:
                oldest_key = next(iter(self._memories))
                del self._memories[oldest_key]
                logger.debug(f"Evicted memory session: {oldest_key}")

            self._memories[session_id] = FloraMemory(session_id=session_id)

        return self._memories[session_id]

    def _extract_facts(self, user_message: str, response: str, memory: FloraMemory) -> None:
        """Extract and store user facts from conversation."""
        # Simple keyword-based fact extraction
        import re

        name_match = re.search(
            r"(?:meu nome e|me chamo|sou o|sou a)\s+(\w+)",
            user_message,
            re.IGNORECASE,
        )
        if name_match:
            memory.user_facts["nome"] = name_match.group(1).capitalize()

        # Track topics
        topic_keywords = {
            "agendamento": "agendamento",
            "horario": "agendamento",
            "preco": "precos",
            "valor": "precos",
            "pagamento": "pagamento",
            "suporte": "suporte",
            "problema": "suporte",
            "duvida": "duvidas",
        }

        for keyword, topic in topic_keywords.items():
            if keyword in user_message.lower() and topic not in memory.conversation_topics:
                memory.conversation_topics.append(topic)

    def _fallback_response(self, message: str) -> str:
        """Fallback response when LLM is unavailable."""
        return (
            "Obrigada por sua mensagem! No momento estou com dificuldades "
            "técnicas para processar sua solicitação. Por favor, tente novamente "
            "em alguns instantes."
        )

    def _error_response(self) -> str:
        """Error response."""
        return (
            "Desculpe, ocorreu um erro inesperado. "
            "Por favor, tente novamente."
        )

    def clear_memory(self, session_id: str) -> None:
        """Clear memory for a session."""
        self._memories.pop(session_id, None)
        logger.info(f"Flora memory cleared: {session_id}")

    def get_memory(self, session_id: str) -> Optional[FloraMemory]:
        """Get memory for a session."""
        return self._memories.get(session_id)

    def update_personality(self, **kwargs) -> None:
        """Update Flora's personality settings."""
        for key, value in kwargs.items():
            if hasattr(self._personality, key):
                setattr(self._personality, key, value)
                logger.info(f"Flora personality updated: {key}={value}")

    def get_stats(self) -> dict:
        """Return engine statistics."""
        return {
            "active_sessions": len(self._memories),
            "total_messages": sum(m.message_count for m in self._memories.values()),
            "personality": {
                "name": self._personality.name,
                "tone": self._personality.tone,
                "language": self._personality.language,
            },
        }
