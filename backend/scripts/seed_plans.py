"""Seed default plans"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import async_session, engine, Base
from backend.models.plan import Plan


DEFAULT_PLANS = [
    {
        "name": "Starter", "slug": "starter", "description": "Seu primeiro bot",
        "price_monthly": 29.90, "price_yearly": 299.00,
        "max_bots": 1, "max_messages_month": 500, "max_commands": 10, "max_memory_items": 50,
        "has_llm": False, "has_media": False, "has_pdf": False, "has_image": False,
        "has_flora": False, "has_custom_commands": False, "has_automations": False,
        "has_webhooks": False, "has_analytics": False, "display_order": 1,
    },
    {
        "name": "Basic", "slug": "basic", "description": "Mais poder",
        "price_monthly": 59.90, "price_yearly": 599.00,
        "max_bots": 1, "max_messages_month": 1000, "max_commands": 25, "max_memory_items": 100,
        "has_llm": False, "has_media": False, "has_pdf": False, "has_image": False,
        "has_flora": False, "has_custom_commands": False, "has_automations": False,
        "has_webhooks": False, "has_analytics": True, "display_order": 2,
    },
    {
        "name": "Plus", "slug": "plus", "description": "Profissional",
        "price_monthly": 99.90, "price_yearly": 999.00,
        "max_bots": 2, "max_messages_month": 2500, "max_commands": 50, "max_memory_items": 250,
        "has_llm": False, "has_media": True, "has_pdf": False, "has_image": False,
        "has_flora": False, "has_custom_commands": False, "has_automations": False,
        "has_webhooks": True, "has_analytics": True, "display_order": 3,
    },
    {
        "name": "Pro", "slug": "pro", "description": "Inteligente",
        "price_monthly": 199.90, "price_yearly": 1999.00,
        "max_bots": 3, "max_messages_month": 5000, "max_commands": 100, "max_memory_items": 500,
        "has_llm": True, "llm_provider": "groq", "llm_model": "llama-3.1-70b-versatile",
        "has_media": True, "has_pdf": True, "has_image": True,
        "has_flora": True, "flora_model": "gemini-1.5-flash",
        "has_custom_commands": True, "has_automations": False,
        "has_webhooks": True, "has_analytics": True, "display_order": 4,
    },
    {
        "name": "Master", "slug": "master", "description": "Poder máximo",
        "price_monthly": 399.90, "price_yearly": 3999.00,
        "max_bots": 5, "max_messages_month": 15000, "max_commands": 250, "max_memory_items": 2000,
        "has_llm": True, "llm_provider": "openai", "llm_model": "gpt-4o-mini",
        "has_media": True, "has_pdf": True, "has_image": True, "has_audio": True, "has_transcription": True,
        "has_flora": True, "flora_model": "gpt-4o-mini",
        "has_custom_commands": True, "has_automations": True,
        "has_webhooks": True, "has_analytics": True, "has_multi_device": True,
        "display_order": 5,
    },
    {
        "name": "Elite", "slug": "elite", "description": "Negócio sério",
        "price_monthly": 799.90, "price_yearly": 7999.00,
        "max_bots": 10, "max_messages_month": 50000, "max_commands": 500, "max_memory_items": 10000,
        "has_llm": True, "llm_provider": "openai", "llm_model": "gpt-4o",
        "has_media": True, "has_pdf": True, "has_image": True, "has_audio": True, "has_transcription": True,
        "has_flora": True, "flora_model": "gpt-4o",
        "has_custom_commands": True, "has_automations": True,
        "has_webhooks": True, "has_analytics": True, "has_api_access": True,
        "has_whitelabel": True, "has_multi_device": True, "has_priority_support": True,
        "display_order": 6,
    },
    {
        "name": "Enterprise", "slug": "enterprise", "description": "Sob medida",
        "price_monthly": 0, "price_yearly": 0,
        "max_bots": 999, "max_messages_month": 999999, "max_commands": 9999, "max_memory_items": 99999,
        "has_llm": True, "llm_provider": "openai", "llm_model": "gpt-4o",
        "has_media": True, "has_pdf": True, "has_image": True, "has_audio": True, "has_transcription": True,
        "has_flora": True, "flora_model": "gpt-4o",
        "has_custom_commands": True, "has_automations": True,
        "has_webhooks": True, "has_analytics": True, "has_api_access": True,
        "has_whitelabel": True, "has_multi_device": True, "has_priority_support": True,
        "is_public": False, "display_order": 7,
    },
]


async def seed_plans():
    async with async_session() as session:
        for plan_data in DEFAULT_PLANS:
            existing = await session.execute(
                __import__("sqlalchemy").select(Plan).where(Plan.slug == plan_data["slug"])
            )
            if not existing.scalar_one_or_none():
                plan = Plan(**plan_data)
                session.add(plan)
                print(f"  Created plan: {plan.name}")
        await session.commit()
        print("✅ Plans seeded!")


if __name__ == "__main__":
    asyncio.run(seed_plans())
