"""
Flora Platform — LLM Router
============================
Unified interface for multiple LLM providers:
OpenAI, Anthropic (Claude), Google (Gemini), Groq, Ollama (local).

Supports:
- Provider auto-selection based on cost, speed, capability
- Automatic fallback on provider failure
- Streaming responses
- Token usage tracking
- Cost estimation
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Optional, Union

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    COHERE = "cohere"


class LLMModelPriority(str, Enum):
    SPEED = "speed"        # Fastest first
    QUALITY = "quality"    # Best quality first
    COST = "cost"          # Cheapest first


@dataclass
class LLMModel:
    """Represents an LLM model."""
    id: str
    provider: LLMProvider
    display_name: str
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_functions: bool = False


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    elapsed_seconds: float = 0.0
    finish_reason: str = "stop"
    raw_response: Any = None

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on token usage."""
        return self.cost


@dataclass
class Message:
    role: str  # "system", "user", "assistant"
    content: str


# ─── Model Registry ───────────────────────────────────────────────

MODEL_REGISTRY: dict[str, LLMModel] = {
    # OpenAI
    "gpt-4o": LLMModel("gpt-4o", LLMProvider.OPENAI, "GPT-4o", 128000, 0.005, 0.015, True, True, True),
    "gpt-4o-mini": LLMModel("gpt-4o-mini", LLMProvider.OPENAI, "GPT-4o Mini", 128000, 0.00015, 0.0006, True, True, True),
    "gpt-4-turbo": LLMModel("gpt-4-turbo", LLMProvider.OPENAI, "GPT-4 Turbo", 128000, 0.01, 0.03, True, True, True),
    "gpt-3.5-turbo": LLMModel("gpt-3.5-turbo", LLMProvider.OPENAI, "GPT-3.5 Turbo", 16385, 0.0005, 0.0015, True, False, True),

    # Anthropic
    "claude-sonnet-4": LLMModel("claude-sonnet-4-20250514", LLMProvider.ANTHROPIC, "Claude Sonnet 4", 200000, 0.003, 0.015, True, True, True),
    "claude-haiku-3.5": LLMModel("claude-3-5-haiku-20241022", LLMProvider.ANTHROPIC, "Claude 3.5 Haiku", 200000, 0.0008, 0.004, True, False, True),
    "claude-opus-4": LLMModel("claude-opus-4-20250514", LLMProvider.ANTHROPIC, "Claude Opus 4", 200000, 0.015, 0.075, True, True, True),

    # Google
    "gemini-2.0-flash": LLMModel("gemini-2.0-flash", LLMProvider.GOOGLE, "Gemini 2.0 Flash", 1048576, 0.0001, 0.0004, True, True, True),
    "gemini-1.5-pro": LLMModel("gemini-1.5-pro", LLMProvider.GOOGLE, "Gemini 1.5 Pro", 2097152, 0.00125, 0.005, True, True, True),
    "gemini-1.5-flash": LLMModel("gemini-1.5-flash", LLMProvider.GOOGLE, "Gemini 1.5 Flash", 1048576, 0.000075, 0.0003, True, True, True),

    # Groq
    "llama-3.3-70b": LLMModel("llama-3.3-70b-versatile", LLMProvider.GROQ, "Llama 3.3 70B", 131072, 0.00059, 0.00079, True, False, False),
    "mixtral-8x7b": LLMModel("mixtral-8x7b-32768", LLMProvider.GROQ, "Mixtral 8x7B", 32768, 0.00027, 0.00027, True, False, False),

    # Mistral
    "mistral-large": LLMModel("mistral-large-latest", LLMProvider.MISTRAL, "Mistral Large", 131072, 0.002, 0.006, True, False, True),
    "mistral-small": LLMModel("mistral-small-latest", LLMProvider.MISTRAL, "Mistral Small", 32768, 0.0002, 0.0006, True, False, True),

    # Ollama (local)
    "llama3": LLMModel("llama3", LLMProvider.OLLAMA, "Llama 3 (Local)", 8192, 0.0, 0.0, True, False, False),
    "mistral": LLMModel("mistral", LLMProvider.OLLAMA, "Mistral (Local)", 32768, 0.0, 0.0, True, False, False),
}


class LLMRouter:
    """
    Routes LLM requests to the appropriate provider with fallback.

    Usage:
        router = LLMRouter(provider="openai", model="gpt-4o")
        response = await router.chat(messages=[{"role": "user", "content": "Hello"}])
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        fallback_provider: Optional[str] = None,
        fallback_model: Optional[str] = None,
        priority: LLMModelPriority = LLMModelPriority.QUALITY,
        max_retries: int = 3,
        timeout_seconds: float = 60.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self._provider = provider
        self._model = model
        self._fallback_provider = fallback_provider or "groq"
        self._fallback_model = fallback_model or "llama-3.3-70b"
        self._priority = priority
        self._max_retries = max_retries
        self._timeout = timeout_seconds
        self._http = http_client
        self._usage_stats: dict[str, dict] = {}

        self._api_keys = {
            "openai": settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else "",
            "anthropic": settings.ANTHROPIC_API_KEY if hasattr(settings, "ANTHROPIC_API_KEY") else "",
            "google": settings.GOOGLE_API_KEY if hasattr(settings, "GOOGLE_API_KEY") else "",
            "groq": settings.GROQ_API_KEY if hasattr(settings, "GROQ_API_KEY") else "",
            "mistral": settings.MISTRAL_API_KEY if hasattr(settings, "MISTRAL_API_KEY") else "",
            "cohere": settings.COHERE_API_KEY if hasattr(settings, "COHERE_API_KEY") else "",
            "ollama": "local",
        }

        logger.info(f"LLMRouter initialized: provider={provider}, model={model}")

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return self._http

    async def close(self):
        """Close HTTP client."""
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system: str = "",
        stop: Optional[list[str]] = None,
        tools: Optional[list] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": str, "content": str}
            model: Override model
            provider: Override provider
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            system: System prompt (added as first message)
            stop: Stop sequences
            tools: Function calling tools

        Returns:
            Standardized LLMResponse
        """
        prov = provider or self._provider
        mdl = model or self._model

        # Add system message if provided
        if system:
            messages = [{"role": "system", "content": system}] + messages

        # Try primary provider, then fallback
        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = await self._dispatch_request(
                    messages=messages,
                    model=mdl,
                    provider=prov,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=stop,
                    tools=tools,
                )
                self._track_usage(prov, mdl, response)
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{self._max_retries}): "
                    f"provider={prov} model={mdl} error={e}"
                )
                # Try fallback on second attempt
                if attempt == 0 and prov != self._fallback_provider:
                    prov = self._fallback_provider
                    mdl = self._fallback_model
                    logger.info(f"Trying fallback: provider={prov} model={mdl}")

        # All retries exhausted
        raise LLMError(f"All LLM requests failed after {self._max_retries} attempts: {last_error}")

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion.

        Yields content chunks as they arrive.
        """
        prov = provider or self._provider
        mdl = model or self._model

        if system:
            messages = [{"role": "system", "content": system}] + messages

        if prov == "openai":
            async for chunk in self._stream_openai(messages, mdl, temperature, max_tokens):
                yield chunk
        elif prov == "anthropic":
            async for chunk in self._stream_anthropic(messages, mdl, temperature, max_tokens):
                yield chunk
        elif prov == "ollama":
            async for chunk in self._stream_ollama(messages, mdl, temperature, max_tokens):
                yield chunk
        else:
            # Default: request full response and yield at once
            response = await self.chat(messages, mdl, prov, temperature, max_tokens)
            yield response.content

    async def _dispatch_request(
        self,
        messages: list[dict],
        model: str,
        provider: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[list[str]],
        tools: Optional[list],
    ) -> LLMResponse:
        """Route to the correct provider."""
        dispatch_map = {
            "openai": self._request_openai,
            "anthropic": self._request_anthropic,
            "google": self._request_google,
            "groq": self._request_groq,
            "ollama": self._request_ollama,
            "mistral": self._request_mistral,
            "cohere": self._request_cohere,
        }

        handler = dispatch_map.get(provider)
        if not handler:
            raise LLMError(f"Unknown provider: {provider}")

        return await handler(messages, model, temperature, max_tokens, stop, tools)

    # ─── OpenAI ─────────────────────────────────────────────────

    async def _request_openai(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("openai")
        if not api_key:
            raise LLMError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop:
            body["stop"] = stop
        if tools:
            body["tools"] = tools

        start = time.time()
        resp = await self.client.post(url, headers=headers, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"OpenAI error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"].get("content", ""),
            provider="openai",
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            elapsed_seconds=elapsed,
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )

    async def _stream_openai(self, messages, model, temperature, max_tokens):
        api_key = self._api_keys.get("openai")
        if not api_key:
            raise LLMError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self.client.stream("POST", url, headers=headers, json=body) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    # ─── Anthropic ──────────────────────────────────────────────

    async def _request_anthropic(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("anthropic")
        if not api_key:
            raise LLMError("Anthropic API key not configured")

        # Separate system and regular messages
        system = ""
        anthropic_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                anthropic_messages.append(m)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
            "temperature": temperature,
        }
        if system:
            body["system"] = system

        start = time.time()
        resp = await self.client.post(url, headers=headers, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Anthropic error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        content_text = ""
        for c in data.get("content", []):
            if c.get("type") == "text":
                content_text += c.get("text", "")

        usage = data.get("usage", {})
        return LLMResponse(
            content=content_text,
            provider="anthropic",
            model=model,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            elapsed_seconds=elapsed,
            finish_reason=data.get("stop_reason", "stop"),
            raw_response=data,
        )

    async def _stream_anthropic(self, messages, model, temperature, max_tokens):
        api_key = self._api_keys.get("anthropic")
        if not api_key:
            raise LLMError("Anthropic API key not configured")

        system = ""
        anthropic_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                anthropic_messages.append(m)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
            "temperature": temperature,
            "stream": True,
        }
        if system:
            body["system"] = system

        async with self.client.stream("POST", url, headers=headers, json=body) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        if event.get("type") == "content_block_delta":
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except (json.JSONDecodeError, KeyError):
                        continue

    # ─── Google ─────────────────────────────────────────────────

    async def _request_google(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("google")
        if not api_key:
            raise LLMError("Google API key not configured")

        # Convert messages to Google format
        google_messages = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            google_messages.append({
                "role": role,
                "parts": [{"text": m["content"]}],
            })

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent?key={api_key}"
        )
        body = {
            "contents": google_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        start = time.time()
        resp = await self.client.post(url, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Google error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        candidate = data["candidates"][0]
        content = ""
        for part in candidate.get("content", {}).get("parts", []):
            content += part.get("text", "")

        usage = data.get("usageMetadata", {})
        return LLMResponse(
            content=content,
            provider="google",
            model=model,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            elapsed_seconds=elapsed,
            raw_response=data,
        )

    # ─── Groq ───────────────────────────────────────────────────

    async def _request_groq(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("groq")
        if not api_key:
            raise LLMError("Groq API key not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        resp = await self.client.post(url, headers=headers, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Groq error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"].get("content", ""),
            provider="groq",
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            elapsed_seconds=elapsed,
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )

    # ─── Mistral ────────────────────────────────────────────────

    async def _request_mistral(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("mistral")
        if not api_key:
            raise LLMError("Mistral API key not configured")

        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        resp = await self.client.post(url, headers=headers, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Mistral error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"].get("content", ""),
            provider="mistral",
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            elapsed_seconds=elapsed,
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )

    # ─── Cohere ─────────────────────────────────────────────────

    async def _request_cohere(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        api_key = self._api_keys.get("cohere")
        if not api_key:
            raise LLMError("Cohere API key not configured")

        # Cohere uses the last user message as message, and prior as chat_history
        last_msg = messages[-1]["content"]
        chat_history = []
        for m in messages[:-1]:
            role = "USER" if m["role"] == "user" else "CHATBOT"
            if m["role"] == "system":
                role = "SYSTEM"
            chat_history.append({"role": role, "message": m["content"]})

        url = "https://api.cohere.ai/v1/chat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "message": last_msg,
            "chat_history": chat_history,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        resp = await self.client.post(url, headers=headers, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Cohere error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        meta = data.get("meta", {})
        tokens = meta.get("tokens", {})

        return LLMResponse(
            content=data.get("text", ""),
            provider="cohere",
            model=model,
            input_tokens=tokens.get("input_tokens", 0),
            output_tokens=tokens.get("output_tokens", 0),
            total_tokens=tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0),
            elapsed_seconds=elapsed,
            raw_response=data,
        )

    # ─── Ollama (Local) ──────────────────────────────────────────

    async def _request_ollama(
        self, messages, model, temperature, max_tokens, stop, tools
    ) -> LLMResponse:
        ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

        url = f"{ollama_url}/api/chat"
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start = time.time()
        resp = await self.client.post(url, json=body)
        elapsed = time.time() - start

        if resp.status_code != 200:
            raise LLMError(f"Ollama error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            provider="ollama",
            model=model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            elapsed_seconds=elapsed,
            raw_response=data,
        )

    async def _stream_ollama(self, messages, model, temperature, max_tokens):
        ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

        url = f"{ollama_url}/api/chat"
        body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with self.client.stream("POST", url, json=body) as resp:
            async for line in resp.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    # ─── Usage Tracking ──────────────────────────────────────────

    def _track_usage(self, provider: str, model: str, response: LLMResponse) -> None:
        """Track token usage for monitoring/billing."""
        key = f"{provider}:{model}"
        if key not in self._usage_stats:
            self._usage_stats[key] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "errors": 0,
            }

        stats = self._usage_stats[key]
        stats["requests"] += 1
        stats["input_tokens"] += response.input_tokens
        stats["output_tokens"] += response.output_tokens
        stats["total_tokens"] += response.total_tokens
        stats["total_cost"] += response.cost

    def get_usage_stats(self) -> dict:
        """Return usage statistics."""
        return dict(self._usage_stats)

    @staticmethod
    def get_available_models(provider: Optional[str] = None) -> list[LLMModel]:
        """Get available models, optionally filtered by provider."""
        models = list(MODEL_REGISTRY.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        return models

    @staticmethod
    def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request."""
        model = MODEL_REGISTRY.get(model_id)
        if not model:
            return 0.0
        return (
            (input_tokens / 1000) * model.cost_per_1k_input
            + (output_tokens / 1000) * model.cost_per_1k_output
        )


class LLMError(Exception):
    """Raised when an LLM request fails."""
    pass
