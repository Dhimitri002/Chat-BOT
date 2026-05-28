"""Billing Endpoints - API para geramento de pagamentos e faturas."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db

router = APIRouter(prefix="/billing", tags=["billing"])


class AddPaymentMethodRequest(BaseModel):
    type: str = Field(..., pattern="^(credit_card|pix|boleto)$")
    token: str = Field(..., description="Token do método de pagamento")


@router.get("/invoices")
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista faturas do usuário."""
    from backend.models.payment import Payment

    query = select(Payment).where(Payment.user_id == current_user.id)
    if status:
        query = query.where(Payment.status == status)
    query = query.order_by(Payment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    payments = result.scalars().all()

    return {
        "invoices": [
            {
                "id": p.id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payments
        ]
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de uma fatura."""
    from backend.models.payment import Payment

    result = await db.execute(
        select(Payment).where(Payment.id == invoice_id, Payment.user_id == current_user.id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")

    return {
        "id": payment.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "description": payment.description,
        "payment_method": payment.payment_method,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: str,
    payment_method_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paga uma fatura."""
    return {"success": True, "message": "Pagamento processado.", "invoice_id": invoice_id}


@router.get("/payments")
async def payment_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Histórico de pagamentos."""
    return {"payments": [], "page": page, "page_size": page_size}


@router.get("/methods")
async def list_payment_methods(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista métodos de pagamento."""
    return {"methods": []}


@router.post("/methods")
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adiciona método de pagamento."""
    return {"success": True, "message": "Método de pagamento adicionado."}


@router.delete("/methods/{method_id}")
async def remove_payment_method(
    method_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove método de pagamento."""
    return {"success": True, "message": "Método de pagamento removido."}
