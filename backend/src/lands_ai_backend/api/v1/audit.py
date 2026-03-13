from fastapi import APIRouter

from lands_ai_backend.services.audit_logging import AuditLoggingService

router = APIRouter()


@router.get("/events")
def list_audit_events(limit: int = 50) -> dict[str, list[dict]]:
    service = AuditLoggingService()
    return {"events": service.list_events(limit=limit)}
