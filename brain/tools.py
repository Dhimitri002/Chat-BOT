"""
Flora AI — Tool Definitions
=============================
Ferramentas que a Flora AI pode acionar para realizar ações.
Cada ferramenta tem um nome, descrição, parâmetros e handler.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime, timezone


# ── Tool Result ──────────────────────────────────────────────────────────────


@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta."""
    success: bool
    data: Any = None
    message: str = ""
    tool_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def ok(cls, tool_name: str, data: Any = None, message: str = "") -> "ToolResult":
        return cls(success=True, tool_name=tool_name, data=data, message=message)

    @classmethod
    def error(cls, tool_name: str, message: str) -> "ToolResult":
        return cls(success=False, tool_name=tool_name, message=message)


# ── Tool Definitions ─────────────────────────────────────────────────────────


class ToolName(str, Enum):
    """Nomes de todas as ferramentas disponíveis."""
    CHECK_STATUS = "check_status"
    CREATE_BOT = "create_bot"
    CONNECT_WHATSAPP = "connect_whatsapp"
    UPGRADE_PLAN = "upgrade_plan"
    GET_HELP = "get_help"
    ONBOARDING_GUIDE = "onboarding_guide"
    GET_PLAN_INFO = "get_plan_info"
    TROUBLESHOOT = "troubleshoot"


@dataclass
class ToolDefinition:
    """Definição de uma ferramenta."""
    name: ToolName
    description: str
    parameters: dict[str, Any]
    handler: Optional[Callable] = None
    requires_auth: bool = False

    def to_openai_schema(self) -> dict[str, Any]:
        """Converte para formato de função OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name.value,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_openrouter_schema(self) -> dict[str, Any]:
        """Converte para formato de função OpenRouter."""
        return self.to_openai_schema()


# ── Tool Registry ────────────────────────────────────────────────────────────


class ToolRegistry:
    """Registro de todas as ferramentas disponíveis para a Flora."""

    def __init__(self):
        self._tools: dict[ToolName, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Registra todas as ferramentas padrão."""

        # Check Status
        self.register(ToolDefinition(
            name=ToolName.CHECK_STATUS,
            description="Verifica o status da conta do usuário, incluindo plano atual, número de bots, e status de conexão.",
            parameters={
                "type": "object",
                "properties": {
                    "detail_level": {
                        "type": "string",
                        "enum": ["basic", "full"],
                        "description": "Nível de detalhe: 'basic' para resumo, 'full' para detalhes completos",
                    },
                },
                "required": [],
            },
            requires_auth=True,
        ))

        # Create Bot Guide
        self.register(ToolDefinition(
            name=ToolName.CREATE_BOT,
            description="Fornece guia passo a passo para criar um novo bot na plataforma.",
            parameters={
                "type": "object",
                "properties": {
                    "bot_purpose": {
                        "type": "string",
                        "description": "Propósito do bot (ex: atendimento, vendas, suporte)",
                    },
                },
                "required": [],
            },
        ))

        # Connect WhatsApp Guide
        self.register(ToolDefinition(
            name=ToolName.CONNECT_WHATSAPP,
            description="Fornece instruções para conectar o WhatsApp ao bot.",
            parameters={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "ID do bot que deseja conectar (opcional)",
                    },
                },
                "required": [],
            },
        ))

        # Upgrade Plan
        self.register(ToolDefinition(
            name=ToolName.UPGRADE_PLAN,
            description="Mostra informações sobre planos e como fazer upgrade.",
            parameters={
                "type": "object",
                "properties": {
                    "target_plan": {
                        "type": "string",
                        "enum": ["starter", "pro", "business", "premium", "enterprise"],
                        "description": "Plano desejado (opcional)",
                    },
                },
                "required": [],
            },
            requires_auth=True,
        ))

        # Get Help
        self.register(ToolDefinition(
            name=ToolName.GET_HELP,
            description="Retorna ajuda sobre um tópico específico da plataforma.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": [
                            "onboarding", "create_bot", "connect_whatsapp",
                            "billing", "troubleshooting", "upgrade",
                        ],
                        "description": "Tópico de ajuda desejado",
                    },
                },
                "required": ["topic"],
            },
        ))

        # Onboarding Guide
        self.register(ToolDefinition(
            name=ToolName.ONBOARDING_GUIDE,
            description="Retorna os passos do onboarding para o usuário.",
            parameters={
                "type": "object",
                "properties": {
                    "step": {
                        "type": "integer",
                        "description": "Número do passo específico (1-6). Se omitido, retorna todos.",
                    },
                },
                "required": [],
            },
        ))

        # Plan Info
        self.register(ToolDefinition(
            name=ToolName.GET_PLAN_INFO,
            description="Mostra informações detalhadas sobre os planos disponíveis.",
            parameters={
                "type": "object",
                "properties": {
                    "plan_name": {
                        "type": "string",
                        "enum": ["free", "starter", "pro", "business", "premium", "enterprise"],
                        "description": "Nome do plano (opcional). Se omitido, mostra todos.",
                    },
                },
                "required": [],
            },
        ))

        # Troubleshoot
        self.register(ToolDefinition(
            name=ToolName.TROUBLESHOOT,
            description="Ajuda a resolver um problema técnico específico.",
            parameters={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "Descrição do problema enfrentado",
                    },
                },
                "required": ["problem"],
            },
        ))

    def register(self, tool: ToolDefinition):
        """Registra uma nova ferramenta."""
        self._tools[tool.name] = tool

    def get(self, name: ToolName) -> Optional[ToolDefinition]:
        """Obtém uma ferramenta pelo nome."""
        return self._tools.get(name)

    def get_all(self) -> list[ToolDefinition]:
        """Retorna todas as ferramentas registradas."""
        return list(self._tools.values())

    def get_openai_schemas(self) -> list[dict[str, Any]]:
        """Retorna schemas de todas as ferramentas no formato OpenAI."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def get_openrouter_schemas(self) -> list[dict[str, Any]]:
        """Retorna schemas de todas as ferramentas no formato OpenRouter."""
        return [tool.to_openrouter_schema() for tool in self._tools.values()]

    def set_handler(self, name: ToolName, handler: Callable):
        """Define o handler para uma ferramenta."""
        if name in self._tools:
            self._tools[name].handler = handler

    async def execute(self, name: ToolName, params: dict[str, Any] = None) -> ToolResult:
        """Executa uma ferramenta com os parâmetros fornecidos."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult.error(str(name), f"Ferramenta '{name}' não encontrada")

        if tool.handler:
            try:
                result = await tool.handler(params or {})
                return result
            except Exception as e:
                return ToolResult.error(str(name), f"Erro ao executar: {str(e)}")

        return ToolResult.ok(str(name), message=f"Ferramenta '{name}' identificada. Processando...")
