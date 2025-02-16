import re
from typing import Any, Dict, List

import httpx  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from fastapi import HTTPException  # type: ignore

BASE_URL = "https://polonus.dworzeconline.pl"


async def fetch_routes_page(url: str, date: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url}?date={date}")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch routes page")

    return response.text


def parse_routes_page(routes_page: str, route_id: str) -> str:
    soup = BeautifulSoup(routes_page, "lxml")

    table = soup.find("table")

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        for cell in cells:
            if re.search(rf"\b{route_id}\b", cell.get_text(strip=True)):
                link = cells[1].find("a")
                if link and link.get("href"):
                    return link["href"]

    raise HTTPException(status_code=404, detail=f"Route ID {route_id} not found")


async def fetch_passenger_file(passenger_file_url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(passenger_file_url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch passenger file")
    return response.text


def parse_station_info(text: str) -> Dict[str, str]:
    parts = text.split(",", 1)
    if len(parts) == 2:
        return {"city": parts[0].strip(), "station": parts[1].strip()}
    return {"city": text.strip(), "station": ""}


def parse_route_number(text: str) -> str:
    match = re.search(r"kurs nr (\d+)", text)
    return match.group(1) if match else ""


def parse_departure_date(text: str) -> str:
    match = re.search(r"o godzinie (\d{4}-\d{2}-\d{2})", text)
    return match.group(1) if match else ""


def parse_passenger_data(text: str) -> List[Dict[str, Any]]:
    passengers = []
    lines = text.split("\n")
    current_station_info = None
    current_time = ""

    for line in lines:
        line = line.strip()

        if not line or line.startswith("====") or line.startswith("####"):
            continue

        station_match = re.match(r"([^,]+(?:,[^,]+)*)\s+(\d{2}:\d{2})", line)
        if station_match:
            station_text = station_match.group(1)
            current_time = station_match.group(2)
            current_station_info = parse_station_info(station_text)
            continue

        if re.match(r"^[A-ZĄĆĘŁŃÓŚŹŻ]", line):
            parts = line.split()

            name_parts = []
            for part in parts:
                if part.isupper():
                    name_parts.append(part)
                else:
                    break
            full_name = " ".join(name_parts)

            ticket_match = re.search(r"\d+/\d+", line)
            ticket_number = ticket_match.group(0) if ticket_match else ""

            price_match = re.search(r"(\d+,\d{2})\s*([a-zA-Zżąćęłńóśźż]+)", line)
            price = (
                float(price_match.group(1).replace(",", ".")) if price_match else 0.0
            )
            currency = price_match.group(2) if price_match else ""

            destination_match = re.search(r"zł\s+(.+)$", line)
            if destination_match and current_station_info:
                destination_info = parse_station_info(destination_match.group(1))
                departure_date = parse_departure_date(text)
                departure_datetime = f"{departure_date}T{current_time}:00"

                passenger = {
                    "full_name": full_name,
                    "ticket_number": ticket_number,
                    "price": price,
                    "currency": currency,
                    "departure_city": current_station_info["city"],
                    "departure_station": current_station_info["station"],
                    "arrival_city": destination_info["city"],
                    "arrival_station": destination_info["station"],
                    "departure_time": departure_datetime,
                }
                passengers.append(passenger)

    return passengers


async def get_passenger_data(date: str, route_id: str) -> List[Dict[str, Any]]:
    routes_page = await fetch_routes_page(
        f"{BASE_URL}/diagrams/display/show/4385782a-5573-11e6-80f2-005056893b9e", date
    )

    passenger_file_url = parse_routes_page(routes_page, route_id)
    passenger_file_url = f"{BASE_URL}{passenger_file_url}"

    passenger_file_text = await fetch_passenger_file(passenger_file_url)

    passengers = parse_passenger_data(passenger_file_text)

    return passengers
