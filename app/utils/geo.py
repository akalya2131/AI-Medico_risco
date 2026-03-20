from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def closest_hospital(patient: dict, hospitals: list[dict]) -> dict | None:
    if not patient.get("lat") or not patient.get("lng"):
        return None

    ranked = []
    for hospital in hospitals:
        distance = haversine_km(patient["lat"], patient["lng"], hospital["lat"], hospital["lng"])
        ranked.append({**hospital, "distance_km": round(distance, 1)})

    ranked.sort(key=lambda item: item["distance_km"])
    return ranked[0] if ranked else None
