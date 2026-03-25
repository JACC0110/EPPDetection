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
            "gafas": "goggles",
            "mascarilla": "mask",
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
        
        # Diccionario para almacenar TODAS las detecciones con sus boxes
        # Formato: {label: [(x1,y1,x2,y2), ...], ...}
        all_detections = {}

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls = int(box.cls.item())
                label = self.model.names[cls].lower()
                coords = box.xyxy[0].tolist()
                
                # Guardar todas las detecciones
                if label not in all_detections:
                    all_detections[label] = []
                all_detections[label].append(coords)

                if label == "person":
                    person = True
                elif label in self.label_map.values():
                    found_labels.add(label)

        # Persona presente si hay detección de persona o de al menos un EPP esperado
        if not person and found_labels:
            person = True

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
            # Anotar imagen con bounding boxes de items cumplidos (verde) y faltantes (rojo)
            annotated_image = original_image.copy()
            
            # Para cada item requerido, dibujar bounding boxes
            for item in required_items_list:
                model_label = self.label_map[item]
                
                # Verde para items detectados (cumplidos)
                if model_label in all_detections:
                    for box in all_detections[model_label]:
                        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(
                            annotated_image,
                            f"OK: {item}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
                
                # Rojo para items no detectados (faltantes) - buscar "no-X"
                no_label = f"no-{model_label}"
                if no_label in all_detections:
                    for box in all_detections[no_label]:
                        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(
                            annotated_image,
                            f"FALTA: {item}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2,
                        )
            
            # Guardar imagen anotada
            filename = f"{uuid.uuid4()}.jpg"
            saved_path = os.path.join(self.violation_folder, filename)
            cv2.imwrite(saved_path, annotated_image)

            image_path = f"http://127.0.0.1:8000/storage/violations/{filename}"

        output["image_url"] = image_path
        output["image_path"] = image_path
        output["video_id"] = video_id
        output["video_time"] = video_time

        return output