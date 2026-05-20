"""
Flora AI Engine - Motor de inteligência artificial da plataforma.
Gerencia conversas com LLMs, contexto, personalidade e custos.
"""
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm_router import llm_router
from backend.models.bot import Bot
from backend.models.flora_session import FloraSession
from backend.models.llm_usage import LLMUsage


class ConversationContext:
    """Gerencia o contexto de uma conversa."""

    def __init__(self, max_messages: int = 20):
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.metadata: dict = {}

    def add_message(self, role: str, content: str):
        """Adiciona uma mensagem ao contexto."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Manter apenas as N mensagens mais recentes
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_messages(self) -> list[dict]:
        """Retorna mensagens no formato para LLM."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self):
        """Limpa o contexto."""
        self.messages = []
        self.metadata = {}


class FloraEngine:
    """Motor de IA Flora para conversas inteligentes."""

    def __init__(self):
        self._contexts: dict[str, ConversationContext] = {}  # session_id -> context

    def _get_context(self, session_id: str) -> ConversationContext:
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext()
        return self._contexts[session_id]

    async def chat(
        self,
        db: AsyncSession,
        bot_id: str,
        user_message: str,
        session_id: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> dict:
        """
        Processa uma mensagem e gera resposta via LLM.
        Retorna dict com resposta, metadados e informações de uso.
        """
        start_time = time.time()

        # Buscar configuração do bot
        bot_result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = bot_result.scalar_one_or_none()

        if not bot:
            return {
                "response": "Bot não encontrado.",
                "source": "error",
                "error": "bot_not_found",
            }

        # Gerenciar sessão
        if not session_id:
            session_id = str(uuid.uuid4())

        flora_session = await self._get_or_create_session(db, session_id, bot_id, sender)
        context = self._get_context(session_id)

        # Adicionar mensagem do usuário ao contexto
        context.add_message("user", user_message)

        # Construir prompt do sistema
        system_prompt = self._build_system_prompt(bot)

        # Preparar mensagens para o LLM
        messages = [{"role": "system", "content": system_prompt}] + context.get_messages()

        # Configurações do LLM
        llm_config = {
            "model": bot.preferred_llm or "gpt-4o-mini",
            "temperature": bot.temperature or 0.7,
            "max_tokens": bot.max_tokens or 1024,
        }

        # Tentar LLM primário, com fallback
        response_text = None
        llm_used = None
        error = None

        try:
            result = await llm_router.chat(
                messages=messages,
                **llm_config,
            )
            response_text = result["response"]
            llm_used = result.get("model", llm_config["model"])

        except Exception as primary_error:
            error = str(primary_error)
            logger.warning(f"LLM primário falhou: {primary_error}. Tentando fallback...")

            # Tentar fallback
            try:
                fallback_model = llm_router.get_fallback_model(llm_config["model"])
                if fallback_model:
                    result = await llm_router.chat(
                        messages=messages,
                        model=fallback_model,
                        temperature=llm_config["temperature"],
                        max_tokens=llm_config["max_tokens"],
                    )
                    response_text = result["response"]
                    llm_used = fallback_model
                    logger.info(f"Fallback bem-sucedido com {fallback_model}")
            except Exception as fallback_error:
                logger.error(f"Fallback também falhou: {fallback_error}")
                response_text = self._get_fallback_response(bot)
                llm_used = "fallback"

        # Adicionar resposta ao contexto
        if response_text:
            context.add_message("assistant", response_text)

        # Calcular tempo de resposta
        response_time_ms = int((time.time() - start_time) * 1000)

        # Registrar uso do LLM
        await self._log_usage(
            db=db,
            bot_id=bot_id,
            session_id=session_id,
            model=llm_used or "unknown",
            user_message=user_message,
            assistant_response=response_text or "",
            response_time_ms=response_time_ms,
            error=error,
        )

        # Atualizar sessão
        flora_session.message_count += 1
        flora_session.last_activity_at = datetime.now(timezone.utc)
        await db.flush()

        return {
            "response": response_text or self._get_fallback_response(bot),
            "source": "llm" if llm_used and llm_used != "fallback" else "fallback",
            "session_id": session_id,
            "model_used": llm_used,
            "response_time_ms": response_time_ms,
            "bot_name": bot.name,
        }

    def _build_system_prompt(self, bot: Bot) -> str:
        """Constrói o prompt do sistema baseado na configuração do bot."""
        parts = []

        # Identidade do bot
        parts.append(f"Você é {bot.name}, um assistente virtual inteligente.")

        # Personalidade
        if bot.personality:
            parts.append(f"Sua personalidade é: {bot.personality}.")

        # Tom
        if bot.tone:
            parts.append(f"Seu tom de comunicação é: {bot.tone}.")

        # Prompt personalizado
        if bot.prompt:
            parts.append(f"\n{bot.prompt}")

        # Idioma
        language = bot.language or "pt-BR"
        lang_map = {
            "pt-BR": "português brasileiro",
            "pt-PT": "português de Portugal",
            "en": "english",
            "es": "español",
        }
        lang_name = lang_map.get(language, language)
        parts.append(f"\nResponda sempre em {lang_name}.")

        # Regras de comportamento
        parts.append("\nRegras importantes:")
        parts.append("- Seja conciso e objetivo nas respostas.")
        parts.append("- Não invente informações que você não tem.")
        parts.append("- Se não souber algo, seja honesto sobre isso.")
        parts.append("- Mantenha o contexto da conversa.")
        parts.append("- Use emojis com moderação para tornar a conversa mais amigável.")

        return "\n".join(parts)

    def _get_fallback_response(self, bot: Bot) -> str:
        """Resposta de fallback quando o LLM falha."""
        fallbacks = [
            f"Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes.",
            f"Oops! Parece que meu sistema está temporariamente indisponível. Tente novamente em breve.",
            f"No momento não consigo processar sua mensagem. Por favor, aguarde um momento e tente novamente.",
        ]
        import random
        return random.choice(fallbacks)

    async def _get_or_create_session(
        self,
        db: AsyncSession,
        session_id: str,
        bot_id: str,
        sender: Optional[str],
    ) -> FloraSession:
        """Busca ou cria uma sessão Flora."""
        result = await db.execute(
            select(FloraSession).where(FloraSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = FloraSession(
                id=session_id,
                bot_id=bot_id,
                sender=sender or "anonymous",
                status="active",
            )
            db.add(session)
            await db.flush()

        return session

    async def _log_usage(
        self,
        db: AsyncSession,
        bot_id: str,
        session_id: str,
        model: str,
        user_message: str,
        assistant_response: str,
        response_time_ms: int,
        error: Optional[str],
    ):
        """Registra uso do LLM para analytics e billing."""
        # Estimar tokens (aproximação: 1 token ≈ 4 caracteres)
        prompt_tokens = len(user_message) // 4
        completion_tokens = len(assistant_response) // 4

        usage = LLMUsage(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            session_id=session_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            response_time_ms=response_time_ms,
            status="error" if error else "success",
            error_message=error,
        )
        db.add(usage)

    async def reset_session(self, session_id: str):
        """Reseta o contexto de uma sessão."""
        if session_id in self._contexts:
            self._contexts[session_id].clear()

    async def delete_session(self, session_id: str):
        """Remove uma sessão completamente."""
        self._contexts.pop(session_id, None)


# Singleton
flora_engine = FloraEngine()
