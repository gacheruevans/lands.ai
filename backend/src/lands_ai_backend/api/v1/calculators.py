from fastapi import APIRouter, Depends, status

from lands_ai_backend.api.errors import ServiceError
from lands_ai_backend.schemas.calculators import (
    StampDutyRequest,
    StampDutyResponse,
    LandRatesRequest,
    LandRatesResponse,
)
from lands_ai_backend.services.legal_calculators import LegalCalculatorsService

router = APIRouter()


def get_calculator_service() -> LegalCalculatorsService:
    return LegalCalculatorsService()


@router.post("/stamp-duty", response_model=StampDutyResponse)
def calculate_stamp_duty(
    payload: StampDutyRequest,
    service: LegalCalculatorsService = Depends(get_calculator_service),
) -> StampDutyResponse:
    try:
        return service.calculate_stamp_duty(payload)
    except Exception as exc:
        raise ServiceError(
            code="STAMP_DUTY_CALCULATION_FAILED",
            message="Unable to calculate stamp duty right now.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc


@router.post("/land-rates", response_model=LandRatesResponse)
def calculate_land_rates(
    payload: LandRatesRequest,
    service: LegalCalculatorsService = Depends(get_calculator_service),
) -> LandRatesResponse:
    try:
        return service.calculate_land_rates(payload)
    except Exception as exc:
        raise ServiceError(
            code="LAND_RATES_CALCULATION_FAILED",
            message="Unable to calculate land rates right now.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
