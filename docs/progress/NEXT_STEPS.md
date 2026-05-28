# 📋 NEXT STEPS — Flora Platform

## Immediate (This Session)
1. Remove `integrated-api/` empty directory
2. Create monitoring module (`monitoring/health.py`, `monitoring/metrics.py`)
3. Create remaining continuity files:
   - `AI_WORKLOG.md`
   - `PENDING.md`
   - `DECISIONS.md`
   - `CURRENT_PHASE.md`
   - `ROADMAP_PROGRESS.md`
   - `LAST_CONTEXT.json`
4. Update README.md with actual project state

## Short Term (Next Sessions)
1. **Merge app structures**: Decide whether to:
   - Migrate run.py to use `apps/admin/` + `apps/client/` (recommended — more complete)
   - Or merge new screens into old `app_admin/` + `app_cliente/`
   - Delete the unused structure after merge
2. **Flora AI integration**: Connect `brain/flora.py` to backend API
3. **WhatsApp connector**: Implement the actual WhatsApp connection flow
4. **End-to-end tests**: Add e2e tests for critical flows
5. **Backup module**: Implement automated database backup
6. **Notification module**: Implement email/push notifications

## Dependencies to Verify
- Check all 279 requirements in `requirements.txt` for Python 3.13.13 compatibility
- Remove packages that don't exist or are abandoned
- Split into modular requirement files
