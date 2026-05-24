"""Command Engine - Motor de comandos personalizados."""
import re
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bot import Bot
from backend.models.command import Command


class CommandEngine:
    """Motor de comandos personalizados com parsing e execução."""

    def __init__(self, db: AsyncSession, bot: Bot):
        self.db = db
        self.bot = bot
        self._custom_handlers: dict[str, Callable] = {}

    def register_command(self, name: str, handler: Callable):
        """Registra um handler customizado para um comando."""
        self._custom_handlers[name.lower()] = handler

    async def get_commands(self) -> list[Command]:
        """Lista todos os comandos ativos do bot."""
        result = await self.db.execute(
            select(Command).where(
                Command.bot_id == self.bot.id,
                Command.is_active == True,
            )
        )
        return result.scalars().all()

    async def parse_and_execute(self, text: str) -> Optional[dict]:
        """
        Analisa o texto e executa comando se encontrado.

        Suporta formatos:
        - /comando
        - /comando parametro1 parametro2
        - !comando
        - comando: parametros

        Args:
            text: Texto da mensagem

        Returns:
            dict com resultado ou None se não for comando
        """
        text = text.strip()

        # Extrair comando do texto
        command_name, params = self._extract_command(text)

        if not command_name:
            return None

        # Buscar comando no banco
        result = await self.db.execute(
            select(Command).where(
                Command.bot_id == self.bot.id,
                Command.is_active == True,
            )
        )
        commands = result.scalars().all()

        matched_command = None
        for cmd in commands:
            triggers = []
            if cmd.trigger:
                triggers = [t.strip().lower() for t in cmd.trigger.split(",")]
            if command_name.lower() in triggers or command_name.lower() == cmd.name.lower():
                matched_command = cmd
                break

        if not matched_command:
            return None

        # Executar comando
        return await self._execute_command(matched_command, params)

    def _extract_command(self, text: str) -> tuple[Optional[str], list[str]]:
        """Extrai nome do comando e parâmetros do texto."""
        text = text.strip()

        # Formato /comando ou !comando
        if text.startswith("/") or text.startswith("!"):
            parts = text[1:].split()
            if parts:
                return parts[0], parts[1:]
            return None, []

        # Formato "comando: parametros"
        if ":" in text:
            parts = text.split(":", 1)
            command_part = parts[0].strip()
            params_part = parts[1].strip()
            params = params_part.split() if params_part else []
            return command_part, params

        # Formato "comando parametros" (verifica se primeira palavra é comando)
        words = text.split()
        if len(words) >= 1:
            # Verificar se a primeira palavra é um comando conhecido
            return words[0], words[1:]

        return None, []

    async def _execute_command(self, command: Command, params: list[str]) -> dict:
        """Executa um comando com os parâmetros fornecidos."""
        # Verificar handler customizado
        handler = self._custom_handlers.get(command.name.lower())
        if handler:
            try:
                if callable(handler):
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(params, command)
                    else:
                        result = handler(params, command)
                else:
                    result = None
                if result:
                    return {
                        "command_name": command.name,
                        "response": str(result),
                        "type": "custom_handler",
                    }
            except Exception as e:
                return {
                    "command_name": command.name,
                    "response": f"Erro ao executar comando: {str(e)}",
                    "type": "error",
                }

        # Usar resposta padrão do comando
        response = command.response or "Comando executado com sucesso."

        # Substituir variáveis na resposta
        response = self._substitute_variables(response, params, command)

        return {
            "command_name": command.name,
            "response": response,
            "type": "static",
            "params": params,
        }

    def _substitute_variables(self, response: str, params: list[str], command: Command) -> str:
        """Substitui variáveis na resposta do comando."""
        # {param1}, {param2}, etc.
        for i, param in enumerate(params):
            response = response.replace(f"{{param{i+1}}}", param)
            response = response.replace(f"{{param{i}}}", param)

        # {params} = todos os parâmetros
        response = response.replace("{params}", " ".join(params))

        # {command} = nome do comando
        response = response.replace("{command}", command.name or "")

        # {date} = data atual
        response = response.replace("{date}", datetime.now().strftime("%d/%m/%Y"))

        # {time} = hora atual
        response = response.replace("{time}", datetime.now().strftime("%H:%M"))

        # {bot_name} = nome do bot
        response = response.replace("{bot_name}", self.bot.name or "Bot")

        return response

    async def create_command(
        self, name: str, trigger: str, response: str, description: str = "", parameters: Optional[dict] = None
    ) -> Command:
        """Cria um novo comando."""
        cmd = Command(
            bot_id=self.bot.id,
            name=name,
            trigger=trigger,
            response=response,
            description=description,
            parameters=parameters or {},
            is_active=True,
        )
        self.db.add(cmd)
        await self.db.commit()
        await db.refresh(cmd)
        return cmd

    async def test_command(self, command_text: str, input_text: str) -> dict:
        """Testa um comando com input simulado."""
        result = await self.parse_and_execute(input_text)
        if result:
            return result

        return {
            "command_name": None,
            "response": "Nenhum comando encontrado para o texto fornecido.",
            "type": "test",
        }
