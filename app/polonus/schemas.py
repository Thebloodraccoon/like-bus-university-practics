from datetime import datetime

from pydantic import BaseModel, field_validator  # type: ignore


class RouteRequest(BaseModel):
    date: str
    route_id: int

    @field_validator("date", mode="before")
    def validate_date(cls, value: str) -> str:
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d")

            if not (1 <= date_obj.month <= 12):
                raise ValueError("Invalid month")

            if not (1 <= date_obj.day <= 31):
                raise ValueError("Invalid day")

            return date_obj.strftime("%Y-%m-%d")

        except ValueError:
            raise ValueError(
                "Invalid date format. Use YYYY-MM-DD and ensure date is valid"
            )


class Passenger(BaseModel):
    full_name: str
    ticket_number: str
    price: float
    currency: str
    departure_city: str
    departure_station: str
    arrival_city: str
    arrival_station: str
    departure_time: str


class RouteResponse(BaseModel):
    route_id: int
    date: str
    passengers: list[Passenger]
