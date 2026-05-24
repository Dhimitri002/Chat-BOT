"""LLM Router - Roteamento inteligente de LLMs com fallback e rate limiting."""
import asyncio
import time
from collections import defaultdict
from typing import Any, AsyncGenerator, Optional

from backend.config import settings


class RateLimiter:
    """Rate limiter por plano usando token bucket."""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._limits: dict[str, dict] = {
            "free": {"rpm": 0, "tpd": 0},
            "starter": {"rpm": 10, "tpd": 50000},
            "pro": {"rpm": 30, "tpd": 200000},
            "business": {"rpm": 100, "tpd": 1000000},
            "premium": {"rpm": 300, "tpd": 5000000},
            "enterprise": {"rpm": 1000, "tpd": 50000000},
            "white_label": {"rpm": 1000, "tpd": 50000000},
        }
        self._token_usage: dict[str, int] = defaultdict(int)
        self._last_reset: float = time.time()

    def check_rate_limit(self, plan: str) -> bool:
        """Verifica se a requisição está dentro do rate limit."""
        limits = self._limits.get(plan, self._limits["starter"])

        # Reset diário de tokens
        if time.time() - self._last_reset > 86400:
            self._token_usage.clear()
            self._last_reset = time.time()

        # Verificar tokens por dia
        if limits["tpd"] > 0 and self._token_usage[plan] >= limits["tpd"]:
            return False

        # Verificar requests por minuto
        now = time.time()
        minute_ago = now - 60
        self._requests[plan] = [t for t in self._requests[plan] if t > minute_ago]

        if limits["rpm"] > 0 and len(self._requests[plan]) >= limits["rpm"]:
            return False

        self._requests[plan].append(now)
        return True

    def record_tokens(self, plan: str, tokens: int):
        """Registra uso de tokens."""
        self._token_usage[plan] += tokens


class LLMRouter:
    """Roteador de LLM com fallback e rate limiting."""

    # Modelos por provedor
    PROVIDERS = {
        "groq": {
            "default_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "api_url": "https://api.groq.com/openai/v1/chat/completions",
        },
        "gemini": {
            "default_model": "gemini-2.0-flash",
            "fallback_model": "gemini-1.5-flash",
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        },
        "openai": {
            "default_model": "gpt-4o-mini",
            "fallback_model": "gpt-3.5-turbo",
            "api_url": "https://api.openai.com/v1/chat/completions",
        },
        "anthropic": {
            "default_model": "claude-sonnet-4-20250514",
            "fallback_model": "claude-3-haiku-20240307",
            "api_url": "https://api.anthropic.com/v1/messages",
        },
    }

    # Mapeamento de planos para provedores
    PLAN_PROVIDERS = {
        "free": [],
        "starter": ["groq"],
        "pro": ["groq", "gemini"],
        "business": ["groq", "gemini", "openai"],
        "premium": ["groq", "gemini", "openai", "anthropic"],
        "enterprise": ["groq", "gemini", "openai", "anthropic"],
        "white_label": ["groq", "gemini", "openai", "anthropic"],
    }

    def __init__(self, provider: str = "groq", **kwargs):
        self.primary_provider = provider
        self.kwargs = kwargs
        self.rate_limiter = RateLimiter()

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Retorna API key do provedor."""
        keys = {
            "groq": settings.GROQ_API_KEY if hasattr(settings, "GROQ_API_KEY") else None,
            "gemini": settings.GEMINI_API_KEY if hasattr(settings, "GEMINI_API_KEY") else None,
            "openai": settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else None,
            "anthropic": settings.ANTHROPIC_API_KEY if hasattr(settings, "ANTHROPIC_API_KEY") else None,
        }
        return keys.get(provider)

    def _build_groq_request(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Constrói request para Groq (compatível com OpenAI)."""
        return {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 1.0),
        }

    def _build_gemini_request(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Constrói request para Gemini."""
        # Converter formato OpenAI para Gemini
        gemini_contents = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": f"[System] {msg['content']}"}]
                })
            elif role == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })
            else:
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

        return {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1024),
                "topP": kwargs.get("top_p", 1.0),
            }
        }

    def _build_openai_request(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Constrói request para OpenAI."""
        return {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 1.0),
        }

    def _build_anthropic_request(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Constrói request para Anthropic."""
        system_msg = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        request = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
        }
        if system_msg:
            request["system"] = system_msg

        return request

    async def _call_groq(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Chama API da Groq."""
        import aiohttp

        api_key = self._get_api_key("groq")
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada")

        request_data = self._build_groq_request(messages, model, **kwargs)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.PROVIDERS["groq"]["api_url"],
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Groq API error {response.status}: {error_text}")

                data = await response.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": model,
                    "provider": "groq",
                    "usage": {
                        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                    },
                }

    async def _call_gemini(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Chama API do Gemini."""
        import aiohttp

        api_key = self._get_api_key("gemini")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada")

        request_data = self._build_gemini_request(messages, model, **kwargs)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Gemini API error {response.status}: {error_text}")

                data = await response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "content": content,
                    "model": model,
                    "provider": "gemini",
                    "usage": {
                        "prompt_tokens": data.get("usageMetadata", {}).get("promptTokenCount", 0),
                        "completion_tokens": data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                        "total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0),
                    },
                }

    async def _call_openai(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Chama API da OpenAI."""
        import aiohttp

        api_key = self._get_api_key("openai")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")

        request_data = self._build_openai_request(messages, model, **kwargs)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.PROVIDERS["openai"]["api_url"],
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"OpenAI API error {response.status}: {error_text}")

                data = await response.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": model,
                    "provider": "openai",
                    "usage": {
                        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                    },
                }

    async def _call_anthropic(self, messages: list[dict], model: str, **kwargs) -> dict:
        """Chama API da Anthropic."""
        import aiohttp

        api_key = self._get_api_key("anthropic")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada")

        request_data = self._build_anthropic_request(messages, model, **kwargs)
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.PROVIDERS["anthropic"]["api_url"],
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Anthropic API error {response.status}: {error_text}")

                data = await response.json()
                return {
                    "content": data["content"][0]["text"],
                    "model": model,
                    "provider": "anthropic",
                    "usage": {
                        "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
                    },
                }

    async def chat(self, messages: list[dict], plan: str = "starter", **kwargs) -> dict:
        """
        Envia mensagem para LLM com fallback automático.

        Args:
            messages: Lista de mensagens no formato OpenAI
            plan: Plano do usuário (determina provedores disponíveis)
            **kwargs: Parâmetros adicionais (temperature, max_tokens, etc.)

        Returns:
            dict com content, model, provider, usage
        """
        # Verificar rate limit
        if not self.rate_limiter.check_rate_limit(plan):
            raise ValueError("Rate limit excedido. Tente novamente em instantes.")

        # Obter provedores disponíveis para o plano
        providers = self.PLAN_PROVIDERS.get(plan, ["groq"])

        if not providers:
            raise ValueError(f"Plano '{plan}' não tem acesso a LLMs")

        last_error = None

        for provider in providers:
            config = self.PROVIDERS.get(provider)
            if not config:
                continue

            model = config["default_model"]
            api_key = self._get_api_key(provider)

            if not api_key:
                continue

            try:
                call_method = getattr(self, f"_call_{provider}")
                result = await call_method(messages, model, **kwargs)

                # Registrar uso de tokens
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                self.rate_limiter.record_tokens(plan, tokens_used)

                return result

            except Exception as e:
                last_error = e
                # Tentar fallback model
                try:
                    fallback_model = config.get("fallback_model")
                    if fallback_model and fallback_model != model:
                        call_method = getattr(self, f"_call_{provider}")
                        result = await call_method(messages, fallback_model, **kwargs)
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                        self.rate_limiter.record_tokens(plan, tokens_used)
                        return result
                except Exception:
                    pass

                # Próximo provedor
                continue

        raise ValueError(f"Todos os provedores falharam. Último erro: {last_error}")

    async def chat_stream(
        self, messages: list[dict], plan: str = "starter", **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streaming de resposta LLM (SSE).
        Atualmente simula streaming caractere por caractere.
        """
        result = await self.chat(messages, plan, **kwargs)
        content = result.get("content", "")

        # Simular streaming palavra por palavra
        words = content.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.02)  # Delay para simular streaming

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estima número de tokens (aproximação: 1 token ≈ 4 caracteres)."""
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_cost(tokens: int, model: str) -> float:
        """Estima custo em USD baseado no modelo."""
        costs_per_1k = {
            "llama-3.3-70b-versatile": 0.00059,
            "llama-3.1-8b-instant": 0.00005,
            "gemini-2.0-flash": 0.000075,
            "gemini-1.5-flash": 0.00001875,
            "gpt-4o-mini": 0.00015,
            "gpt-3.5-turbo": 0.0005,
            "claude-sonnet-4-20250514": 0.003,
            "claude-3-haiku-20240307": 0.00025,
        }
        cost_per_1k = costs_per_1k.get(model, 0.0005)
        return (tokens / 1000) * cost_per_1k
