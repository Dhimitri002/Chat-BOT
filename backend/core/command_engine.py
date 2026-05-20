"""
Command Engine - Sistema de comandos personalizados para bots.
Suporta comandos por prefixo, palavra-chave e regex.
"""
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from loguru import logger


@dataclass
class Command:
    """Representa um comando personalizado."""
    id: str
    bot_id: str
    trigger: str  # O que ativa o comando
    trigger_type: str  # "prefix" | "keyword" | "regex"
    response: str  # Resposta (pode conter variáveis)
    command_type: str  # "text" | "action" | "ai"
    is_active: bool = True
    is_admin_only: bool = False
    cooldown_seconds: int = 0
    usage_count: int = 0
    last_used: float = 0
    metadata: dict = field(default_factory=dict)

    def can_execute(self, user_is_admin: bool = False) -> tuple[bool, str]:
        """Verifica se o comando pode ser executado."""
        if not self.is_active:
            return False, "Comando desativado"

        if self.is_admin_only and not user_is_admin:
            return False, "Comando restrito a administradores"

        if self.cooldown_seconds > 0 and self.last_used > 0:
            elapsed = time.time() - self.last_used
            if elapsed < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - elapsed)
                return False, f"Aguarde {remaining}s para usar novamente"

        return True, ""

    def record_usage(self):
        self.usage_count += 1
        self.last_used = time.time()


class CommandEngine:
    """Motor de comandos personalizados."""

    # Comandos built-in disponíveis para todos os bots
    BUILTIN_COMMANDS = {
        "help": {
            "trigger": "help",
            "trigger_type": "keyword",
            "response": "📋 *Comandos disponíveis:*\n\n{command_list}\n\nDigite o nome do comando para mais informações.",
            "description": "Mostra lista de comandos",
        },
        "menu": {
            "trigger": "menu",
            "trigger_type": "keyword",
            "response": "🍽️ *Menu*\n\n{menu_items}\n\nPara fazer um pedido, digite: *pedir [número]*",
            "description": "Mostra menu",
        },
        "info": {
            "trigger": "info",
            "trigger_type": "keyword",
            "response": "ℹ️ *Informações*\n\n{bot_name}\n{prompt_summary}\n\nPara falar com um atendente, digite: *atendente*",
            "description": "Informações sobre o bot",
        },
        "transfer": {
            "trigger": "transfer",
            "trigger_type": "keyword",
            "response": "🔄 Transferindo para atendimento humano...\n\nAguarde um momento, um atendente responderá em breve.",
            "description": "Transferir para humano",
        },
        "reset": {
            "trigger": "reset",
            "trigger_type": "keyword",
            "response": "🔄 Conversa reiniciada. Como posso ajudar?",
            "description": "Reiniciar conversa",
        },
        "horario": {
            "trigger": "horario",
            "trigger_type": "keyword",
            "response": "🕐 *Horário de atendimento:*\n\n{working_hours}\n\nFora deste horário, deixe sua mensagem e retornaremos em breve.",
            "description": "Horário de funcionamento",
        },
    }

    def __init__(self):
        self._commands: dict[str, dict[str, Command]] = {}  # bot_id -> {trigger: Command}
        self._action_handlers: dict[str, Callable] = {}

    def register_action(self, action_name: str, handler: Callable):
        """Registra um handler para comandos do tipo 'action'."""
        self._action_handlers[action_name] = handler

    def load_bot_commands(self, bot_id: str, commands: list[dict]):
        """Carrega comandos de um bot a partir de dados do banco."""
        if bot_id not in self._commands:
            self._commands[bot_id] = {}

        for cmd_data in commands:
            cmd = Command(
                id=cmd_data.get("id", ""),
                bot_id=bot_id,
                trigger=cmd_data["trigger"],
                trigger_type=cmd_data.get("trigger_type", "keyword"),
                response=cmd_data["response"],
                command_type=cmd_data.get("command_type", "text"),
                is_active=cmd_data.get("is_active", True),
                is_admin_only=cmd_data.get("is_admin_only", False),
                cooldown_seconds=cmd_data.get("cooldown_seconds", 0),
                metadata=cmd_data.get("metadata", {}),
            )
            self._commands[bot_id][cmd.trigger.lower()] = cmd

        logger.info(f"Carregados {len(commands)} comandos para bot {bot_id}")

    def add_command(self, bot_id: str, cmd: Command):
        """Adiciona um comando para um bot."""
        if bot_id not in self._commands:
            self._commands[bot_id] = {}
        self._commands[bot_id][cmd.trigger.lower()] = cmd

    def remove_command(self, bot_id: str, trigger: str):
        """Remove um comando de um bot."""
        if bot_id in self._commands:
            self._commands[bot_id].pop(trigger.lower(), None)

    def get_bot_commands(self, bot_id: str) -> list[Command]:
        """Retorna todos os comandos de um bot."""
        return list(self._commands.get(bot_id, {}).values())

    async def process_message(
        self,
        bot_id: str,
        message: str,
        user_is_admin: bool = False,
        variables: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Processa uma mensagem para verificar se ativa algum comando.
        Retorna None se nenhum comando foi ativado.
        """
        message_lower = message.strip().lower()
        bot_commands = self._commands.get(bot_id, {})

        # 1. Verificar comandos do bot (prefix-based: /comando)
        if message_lower.startswith("/"):
            trigger = message_lower.split()[0][1:]  # Remove a /
            cmd = bot_commands.get(trigger)
            if cmd:
                return await self._execute_command(cmd, message, variables)

        # 2. Verificar comandos do bot (keyword-based)
        for trigger, cmd in bot_commands.items():
            if cmd.trigger_type == "keyword" and trigger in message_lower:
                return await self._execute_command(cmd, message, variables)

        # 3. Verificar comandos do bot (regex-based)
        for trigger, cmd in bot_commands.items():
            if cmd.trigger_type == "regex":
                try:
                    if re.search(trigger, message, re.IGNORECASE):
                        return await self._execute_command(cmd, message, variables)
                except re.error:
                    logger.error(f"Regex inválida no comando {cmd.id}: {trigger}")

        # 4. Verificar comandos built-in
        for name, builtin in self.BUILTIN_COMMANDS.items():
            if builtin["trigger"] in message_lower:
                return await self._execute_builtin(name, bot_id, variables)

        return None

    async def _execute_command(
        self, cmd: Command, message: str, variables: Optional[dict] = None
    ) -> Optional[dict]:
        """Executa um comando personalizado."""
        can_exec, reason = cmd.can_execute()
        if not can_exec:
            return {
                "response": f"⚠️ {reason}",
                "source": "command_blocked",
                "command_id": cmd.id,
            }

        cmd.record_usage()

        if cmd.command_type == "text":
            response = self._substitute_variables(cmd.response, variables or {})
            return {
                "response": response,
                "source": "command",
                "command_id": cmd.id,
                "command_type": "text",
            }

        elif cmd.command_type == "action":
            action_name = cmd.metadata.get("action_name", "")
            handler = self._action_handlers.get(action_name)
            if handler:
                try:
                    if asyncio := __import__("asyncio"):
                        if asyncio.iscoroutinefunction(handler):
                            result = await handler(cmd, message, variables)
                        else:
                            result = handler(cmd, message, variables)
                    else:
                        result = handler(cmd, message, variables)

                    return {
                        "response": result.get("response", "Ação executada."),
                        "source": "command",
                        "command_id": cmd.id,
                        "command_type": "action",
                        "action_result": result,
                    }
                except Exception as e:
                    logger.error(f"Erro ao executar ação {action_name}: {e}")
                    return {
                        "response": "⚠️ Erro ao executar comando.",
                        "source": "command_error",
                        "command_id": cmd.id,
                    }

        elif cmd.command_type == "ai":
            # Comando AI-powered: usa o LLM para gerar resposta
            return {
                "response": cmd.response,  # Prompt para o LLM
                "source": "command_ai",
                "command_id": cmd.id,
                "command_type": "ai",
                "use_llm": True,
            }

        return None

    async def _execute_builtin(
        self, name: str, bot_id: str, variables: Optional[dict] = None
    ) -> dict:
        """Executa um comando built-in."""
        builtin = self.BUILTIN_COMMANDS[name]
        response = builtin["response"]

        # Substituir variáveis específicas de built-in
        vars_dict = variables or {}

        if name == "help":
            bot_commands = self._commands.get(bot_id, {})
            command_list = "\n".join([
                f"• *{c.trigger}* - {c.metadata.get('description', 'Comando')}"
                for c in bot_commands.values() if c.is_active
            ])
            vars_dict["command_list"] = command_list or "Nenhum comando configurado."

        response = self._substitute_variables(response, vars_dict)

        return {
            "response": response,
            "source": "builtin_command",
            "command_name": name,
        }

    def _substitute_variables(self, text: str, variables: dict) -> str:
        """Substitui variáveis no formato {variavel} no texto."""
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


# Singleton
command_engine = CommandEngine()
