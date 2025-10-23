from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SmoothRequest(BaseModel):
    seriesId: str
    method: str
    params: Dict[str, Any] = {}
    returnFeatures: Optional[List[str]] = None
    banking: bool = True

class MatchPAERequest(BaseModel):
    seriesId: str
    paeTarget: float
    methods: List[Dict[str, Any]]
    banking: bool = True

class Series(BaseModel):
    id: str
    y: List[float]
    x: Optional[List[float]] = None

class SmoothResponse(BaseModel):
    seriesId: str
    method: str
    params: Dict[str, Any]
    yhat: List[Dict[str, float]]
    pae: float
    banking: Dict[str, float]
    features: Dict[str, Any]
    metrics: Dict[str, float]
