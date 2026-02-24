from __future__ import annotations

from typing import Any
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request
import json
import os


class MapsRoutesService:
    """Google Maps/Routes utility wrapper (Places, Directions, Distance Matrix)."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()

    def _ensure_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("Set GOOGLE_MAPS_API_KEY in environment.")

    def places_search_text(self, query: str, limit: int = 5) -> dict[str, Any]:
        try:
            self._ensure_key()
            endpoint = "https://places.googleapis.com/v1/places:searchText"
            req = url_request.Request(
                endpoint,
                method="POST",
                data=json.dumps({"textQuery": query, "pageSize": limit}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
                },
            )
            with url_request.urlopen(req) as response:
                payload = json.loads(response.read().decode("utf-8"))

            places = payload.get("places", [])
            normalized = [
                {
                    "place_id": item.get("id"),
                    "name": item.get("displayName", {}).get("text", ""),
                    "address": item.get("formattedAddress", ""),
                    "location": item.get("location", {}),
                }
                for item in places
            ]
            return {
                "status": "success",
                "query": query,
                "count": len(normalized),
                "places": normalized,
            }
        except url_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {"status": "error", "code": "GMAPS_PLACES_HTTP_ERROR", "message": f"{exc.code} {exc.reason}: {detail}"}
        except Exception as exc:
            return {"status": "error", "code": "GMAPS_PLACES_FAILED", "message": str(exc)}

    def directions(self, origin: str, destination: str, mode: str = "driving") -> dict[str, Any]:
        try:
            self._ensure_key()
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": self.api_key,
            }
            endpoint = f"https://maps.googleapis.com/maps/api/directions/json?{url_parse.urlencode(params)}"
            with url_request.urlopen(endpoint) as response:
                payload = json.loads(response.read().decode("utf-8"))

            routes = payload.get("routes", [])
            if not routes:
                return {
                    "status": "error",
                    "code": "GMAPS_DIRECTIONS_EMPTY",
                    "message": payload.get("error_message", "No routes returned."),
                }
            leg = routes[0].get("legs", [{}])[0]
            return {
                "status": "success",
                "origin": origin,
                "destination": destination,
                "distance": leg.get("distance", {}),
                "duration": leg.get("duration", {}),
                "status_text": payload.get("status"),
            }
        except Exception as exc:
            return {"status": "error", "code": "GMAPS_DIRECTIONS_FAILED", "message": str(exc)}

    def distance_matrix(self, origins: list[str], destinations: list[str], mode: str = "driving") -> dict[str, Any]:
        try:
            self._ensure_key()
            params = {
                "origins": "|".join(origins),
                "destinations": "|".join(destinations),
                "mode": mode,
                "key": self.api_key,
            }
            endpoint = f"https://maps.googleapis.com/maps/api/distancematrix/json?{url_parse.urlencode(params)}"
            with url_request.urlopen(endpoint) as response:
                payload = json.loads(response.read().decode("utf-8"))

            rows = payload.get("rows", [])
            normalized_rows = []
            for row in rows:
                elements = row.get("elements", [])
                normalized_rows.append(
                    [
                        {
                            "status": element.get("status"),
                            "distance": element.get("distance", {}),
                            "duration": element.get("duration", {}),
                        }
                        for element in elements
                    ]
                )

            return {
                "status": "success",
                "origins": origins,
                "destinations": destinations,
                "matrix": normalized_rows,
                "status_text": payload.get("status"),
            }
        except Exception as exc:
            return {"status": "error", "code": "GMAPS_DISTANCE_MATRIX_FAILED", "message": str(exc)}
