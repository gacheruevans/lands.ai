from enum import Enum
from pydantic import BaseModel


class PropertyType(str, Enum):
    URBAN = "urban"
    RURAL = "rural"
    AGRICULTURAL = "agricultural"


class StampDutyRequest(BaseModel):
    property_value: float
    property_type: PropertyType


class StampDutyResponse(BaseModel):
    property_value: float
    property_type: PropertyType
    stamp_duty: float
    rate_applied: float
    currency: str = "KES"


class LandRatesRequest(BaseModel):
    property_value: float
    county: str


class LandRatesResponse(BaseModel):
    property_value: float
    county: str
    estimated_annual_rates: float
    currency: str = "KES"
    note: str
