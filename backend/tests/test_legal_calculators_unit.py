from lands_ai_backend.schemas.calculators import LandRatesRequest, StampDutyRequest
from lands_ai_backend.services.legal_calculators import LegalCalculatorsService


def test_calculate_stamp_duty_urban() -> None:
    payload = StampDutyRequest(property_value=1_000_000, property_type="urban")
    result = LegalCalculatorsService.calculate_stamp_duty(payload)

    assert result.rate_applied == 0.04
    assert result.stamp_duty == 40_000
    assert result.currency == "KES"


def test_calculate_stamp_duty_rural_and_agricultural() -> None:
    rural = StampDutyRequest(property_value=500_000, property_type="rural")
    agricultural = StampDutyRequest(property_value=500_000, property_type="agricultural")

    rural_result = LegalCalculatorsService.calculate_stamp_duty(rural)
    agricultural_result = LegalCalculatorsService.calculate_stamp_duty(agricultural)

    assert rural_result.rate_applied == 0.02
    assert rural_result.stamp_duty == 10_000

    assert agricultural_result.rate_applied == 0.01
    assert agricultural_result.stamp_duty == 5_000


def test_calculate_land_rates_estimate() -> None:
    payload = LandRatesRequest(property_value=2_000_000, county="Nairobi")
    result = LegalCalculatorsService.calculate_land_rates(payload)

    assert result.estimated_annual_rates == 10_000
    assert result.currency == "KES"
    assert "estimate" in result.note.lower()
