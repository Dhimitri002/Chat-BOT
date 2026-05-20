"""
Flora Platform — Flora AI Service
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.models.flora_session import FloraSession


class FloraService:
    """Service for managing Flora AI chat sessions and context."""

    @staticmethod
    async def create_session(db: AsyncSession, user_id: str) -> FloraSession:
        """Create a new Flora chat session for a user."""
        now = datetime.now(timezone.utc)
        session = FloraSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=f"flora_{uuid.uuid4().hex[:12]}",
            title="Nova conversa",
            messages=[],
            message_count=0,
            tokens_used=0,
            is_active=True,
            last_activity=now,
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> FloraSession:
        """Get a Flora session by its session_id field."""
        result = await db.execute(
            select(FloraSession).where(FloraSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flora session not found",
            )
        return session

    @staticmethod
    async def get_user_sessions(db: AsyncSession, user_id: str, limit: int = 10) -> list[FloraSession]:
        """List the most recent Flora sessions for a user."""
        result = await db.execute(
            select(FloraSession)
            .where(FloraSession.user_id == user_id)
            .where(FloraSession.is_active == True)
            .order_by(FloraSession.last_activity.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
    ) -> FloraSession:
        """Add a message to a Flora session's conversation history."""
        session = await FloraService.get_session(db, session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        messages = list(session.messages)
        messages.append(message)

        session.messages = messages
        session.message_count = len(messages)
        session.last_activity = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_messages(db: AsyncSession, session_id: str, limit: int = 50) -> list[dict]:
        """Get the conversation history for a Flora session, limited to the last N messages."""
        session = await FloraService.get_session(db, session_id)
        messages = list(session.messages)
        return messages[-limit:]

    @staticmethod
    async def close_session(db: AsyncSession, session_id: str) -> FloraSession:
        """Close a Flora session (mark as inactive)."""
        session = await FloraService.get_session(db, session_id)

        session.is_active = False
        session.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    def get_suggestions(context: dict) -> list[str]:
        """
        Return quick suggestion chips based on the current user context.

        Context keys:
            - license_status: str (active, expired, none)
            - bot_status: str (connected, disconnected, none)
            - plan_name: str
            - current_screen: str (dashboard, bots, analytics, billing, settings)
            - has_bots: bool
            - has_active_license: bool
        """
        suggestions = []
        license_status = context.get("license_status", "none")
        bot_status = context.get("bot_status", "none")
        current_screen = context.get("current_screen", "dashboard")
        has_bots = context.get("has_bots", False)
        has_active_license = context.get("has_active_license", False)

        # License-related suggestions
        if license_status == "expired":
            suggestions.append("Renovar licença")
            suggestions.append("Ver planos disponíveis")
        elif license_status == "none":
            suggestions.append("Ativar licença")
            suggestions.append("Iniciar trial grátis")

        # Bot-related suggestions
        if not has_bots:
            suggestions.append("Criar meu primeiro bot")
            suggestions.append("Ver templates de bots")
        elif bot_status == "disconnected":
            suggestions.append("Conectar bot ao WhatsApp")
            suggestions.append("Configurar bot")
        elif bot_status == "connected":
            suggestions.append("Ver métricas do bot")
            suggestions.append("Adicionar intenções")

        # Screen-specific suggestions
        if current_screen == "analytics":
            suggestions.append("Exportar relatório")
            suggestions.append("Ver uso de LLM")
        elif current_screen == "billing":
            suggestions.append("Ver meu plano")
            suggestions.append("Atualizar pagamento")
        elif current_screen == "settings":
            suggestions.append("Configurar notificações")
            suggestions.append("Alterar senha")

        # Always-available suggestions
        if len(suggestions) < 4:
            suggestions.append("Falar com suporte")

        # Deduplicate and limit
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique[:6]

    @staticmethod
    def build_system_prompt(
        user,
        license_obj,
        bot,
        plan,
    ) -> str:
        """
        Build the Flora system prompt with full client context.

        This prompt gives Flora AI awareness of the user's account,
        plan limits, and current state so it can provide contextual help.
        """
        parts = [
            "Você é Flora, assistente inteligente da Flora Platform.",
            "Você ajuda usuários a gerenciar seus chatbots WhatsApp, "
            "configurar intenções, comandos, e entender métricas.",
            "",
            "## Contexto do Cliente:",
            f"- Nome: {user.full_name}",
            f"- Email: {user.email}",
        ]

        # Plan context
        if plan:
            parts.extend([
                f"- Plano atual: {plan.name}",
                f"- Limite de bots: {plan.max_bots}",
                f"- Limite de mensagens/mês: {plan.max_messages_per_month}",
                f"- Limite de intenções: {plan.max_intents}",
                f"- Limite de comandos: {plan.max_commands}",
            ])
            if plan.has_llm:
                parts.append(f"- LLM disponível: {plan.llm_provider} ({plan.llm_model})")
                parts.append(f"- Tokens LLM/dia: {plan.llm_tokens_per_day}")
            if plan.has_flora_ai:
                parts.append("- Acesso à Flora AI: Sim")
            if plan.has_analytics:
                parts.append("- Analytics avançado: Sim")
            if plan.has_api_access:
                parts.append("- Acesso à API: Sim")

        # License context
        if license_obj:
            parts.extend([
                "",
                "## Licença:",
                f"- Status: {license_obj.status}",
            ])
            if hasattr(license_obj, 'days_remaining'):
                parts.append(f"- Dias restantes: {license_obj.days_remaining}")
            if hasattr(license_obj, 'expires_at') and license_obj.expires_at:
                parts.append(f"- Expira em: {license_obj.expires_at.strftime('%d/%m/%Y')}")

        # Bot context
        if bot:
            parts.extend([
                "",
                "## Bot Atual:",
                f"- Nome: {bot.name}",
                f"- Status: {bot.status}",
                f"- Modelo LLM: {bot.llm_model or 'Não configurado'}",
                f"- Provedor LLM: {bot.llm_provider or 'Não configurado'}",
            ])

        parts.extend([
            "",
            "## Instruções:",
            "- Seja objetiva, amigável e use português brasileiro.",
            "- Se o usuário pedir ajuda com configuração, guie passo a passo.",
            "- Se o usuário estiver com problemas de conexão, sugira verificar o QR code.",
            "- Se o usuário perguntar sobre limites, consulte o contexto do plano acima.",
            "- Se não souber algo, sugira falar com o suporte humano.",
        ])

        return "\n".join(parts)
