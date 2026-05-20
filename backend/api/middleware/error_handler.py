"""
Flora Platform — Global Error Handler
"""
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import datetime, timezone
import logging
import traceback

logger = logging.getLogger("flora.errors")


def register_error_handlers(app: FastAPI):
    """Register all global error handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "validation_error",
                "message": "Request validation failed",
                "details": errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": "integrity_error",
                "message": "Database constraint violation. The resource may already exist.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        logger.critical(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "database_error",
                "message": "Database is temporarily unavailable. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "not_found",
                "message": f"Resource not found: {request.url.path}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.critical(f"Internal server error: {exc}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "unexpected_error",
                "message": "An unexpected error occurred.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
