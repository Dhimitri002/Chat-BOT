"""Webhook Service - Serviço de webhooks para notificações de eventos."""
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiohttp
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.webhook import Webhook


# Tipos de eventos suportados
WEBHOOK_EVENTS = [
    "bot.created",
    "bot.updated",
    "bot.deleted",
    "bot.connected",
    "bot.disconnected",
    "message.received",
    "message.sent",
    "message.failed",
    "license.created",
    "license.expired",
    "license.revoked",
    "payment.received",
    "payment.failed",
    "user.registered",
    "user.suspended",
    "support_ticket.created",
    "support_ticket.updated",
]


class WebhookService:
    """Serviço de envio e recebimento de webhooks."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._max_retries = 3
        self._retry_delays = [5, 30, 300]  # segundos

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Content-Type": "application/json"},
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Gera assinatura HMAC do payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def trigger_event(
        self,
        db: AsyncSession,
        event_type: str,
        data: dict[str, Any],
        owner_id: Optional[str] = None,
    ):
        """
        Dispara um evento para todos os webhooks registrados que escutam esse evento.
        """
        if event_type not in WEBHOOK_EVENTS:
            logger.warning(f"Evento de webhook desconhecido: {event_type}")
            return

        # Buscar webhooks que escutam esse evento
        query = select(Webhook).where(
            Webhook.is_active == True,
        )
        if owner_id:
            query = query.where(Webhook.owner_id == owner_id)

        result = await db.execute(query)
        webhooks = result.scalars().all()

        # Filtrar webhooks que escutam esse evento
        matching = [w for w in webhooks if event_type in (w.events or [])]

        if not matching:
            return

        # Preparar payload
        payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        payload_json = json.dumps(payload, default=str)

        # Enviar para cada webhook
        for webhook in matching:
            await self._send_webhook(webhook, payload_json, event_type)

    async def _send_webhook(
        self,
        webhook: Webhook,
        payload_json: str,
        event_type: str,
    ):
        """Envia webhook com retry."""
        headers = {
            "Content-Type": "application/json",
            "X-Flora-Event": event_type,
            "X-Flora-Timestamp": str(int(time.time())),
        }

        # Adicionar assinatura se tiver secret
        if webhook.secret:
            signature = self._sign_payload(payload_json, webhook.secret)
            headers["X-Flora-Signature"] = f"sha256={signature}"

        session = await self._get_session()

        for attempt in range(self._max_retries):
            try:
                async with session.post(
                    webhook.url,
                    data=payload_json,
                    headers=headers,
                ) as response:
                    if response.status < 400:
                        logger.info(
                            f"Webhook enviado: {event_type} -> {webhook.url} "
                            f"(status: {response.status})"
                        )
                        return
                    else:
                        logger.warning(
                            f"Webhook falhou: {event_type} -> {webhook.url} "
                            f"(status: {response.status})"
                        )
            except Exception as e:
                logger.error(
                    f"Erro ao enviar webhook: {event_type} -> {webhook.url} "
                    f"(tentativa {attempt + 1}): {e}"
                )

            if attempt < self._max_retries - 1:
                await asyncio.sleep(self._retry_delays[attempt])

        logger.error(f"Webhook falhou após {self._max_retries} tentativas: {webhook.url}")

    async def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """Verifica a assinatura de um webhook recebido."""
        expected = self._sign_payload(payload, secret)
        return hmac.compare_digest(f"sha256={expected}", signature)


# Import asyncio at module level
import asyncio

# Singleton
webhook_service = WebhookService()
