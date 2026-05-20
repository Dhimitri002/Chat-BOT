"""Flora Platform - LLM Router"""
import httpx
import time
from loguru import logger
from backend.config import get_settings

settings = get_settings()


PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": settings.GROQ_API_KEY,
        "models": [
            {"name": "llama-3.1-8b-instant", "speed": "ultra", "cost": 0, "context": 131072, "quality": "medium"},
            {"name": "llama-3.1-70b-versatile", "speed": "fast", "cost": 0, "context": 131072, "quality": "high"},
        ],
        "priority": 1,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_key": settings.GEMINI_API_KEY,
        "models": [
            {"name": "gemini-1.5-flash", "speed": "fast", "cost": 0.00001, "context": 1048576, "quality": "high"},
            {"name": "gemini-1.5-pro", "speed": "medium", "cost": 0.00125, "context": 2097152, "quality": "very_high"},
        ],
        "priority": 2,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": settings.OPENAI_API_KEY,
        "models": [
            {"name": "gpt-4o-mini", "speed": "fast", "cost": 0.00015, "context": 131072, "quality": "high"},
            {"name": "gpt-4o", "speed": "medium", "cost": 0.0025, "context": 131072, "quality": "very_high"},
        ],
        "priority": 3,
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key": settings.ANTHROPIC_API_KEY,
        "models": [
            {"name": "claude-3-haiku-20240307", "speed": "fast", "cost": 0.00025, "context": 200000, "quality": "high"},
            {"name": "claude-3-5-sonnet-20241022", "speed": "medium", "cost": 0.003, "context": 200000, "quality": "very_high"},
        ],
        "priority": 4,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": settings.DEEPSEEK_API_KEY,
        "models": [
            {"name": "deepseek-chat", "speed": "fast", "cost": 0.00014, "context": 65536, "quality": "high"},
        ],
        "priority": 5,
    },
}

PLAN_PROVIDERS = {
    "starter": [],
    "basic": [],
    "plus": [],
    "pro": ["groq"],
    "master": ["groq", "gemini", "openai"],
    "elite": ["groq", "gemini", "openai", "anthropic", "deepseek"],
    "enterprise": ["groq", "gemini", "openai", "anthropic", "deepseek"],
}

PLAN_MODELS = {
    "starter": None,
    "basic": None,
    "plus": None,
    "pro": "llama-3.1-70b-versatile",
    "master": "gpt-4o-mini",
    "elite": "gpt-4o-mini",
    "enterprise": "gpt-4o",
}


async def call_llm(provider, model, messages, max_tokens=1024, temperature=0.7):
    """Call an LLM provider and return the response."""
    cfg = PROVIDERS.get(provider)
    if not cfg or not cfg["api_key"]:
        raise ValueError(f"Provider {provider} not configured")

    api_key = cfg["api_key"]
    base_url = cfg["base_url"]
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    if provider == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        headers["content-type"] = "application/json"
        del headers["Authorization"]
        payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
        url = f"{base_url}/messages"
    elif provider == "gemini":
        url = f"{base_url}/models/{model}:generateContent?key={api_key}"
        headers = {"content-type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": m["content"]} for m in messages]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }
    else:
        url = f"{base_url}/chat/completions"
        headers["content-type"] = "application/json"
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    latency_ms = int((time.time() - start) * 1000)

    if provider == "anthropic":
        content = data["content"][0]["text"]
        tokens_in = data["usage"]["input_tokens"]
        tokens_out = data["usage"]["output_tokens"]
    elif provider == "gemini":
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens_in = data.get("usageMetadata", {}).get("promptTokenCount", 0)
        tokens_out = data.get("usageMetadata", {}).get("candidatesTokenCount", 0)
    else:
        content = data["choices"][0]["message"]["content"]
        tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
        tokens_out = data.get("usage", {}).get("completion_tokens", 0)

    return {
        "content": content,
        "provider": provider,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": latency_ms,
    }


async def route_and_call(plan, messages, max_tokens=1024, temperature=0.7, preferred_provider=None):
    """Route to the best LLM based on plan and call it with fallback."""
    allowed = PLAN_PROVIDERS.get(plan, [])
    if not allowed:
        raise ValueError(f"Plan '{plan}' has no LLM access")

    if preferred_provider and preferred_provider in allowed:
        provider_order = [preferred_provider] + [p for p in allowed if p != preferred_provider]
    else:
        provider_order = sorted(allowed, key=lambda p: PROVIDERS.get(p, {}).get("priority", 99))

    last_error = None
    for provider in provider_order:
        cfg = PROVIDERS.get(provider)
        if not cfg or not cfg["api_key"]:
            continue
        model = PLAN_MODELS.get(plan, cfg["models"][0]["name"])
        try:
            result = await call_llm(provider, model, messages, max_tokens, temperature)
            result["was_fallback"] = provider != provider_order[0]
            if result["was_fallback"]:
                result["fallback_from"] = provider_order[0]
            logger.info(f"LLM response: {provider}/{model} ({result['latency_ms']}ms)")
            return result
        except Exception as e:
            logger.warning(f"LLM provider {provider} failed: {e}")
            last_error = e
            continue

    raise Exception(f"All LLM providers failed. Last error: {last_error}")
