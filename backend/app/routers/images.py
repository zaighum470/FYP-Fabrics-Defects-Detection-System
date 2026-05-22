from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
import cv2
import numpy as np
from datetime import datetime
from ..database import get_db
from ..models.defect import Defect
from ..schemas.defect import DefectResponse, DetectionResult
from ..services.detector import Detector
from ..config import UPLOAD_DIR, MAX_UPLOAD_SIZE
from ..deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/images", tags=["Image Detection"])

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_detector():
    return Detector()


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    detector: Detector = Depends(get_detector),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Check file size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": unique_filename, "path": file_path}


@router.post("/detect", response_model=DetectionResult)
async def detect_defects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    detector: Detector = Depends(get_detector),
    current_user: User = Depends(get_current_user)
):
    # Validate and read file
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid image file")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Decode image
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    cv2.imwrite(file_path, img)

    # Run detection
    result_img, detections = detector.detect_from_array(img)

    # Save result image with bounding boxes
    result_filename = f"result_{unique_filename}"
    result_path = os.path.join(UPLOAD_DIR, result_filename)
    cv2.imwrite(result_path, result_img)

    # Log defects to database with user_id
    saved_defects = []
    print(f"DEBUG: Saving {len(detections)} defects for user_id: {current_user.id}")
    for det in detections:
        db_defect = Defect(
            defect_type=det["class"],
            confidence=det["confidence"],
            bbox_x1=det["bbox"][0],
            bbox_y1=det["bbox"][1],
            bbox_x2=det["bbox"][2],
            bbox_y2=det["bbox"][3],
            image_path=file_path,
            source="image_upload",
            user_id=current_user.id
        )
        db.add(db_defect)
        saved_defects.append(db_defect)

    db.commit()
    for d in saved_defects:
        db.refresh(d)

    return DetectionResult(
        detections=saved_defects,
        image_path=result_filename
    )
