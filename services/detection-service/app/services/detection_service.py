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

        # mapeo de nombres genéricos a etiquetas del modelo
        self.label_map = {
            "helmet": "hardhat",
            "vest": "safety vest",
            "boots": "boots",
            "gloves": "gloves",
            "goggles": "safety glasses",
            "mask": "face mask",
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

        results = self.model(image)

        found_labels: set[str] = set()
        person = False

        # collect bounding boxes so we can highlight offenders
        person_boxes = []  # list of [x1,y1,x2,y2]
        other_boxes = []  # boxes of PPE items (fallback)

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
                else:
                    found_labels.add(label)
                    other_boxes.append(coords)

        # algunos modelos no detectan persona pero sí PPE
        if not person and ("hardhat" in found_labels or "safety vest" in found_labels):
            person = True

        # if we didn't detect a person box, fallback to any PPE box so we can draw a bounding box
        if not person_boxes and other_boxes:
            person_boxes = [other_boxes[0]]

        # reportar todos los items de PPE que el modelo conoce (para que el frontend pueda decidir)
        output: dict = {"person": person}

        ppe_results = {
            item: (self.label_map[item] in found_labels)
            for item in self.label_map
        }
        output.update(ppe_results)

        # determinar qué items se usan para calcular compliance
        default_required = ["helmet", "vest", "gloves", "goggles", "mask"]
        required_items_list = required_items if required_items is not None else default_required

        missing = []
        for item in required_items_list:
            if not output.get(item, False):
                missing.append(item)

        output["required_items"] = required_items_list
        output["missing_items"] = missing

        # consider frames with no person as compliant (no violation to store)
        compliance = True if not person else len(missing) == 0
        output["compliance"] = compliance

        image_path = None
        bounding_box = None

        if not output["compliance"]:
            # Dibujar bounding box en la imagen para llevar registro visual de la violación
            if person_boxes:
                x1, y1, x2, y2 = [int(c) for c in person_boxes[0]]
                h, w = image.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                bounding_box = [x1, y1, x2, y2]

            filename = f"{uuid.uuid4()}.jpg"
            saved_path = os.path.join(self.violation_folder, filename)
            cv2.imwrite(saved_path, image)

            # Return a URL that can be fetched from the frontend.
            # Assumes detection-service runs on localhost:8000.
            image_path = f"http://127.0.0.1:8000/storage/violations/{filename}"

        output["image_path"] = image_path
        output["bounding_box"] = bounding_box
        output["video_id"] = video_id
        output["video_time"] = video_time

        return output