from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DefectBase(BaseModel):
    defect_type: str
    confidence: float
    bbox_x1: Optional[int] = None
    bbox_y1: Optional[int] = None
    bbox_x2: Optional[int] = None
    bbox_y2: Optional[int] = None
    source: str


class DefectCreate(DefectBase):
    user_id: Optional[int] = None
    image_path: Optional[str] = None


class DefectResponse(DefectBase):
    id: int
    user_id: Optional[int]
    image_path: Optional[str]
    detected_at: datetime

    class Config:
        from_attributes = True


class DetectionResult(BaseModel):
    detections: List[DefectResponse]
    image_path: Optional[str] = None


class DashboardStats(BaseModel):
    total_defects: int
    defects_by_type: dict
    defects_by_source: dict
    recent_defects: List[DefectResponse]
    pending_defects_count: int = 0


class PendingDefectResponse(BaseModel):
    id: int
    defect_type: str
    confidence: float
    bbox_x1: Optional[int] = None
    bbox_y1: Optional[int] = None
    bbox_x2: Optional[int] = None
    bbox_y2: Optional[int] = None
    image_path: Optional[str] = None
    detected_at: datetime

    class Config:
        from_attributes = True


class PendingStats(BaseModel):
    pending_count: int
    pending_by_type: dict


class ChartData(BaseModel):
    labels: List[str]
    values: List[int]
