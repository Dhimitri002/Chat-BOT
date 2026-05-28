# 🔨 DECISIONS — Flora Platform

## 2026-05-28

### D1: Middleware Integration
**Decision**: Use `setup_security_middleware(app)` from `backend/core/middleware.py` in main.py  
**Why**: The middleware was implemented but never connected, leaving the API without rate limiting or security headers  
**Impact**: All API endpoints now have security headers, rate limiting, and request logging

### D2: App Structure Status
**Decision**: `app_admin/` and `app_cliente/` remain primary; `apps/admin/` and `apps/client/` pending migration  
**Why**: `run.py` references the old structure; `apps/` has more complete screens but needs careful merge  
**Impact**: No user-facing change yet; needs resolution in next session

### D3: Compatibility Target
**Decision**: Python 3.13.13 is the target  
**Why**: Project spec explicitly requires it  
**Impact**: All dependencies must be verified for 3.13 compatibility

### D4: Database
**Decision**: SQLAlchemy with async engine (asyncpg for PostgreSQL)  
**Why**: Already established in the codebase with 21 models  
**Impact**: All models use async-compatible patterns

### D5: LLM Router
**Decision**: Multi-provider with fallback chain  
**Why**: `backend/core/llm_router.py` already implements this  
**Impact**: Supports OpenAI, Gemini, Anthropic, Groq, and local models

### D6: Security Architecture
**Decision**: AES-256-GCM for data at rest, RSA for license signatures, JWT for auth  
**Why**: Already implemented; industry standard  
**Impact**: Full encryption chain for all sensitive data

### D7: Testing Strategy
**Decision**: pytest with async support, conftest for fixtures  
**Why**: 14 test files already use this pattern  
**Impact**: Backend is tested; apps need UI testing added
