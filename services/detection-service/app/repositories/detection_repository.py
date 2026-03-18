from sqlalchemy.orm import Session
from app.models.detection_model import Detection


class DetectionRepository:

    def __init__(self, db: Session):
        self.db = db

    def save_detection(self, data):

        # allow new keys to be optional
        bbox = data.get("bounding_box") or []
        detection = Detection(
            video_id=data.get("video_id"),
            video_time=float(data.get("video_time")) if data.get("video_time") is not None else None,
            person=data.get("person"),
            helmet=data.get("helmet"),
            vest=data.get("vest"),
            gloves=data.get("gloves"),
            goggles=data.get("goggles"),
            mask=data.get("mask"),
            compliance=data.get("compliance"),
            bbox_x1=int(bbox[0]) if len(bbox) > 0 else None,
            bbox_y1=int(bbox[1]) if len(bbox) > 1 else None,
            bbox_x2=int(bbox[2]) if len(bbox) > 2 else None,
            bbox_y2=int(bbox[3]) if len(bbox) > 3 else None,
            image_path=data.get("image_path"),
            required_items=list(data.get("required_items")) if data.get("required_items") else None,
            missing_items=list(data.get("missing_items")) if data.get("missing_items") else None,
        )

        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)

        return detection