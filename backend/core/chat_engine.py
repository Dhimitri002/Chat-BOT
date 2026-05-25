"""
Flora Platform — Chat Engine
=============================
Processes incoming chat messages through the pipeline:
1. Pre-processing (sanitize, detect language)
2. Intent detection
3. Context assembly (memory, bot config)
4. LLM request
5. Post-processing (format, filter)
6. Response delivery
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from backend.core.llm_router import LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    """Context for a chat interaction."""
    bot_id: str
    user_id: str
    user_name: str = ""
    user_phone: str = ""
    session_id: str = ""
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    language: str = "pt-BR"


@dataclass
class ChatResult:
    """Result of chat processing."""
    response: str
    success: bool = True
    error: str = ""
    llm_response: Optional[LLMResponse] = None
    intent: str = ""
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ChatEngine:
    """
    Main chat processing pipeline.

    Handles:
    - Message pre-processing
    - Context assembly
    - LLM routing
    - Response post-processing
    - Error handling
    """

    def __init__(
        self,
        llm_router=None,
        command_engine=None,
        flora_engine=None,
        max_history: int = 20,
        default_language: str = "pt-BR",
    ):
        self._router = llm_router
        self._commands = command_engine
        self._flora = flora_engine
        self._max_history = max_history
        self._default_language = default_language
        self._sessions: dict[str, list[dict]] = {}

        logger.info("ChatEngine initialized")

    async def process_message(
        self,
        message: str,
        context: ChatContext,
    ) -> ChatResult:
        """
        Process an incoming message through the full pipeline.

        Pipeline:
        1. Pre-process message
        2. Check for commands
        3. Assemble context (history + bot config)
        4. Send to LLM
        5. Post-process response
        6. Return result
        """
        start = time.time()

        try:
            # Step 1: Pre-process
            clean_message = self._preprocess(message)
            if not clean_message:
                return ChatResult(
                    response="Desculpe, não entendi sua mensagem. Pode reformular?",
                    success=True,
                    processing_time_ms=(time.time() - start) * 1000,
                )

            # Step 2: Check for commands
            if self._commands and self._is_command(clean_message):
                cmd_result = await self._commands.execute(clean_message, context)
                if cmd_result:
                    return ChatResult(
                        response=cmd_result,
                        success=True,
                        intent="command",
                        confidence=1.0,
                        processing_time_ms=(time.time() - start) * 1000,
                    )

            # Step 3: Assemble context
            history = self._get_history(context.session_id)
            history.append({"role": "user", "content": clean_message})

            # Step 4: Send to LLM
            if self._router:
                llm_response = await self._router.chat(
                    messages=history,
                    system=self._build_system_prompt(context),
                    temperature=0.7,
                    max_tokens=2048,
                )
                response_text = llm_response.content
            elif self._flora:
                llm_response = await self._flora.generate(
                    message=clean_message,
                    context=context,
                    history=history,
                )
                response_text = llm_response
            else:
                response_text = "Desculpe, o assistente não está disponível no momento."

            # Step 5: Post-process
            response_text = self._postprocess(response_text, context)

            # Update history
            history.append({"role": "assistant", "content": response_text})
            self._trim_history(context.session_id, history)

            elapsed = (time.time() - start) * 1000

            return ChatResult(
                response=response_text,
                success=True,
                llm_response=llm_response if isinstance(llm_response, LLMResponse) else None,
                processing_time_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"ChatEngine error: {e}", exc_info=True)
            return ChatResult(
                response="Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                success=False,
                error=str(e),
                processing_time_ms=elapsed,
            )

    def _preprocess(self, message: str) -> str:
        """Clean and normalize incoming message."""
        if not message:
            return ""

        # Strip whitespace
        message = message.strip()

        # Remove excessive whitespace
        import re
        message = re.sub(r"\s+", " ", message)

        # Basic sanitization
        if len(message) > 4000:
            message = message[:4000]
            logger.warning("Message truncated to 4000 chars")

        return message

    def _postprocess(self, response: str, context: ChatContext) -> str:
        """Clean and format the response."""
        if not response:
            return "Desculpe, não consegui gerar uma resposta."

        response = response.strip()

        # Remove common LLM artifacts
        if response.startswith("Assistant:"):
            response = response[len("Assistant:"):].strip()
        if response.startswith("Bot:"):
            response = response[len("Bot:"):].strip()

        return response

    def _is_command(self, message: str) -> bool:
        """Check if message is a bot command."""
        return message.startswith("/") or message.startswith("!")

    def _build_system_prompt(self, context: ChatContext) -> str:
        """Build the system prompt from bot config and context."""
        base_prompt = (
            f"Você é um assistente virtual inteligente. "
            f"Responda de forma clara, útil e amigável em português brasileiro."
        )

        if context.user_name:
            base_prompt += f" O usuário se chama {context.user_name}."

        if context.metadata.get("bot_name"):
            base_prompt += f" Você é o {context.metadata['bot_name']}."

        if context.metadata.get("system_prompt"):
            base_prompt = context.metadata["system_prompt"]

        return base_prompt

    def _get_history(self, session_id: str) -> list[dict]:
        """Get message history for a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def _trim_history(self, session_id: str, history: list[dict]) -> None:
        """Trim history to max length."""
        if len(history) > self._max_history * 2:
            # Keep system message if present, trim the rest
            system_msgs = [m for m in history if m.get("role") == "system"]
            other_msgs = [m for m in history if m.get("role") != "system"]
            history[:] = system_msgs + other_msgs[-self._max_history * 2:]
        self._sessions[session_id] = history

    def clear_session(self, session_id: str) -> None:
        """Clear a chat session."""
        self._sessions.pop(session_id, None)
        logger.info(f"Session cleared: {session_id}")

    def get_session_count(self) -> int:
        """Return number of active sessions."""
        return len(self._sessions)
