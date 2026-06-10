from urllib.parse import quote_plus


REMOTE_LABEL = "Remote"
REMOTE_SYNONYMS = {
    "remote",
    "remotely",
    "wfh",
    "work from home",
    "home office",
    "telework",
    "teleworking",
    "teletravail",
    "télétravail",
    "a distance",
    "à distance",
    "distanciel",
}


def is_remote_location(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in REMOTE_SYNONYMS


def normalize_location(value: str) -> str:
    value = value.strip()
    if is_remote_location(value):
        return REMOTE_LABEL
    return value


def normalize_locations(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized_values: list[str] = []
    for value in values:
        normalized = normalize_location(value)
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            normalized_values.append(normalized)
    return normalized_values


def normalize_locations_csv(value: str | None) -> str:
    if not value:
        return ""
    return ", ".join(normalize_locations([item for item in value.split(",")]))


def ensure_remote_location(value: str | None) -> str:
    locations = normalize_locations([item for item in (value or "").split(",")])
    if not any(is_remote_location(location) for location in locations):
        locations.insert(0, REMOTE_LABEL)
    return ", ".join(locations)


def remove_remote_location(value: str | None) -> str:
    locations = normalize_locations([item for item in (value or "").split(",")])
    return ", ".join(location for location in locations if not is_remote_location(location))


def has_remote_location(value: str | None) -> bool:
    return any(is_remote_location(item) for item in (value or "").split(","))


def location_matches(text: str, preferred_locations: list[str]) -> bool:
    text_lower = text.lower()
    for location in preferred_locations:
        if is_remote_location(location):
            if any(synonym in text_lower for synonym in REMOTE_SYNONYMS):
                return True
            continue
        if location.lower() in text_lower:
            return True
    return False


def encode_location_for_url(location: str) -> str:
    if is_remote_location(location):
        return quote_plus(REMOTE_LABEL)
    return quote_plus(location)
