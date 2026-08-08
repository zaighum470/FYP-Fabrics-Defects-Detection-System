from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.live_stream import LiveStreamManager
from ..schemas.defect import DefectResponse
from ..models.pending_defect import PendingDefect
from ..deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/live", tags=["Live Stream"])


def get_stream_manager():
    return LiveStreamManager.get_instance()


@router.get("/status")
def get_status(manager: LiveStreamManager = Depends(get_stream_manager)):
    return {
        "running": manager.is_running(),
        "source": manager.get_source(),
        "esp32_connected": manager.is_esp32_connected(),
        "local_connected": manager.is_local_connected(),
        "fps": manager.get_fps(),
        "defect_count": manager.get_defect_count(),
        "last_defect": manager.get_last_defect_name()
    }


@router.post("/start")
def start_stream(
    source: str = "esp32",
    model: str = "medium",
    manager: LiveStreamManager = Depends(get_stream_manager)
):
    if source not in ["esp32", "local"]:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'esp32' or 'local'")
    if model not in ["medium", "nano"]:
        raise HTTPException(status_code=400, detail="Invalid model. Use 'medium' or 'nano'")

    # For testing, use a fixed user_id (we assume user with id 1 exists)
    manager.set_user_id(1)
    manager.start(source=source, model=model)
    return {"message": "Stream started", "source": source, "model": model}


@router.post("/stop")
def stop_stream(manager: LiveStreamManager = Depends(get_stream_manager)):
    manager.stop()
    return {"message": "Stream stopped"}


@router.get("/frame")
def get_frame(manager: LiveStreamManager = Depends(get_stream_manager)):
    frame_bytes = manager.get_frame()
    if frame_bytes is None:
        raise HTTPException(status_code=404, detail="No frame available")

    return StreamingResponse(
        iter([frame_bytes]),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/recent-defects")
def get_recent_defects(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get recent defects from pending table ONLY for current user
    defects = db.query(PendingDefect).filter(
        PendingDefect.user_id == current_user.id
    ).order_by(
        PendingDefect.detected_at.desc()
    ).limit(limit).all()
    return defects


@router.post("/record-defect")
def record_defect(
    defect_type: str,
    confidence: float,
    bbox_x1: int = None,
    bbox_y1: int = None,
    bbox_x2: int = None,
    bbox_y2: int = None,
    auto_save: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a detected defect. If auto_save is True, it goes directly to the dashboard."""
    print(f"DEBUG: Recording defect {defect_type} for user_id: {current_user.id} (auto_save: {auto_save})")
    if auto_save:
        defect = Defect(
            defect_type=defect_type,
            confidence=confidence,
            bbox_x1=bbox_x1,
            bbox_y1=bbox_y1,
            bbox_x2=bbox_x2,
            bbox_y2=bbox_y2,
            source="live_stream",
            user_id=current_user.id
        )
        db.add(defect)
        db.commit()
        db.refresh(defect)
        return {"message": "Defect recorded directly to dashboard", "id": defect.id, "saved": True}

    pending = PendingDefect(
        defect_type=defect_type,
        confidence=confidence,
        bbox_x1=bbox_x1,
        bbox_y1=bbox_y1,
        bbox_x2=bbox_x2,
        bbox_y2=bbox_y2,
        user_id=current_user.id
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)
    return {"message": "Defect recorded to pending", "id": pending.id, "saved": False}
