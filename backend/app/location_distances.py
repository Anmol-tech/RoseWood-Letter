from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass

import httpx

from app.schemas import SuggestedLocationDistance


@dataclass(frozen=True)
class PlaceAlias:
    property_location: str
    place_name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class Coordinates:
    lat: float
    lon: float
    label: str


PROPERTY_QUERIES = {
    "Rosewood Hong Kong": "Victoria Dockside Hong Kong",
    "Rosewood Washington DC": "Rosewood Washington DC, 1050 31st St NW, Washington, DC 20007",
    "Rosewood Menlo Park": "Rosewood Sand Hill, 2825 Sand Hill Road, Menlo Park, CA 94025",
    "Rosewood London": "Rosewood London, 252 High Holborn, London",
    "Rosewood New York": "The Carlyle, A Rosewood Hotel, 35 East 76th Street, New York, NY",
}

PLACE_ALIASES: tuple[PlaceAlias, ...] = (
    PlaceAlias(
        property_location="Rosewood Hong Kong",
        place_name="Lai Ching Heen",
        aliases=("lai ching heen", "yan toh heen", "regent hong kong", "intercontinental"),
    ),
    PlaceAlias(
        property_location="Rosewood Washington DC",
        place_name="Blue Duck Tavern",
        aliases=("blue duck tavern", "park hyatt washington", "24th street nw", "m street"),
    ),
    PlaceAlias(
        property_location="Rosewood Menlo Park",
        place_name="Stanford Dish Loop",
        aliases=("stanford dish", "dish loop", "dish reserve", "the dish"),
    ),
    PlaceAlias(
        property_location="Rosewood Menlo Park",
        place_name="Filoli Historic House & Garden",
        aliases=("filoli", "filoli historic house", "filoli historic house & garden", "filoli historic house and garden"),
    ),
    PlaceAlias(
        property_location="Rosewood Menlo Park",
        place_name="Allied Arts Guild",
        aliases=("allied arts guild", "allied arts"),
    ),
    PlaceAlias(
        property_location="Rosewood Menlo Park",
        place_name="Cantor Arts Center",
        aliases=("cantor arts center", "cantor", "rodin sculpture garden", "stanford museum"),
    ),
    PlaceAlias(
        property_location="Rosewood London",
        place_name="Sir John Soane's Museum",
        aliases=("sir john soane", "sir john soane's museum", "soane museum"),
    ),
    PlaceAlias(
        property_location="Rosewood London",
        place_name="The British Museum",
        aliases=("british museum", "the british museum"),
    ),
    PlaceAlias(
        property_location="Rosewood New York",
        place_name="Neue Galerie",
        aliases=("neue galerie", "neue galerie new york"),
    ),
)

_GEOCODE_CACHE: dict[str, Coordinates | None] = {}
_ROUTE_CACHE: dict[str, tuple[float, float] | None] = {}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _property_matches(entry_property: str, requested_property: str) -> bool:
    normalized_entry = _normalize(entry_property)
    normalized_requested = _normalize(requested_property)
    return normalized_entry == normalized_requested or normalized_entry in normalized_requested


def _known_place_for_text(property_location: str, recommendation: str) -> PlaceAlias | None:
    normalized_recommendation = _normalize(recommendation)
    for alias in PLACE_ALIASES:
        if not _property_matches(alias.property_location, property_location):
            continue
        names = (alias.place_name, *alias.aliases)
        if any(_normalize(name) in normalized_recommendation for name in names):
            return alias
    return None


def _clean_candidate(candidate: str) -> str:
    candidate = re.sub(r"\s+", " ", candidate).strip(" .,:;\"'")
    candidate = re.split(
        r"\s+(?:before|after|tonight|today|tomorrow|because|where|when|while|so|and then|for a|with a)\b",
        candidate,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    candidate = re.sub(r"\s+(?:on|in|near|across|beside)\s+.+$", "", candidate, flags=re.IGNORECASE)
    return candidate.strip(" .,:;\"'")


def extract_suggested_place(property_location: str, recommendation: str) -> tuple[str, list[str]]:
    known_place = _known_place_for_text(property_location, recommendation)
    if known_place:
        aliases = list(dict.fromkeys((known_place.place_name, *known_place.aliases)))
        return known_place.place_name, aliases

    patterns = (
        r"(?:reserve|book|hold|visit|try|walk to|table at|room at|dinner at)\s+([A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*){0,7})",
        r"\bat\s+([A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*){0,7})",
        r"\bto\s+([A-Z][A-Za-z0-9'&.-]*(?:\s+[A-Z][A-Za-z0-9'&.-]*){0,7})",
    )
    for pattern in patterns:
        match = re.search(pattern, recommendation)
        if match:
            candidate = _clean_candidate(match.group(1))
            if len(candidate) >= 4:
                return candidate, [candidate]

    title_chunks = re.findall(
        r"\b[A-Z][A-Za-z0-9'&.-]*(?:\s+(?:[A-Z][A-Za-z0-9'&.-]*|&)){1,6}",
        recommendation,
    )
    if title_chunks:
        candidate = _clean_candidate(max(title_chunks, key=len))
        return candidate, [candidate]

    return "", []


def _property_query(property_location: str) -> str:
    for property_name, query in PROPERTY_QUERIES.items():
        if _property_matches(property_name, property_location):
            return query
    return property_location


def _place_query(place_name: str, property_location: str) -> str:
    property_query = _property_query(property_location)
    return f"{place_name}, {property_query}"


def _place_queries(place_name: str, property_location: str, aliases: list[str]) -> list[str]:
    property_query = _property_query(property_location)
    candidates = [
        f"{place_name}, {property_location}",
        f"{place_name}, {property_query}",
        place_name,
    ]
    for alias in aliases:
        if len(alias) >= 4:
            candidates.extend(
                [
                    f"{alias}, {property_location}",
                    alias,
                ]
            )
    return list(dict.fromkeys(candidates))


def _user_agent() -> str:
    return os.getenv(
        "LOCATION_LOOKUP_USER_AGENT",
        "RosewoodLetterHackathon/0.1 (local demo distance lookup)",
    )


async def _geocode(query: str) -> Coordinates | None:
    cache_key = _normalize(query)
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": _user_agent()},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        _GEOCODE_CACHE[cache_key] = None
        return None

    results = response.json()
    if not results:
        _GEOCODE_CACHE[cache_key] = None
        return None

    result = results[0]
    coordinates = Coordinates(
        lat=float(result["lat"]),
        lon=float(result["lon"]),
        label=result.get("display_name", query),
    )
    _GEOCODE_CACHE[cache_key] = coordinates
    return coordinates


def _geocode_sync(query: str) -> Coordinates | None:
    cache_key = _normalize(query)
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    try:
        with httpx.Client(timeout=6) as client:
            response = client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": _user_agent()},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        _GEOCODE_CACHE[cache_key] = None
        return None

    results = response.json()
    if not results:
        _GEOCODE_CACHE[cache_key] = None
        return None

    result = results[0]
    coordinates = Coordinates(
        lat=float(result["lat"]),
        lon=float(result["lon"]),
        label=result.get("display_name", query),
    )
    _GEOCODE_CACHE[cache_key] = coordinates
    return coordinates


async def _driving_route(origin: Coordinates, destination: Coordinates) -> tuple[float, float] | None:
    cache_key = f"{origin.lon:.5f},{origin.lat:.5f};{destination.lon:.5f},{destination.lat:.5f}"
    if cache_key in _ROUTE_CACHE:
        return _ROUTE_CACHE[cache_key]

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.get(
                f"https://router.project-osrm.org/route/v1/driving/{cache_key}",
                params={"overview": "false"},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        _ROUTE_CACHE[cache_key] = None
        return None

    routes = response.json().get("routes", [])
    if not routes:
        _ROUTE_CACHE[cache_key] = None
        return None

    route = routes[0]
    value = (float(route["distance"]) / 1000, float(route["duration"]) / 60)
    _ROUTE_CACHE[cache_key] = value
    return value


def _driving_route_sync(origin: Coordinates, destination: Coordinates) -> tuple[float, float] | None:
    cache_key = f"{origin.lon:.5f},{origin.lat:.5f};{destination.lon:.5f},{destination.lat:.5f}"
    if cache_key in _ROUTE_CACHE:
        return _ROUTE_CACHE[cache_key]

    try:
        with httpx.Client(timeout=6) as client:
            response = client.get(
                f"https://router.project-osrm.org/route/v1/driving/{cache_key}",
                params={"overview": "false"},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        _ROUTE_CACHE[cache_key] = None
        return None

    routes = response.json().get("routes", [])
    if not routes:
        _ROUTE_CACHE[cache_key] = None
        return None

    route = routes[0]
    value = (float(route["distance"]) / 1000, float(route["duration"]) / 60)
    _ROUTE_CACHE[cache_key] = value
    return value


def _haversine_km(origin: Coordinates, destination: Coordinates) -> float:
    radius_km = 6371
    lat1 = math.radians(origin.lat)
    lat2 = math.radians(destination.lat)
    delta_lat = math.radians(destination.lat - origin.lat)
    delta_lon = math.radians(destination.lon - origin.lon)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _format_distance(km: float) -> str:
    miles = km * 0.621371
    if km < 1:
        meters = round(km * 1000 / 50) * 50
        return f"about {miles:.1f} mi / {meters:.0f} m"
    return f"about {miles:.1f} mi / {km:.1f} km"


def _format_time(minutes: float, mode: str) -> str:
    low = max(2, int(round(minutes * 0.85)))
    high = max(low + 1, int(round(minutes * 1.2)))
    if high <= 3:
        return f"{low} to {high} minutes {mode}"
    low = max(3, round(low / 5) * 5 if low >= 10 else low)
    high = max(low + 2, round(high / 5) * 5 if high >= 10 else high)
    return f"{low} to {high} minutes {mode}"


async def lookup_suggested_location_distance(
    property_location: str, recommendation: str, place_name: str | None = None
) -> SuggestedLocationDistance | None:
    extracted_place_name, aliases = extract_suggested_place(property_location, recommendation)
    place_name = (place_name or "").strip() or extracted_place_name
    if not place_name:
        return None
    aliases = list(dict.fromkeys([place_name, *aliases]))

    property_coordinates, place_coordinates = await _lookup_coordinates(
        property_location,
        place_name,
        aliases,
    )
    if property_coordinates is None or place_coordinates is None:
        return None

    return await _distance_hint_from_coordinates(
        property_location,
        place_name,
        aliases,
        property_coordinates,
        place_coordinates,
    )


def lookup_suggested_location_distance_sync(
    property_location: str, recommendation: str, place_name: str | None = None
) -> SuggestedLocationDistance | None:
    extracted_place_name, aliases = extract_suggested_place(property_location, recommendation)
    place_name = (place_name or "").strip() or extracted_place_name
    if not place_name:
        return None
    aliases = list(dict.fromkeys([place_name, *aliases]))

    property_coordinates = _geocode_sync(_property_query(property_location))
    place_coordinates = _lookup_place_coordinates_sync(place_name, property_location, aliases)
    if property_coordinates is None or place_coordinates is None:
        return None

    return _distance_hint_from_coordinates_sync(
        property_location,
        place_name,
        aliases,
        property_coordinates,
        place_coordinates,
    )


async def _lookup_coordinates(
    property_location: str,
    place_name: str,
    aliases: list[str],
) -> tuple[Coordinates | None, Coordinates | None]:
    property_coordinates = await _geocode(_property_query(property_location))
    place_coordinates = await _lookup_place_coordinates(place_name, property_location, aliases)
    return property_coordinates, place_coordinates


async def _lookup_place_coordinates(
    place_name: str,
    property_location: str,
    aliases: list[str],
) -> Coordinates | None:
    for query in _place_queries(place_name, property_location, aliases):
        coordinates = await _geocode(query)
        if coordinates is not None:
            return coordinates
    return None


def _lookup_place_coordinates_sync(
    place_name: str,
    property_location: str,
    aliases: list[str],
) -> Coordinates | None:
    for query in _place_queries(place_name, property_location, aliases):
        coordinates = _geocode_sync(query)
        if coordinates is not None:
            return coordinates
    return None


async def _distance_hint_from_coordinates(
    property_location: str,
    place_name: str,
    aliases: list[str],
    property_coordinates: Coordinates,
    place_coordinates: Coordinates,
) -> SuggestedLocationDistance:
    direct_km = _haversine_km(property_coordinates, place_coordinates)
    if direct_km <= 1.2:
        route_km = max(0.1, direct_km * 1.25)
        minutes = route_km / 4.8 * 60
        mode = "on foot"
        confidence = "geocoded_estimate"
    else:
        route = await _driving_route(property_coordinates, place_coordinates)
        route_km, minutes = route if route else (direct_km * 1.3, direct_km * 1.3 / 26 * 60)
        mode = "by car"
        confidence = "geocoded_route" if route else "geocoded_estimate"

    return _build_distance_hint(property_location, place_name, aliases, route_km, minutes, mode, confidence)


def _distance_hint_from_coordinates_sync(
    property_location: str,
    place_name: str,
    aliases: list[str],
    property_coordinates: Coordinates,
    place_coordinates: Coordinates,
) -> SuggestedLocationDistance:
    direct_km = _haversine_km(property_coordinates, place_coordinates)
    if direct_km <= 1.2:
        route_km = max(0.1, direct_km * 1.25)
        minutes = route_km / 4.8 * 60
        mode = "on foot"
        confidence = "geocoded_estimate"
    else:
        route = _driving_route_sync(property_coordinates, place_coordinates)
        route_km, minutes = route if route else (direct_km * 1.3, direct_km * 1.3 / 26 * 60)
        mode = "by car"
        confidence = "geocoded_route" if route else "geocoded_estimate"

    return _build_distance_hint(property_location, place_name, aliases, route_km, minutes, mode, confidence)


def _build_distance_hint(
    property_location: str,
    place_name: str,
    aliases: list[str],
    route_km: float,
    minutes: float,
    mode: str,
    confidence: str,
) -> SuggestedLocationDistance:
    return SuggestedLocationDistance(
        place_name=place_name,
        property_location=property_location,
        distance_label=_format_distance(route_km),
        travel_time_label=_format_time(minutes, mode),
        travel_mode=mode.replace("by ", "").replace("on ", ""),
        note="Looked up from the property and suggested place; timing is approximate and not live traffic.",
        confidence=confidence,
        aliases=aliases,
    )
