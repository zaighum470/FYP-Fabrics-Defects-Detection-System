from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Defect(Base):
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    defect_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Integer, nullable=True)
    bbox_y1 = Column(Integer, nullable=True)
    bbox_x2 = Column(Integer, nullable=True)
    bbox_y2 = Column(Integer, nullable=True)
    image_path = Column(String(500), nullable=True)
    source = Column(Enum('image_upload', 'live_stream'), nullable=False)
    detected_at = Column(DateTime, server_default=func.now(), index=True)
