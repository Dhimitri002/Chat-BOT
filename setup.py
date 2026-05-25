"""🌸 Flora Platform — Setup do Projeto."""
from setuptools import find_packages, setup

setup(
    name="flora-platform",
    version="1.0.0",
    description="🌸 Plataforma Completa de Chatbots WhatsApp com Licenciamento",
    author="TiltzOff",
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests*", "docs*"]),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.34.0",
        "sqlalchemy[asyncio]>=2.0.36",
        "aiosqlite>=0.20.0",
        "pydantic>=2.10.0",
        "pydantic-settings>=2.6.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.18",
        "python-dotenv>=1.0.0",
        "httpx>=0.28.0",
        "orjson>=3.10.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.25.0",
            "pytest-cov>=6.0.0",
            "black>=24.10.0",
            "isort>=5.13.0",
            "flake8>=7.1.0",
        ],
        "admin": [
            "kivy[full]>=2.3.1",
            "kivymd>=2.0.1",
            "matplotlib>=3.9.0",
        ],
        "client": [
            "kivy[full]>=2.3.1",
            "kivymd>=2.0.1",
        ],
        "security": [
            "cryptography>=44.0.0",
            "argon2-cffi>=23.1.0",
            "pyotp>=2.9.0",
        ],
        "ai": [
            "openai>=1.57.0",
            "anthropic>=0.40.0",
        ],
        "redis": [
            "redis[hiredis]>=5.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flora-backend=backend.main:main",
            "flora-admin=app_admin.main:main",
            "flora-client=app_cliente.main:main",
        ],
    },
)
