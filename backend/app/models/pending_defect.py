from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class PendingDefect(Base):
    __tablename__ = "pending_defects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    defect_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Integer, nullable=True)
    bbox_y1 = Column(Integer, nullable=True)
    bbox_x2 = Column(Integer, nullable=True)
    bbox_y2 = Column(Integer, nullable=True)
    image_path = Column(String(500), nullable=True)
    detected_at = Column(DateTime, server_default=func.now(), index=True)
