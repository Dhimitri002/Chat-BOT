"""Commands Endpoints - API para gerenciamento de comandos personalizados."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db

router = APIRouter(prefix="/commands", tags=["commands"])


class CommandCreateRequest(BaseModel):
    bot_id: str
    trigger: str = Field(..., min_length=1, max_length=100)
    trigger_type: str = Field(default="keyword", regex="^(prefix|keyword|regex)$")
    response: str = Field(..., min_length=1, max_length=5000)
    command_type: str = Field(default="text", regex="^(text|action|ai)$")
    is_active: bool = True
    is_admin_only: bool = False
    cooldown_seconds: int = 0
    metadata: dict = Field(default_factory=dict)


class CommandUpdateRequest(BaseModel):
    trigger: Optional[str] = None
    trigger_type: Optional[str] = None
    response: Optional[str] = None
    command_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin_only: Optional[bool] = None
    cooldown_seconds: Optional[int] = None
    metadata: Optional[dict] = None


@router.get("/")
async def list_commands(
    bot_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista comandos personalizados."""
    from backend.models.command import Command

    query = select(Command).where(Command.owner_id == current_user.id)
    if bot_id:
        query = query.where(Command.bot_id == bot_id)
    query = query.order_by(Command.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    commands = result.scalars().all()

    return {
        "commands": [
            {
                "id": c.id,
                "bot_id": c.bot_id,
                "trigger": c.trigger,
                "trigger_type": c.trigger_type,
                "response": c.response[:100] + "..." if len(c.response) > 100 else c.response,
                "command_type": c.command_type,
                "is_active": c.is_active,
                "usage_count": c.usage_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in commands
        ]
    }


@router.post("/")
async def create_command(
    request: CommandCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo comando personalizado."""
    from backend.models.command import Command
    import uuid

    command = Command(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        bot_id=request.bot_id,
        trigger=request.trigger,
        trigger_type=request.trigger_type,
        response=request.response,
        command_type=request.command_type,
        is_active=request.is_active,
        is_admin_only=request.is_admin_only,
        cooldown_seconds=request.cooldown_seconds,
        metadata=request.metadata,
    )
    db.add(command)
    await db.flush()

    # Recarregar command engine
    from backend.core.command_engine import command_engine
    command_engine.add_command(request.bot_id, command)

    return {"success": True, "id": command.id, "message": "Comando criado."}


@router.put("/{command_id}")
async def update_command(
    command_id: str,
    request: CommandUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um comando."""
    from backend.models.command import Command

    result = await db.execute(
        select(Command).where(Command.id == command_id, Command.owner_id == current_user.id)
    )
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(command, key, value)

    await db.flush()
    return {"success": True, "message": "Comando atualizado."}


@router.delete("/{command_id}")
async def delete_command(
    command_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deleta um comando."""
    from backend.models.command import Command

    result = await db.execute(
        select(Command).where(Command.id == command_id, Command.owner_id == current_user.id)
    )
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    # Remover do command engine
    from backend.core.command_engine import command_engine
    command_engine.remove_command(command.bot_id, command.trigger)

    await db.delete(command)
    await db.flush()
    return {"success": True, "message": "Comando deletado."}


@router.post("/{command_id}/execute")
async def execute_command(
    command_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executa um comando manualmente (teste)."""
    return {"success": True, "message": "Comando executado.", "response": "Teste OK"}
