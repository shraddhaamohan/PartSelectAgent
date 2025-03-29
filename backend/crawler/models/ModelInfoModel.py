from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class Manual(BaseModel):
    """Pydantic model representing a manual."""
    title: str
    url: HttpUrl

class Diagram(BaseModel):
    """Pydantic model representing a diagram."""
    title: str
    url: HttpUrl

class Video(BaseModel):
    """Pydantic model representing a video."""
    title: str
    url: HttpUrl

class ModelInfoModel(BaseModel):
    """Pydantic model representing model details."""
    type: str
    model_name: str
    model_url: HttpUrl
    manuals: List[Manual]
    diagrams: List[Diagram]
    videos: List[Video]
    parts_url: Optional[HttpUrl]