from ultralytics import YOLO
import cv2
import os
import uuid


class DetectionService:

    def __init__(self):
        # cargar modelo
        self.model = YOLO("app/models/best.pt")

        # carpeta donde se guardan violaciones
        self.violation_folder = "storage/violations"
        os.makedirs(self.violation_folder, exist_ok=True)

        # mapeo de nombres en español a etiquetas del modelo
        self.label_map = {
            "casco": "hardhat",
            "chaleco": "safety vest",
            "guantes": "gloves",
            "gafas": "safety glasses",
            "mascarilla": "face mask",
        }

    def detect(
        self,
        image,
        required_items: list[str] | None = None,
        video_id: str | None = None,
        video_time: float | None = None,
    ):
        """Detecta los items requeridos en una imagen/frame.

        Si `required_items` es `None`, evalúa los 5 elementos principales:
        helmet, vest, gloves, goggles, mask.
        """

        original_image = image.copy()
        results = self.model(image)

        found_labels: set[str] = set()
        person = False

        # collect bounding boxes for decision, but we will not use them for display if full images are required
        person_boxes = []  # list of [x1,y1,x2,y2]
        other_boxes = []  # boxes of PPE items

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls = int(box.cls.item())
                label = self.model.names[cls].lower()

                coords = box.xyxy[0].tolist()
                if label == "person":
                    person = True
                    person_boxes.append(coords)
                elif label in self.label_map.values():
                    found_labels.add(label)
                    other_boxes.append(coords)

        # Persona presente si hay detección de persona o de al menos un EPP esperado
        if not person and found_labels:
            person = True

        # When drawing the violation box, try to cover the whole person.
        # Prefer a detected person box; if not found, use all detected PPE boxes combined.
        all_boxes = person_boxes + other_boxes
        if all_boxes:
            xs = [b[0] for b in all_boxes] + [b[2] for b in all_boxes]
            ys = [b[1] for b in all_boxes] + [b[3] for b in all_boxes]
            person_boxes = [[min(xs), min(ys), max(xs), max(ys)]]

        # reportar todos los items de PPE que el modelo conoce (para que el frontend pueda decidir)
        output: dict = {"persona": person, "found_labels": sorted(list(found_labels))}

        ppe_status = {
            item: (self.label_map[item] in found_labels)
            for item in self.label_map
        }
        output.update(ppe_status)

        # determinar qué items se usan para calcular cumplimiento
        default_required = ["casco", "chaleco", "guantes", "gafas", "mascarilla"]
        required_items_list = required_items if required_items is not None else default_required

        completed = [item for item, status in ppe_status.items() if status and item in required_items_list]
        missing = [item for item in required_items_list if not ppe_status.get(item, False)]

        output["requeridos"] = required_items_list
        output["cumplidos"] = completed
        output["faltantes"] = missing

        # considerar frames sin persona como cumplimiento (no guardar violación)
        cumplimiento = True if not person else len(missing) == 0
        output["cumplimiento"] = cumplimiento

        image_path = None

        if not output["cumplimiento"]:
            # Guardar imagen original completa del frame (sin recorte)
            filename = f"{uuid.uuid4()}.jpg"
            saved_path = os.path.join(self.violation_folder, filename)
            cv2.imwrite(saved_path, original_image)

            image_path = f"http://127.0.0.1:8000/storage/violations/{filename}"

        output["image_url"] = image_path
        output["image_path"] = image_path
        output["video_id"] = video_id
        output["video_time"] = video_time

        return output