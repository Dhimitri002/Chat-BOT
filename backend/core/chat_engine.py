"""Chat Engine - Motor de chat que roteia entre comandos e LLM."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.command_engine import CommandEngine
from backend.core.flora_engine import FloraEngine
from backend.core.llm_router import LLMRouter
from backend.models.bot import Bot
from backend.models.message import Message


class ChatEngine:
    """Motor de chat principal. Roteia mensagens entre comandos e LLM."""

    def __init__(self, db: AsyncSession, bot: Bot):
        self.db = db
        self.bot = bot
        self.llm_router = LLMRouter()
        self.flora_engine = FloraEngine(db, bot, self.llm_router)
        self.command_engine = CommandEngine(db, bot)

    async def process_message(
        self, message: str, session_id: Optional[str] = None
    ) -> dict:
        """
        Processa uma mensagem e retorna a resposta.

        Fluxo:
        1. Tenta匹配 comando personalizado
        2. Se não for comando, tenta匹配 intent
        3. Se não for intent, usa Flora AI (LLM)

        Args:
            message: Texto da mensagem
            session_id: ID da sessão de chat

        Returns:
            dict com content, type, session_id, metadata
        """
        # Criar session_id se não existir
        if not session_id:
            session_id = str(uuid.uuid4())

        # 1. Tentar comando personalizado
        command_result = await self.command_engine.parse_and_execute(message)
        if command_result:
            response_content = command_result.get("response", "")
            await self._save_message(session_id, message, "inbound")
            await self._save_message(session_id, response_content, "outbound", {
                "type": "command",
                "command": command_result.get("command_name"),
            })
            return {
                "content": response_content,
                "type": "command",
                "session_id": session_id,
                "metadata": command_result,
            }

        # 2. Tentar intent matching
        intent_result = await self._match_intent(message)
        if intent_result:
            response_content = intent_result.get("response", "")
            await self._save_message(session_id, message, "inbound")
            await self._save_message(session_id, response_content, "outbound", {
                "type": "intent",
                "intent": intent_result.get("intent_name"),
                "confidence": intent_result.get("confidence", 0),
            })
            return {
                "content": response_content,
                "type": "intent",
                "session_id": session_id,
                "metadata": intent_result,
            }

        # 3. Usar Flora AI (LLM)
        flora_result = await self.flora_engine.chat(message, session_id)
        await self._save_message(session_id, message, "inbound")
        await self._save_message(session_id, flora_result["content"], "outbound", {
            "type": "llm",
            "model": flora_result.get("model"),
            "provider": flora_result.get("provider"),
            "usage": flora_result.get("usage"),
        })

        return {
            "content": flora_result["content"],
            "type": "llm",
            "session_id": session_id,
            "metadata": {
                "model": flora_result.get("model"),
                "provider": flora_result.get("provider"),
                "usage": flora_result.get("usage"),
            },
        }

    async def _match_intent(self, message: str) -> Optional[dict]:
        """Tenta匹配 a mensagem com um intent treinado."""
        from backend.models.intent import Intent

        result = await self.db.execute(
            select(Intent).where(
                Intent.bot_id == self.bot.id,
                Intent.is_active == True,
            )
        )
        intents = result.scalars().all()

        message_lower = message.lower().strip()
        best_match = None
        best_score = 0.0

        for intent in intents:
            training_phrases = intent.training_phrases or []
            if isinstance(training_phrases, str):
                try:
                    training_phrases = json.loads(training_phrases)
                except Exception:
                    training_phrases = []

            for phrase in training_phrases:
                phrase_lower = phrase.lower().strip()
                # Matching simples: contém ou similar
                if phrase_lower in message_lower or message_lower in phrase_lower:
                    score = len(phrase_lower) / max(len(message_lower), 1)
                    if score > best_score and score > 0.5:
                        best_score = score
                        best_match = intent

        if best_match:
            responses = best_match.responses or []
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except Exception:
                    responses = []

            import random
            response = random.choice(responses) if responses else "Entendi!"

            return {
                "intent_name": best_match.name,
                "confidence": best_score,
                "response": response,
            }

        return None

    async def _save_message(
        self, session_id: str, content: str, direction: str, metadata: Optional[dict] = None
    ) -> Message:
        """Salva mensagem no banco de dados."""
        msg = Message(
            bot_id=self.bot.id,
            session_id=session_id,
            content=content,
            direction=direction,
            message_type="text",
            metadata=metadata or {},
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg


import json  # noqa: E402
