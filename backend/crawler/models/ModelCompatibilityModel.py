from pydantic import BaseModel, HttpUrl
from typing import Optional

class ModelCompatibilityModel(BaseModel):
    """Pydantic model representing part and model compatibility."""
            # Return compatibility as True, product link, and model list

    compatibility: bool
    product_link: Optional[HttpUrl] = None
    model_link: Optional[HttpUrl] = None

