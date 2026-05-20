"""Support Ticket Service - Serviço de tickets de suporte."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.support_ticket import SupportTicket


class SupportService:
    """Serviço de gerenciamento de tickets de suporte."""

    async def create_ticket(
        self,
        db: AsyncSession,
        user_id: str,
        subject: str,
        description: str,
        priority: str = "medium",
        category: str = "general",
    ) -> SupportTicket:
        """Cria um novo ticket de suporte."""
        ticket = SupportTicket(
            id=str(uuid4()),
            user_id=user_id,
            subject=subject,
            description=description,
            priority=priority,
            category=category,
            status="open",
        )
        db.add(ticket)
        await db.flush()

        logger.info(f"Ticket criado: {ticket.id} - {subject}")
        return ticket

    async def get_ticket(
        self, db: AsyncSession, ticket_id: str
    ) -> Optional[SupportTicket]:
        """Obtém um ticket pelo ID."""
        result = await db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def update_ticket(
        self,
        db: AsyncSession,
        ticket_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> Optional[SupportTicket]:
        """Atualiza um ticket."""
        ticket = await self.get_ticket(db, ticket_id)
        if not ticket:
            return None

        if status:
            ticket.status = status
            if status in ("resolved", "closed"):
                ticket.resolved_at = datetime.now(timezone.utc)
        if assigned_to:
            ticket.assigned_to = assigned_to
        if priority:
            ticket.priority = priority
        if resolution:
            ticket.resolution = resolution

        ticket.updated_at = datetime.now(timezone.utc)
        await db.flush()

        logger.info(f"Ticket atualizado: {ticket_id}")
        return ticket

    async def add_comment(
        self,
        db: AsyncSession,
        ticket_id: str,
        user_id: str,
        comment: str,
        is_internal: bool = False,
    ) -> dict:
        """Adiciona um comentário ao ticket."""
        ticket = await self.get_ticket(db, ticket_id)
        if not ticket:
            return {"success": False, "error": "Ticket não encontrado"}

        comments = ticket.comments or []
        comments.append({
            "id": str(uuid4()),
            "user_id": user_id,
            "comment": comment,
            "is_internal": is_internal,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        ticket.comments = comments
        ticket.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return {"success": True, "comment_id": comments[-1]["id"]}

    async def list_tickets(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Lista tickets com filtros."""
        query = select(SupportTicket)

        if user_id:
            query = query.where(SupportTicket.user_id == user_id)
        if status:
            query = query.where(SupportTicket.status == status)
        if priority:
            query = query.where(SupportTicket.priority == priority)

        # Total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        # Paginação
        query = query.order_by(SupportTicket.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tickets = result.scalars().all()

        return {
            "tickets": [
                {
                    "id": t.id,
                    "subject": t.subject,
                    "status": t.status,
                    "priority": t.priority,
                    "category": t.category,
                    "user_id": t.user_id,
                    "assigned_to": t.assigned_to,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in tickets
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_stats(self, db: AsyncSession) -> dict:
        """Obtém estatísticas de tickets."""
        total = (await db.execute(select(func.count(SupportTicket.id)))).scalar()
        open_count = (await db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "open")
        )).scalar()
        resolved_count = (await db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "resolved")
        )).scalar()

        return {
            "total": total,
            "open": open_count,
            "resolved": resolved_count,
            "resolution_rate": round(resolved_count / total * 100, 1) if total > 0 else 0,
        }


# Singleton
support_service = SupportService()
