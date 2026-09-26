"""
Canonical Organizational Reference Definitions for ManoBal System.
Centralized repository for Battalions and Base Locations.
Used by:
- Backend data validation and scope checking
- Organization lookup APIs
- Commander and Jawan self-signup forms
"""

from typing import List

CANONICAL_BATTALIONS: List[str] = [
    "7th Battalion",
    "8th Battalion",
    "12th Battalion",
    "21st Battalion",
    "45th Battalion",
    "102nd Rapid Action Battalion",
]

CANONICAL_LOCATIONS: List[str] = [
    "Jamshedpur",
    "Ranchi",
    "Delhi",
    "Srinagar",
    "Leh",
    "Dantewada",
    "Bhubaneswar",
    "Guwahati",
    "Shillong",
    "Imphal",
    "Sukma",
    "Jammu",
    "Bhopal",
]

def validate_battalion(val: str) -> str:
    """Validates and normalizes battalion against canonical list."""
    if not val or not isinstance(val, str):
        raise ValueError("Battalion must be a non-empty string.")
    cleaned = val.strip()
    match = next((b for b in CANONICAL_BATTALIONS if b.lower() == cleaned.lower()), None)
    if not match:
        raise ValueError(
            f"Invalid battalion '{val}'. Allowed options: {', '.join(CANONICAL_BATTALIONS)}"
        )
    return match

def validate_location(val: str) -> str:
    """Validates and normalizes location against canonical list."""
    if not val or not isinstance(val, str):
        raise ValueError("Location must be a non-empty string.")
    cleaned = val.strip()
    match = next((l for l in CANONICAL_LOCATIONS if l.lower() == cleaned.lower()), None)
    if not match:
        raise ValueError(
            f"Invalid location '{val}'. Allowed options: {', '.join(CANONICAL_LOCATIONS)}"
        )
    return match
