"""Flora Engine - Motor de conversa da Flora AI com LLMs reais."""
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm_router import LLMRouter
from backend.models.bot import Bot
from backend.models.flora_session import FloraSession
from backend.models.memory import Memory


class FloraEngine:
    """Motor de conversa da Flora AI."""

    def __init__(self, db: AsyncSession, bot: Bot, llm_router: Optional[LLMRouter] = None):
        self.db = db
        self.bot = bot
        self.llm_router = llm_router or LLMRouter()

    def _get_system_prompt(self) -> str:
        """Constrói o system prompt baseado na personalidade do bot."""
        personality = self.bot.personality or "amigável e prestativa"
        bot_name = self.bot.name or "Flora"

        return f"""Você é {bot_name}, uma assistente virtual {personality}.

Regras importantes:
- Seja concisa e direta nas respostas
- Use linguagem natural e amigável
- Se não souber algo, seja honesta e sugira alternativas
- Não invente informações
- Responda sempre em português brasileiro
- Use emojis com moderação para tornar a conversa mais agradável
- Se o usuário pedir algo fora do seu escopo, redirecione educadamente

Personalidade: {personality}"""

    async def _get_or_create_session(self, session_id: Optional[str] = None) -> FloraSession:
        """Obtém ou cria uma sessão de conversa."""
        if session_id:
            result = await self.db.execute(
                select(FloraSession).where(FloraSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        # Criar nova sessão
        new_session = FloraSession(
            id=str(uuid.uuid4()),
            bot_id=self.bot.id,
            session_data={},
            context={"message_count": 0},
            is_active=True,
        )
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session

    async def _get_memory(self, session_id: str) -> list[dict]:
        """Recupera histórico de conversa formatado para LLM."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.session_id == session_id)
            .order_by(Memory.created_at.asc())
            .limit(20)  # Últimas 20 mensagens
        )
        memories = result.scalars().all()

        messages = []
        for mem in memories:
            role = "user" if mem.memory_type == "user" else "assistant"
            messages.append({"role": role, "content": mem.content})

        return messages

    async def _save_to_memory(self, session_id: str, role: str, content: str):
        """Salva mensagem na memória da conversa."""
        memory = Memory(
            bot_id=self.bot.id,
            session_id=session_id,
            content=content,
            memory_type="user" if role == "user" else "assistant",
        )
        self.db.add(memory)
        await self.db.commit()

    def _build_context(self, session_id: str, message: str, history: list[dict]) -> list[dict]:
        """Constrói o contexto completo para a LLM."""
        messages = [{"role": "system", "content": self._get_system_prompt()}]

        # Adicionar histórico
        messages.extend(history)

        # Adicionar mensagem atual
        messages.append({"role": "user", "content": message})

        return messages

    async def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        Processa mensagem e retorna resposta da Flora AI.

        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (opcional, cria nova se não existir)

        Returns:
            dict com content, session_id, model, provider, usage
        """
        # Obter ou criar sessão
        session = await self._get_or_create_session(session_id)
        sid = str(session.id)

        # Recuperar histórico
        history = await self._get_memory(sid)

        # Salvar mensagem do usuário
        await self._save_to_memory(sid, "user", message)

        # Construir contexto
        messages = self._build_context(sid, message, history)

        # Determinar plano (padrão starter se não houver)
        plan = "starter"
        if self.bot.config and isinstance(self.bot.config, dict):
            plan = self.bot.config.get("plan", "starter")

        # Chamar LLM
        try:
            result = await self.llm_router.chat(messages, plan=plan)
        except ValueError as e:
            # Rate limit ou sem provedores
            result = {
                "content": f"Desculpe, estou temporariamente indisponível. {str(e)}",
                "model": "error",
                "provider": "none",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        except Exception as e:
            result = {
                "content": "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                "model": "error",
                "provider": "none",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }

        # Salvar resposta
        await self._save_to_memory(sid, "assistant", result["content"])

        # Atualizar sessão
        if session.context is None:
            session.context = {}
        session.context["message_count"] = session.context.get("message_count", 0) + 1
        session.updated_at = datetime.utcnow()
        await self.db.commit()

        return {
            "content": result["content"],
            "session_id": sid,
            "model": result.get("model", "unknown"),
            "provider": result.get("provider", "unknown"),
            "usage": result.get("usage", {}),
        }

    async def chat_stream(
        self, message: str, session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streaming de resposta da Flora AI.

        Args:
            message: Mensagem do usuário
            session_id: ID da sessão

        Yields:
            Chunks da resposta
        """
        # Obter ou criar sessão
        session = await self._get_or_create_session(session_id)
        sid = str(session.id)

        # Recuperar histórico
        history = await self._get_memory(sid)

        # Salvar mensagem do usuário
        await self._save_to_memory(sid, "user", message)

        # Construir contexto
        messages = self._build_context(sid, message, history)

        # Determinar plano
        plan = "starter"
        if self.bot.config and isinstance(self.bot.config, dict):
            plan = self.bot.config.get("plan", "starter")

        # Chamar LLM com streaming
        full_response = ""
        try:
            async for chunk in self.llm_router.chat_stream(messages, plan=plan):
                full_response += chunk
                yield chunk
        except Exception as e:
            error_msg = "Desculpe, ocorreu um erro ao processar sua mensagem."
            yield error_msg
            full_response = error_msg

        # Salvar resposta completa
        await self._save_to_memory(sid, "assistant", full_response)

        # Atualizar sessão
        if session.context is None:
            session.context = {}
        session.context["message_count"] = session.context.get("message_count", 0) + 1
        session.updated_at = datetime.utcnow()
        await self.db.commit()

    async def clear_memory(self, session_id: str):
        """Limpa a memória de uma sessão."""
        await self.db.execute(
            Memory.__table__.delete().where(Memory.session_id == session_id)
        )
        await self.db.commit()
