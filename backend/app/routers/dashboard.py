from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, literal, union_all, desc
from datetime import datetime, timedelta
from ..database import get_db
from ..models.defect import Defect
from ..models.pending_defect import PendingDefect
from ..schemas.defect import DashboardStats, DefectResponse, ChartData, PendingDefectResponse, PendingStats
from ..deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the current user"""
    user_id = current_user.id
    print(f"DEBUG: Fetching stats for user_id: {user_id}")
    print("ABOUT TO ENTER TRY BLOCK")
    try:
        print("ENTERED TRY BLOCK")
        # Total defects for this user (Permanent + Pending)
        total_permanent = db.query(func.count(Defect.id)).filter(Defect.user_id == user_id).scalar() or 0
        pending_count = db.query(func.count(PendingDefect.id)).filter(PendingDefect.user_id == user_id).scalar() or 0
        total = total_permanent + pending_count
        print(f"DEBUG: User {user_id} - Permanent: {total_permanent}, Pending: {pending_count}, Total: {total}")

        # Defects by type for this user (including pending defects)
        # Permanent defects by type
        permanent_type_counts = db.query(
            Defect.defect_type,
            func.count(Defect.id)
        ).filter(Defect.user_id == user_id).group_by(Defect.defect_type).all()

        # Pending defects by type (assume source is live_stream for pending)
        pending_type_counts = db.query(
            PendingDefect.defect_type,
            func.count(PendingDefect.id)
        ).filter(PendingDefect.user_id == user_id).group_by(PendingDefect.defect_type).all()

        # Combine the counts
        defects_by_type = {}
        for defect_type, count in permanent_type_counts:
            defects_by_type[defect_type] = defects_by_type.get(defect_type, 0) + count
        for defect_type, count in pending_type_counts:
            defects_by_type[defect_type] = defects_by_type.get(defect_type, 0) + count

        # Defects by source for this user (including pending defects as live_stream)
        # Permanent defects by source
        permanent_source_counts = db.query(
            Defect.source,
            func.count(Defect.id)
        ).filter(Defect.user_id == user_id).group_by(Defect.source).all()

        # Pending defects by source (all pending defects are from live_stream)
        pending_source_count = db.query(
            func.count(PendingDefect.id)
        ).filter(PendingDefect.user_id == user_id).scalar() or 0

        # Combine the counts
        defects_by_source = {}
        for source, count in permanent_source_counts:
            defects_by_source[source] = defects_by_source.get(source, 0) + count
        if pending_source_count > 0:
            defects_by_source['live_stream'] = defects_by_source.get('live_stream', 0) + pending_source_count

        # Recent defects (last 10) for this user (including pending defects)
        # Get recent permanent defects
        permanent_recent = db.query(
            Defect.id,
            Defect.defect_type,
            Defect.confidence,
            Defect.bbox_x1,
            Defect.bbox_y1,
            Defect.bbox_x2,
            Defect.bbox_y2,
            Defect.image_path,
            Defect.source,
            Defect.detected_at
        ).filter(Defect.user_id == user_id)

        # Get recent pending defects (assign source as live_stream for pending)
        pending_recent = db.query(
            PendingDefect.id,
            PendingDefect.defect_type,
            PendingDefect.confidence,
            PendingDefect.bbox_x1,
            PendingDefect.bbox_y1,
            PendingDefect.bbox_x2,
            PendingDefect.bbox_y2,
            PendingDefect.image_path,
            literal('live_stream').label('source'),
            PendingDefect.detected_at
        ).filter(PendingDefect.user_id == user_id)

        # Union and order by detected_at descending, limit 10
        from sqlalchemy import union_all, desc
        combined_recent = union_all(
            permanent_recent,
            pending_recent
        ).order_by(desc(Defect.detected_at)).limit(10)

        # Convert to Defect objects for compatibility
        recent = []
        for row in db.execute(combined_recent):
            defect = Defect(
                id=row.id,
                defect_type=row.defect_type,
                confidence=row.confidence,
                bbox_x1=row.bbox_x1,
                bbox_y1=row.bbox_y1,
                bbox_x2=row.bbox_x2,
                bbox_y2=row.bbox_y2,
                image_path=row.image_path,
                source=row.source,
                detected_at=row.detected_at
            )
            recent.append(defect)

        return DashboardStats(
            total_defects=total,
            defects_by_type=defects_by_type,
            defects_by_source=defects_by_source,
            recent_defects=recent,
            pending_defects_count=pending_count
        )
    except Exception as e:
        print(f"ERROR in get_stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defects", response_model=list[DefectResponse])
def get_defects(
    skip: int = 0,
    limit: int = 20,
    defect_type: str = None,
    source: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Defect).filter(Defect.user_id == current_user.id)

    if defect_type:
        query = query.filter(Defect.defect_type == defect_type)
    if source:
        query = query.filter(Defect.source == source)

    defects = query.order_by(Defect.detected_at.desc()).offset(skip).limit(limit).all()
    return defects


@router.get("/chart/type-distribution", response_model=ChartData)
def get_type_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get permanent defects by type
    permanent_results = db.query(
        Defect.defect_type,
        func.count(Defect.id)
    ).filter(Defect.user_id == current_user.id).group_by(Defect.defect_type).all()

    # Get pending defects by type
    pending_results = db.query(
        PendingDefect.defect_type,
        func.count(PendingDefect.id)
    ).filter(PendingDefect.user_id == current_user.id).group_by(PendingDefect.defect_type).all()

    # Combine the counts
    type_counts = {}
    for defect_type, count in permanent_results:
        type_counts[defect_type] = type_counts.get(defect_type, 0) + count
    for defect_type, count in pending_results:
        type_counts[defect_type] = type_counts.get(defect_type, 0) + count

    # Sort by defect type for consistent ordering
    sorted_items = sorted(type_counts.items())

    return ChartData(
        labels=[item[0] for item in sorted_items],
        values=[item[1] for item in sorted_items]
    )


@router.get("/chart/daily-defects", response_model=ChartData)
def get_daily_defects(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get defects from last N days for this user
    since = datetime.utcnow() - timedelta(days=days)

    # Get permanent defects from last N days
    permanent_results = db.query(
        func.date(Defect.detected_at).label('date'),
        func.count(Defect.id)
    ).filter(
        Defect.user_id == current_user.id,
        Defect.detected_at >= since
    ).group_by(
        func.date(Defect.detected_at)
    ).all()

    # Get pending defects from last N days
    pending_results = db.query(
        func.date(PendingDefect.detected_at).label('date'),
        func.count(PendingDefect.id)
    ).filter(
        PendingDefect.user_id == current_user.id,
        PendingDefect.detected_at >= since
    ).group_by(
        func.date(PendingDefect.detected_at)
    ).all()

    # Combine the counts by date
    daily_counts = {}
    for date_str, count in permanent_results:
        daily_counts[date_str] = daily_counts.get(date_str, 0) + count
    for date_str, count in pending_results:
        daily_counts[date_str] = daily_counts.get(date_str, 0) + count

    # Sort by date for consistent ordering
    sorted_items = sorted(daily_counts.items())

    return ChartData(
        labels=[str(item[0]) for item in sorted_items],
        values=[item[1] for item in sorted_items]
    )


@router.get("/chart/confidence-distribution", response_model=ChartData)
def get_confidence_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get confidence level distribution for a distribution plot"""
    # Get permanent defects confidence levels
    permanent_results = db.query(
        Defect.confidence
    ).filter(Defect.user_id == current_user.id).all()

    # Get pending defects confidence levels
    pending_results = db.query(
        PendingDefect.confidence
    ).filter(PendingDefect.user_id == current_user.id).all()

    # Combine all confidence values
    all_results = list(permanent_results) + list(pending_results)

    # Binning confidence levels (0-100%) into 10% buckets
    bins = {f"{i*10}-{(i+1)*10}%": 0 for i in range(10)}
    for conf in all_results:
        # Normalize confidence to 0-100 if it's 0.0-1.0
        val = conf[0] * 100 if conf[0] <= 1.0 else conf[0]
        bin_idx = int(min(val, 99) // 10)
        label = f"{bin_idx*10}-{(bin_idx+1)*10}%"
        bins[label] += 1

    return ChartData(
        labels=list(bins.keys()),
        values=list(bins.values())
    )


# Pending Defects Management
@router.get("/pending", response_model=list[PendingDefectResponse])
def get_pending_defects(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending defects for current user that haven't been converted to dashboard"""
    defects = db.query(PendingDefect).filter(
        PendingDefect.user_id == current_user.id
    ).order_by(
        PendingDefect.detected_at.desc()
    ).offset(skip).limit(limit).all()
    return defects


@router.get("/pending/stats", response_model=PendingStats)
def get_pending_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending defects statistics for current user"""
    pending_count = db.query(func.count(PendingDefect.id)).filter(
        PendingDefect.user_id == current_user.id
    ).scalar() or 0

    type_counts = db.query(
        PendingDefect.defect_type,
        func.count(PendingDefect.id)
    ).filter(
        PendingDefect.user_id == current_user.id
    ).group_by(PendingDefect.defect_type).all()
    pending_by_type = {row[0]: row[1] for row in type_counts}

    return PendingStats(
        pending_count=pending_count,
        pending_by_type=pending_by_type
    )


@router.post("/pending/add")
def add_pending_defect(
    defect_type: str,
    confidence: float,
    bbox_x1: int = None,
    bbox_y1: int = None,
    bbox_x2: int = None,
    bbox_y2: int = None,
    image_path: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a defect to pending list (called from live stream)"""
    pending = PendingDefect(
        defect_type=defect_type,
        confidence=confidence,
        bbox_x1=bbox_x1,
        bbox_y1=bbox_y1,
        bbox_x2=bbox_x2,
        bbox_y2=bbox_y2,
        image_path=image_path,
        user_id=current_user.id
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)
    return {"message": "Defect added to pending", "id": pending.id}


@router.post("/pending/{defect_id}/accept")
def accept_pending_defect(
    defect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a pending defect and move it to the defects table"""
    # Get the pending defect
    pending_defect = db.query(PendingDefect).filter(
        PendingDefect.id == defect_id,
        PendingDefect.user_id == current_user.id
    ).first()

    if not pending_defect:
        raise HTTPException(status_code=404, detail="Pending defect not found")

    # Create a new defect in the defects table
    defect = Defect(
        defect_type=pending_defect.defect_type,
        confidence=pending_defect.confidence,
        bbox_x1=pending_defect.bbox_x1,
        bbox_y1=pending_defect.bbox_y1,
        bbox_x2=pending_defect.bbox_x2,
        bbox_y2=pending_defect.bbox_y2,
        image_path=pending_defect.image_path,
        source="pending_approval",  # or could be "live_stream" or similar
        user_id=current_user.id
    )

    # Add the defect to the defects table
    db.add(defect)

    # Delete the pending defect
    db.delete(pending_defect)

    # Commit the transaction
    db.commit()

    # Refresh the defect to get the ID
    db.refresh(defect)

    return {"message": "Pending defect accepted and moved to defects", "defect_id": defect.id}


@router.post("/pending/{defect_id}/delete")
def delete_pending_defect(
    defect_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a pending defect (reject/discard it)"""
    # Get the pending defect
    pending_defect = db.query(PendingDefect).filter(
        PendingDefect.id == defect_id,
        PendingDefect.user_id == current_user.id
    ).first()

    if not pending_defect:
        raise HTTPException(status_code=404, detail="Pending defect not found")

    # Delete the pending defect
    db.delete(pending_defect)

    # Commit the transaction
    db.commit()

    return {"message": "Pending defect deleted"}


@router.post("/pending/convert-all")
def convert_all_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert all pending defects to confirmed defects"""
    # Get all pending defects for the current user
    pending_defects = db.query(PendingDefect).filter(
        PendingDefect.user_id == current_user.id
    ).all()

    if not pending_defects:
        return {"message": "No pending defects to convert", "converted_count": 0}

    converted_count = 0
    # Convert each pending defect to a confirmed defect
    for pending in pending_defects:
        defect = Defect(
            defect_type=pending.defect_type,
            confidence=pending.confidence,
            bbox_x1=pending.bbox_x1,
            bbox_y1=pending.bbox_y1,
            bbox_x2=pending.bbox_x2,
            bbox_y2=pending.bbox_y2,
            image_path=pending.image_path,
            source="pending_conversion",  # or could be "pending_approved"
            user_id=current_user.id
        )
        db.add(defect)
        converted_count += 1

    # Delete all pending defects
    db.query(PendingDefect).filter(PendingDefect.user_id == current_user.id).delete()

    # Commit the transaction
    db.commit()

    return {"message": f"Converted {converted_count} pending defects to confirmed defects", "converted_count": converted_count}


@router.post("/pending/discard-all")
def discard_all_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discard/delete all pending defects"""
    # Delete all pending defects for the current user
    deleted_count = db.query(PendingDefect).filter(PendingDefect.user_id == current_user.id).delete()

    # Commit the transaction
    db.commit()

    return {"message": f"Discarded {deleted_count} pending defects", "discarded_count": deleted_count}