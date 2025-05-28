from fastapi import FastAPI  # type: ignore

from app.polonus.schemas import RouteRequest, RouteResponse
from app.polonus.utils import get_passenger_data

polonus = FastAPI(title="Polonus", description="Polonus SubApp", version="1.0.0")


@polonus.post("/get-passengers", response_model=RouteResponse)
async def get_passengers_v2(route_request: RouteRequest):
    passengers = await get_passenger_data(
        route_request.date, str(route_request.route_id)
    )

    return RouteResponse(
        route_id=route_request.route_id, date=route_request.date, passengers=passengers
    )
