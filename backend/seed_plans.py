"""
Flora Platform — Seed Default Plans
Creates the 7 default plans if they don't exist.
"""
import asyncio
import uuid

from sqlalchemy import select

from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models.plan import Plan


DEFAULT_PLANS = [
    {
        "name": "Gratuito",
        "slug": "free",
        "description": "Para testar a plataforma",
        "price_monthly": 0,
        "price_yearly": 0,
        "max_bots": 1,
        "max_messages_per_day": 50,
        "max_contacts": 100,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": False,
            "analytics": False,
            "priority_support": False,
            "api_access": False,
            "webhooks": False,
            "multi_agent": False,
            "custom_llm": False,
        },
        "is_public": True,
        "sort_order": 1,
    },
    {
        "name": "Starter",
        "slug": "starter",
        "description": "Para pequenos negócios",
        "price_monthly": 49.90,
        "price_yearly": 479.90,
        "max_bots": 1,
        "max_messages_per_day": 500,
        "max_contacts": 1000,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": True,
            "analytics": True,
            "priority_support": False,
            "api_access": False,
            "webhooks": False,
            "multi_agent": False,
            "custom_llm": False,
        },
        "is_public": True,
        "sort_order": 2,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "Para negócios em crescimento",
        "price_monthly": 99.90,
        "price_yearly": 959.90,
        "max_bots": 3,
        "max_messages_per_day": 2000,
        "max_contacts": 5000,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": True,
            "analytics": True,
            "priority_support": True,
            "api_access": True,
            "webhooks": True,
            "multi_agent": False,
            "custom_llm": False,
        },
        "is_public": True,
        "sort_order": 3,
    },
    {
        "name": "Business",
        "slug": "business",
        "description": "Para empresas",
        "price_monthly": 199.90,
        "price_yearly": 1919.90,
        "max_bots": 5,
        "max_messages_per_day": 10000,
        "max_contacts": 20000,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": True,
            "analytics": True,
            "priority_support": True,
            "api_access": True,
            "webhooks": True,
            "multi_agent": True,
            "custom_llm": False,
        },
        "is_public": True,
        "sort_order": 4,
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "description": "Para grandes operações",
        "price_monthly": 499.90,
        "price_yearly": 4799.90,
        "max_bots": 20,
        "max_messages_per_day": 50000,
        "max_contacts": 100000,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": True,
            "analytics": True,
            "priority_support": True,
            "api_access": True,
            "webhooks": True,
            "multi_agent": True,
            "custom_llm": True,
        },
        "is_public": True,
        "sort_order": 5,
    },
    {
        "name": "Reseller",
        "slug": "reseller",
        "description": "Para revendedores",
        "price_monthly": 799.90,
        "price_yearly": 7679.90,
        "max_bots": 50,
        "max_messages_per_day": 100000,
        "max_contacts": 500000,
        "features": {
            "ai_chat": True,
            "basic_commands": True,
            "whatsapp_connection": True,
            "custom_personality": True,
            "analytics": True,
            "priority_support": True,
            "api_access": True,
            "webhooks": True,
            "multi_agent": True,
            "custom_llm": True,
            "white_label": True,
        },
        "is_public": False,
        "sort_order": 6,
    },
    {
        "name": "Custom",
        "slug": "custom",
        "description": "Plano personalizado",
        "price_monthly": 0,
        "price_yearly": 0,
        "max_bots": 0,
        "max_messages_per_day": 0,
        "max_contacts": 0,
        "features": {
            "ai_chat": True,
            "custom": True,
        },
        "is_public": False,
        "sort_order": 7,
    },
]


async def seed_plans():
    """Seed default plans into the database."""
    async with AsyncSessionLocal() as db:
        created = 0
        for plan_data in DEFAULT_PLANS:
            existing = await db.execute(
                select(Plan).where(Plan.slug == plan_data["slug"])
            )
            if not existing.scalar_one_or_none():
                plan = Plan(
                    id=str(uuid.uuid4()),
                    **plan_data,
                )
                db.add(plan)
                created += 1
                print(f"  ✅ Created plan: {plan_data['name']}")
            else:
                print(f"  ⏭️  Plan already exists: {plan_data['name']}")

        await db.commit()
        print(f"\n🌸 {created} plans created!")


if __name__ == "__main__":
    asyncio.run(seed_plans())
