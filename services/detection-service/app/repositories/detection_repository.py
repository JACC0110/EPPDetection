from sqlalchemy.orm import Session
from app.models.detection_model import Detection


class DetectionRepository:

    def __init__(self, db: Session):
        self.db = db

    def save_detection(self, data):

        detection = Detection(
            persona=data.get("persona"),
            casco=data.get("casco"),
            chaleco=data.get("chaleco"),
            guantes=data.get("guantes"),
            gafas=data.get("gafas"),
            mascarilla=data.get("mascarilla"),
            cumplimiento=data.get("cumplimiento"),
            ruta_imagen=data.get("ruta_imagen"),
            requeridos=data.get("requeridos") if data.get("requeridos") else None,
            faltantes=data.get("faltantes") if data.get("faltantes") else None,
            video_time=data.get("video_time"),
        )

        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)

        return detection