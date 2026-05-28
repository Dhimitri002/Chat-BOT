# ⏳ PENDING — Flora Platform

## Critical (P0)
- [ ] Remove empty `integrated-api/` directory
- [ ] Remove temporary `compile_check.py` from root
- [ ] Implement monitoring module (health checks, metrics, alerting)
- [ ] Merge duplicate app structures or update run.py to use `apps/`

## Important (P1)
- [ ] Update README.md with accurate project state
- [ ] Connect Flora AI (brain/flora.py) to backend API
- [ ] Implement WhatsApp connection flow (QR code → session)
- [ ] Add end-to-end tests for critical flows
- [ ] Verify all 279 requirements for Python 3.13.13 compatibility
- [ ] Split requirements.txt into modular files
- [ ] Fill `backend/services/__init__.py` with proper exports

## Enhancement (P2)
- [ ] Implement automated database backup
- [ ] Implement notification system (email/push)
- [ ] Add Prometheus metrics endpoint
- [ ] Implement audit log viewer in admin app
- [ ] Add multi-language support (i18n)
- [ ] Implement dark/light theme toggle in apps
- [ ] Add API versioning strategy (v1 → v2)

## Known Issues
- `apps/admin/` and `apps/client/` have more complete screens but aren't used by run.py
- Tests cover backend, but not app UI
- `whatsapp-bot/` directory is Node.js code (separate connector) — needs documentation
- `integrated-api/` is an empty orphan directory
- `monitoring/` and `scripts/` directories are empty
