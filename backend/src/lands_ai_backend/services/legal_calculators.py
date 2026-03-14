from lands_ai_backend.schemas.calculators import (
    PropertyType,
    StampDutyRequest,
    StampDutyResponse,
    LandRatesRequest,
    LandRatesResponse,
)


class LegalCalculatorsService:
    @staticmethod
    def calculate_stamp_duty(payload: StampDutyRequest) -> StampDutyResponse:
        """
        Calculate stamp duty based on Kenyan law:
        - Agricultural: 1%
        - Rural: 2%
        - Urban/Commercial: 4%
        """
        rates = {
            PropertyType.AGRICULTURAL: 0.01,
            PropertyType.RURAL: 0.02,
            PropertyType.URBAN: 0.04,
        }
        rate = rates.get(payload.property_type, 0.04)
        stamp_duty = payload.property_value * rate

        return StampDutyResponse(
            property_value=payload.property_value,
            property_type=payload.property_type,
            stamp_duty=stamp_duty,
            rate_applied=rate,
        )

    @staticmethod
    def calculate_land_rates(payload: LandRatesRequest) -> LandRatesResponse:
        """
        Placeholder logic for land rates.
        In reality, this varies by county and valuation roll.
        Typically around 0.1% to 1% of unimproved site value.
        """
        # Default placeholder rate
        estimated_rate = 0.005 
        estimated_annual_rates = payload.property_value * estimated_rate

        return LandRatesResponse(
            property_value=payload.property_value,
            county=payload.county,
            estimated_annual_rates=estimated_annual_rates,
            note="This is an estimate based on a standard 0.5% rate. Actual rates depend on the specific county valuation roll."
        )
