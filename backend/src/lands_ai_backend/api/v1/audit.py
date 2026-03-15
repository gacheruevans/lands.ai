from fastapi import APIRouter, status

from lands_ai_backend.api.errors import ServiceError
from lands_ai_backend.services.audit_logging import AuditLoggingService

router = APIRouter()


@router.get("/events")
def list_audit_events(limit: int = 50) -> dict[str, list[dict]]:
    try:
        service = AuditLoggingService()
        return {"events": service.list_events(limit=limit)}
    except Exception as exc:
        raise ServiceError(
            code="AUDIT_EVENTS_FETCH_FAILED",
            message="Unable to fetch audit events right now.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
