from fastapi import APIRouter
from services.detection_service import DetectionService

router = APIRouter()
service = DetectionService()

@router.post("/detect")

def detect(frame_path: str):
    return service.detect_ppe(frame_path)