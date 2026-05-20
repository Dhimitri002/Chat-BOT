"""CORS Middleware Configuration."""
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings


def setup_cors(app):
    """Configura CORS para a aplicação."""
    origins = settings.CORS_ORIGINS or [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
