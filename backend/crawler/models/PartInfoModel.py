from pydantic import BaseModel, HttpUrl
from typing import Optional

class PartInfoModel(BaseModel):
    """Pydantic model representing part details."""
    part_number: str
    part_url: HttpUrl
    image_url: Optional[HttpUrl] = None
    product_description: str
    symptoms_it_fixes: str = "N/A"
    appliances_its_for: str = "N/A"
    compatible_brands: str = "N/A"
    installation_video: Optional[HttpUrl] = None
    price: str = "Price not available"
    availability: str = "Availability unknown"
    ps_number: str = "N/A"
    mfg_number: str = "N/A"
    installation_difficulty: str = "Unknown"
    installation_time: str = "Unknown"
    review_count: str = "No reviews"
    rating: str = "No rating"

