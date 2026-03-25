from fastapi import APIRouter, UploadFile, File, Depends, Form
import numpy as np
import cv2

from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.detection_service import DetectionService
from app.repositories.detection_repository import DetectionRepository

router = APIRouter()

service = DetectionService()


@router.post("/detect")
async def detect_ppe(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        video_id: str | None = None,
        video_time: float | None = None,
        required_items: str | None = Form(None),
        required_items_q: str | None = None,
):

    contents = await file.read()

    np_image = np.frombuffer(contents, np.uint8)

    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    items_raw = required_items or required_items_q
    items_list = None
    if items_raw:
        items_list = [i.strip() for i in items_raw.split(",") if i.strip()]

    result = service.detect(image, required_items=items_list)

    if result is not None:
        if video_id is not None:
            result["video_id"] = video_id
        if video_time is not None:
            result["video_time"] = video_time
        if items_list is not None:
            result["requeridos"] = items_list

    if result and not result.get("cumplimiento"):
        repo = DetectionRepository(db)

        db_data = {
            "persona": result.get("persona"),
            "casco": result.get("casco"),
            "chaleco": result.get("chaleco"),
            "guantes": result.get("guantes"),
            "gafas": result.get("gafas"),
            "mascarilla": result.get("mascarilla"),
            "cumplimiento": result.get("cumplimiento"),
            "ruta_imagen": result.get("image_path"),
            "requeridos": result.get("requeridos") or result.get("required_items"),
            "faltantes": result.get("faltantes") or result.get("missing_items"),
            "video_time": result.get("video_time"),
        }

        repo.save_detection(db_data)

    return result