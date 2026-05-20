"""Flora Platform — Chat Engine (Brain)"""
import random
from loguru import logger
from backend.core.llm_router import route_and_call

FLORA_SYSTEM_PROMPT = """Você é a Flora AI, assistente oficial da Flora Platform.

## Sua Identidade
- Nome: Flora 🌸
- Personalidade: acolhedora, inteligente, clara, elegante, prestativa
- Tom: amigável mas profissional, objetiva quando necessário
- Idioma: responda no mesmo idioma do usuário
- Use emojis com moderação para ser elegante

## Seu Papel
Você ajuda clientes a:
1. Entender e validar sua licença
2. Conectar o WhatsApp via QR Code
3. Configurar e personalizar o bot
4. Criar comandos e automações
5. Resolver problemas comuns
6. Decidir sobre upgrades de plano

## Regras Importantes
- Nunca revele informações técnicas internas do sistema
- Nunca gere, valide ou modifique licenças diretamente
- Se não souber algo, seja honesta e sugira abrir um ticket
- Seja concisa mas completa
- Sempre termine oferecendo ajuda adicional

## Contexto do Cliente
- Nome: {client_name}
- Plano: {plan_name}
- Dias restantes: {days_left}
- Status do bot: {bot_status}

Responda de forma útil, acolhedora e profissional. 🌸"""


async def process_message(
    user_text: str,
    intents: list[dict],
    bot_config: dict,
    contact_context: dict = None,
) -> dict:
    """
    Process a message through the chat engine.
    Returns: {"reply": str, "source": "intent"|"llm"|"fallback", "metadata": dict}
    """
    text_lower = user_text.lower().strip()

    # 1. Try intent matching
    matched_intent = match_intent(text_lower, intents)
    if matched_intent:
        response = random.choice(matched_intent["responses"])
        logger.info(f"Intent matched: {matched_intent['tag']}")
        return {
            "reply": response,
            "source": "intent",
            "metadata": {"intent_tag": matched_intent["tag"]},
        }

    # 2. Try command matching
    # (commands are handled separately in the API)

    # 3. Fallback to LLM if bot has LLM access
    if bot_config.get("has_llm") and bot_config.get("preferred_llm"):
        try:
            messages = [
                {"role": "system", "content": bot_config.get("prompt", "Você é um assistente útil.")},
                {"role": "user", "content": user_text},
            ]

            result = await route_and_call(
                plan=bot_config.get("plan", "pro"),
                messages=messages,
                max_tokens=bot_config.get("max_tokens", 512),
                temperature=bot_config.get("temperature", 0.7),
                preferred_provider=bot_config.get("preferred_llm"),
            )

            return {
                "reply": result["content"],
                "source": "llm",
                "metadata": {
                    "provider": result["provider"],
                    "model": result["model"],
                    "tokens_in": result["tokens_in"],
                    "tokens_out": result["tokens_out"],
                    "latency_ms": result["latency_ms"],
                },
            }
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")

    # 4. Final fallback
    fallback = bot_config.get(
        "fallback_message",
        "Desculpa, não entendi. Pode reformular? 🤔"
    )
    return {
        "reply": fallback,
        "source": "fallback",
        "metadata": {},
    }


def match_intent(text: str, intents: list[dict]) -> dict | None:
    """Match text against intents using substring matching."""
    # Sort by priority (highest first)
    sorted_intents = sorted(intents, key=lambda i: i.get("priority", 0), reverse=True)

    for intent in sorted_intents:
        if not intent.get("is_active", True):
            continue
        for pattern in intent.get("patterns", []):
            if pattern.lower() in text:
                return intent
    return None


async def process_flora_message(
    user_text: str,
    client_context: dict,
    history: list[dict] = None,
) -> dict:
    """Process a message for Flora AI chat."""
    system_prompt = FLORA_SYSTEM_PROMPT.format(
        client_name=client_context.get("client_name", "Cliente"),
        plan_name=client_context.get("plan_name", "Starter"),
        days_left=client_context.get("days_left", 0),
        bot_status=client_context.get("bot_status", "desconectado"),
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Add history (last 10 messages)
    if history:
        for msg in history[-10:]:
            role = "user" if msg.get("direction") == "inbound" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})

    messages.append({"role": "user", "content": user_text})

    plan = client_context.get("plan", "pro")
    result = await route_and_call(
        plan=plan,
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return {
        "reply": result["content"],
        "source": "llm",
        "metadata": {
            "provider": result["provider"],
            "model": result["model"],
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
        },
    }
