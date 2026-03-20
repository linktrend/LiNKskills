from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any
from urllib import parse as url_parse
from urllib import request as url_request
import json


class EnvContextService:
    """Environment context service (weather, timezone, route optimization)."""

    def weather_current(self, latitude: float, longitude: float) -> dict[str, Any]:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                "timezone": "auto",
            }
            endpoint = f"https://api.open-meteo.com/v1/forecast?{url_parse.urlencode(params)}"
            with url_request.urlopen(endpoint) as response:
                payload = json.loads(response.read().decode("utf-8"))
            current = payload.get("current", {})
            return {
                "status": "success",
                "latitude": payload.get("latitude", latitude),
                "longitude": payload.get("longitude", longitude),
                "timezone": payload.get("timezone"),
                "current": current,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GENV_WEATHER_FAILED",
                "message": str(exc),
            }

    def time_zone(self, latitude: float, longitude: float) -> dict[str, Any]:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m",
                "timezone": "auto",
            }
            endpoint = f"https://api.open-meteo.com/v1/forecast?{url_parse.urlencode(params)}"
            with url_request.urlopen(endpoint) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "status": "success",
                "timezone": payload.get("timezone"),
                "timezone_abbreviation": payload.get("timezone_abbreviation"),
                "utc_offset_seconds": payload.get("utc_offset_seconds"),
                "current_time": payload.get("current", {}).get("time"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GENV_TIMEZONE_FAILED",
                "message": str(exc),
            }

    def route_optimize(
        self,
        origin: dict[str, float],
        stops: list[dict[str, float]],
        round_trip: bool = False,
    ) -> dict[str, Any]:
        try:
            if not stops:
                return {
                    "status": "success",
                    "route": [origin],
                    "distance_km": 0.0,
                    "round_trip": round_trip,
                }

            remaining = [dict(stop) for stop in stops]
            route = [dict(origin)]
            total_distance = 0.0
            current = dict(origin)

            while remaining:
                next_stop = min(
                    remaining,
                    key=lambda stop: self._haversine_km(current["lat"], current["lng"], stop["lat"], stop["lng"]),
                )
                total_distance += self._haversine_km(current["lat"], current["lng"], next_stop["lat"], next_stop["lng"])
                route.append(next_stop)
                current = next_stop
                remaining.remove(next_stop)

            if round_trip:
                total_distance += self._haversine_km(current["lat"], current["lng"], origin["lat"], origin["lng"])
                route.append(dict(origin))

            return {
                "status": "success",
                "route": route,
                "distance_km": round(total_distance, 3),
                "round_trip": round_trip,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GENV_ROUTE_OPTIMIZE_FAILED",
                "message": str(exc),
            }

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        earth_radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = (
            sin(d_lat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        )
        c = 2 * asin(sqrt(a))
        return earth_radius_km * c
