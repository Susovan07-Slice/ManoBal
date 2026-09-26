from typing import List
from fastapi import APIRouter
from core.organization import CANONICAL_BATTALIONS, CANONICAL_LOCATIONS

router = APIRouter(prefix="/organizations", tags=["Organizational Structure"])

@router.get(
    "/battalions",
    response_model=List[str],
    summary="Get canonical battalion units list"
)
def get_battalions() -> List[str]:
    """Returns canonical reference list of recognized battalions."""
    return list(CANONICAL_BATTALIONS)

@router.get(
    "/locations",
    response_model=List[str],
    summary="Get canonical duty station locations list"
)
def get_locations() -> List[str]:
    """Returns canonical reference list of recognized duty station locations."""
    return list(CANONICAL_LOCATIONS)
