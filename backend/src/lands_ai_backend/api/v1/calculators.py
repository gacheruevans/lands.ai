from fastapi import APIRouter, Depends

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
    return service.calculate_stamp_duty(payload)


@router.post("/land-rates", response_model=LandRatesResponse)
def calculate_land_rates(
    payload: LandRatesRequest,
    service: LegalCalculatorsService = Depends(get_calculator_service),
) -> LandRatesResponse:
    return service.calculate_land_rates(payload)
