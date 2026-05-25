"""
Flora Platform — Command Engine
================================
Parses and executes bot commands from user messages.

Commands start with / or ! and can be:
- Built-in commands (help, reset, config, stats)
- Custom commands defined per bot
- Flora AI specific commands
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Represents a bot command."""
    name: str
    description: str
    usage: str = ""
    handler: Optional[Callable] = None
    admin_only: bool = False
    category: str = "general"


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    response: str
    data: Any = None
    error: str = ""


class CommandEngine:
    """
    Parses and executes bot commands.

    Built-in commands:
    - /help - Show available commands
    - /reset - Reset chat session
    - /config - Show bot configuration
    - /stats - Show usage statistics
    - /language - Change language
    """

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._custom_commands: dict[str, Command] = {}
        self._register_builtins()
        logger.info(f"CommandEngine initialized with {len(self._commands)} built-in commands")

    def _register_builtins(self):
        """Register built-in commands."""
        builtins = [
            Command(
                name="help",
                description="Mostra os comandos disponíveis",
                usage="/help [comando]",
                handler=self._cmd_help,
                category="general",
            ),
            Command(
                name="reset",
                description="Reinicia a conversa atual",
                usage="/reset",
                handler=self._cmd_reset,
                category="general",
            ),
            Command(
                name="config",
                description="Mostra a configuração do bot",
                usage="/config",
                handler=self._cmd_config,
                category="general",
            ),
            Command(
                name="stats",
                description="Mostra estatísticas de uso",
                usage="/stats",
                handler=self._cmd_stats,
                category="general",
            ),
            Command(
                name="language",
                description="Altera o idioma do bot",
                usage="/language [pt/en/es]",
                handler=self._cmd_language,
                category="general",
            ),
            Command(
                name="menu",
                description="Mostra o menu principal",
                usage="/menu",
                handler=self._cmd_menu,
                category="general",
            ),
            Command(
                name="agendar",
                description="Inicia um agendamento",
                usage="/agendar",
                handler=self._cmd_schedule,
                category="business",
            ),
            Command(
                name="suporte",
                description="Abre um chamado de suporte",
                usage="/suporte [mensagem]",
                handler=self._cmd_support,
                category="general",
            ),
            Command(
                name="botinfo",
                description="Informações sobre este bot",
                usage="/botinfo",
                handler=self._cmd_botinfo,
                category="general",
            ),
            Command(
                name="admin",
                description="Comandos administrativos (apenas admin)",
                usage="/admin [subcomando]",
                handler=self._cmd_admin,
                admin_only=True,
                category="admin",
            ),
        ]

        for cmd in builtins:
            self._commands[f"/{cmd.name}"] = cmd
            self._commands[f"!{cmd.name}"] = cmd

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        category: str = "custom",
        admin_only: bool = False,
    ) -> None:
        """Register a custom command."""
        cmd = Command(
            name=name.lstrip("/!"),
            description=description,
            usage=usage or f"/{name}",
            handler=handler,
            admin_only=admin_only,
            category=category,
        )
        self._commands[f"/{cmd.name}"] = cmd
        self._custom_commands[f"/{cmd.name}"] = cmd
        logger.info(f"Command registered: /{cmd.name}")

    def unregister_command(self, name: str) -> bool:
        """Remove a custom command."""
        key = f"/{name.lstrip('/!')}"
        if key in self._custom_commands:
            del self._commands[key]
            del self._custom_commands[key]
            logger.info(f"Command unregistered: {key}")
            return True
        return False

    async def execute(self, message: str, context: Any = None) -> Optional[str]:
        """
        Parse and execute a command from a message.

        Returns the command response string, or None if not a command
        or the command is not recognized.
        """
        if not self._is_command(message):
            return None

        # Parse command and arguments
        parts = message.strip().split(maxsplit=1)
        cmd_key = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        command = self._commands.get(cmd_key)
        if not command:
            return None

        if not command.handler:
            return f"Comando {cmd_key} não implementado."

        logger.info(f"Executing command: {cmd_key} args='{args}'")

        try:
            result = await command.handler(args, context, command)
            if isinstance(result, CommandResult):
                return result.response
            return str(result)
        except Exception as e:
            logger.error(f"Command error: {cmd_key} - {e}", exc_info=True)
            return "Erro ao executar o comando. Tente novamente."

    def _is_command(self, message: str) -> bool:
        """Check if a message starts with a command prefix and matches a known command."""
        if not message:
            return False
        message = message.strip()
        if not (message.startswith("/") or message.startswith("!")):
            return False
        parts = message.split(maxsplit=1)
        cmd_key = parts[0].lower()
        return cmd_key in self._commands

    def get_commands(self, category: Optional[str] = None, include_admin: bool = False) -> list[Command]:
        """Get registered commands."""
        commands = list(self._commands.values())
        if category:
            commands = [c for c in commands if c.category == category]
        if not include_admin:
            commands = [c for c in commands if not c.admin_only]
        # De-duplicate (each command is registered with / and !)
        seen = set()
        unique = []
        for cmd in commands:
            if cmd.name not in seen:
                seen.add(cmd.name)
                unique.append(cmd)
        return unique

    # ─── Built-in Command Handlers ───────────────────────────────

    async def _cmd_help(self, args: str, context: Any, cmd: Command) -> CommandResult:
        if args:
            # Help for a specific command
            target = args.strip().lower()
            if not target.startswith("/"):
                target = f"/{target}"
            found = self._commands.get(target)
            if found:
                return CommandResult(
                    success=True,
                    response=f"*{found.name}*\n{found.description}\n\nUso: {found.usage}",
                )
            return CommandResult(
                success=False,
                response=f"Comando {target} não encontrado.",
            )

        # List all commands
        categories = {}
        for c in self.get_commands(include_admin=False):
            categories.setdefault(c.category, []).append(c)

        lines = ["*Comandos disponiveis:*\n"]
        for cat, cmds in sorted(categories.items()):
            lines.append(f"*{cat.title()}:*")
            for c in cmds:
                lines.append(f"  {c.usage or '/' + c.name} - {c.description}")
            lines.append("")

        lines.append("Digite /help [comando] para mais detalhes.")
        return CommandResult(success=True, response="\n".join(lines))

    async def _cmd_reset(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response="Conversa reiniciada! Como posso te ajudar?",
        )

    async def _cmd_config(self, args: str, context: Any, cmd: Command) -> CommandResult:
        bot_name = "Flora Bot"
        if context and hasattr(context, "metadata"):
            bot_name = context.metadata.get("bot_name", "Flora Bot")

        return CommandResult(
            success=True,
            response=(
                f"*Configuracao do Bot*\n"
                f"Nome: {bot_name}\n"
                f"Idioma: Portugues (BR)\n"
                f"Versao: 1.0.0"
            ),
        )

    async def _cmd_stats(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response=(
                "*Estatisticas de Uso*\n"
                "Mensagens hoje: --\n"
                "Mensagens totais: --\n"
                "Tempo medio de resposta: --ms\n\n"
                "_Estatisticas detalhadas disponiveis no painel admin._"
            ),
        )

    async def _cmd_language(self, args: str, context: Any, cmd: Command) -> CommandResult:
        if not args:
            return CommandResult(
                success=True,
                response=(
                    "Idiomas disponiveis:\n"
                    "/language pt - Portugues\n"
                    "/language en - English\n"
                    "/language es - Espanol"
                ),
            )

        lang = args.strip().lower()
        lang_map = {
            "pt": ("pt-BR", "Portugues"),
            "en": ("en-US", "English"),
            "es": ("es", "Espanol"),
        }

        if lang in lang_map:
            code, name = lang_map[lang]
            return CommandResult(
                success=True,
                response=f"Idioma alterado para *{name}* ({code})",
            )
        return CommandResult(
            success=False,
            response=f"Idioma '{lang}' nao suportado. Use: pt, en, ou es.",
        )

    async def _cmd_menu(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response=(
                "*Menu Principal*\n\n"
                "1. Atendimento\n"
                "2. Agendamento\n"
                "3. Informacoes\n"
                "4. Suporte\n\n"
                "Digite o numero ou nome da opcao desejada."
            ),
        )

    async def _cmd_schedule(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response=(
                "*Agendamento*\n\n"
                "Para agendar, me informe:\n"
                "- Data desejada\n"
                "- Horario preferido\n"
                "- Tipo de servico\n\n"
                "Ou digite /cancelar para voltar."
            ),
        )

    async def _cmd_support(self, args: str, context: Any, cmd: Command) -> CommandResult:
        if args:
            return CommandResult(
                success=True,
                response=(
                    "Chamado de suporte registrado!\n\n"
                    f"Mensagem: {args}\n\n"
                    "Um atendente retornara em breve."
                ),
            )
        return CommandResult(
            success=True,
            response="Digite sua mensagem de suporte apos o comando.\nExemplo: /suporte Minha duvida e sobre...",
        )

    async def _cmd_botinfo(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response=(
                "*Flora Bot*\n\n"
                "Powered by Flora Platform\n"
                "Versao: 1.0.0\n"
                "AI: Multi-provider LLM\n\n"
                "_Um chatbot inteligente para seu negocio._"
            ),
        )

    async def _cmd_admin(self, args: str, context: Any, cmd: Command) -> CommandResult:
        return CommandResult(
            success=True,
            response=(
                "*Painel Admin*\n\n"
                "Comandos administrativos:\n"
                "/admin users - Listar usuarios\n"
                "/admin bots - Listar bots\n"
                "/admin stats - Estatisticas\n"
                "/admin broadcast - Enviar mensagem"
            ),
        )
