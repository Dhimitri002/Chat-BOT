"""
Flora AI — Tool Definitions
=============================
Ferramentas que a Flora AI pode acionar para realizar acoes.
Cada ferramenta tem um nome, descricao, parametros e handler.
"""

from __future__ import annotations

import ast
import logging
import math
import operator
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ─── Tool Result ───────────────────────────────────────────────────────

@dataclass
class ToolResult:
    """Resultado da execucao de uma ferramenta."""
    success: bool
    data: Any = None
    message: str = ""
    tool_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def ok(cls, tool_name: str, data: Any = None, message: str = "") -> ToolResult:
        return cls(success=True, tool_name=tool_name, data=data, message=message)

    @classmethod
    def error(cls, tool_name: str, message: str) -> ToolResult:
        return cls(success=False, tool_name=tool_name, message=message)


# ─── Tool Name Enum ────────────────────────────────────────────────────

class ToolName(str, Enum):
    """Nomes de todas as ferramentas disponiveis."""
    CALCULATOR = "calculator"
    DATETIME = "datetime"
    PLAN_INFO = "plan_info"
    LICENSE_INFO = "license_info"
    WHATSAPP_STATUS = "whatsapp_status"
    CHECK_STATUS = "check_status"
    CREATE_BOT = "create_bot"
    CONNECT_WHATSAPP = "connect_whatsapp"
    UPGRADE_PLAN = "upgrade_plan"
    GET_HELP = "get_help"
    ONBOARDING_GUIDE = "onboarding_guide"
    TROUBLESHOOT = "troubleshoot"


# ─── Tool Definition ───────────────────────────────────────────────────

@dataclass
class ToolDefinition:
    """Definicao de uma ferramenta."""
    name: ToolName
    description: str
    parameters: dict[str, Any]
    handler: Optional[Callable] = None
    requires_auth: bool = False

    def to_openai_schema(self) -> dict[str, Any]:
        """Converte para formato de funcao OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name.value,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ─── Calculator Tool ───────────────────────────────────────────────────

class CalculatorTool:
    """
    Calculadora segura para operacoes matematicas basicas.
    Suporta: +, -, *, /, **, %, raiz quadrada, potencia.
    """

    # Safe operators for eval
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    _FUNCTIONS = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "max": max,
        "min": min,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    @classmethod
    def execute(cls, expression: str) -> ToolResult:
        """
        Executa uma expressao matematica de forma segura.

        Args:
            expression: Expressao matematica (ex: "2 + 2", "sqrt(16)")

        Returns:
            ToolResult com o resultado
        """
        try:
            # Clean the expression
            expression = expression.strip()
            if not expression:
                return ToolResult.error("calculator", "Expressao vazia")

            # Parse and evaluate safely
            tree = ast.parse(expression, mode="eval")
            result = cls._eval_node(tree.body)

            # Format result
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 10)

            return ToolResult.ok(
                tool_name="calculator",
                data={"expression": expression, "result": result},
                message=f"{expression} = {result}",
            )

        except ZeroDivisionError:
            return ToolResult.error("calculator", "Divisao por zero!")
        except (SyntaxError, ValueError) as e:
            return ToolResult.error("calculator", f"Expressao invalida: {e}")
        except Exception as e:
            logger.error("Calculator error: %s", e)
            return ToolResult.error("calculator", f"Erro ao calcular: {e}")

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Any:
        """Recursively evaluate an AST node safely."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Tipo nao suportado: {type(node.value)}")

        if isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            op_type = type(node.op)
            if op_type in cls._OPERATORS:
                return cls._OPERATORS[op_type](left, right)
            raise ValueError(f"Operador nao suportado: {op_type.__name__}")

        if isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in cls._OPERATORS:
                return cls._OPERATORS[op_type](operand)
            raise ValueError(f"Operador unario nao suportado: {op_type.__name__}")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls._FUNCTIONS:
                    args = [cls._eval_node(arg) for arg in node.args]
                    return cls._FUNCTIONS[func_name](*args)
                raise ValueError(f"Funcao nao suportada: {func_name}")
            raise ValueError("Chamada de funcao complexa nao suportada")

        if isinstance(node, ast.Name):
            # Support constants like pi, e
            constants = {"pi": math.pi, "e": math.e}
            if node.id in constants:
                return constants[node.id]
            raise ValueError(f"Identificador nao suportado: {node.id}")

        raise ValueError(f"Tipo de no nao suportado: {type(node).__name__}")


# ─── DateTime Tool ─────────────────────────────────────────────────────

class DateTimeTool:
    """Ferramenta de data e hora."""

    @classmethod
    def execute(cls, timezone_str: str = "America/Sao_Paulo") -> ToolResult:
        """
        Retorna a data e hora atual.

        Args:
            timezone_str: Timezone (default: America/Sao_Paulo)

        Returns:
            ToolResult com data/hora formatada
        """
        try:
            now = datetime.now(timezone.utc)

            # Common timezone offsets
            tz_offsets = {
                "America/Sao_Paulo": -3,
                "America/New_York": -5,
                "America/Los_Angeles": -8,
                "Europe/London": 0,
                "Europe/Paris": 1,
                "Asia/Tokyo": 9,
                "UTC": 0,
            }

            offset_hours = tz_offsets.get(timezone_str, -3)
            local_now = now + timedelta(hours=offset_hours)

            # Portuguese day/month names
            dias = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]
            meses = [
                "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
            ]

            dia_semana = dias[local_now.weekday()]
            mes = meses[local_now.month - 1]

            formatted = (
                f"{dia_semana}, {local_now.day} de {mes} de {local_now.year}\n"
                f"Hora: {local_now.strftime('%H:%M:%S')}\n"
                f"Timezone: {timezone_str} (UTC{'+' if offset_hours >= 0 else ''}{offset_hours})"
            )

            return ToolResult.ok(
                tool_name="datetime",
                data={
                    "iso": now.isoformat(),
                    "local_formatted": formatted,
                    "date": local_now.strftime("%d/%m/%Y"),
                    "time": local_now.strftime("%H:%M:%S"),
                    "day_of_week": dia_semana,
                    "timezone": timezone_str,
                },
                message=formatted,
            )

        except Exception as e:
            logger.error("DateTime error: %s", e)
            return ToolResult.error("datetime", f"Erro ao obter data/hora: {e}")


# ─── Plan Info Tool ────────────────────────────────────────────────────

class PlanInfoTool:
    """Ferramenta para obter informacoes sobre planos."""

    PLANS = {
        "free": {
            "name": "Free",
            "price": "R$0/mes",
            "messages": "100 msgs/mes",
            "bots": "1 bot",
            "features": ["Suporte basico", "100 mensagens/mes", "1 bot", "Sem IA avancada"],
        },
        "starter": {
            "name": "Starter",
            "price": "R$29/mes",
            "messages": "1.000 msgs/mes",
            "bots": "2 bots",
            "features": ["Suporte por email", "1.000 mensagens/mes", "2 bots", "Intencoes basicas"],
        },
        "growth": {
            "name": "Growth",
            "price": "R$79/mes",
            "messages": "5.000 msgs/mes",
            "bots": "5 bots",
            "features": ["Suporte prioritario", "5.000 mensagens/mes", "5 bots", "IA avancada", "API basica"],
        },
        "pro": {
            "name": "Pro",
            "price": "R$149/mes",
            "messages": "15.000 msgs/mes",
            "bots": "10 bots",
            "features": ["Suporte 24/7", "15.000 mensagens/mes", "10 bots", "IA avancada", "API completa", "Webhooks"],
        },
        "business": {
            "name": "Business",
            "price": "R$299/mes",
            "messages": "50.000 msgs/mes",
            "bots": "25 bots",
            "features": ["Suporte dedicado", "50.000 mensagens/mes", "25 bots", "White-label", "API completa", "Webhooks", "Multi-usuario"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "R$599/mes",
            "messages": "200.000 msgs/mes",
            "bots": "Ilimitados",
            "features": ["Suporte VIP", "200.000 mensagens/mes", "Bots ilimitados", "White-label", "SLA 99.9%", "On-premise opcional"],
        },
        "custom": {
            "name": "Custom",
            "price": "Sob consulta",
            "messages": "Ilimitado",
            "bots": "Ilimitados",
            "features": ["Tudo do Enterprise", "Infraestrutura dedicada", "Treinamento personalizado", "Integracoes customizadas"],
        },
    }

    @classmethod
    def execute(cls, plan_name: str = "all") -> ToolResult:
        """
        Retorna informacoes sobre um plano ou todos os planos.

        Args:
            plan_name: Nome do plano ou "all" para todos

        Returns:
            ToolResult com informacoes do plano
        """
        try:
            plan_key = plan_name.strip().lower()

            if plan_key in ("all", "todos", "todos os planos"):
                return ToolResult.ok(
                    tool_name="plan_info",
                    data=cls.PLANS,
                    message=f"Informacoes de todos os {len(cls.PLANS)} planos obtidas com sucesso.",
                )

            if plan_key in cls.PLANS:
                plan = cls.PLANS[plan_key]
                return ToolResult.ok(
                    tool_name="plan_info",
                    data=plan,
                    message=f"Plano {plan['name']}: {plan['price']}",
                )

            # Try partial match
            for key, plan in cls.PLANS.items():
                if plan_key in key or plan_key in plan["name"].lower():
                    return ToolResult.ok(
                        tool_name="plan_info",
                        data=plan,
                        message=f"Plano {plan['name']}: {plan['price']}",
                    )

            available = ", ".join(cls.PLANS.keys())
            return ToolResult.error(
                "plan_info",
                f"Plano '{plan_name}' nao encontrado. Planos disponiveis: {available}",
            )

        except Exception as e:
            logger.error("PlanInfo error: %s", e)
            return ToolResult.error("plan_info", f"Erro ao obter info do plano: {e}")


# ─── License Info Tool ─────────────────────────────────────────────────

class LicenseInfoTool:
    """Ferramenta para obter informacoes sobre licencas."""

    @classmethod
    def execute(cls, license_key: str = "") -> ToolResult:
        """
        Retorna informacoes sobre uma licenca.

        Args:
            license_key: Chave de licenca (opcional — retorna info geral se vazio)

        Returns:
            ToolResult com informacoes da licenca
        """
        try:
            if not license_key:
                return ToolResult.ok(
                    tool_name="license_info",
                    data={
                        "info": "Sistema de licencas Flora Platform",
                        "types": ["Free", "Starter", "Growth", "Pro", "Business", "Enterprise", "Custom"],
                        "features": [
                            "Licencas sao vinculadas a conta do usuario",
                            "Upgrade pode ser feito a qualquer momento",
                            "7 dias de teste gratis para planos pagos",
                            "Licencas incluem suporte tecnico",
                        ],
                    },
                    message="Sistema de licencas Flora Platform. Use uma chave especifica para detalhes.",
                )

            # In production, this would query the database
            return ToolResult.ok(
                tool_name="license_info",
                data={
                    "key": license_key[:8] + "..." if len(license_key) > 8 else license_key,
                    "status": "active",
                    "message": "Licenca valida. (Em producao, consultaria o banco de dados)",
                },
                message="Licenca encontrada e valida.",
            )

        except Exception as e:
            logger.error("LicenseInfo error: %s", e)
            return ToolResult.error("license_info", f"Erro ao consultar licenca: {e}")


# ─── WhatsApp Status Tool ──────────────────────────────────────────────

class WhatsAppStatusTool:
    """Ferramenta para verificar status de conexao WhatsApp."""

    @classmethod
    def execute(cls, bot_id: str = "") -> ToolResult:
        """
        Retorna o status da conexao WhatsApp.

        Args:
            bot_id: ID do bot (opcional — retorna status geral se vazio)

        Returns:
            ToolResult com status da conexao
        """
        try:
            # In production, this would check the actual WhatsApp connection
            status = {
                "platform": "online",
                "whatsapp_api": "operational",
                "connected_numbers": 0,
                "messages_today": 0,
                "uptime": "99.9%",
            }

            if bot_id:
                status["bot_id"] = bot_id
                status["bot_status"] = "not_connected"  # Would check actual status

            return ToolResult.ok(
                tool_name="whatsapp_status",
                data=status,
                message="Plataforma operacional. WhatsApp API funcionando normalmente.",
            )

        except Exception as e:
            logger.error("WhatsAppStatus error: %s", e)
            return ToolResult.error("whatsapp_status", f"Erro ao verificar status: {e}")


# ─── Tool Registry ─────────────────────────────────────────────────────

class ToolRegistry:
    """
    Registro central de todas as ferramentas disponiveis.
    Gerencia definicoes, execucao e schemas LLM.
    """

    def __init__(self):
        self._tools: dict[ToolName, ToolDefinition] = {}
        self._handlers: dict[ToolName, Callable] = {}
        self._register_defaults()
        logger.info("ToolRegistry initialized with %d tools", len(self._tools))

    def _register_defaults(self) -> None:
        """Register all default tools."""
        # Calculator
        self.register(
            ToolDefinition(
                name=ToolName.CALCULATOR,
                description="Executa calculos matematicos. Suporta: +, -, *, /, **, %, sqrt(), sin(), cos(), etc.",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Expressao matematica (ex: '2 + 2', 'sqrt(16)', '10 * 5')",
                        },
                    },
                    "required": ["expression"],
                },
            ),
            CalculatorTool.execute,
        )

        # DateTime
        self.register(
            ToolDefinition(
                name=ToolName.DATETIME,
                description="Retorna a data e hora atual. Pode especificar timezone.",
                parameters={
                    "type": "object",
                    "properties": {
                        "timezone_str": {
                            "type": "string",
                            "description": "Timezone (default: America/Sao_Paulo). Opcoes: America/Sao_Paulo, America/New_York, Europe/London, UTC",
                        },
                    },
                    "required": [],
                },
            ),
            DateTimeTool.execute,
        )

        # Plan Info
        self.register(
            ToolDefinition(
                name=ToolName.PLAN_INFO,
                description="Retorna informacoes sobre os planos da Flora Platform.",
                parameters={
                    "type": "object",
                    "properties": {
                        "plan_name": {
                            "type": "string",
                            "description": "Nome do plano (free, starter, growth, pro, business, enterprise, custom) ou 'all' para todos",
                        },
                    },
                    "required": [],
                },
            ),
            PlanInfoTool.execute,
        )

        # License Info
        self.register(
            ToolDefinition(
                name=ToolName.LICENSE_INFO,
                description="Retorna informacoes sobre licencas da Flora Platform.",
                parameters={
                    "type": "object",
                    "properties": {
                        "license_key": {
                            "type": "string",
                            "description": "Chave de licenca (opcional — retorna info geral se vazio)",
                        },
                    },
                    "required": [],
                },
            ),
            LicenseInfoTool.execute,
        )

        # WhatsApp Status
        self.register(
            ToolDefinition(
                name=ToolName.WHATSAPP_STATUS,
                description="Verifica o status da conexao WhatsApp.",
                parameters={
                    "type": "object",
                    "properties": {
                        "bot_id": {
                            "type": "string",
                            "description": "ID do bot (opcional — retorna status geral se vazio)",
                        },
                    },
                    "required": [],
                },
            ),
            WhatsAppStatusTool.execute,
        )

    def register(self, definition: ToolDefinition, handler: Callable) -> None:
        """
        Register a new tool.

        Args:
            definition: Tool definition
            handler: Function to call when tool is invoked
        """
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler
        logger.debug("Registered tool: %s", definition.name.value)

    def get(self, name: ToolName) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def get_handler(self, name: ToolName) -> Optional[Callable]:
        """Get a tool handler by name."""
        return self._handlers.get(name)

    def execute(self, name: ToolName, **kwargs: Any) -> ToolResult:
        """
        Execute a tool by name with given parameters.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution result
        """
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult.error(name.value, f"Ferramenta '{name.value}' nao encontrada")

        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("Tool execution error (%s): %s", name.value, e)
            return ToolResult.error(name.value, f"Erro ao executar ferramenta: {e}")

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_openai_schemas(self) -> list[dict[str, Any]]:
        """Get all tool schemas in OpenAI function format."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def __contains__(self, name: ToolName) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        names = [t.value for t in self._tools]
        return f"<ToolRegistry(tools={names})>"


# ─── Module-level convenience ──────────────────────────────────────────

# Global registry instance
_default_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def execute_tool(name: str, **kwargs: Any) -> ToolResult:
    """Execute a tool by name using the global registry."""
    registry = get_tool_registry()
    try:
        tool_name = ToolName(name)
    except ValueError:
        return ToolResult.error(name, f"Ferramenta '{name}' nao existe")
    return registry.execute(tool_name, **kwargs)
