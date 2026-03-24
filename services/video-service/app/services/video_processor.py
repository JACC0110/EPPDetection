import os
import cv2
import requests
import tempfile


class VideoProcessor:

    def __init__(self):
        # Allow overriding via environment variables for containerized deployment
        self.detection_api = os.getenv("DETECTION_API_URL", "http://127.0.0.1:8000/detect")
        self.frame_interval = float(os.getenv("FRAME_INTERVAL_SECONDS", "5"))  # segundos

    def process_video(self, video_path, video_id: str | None = None, required_items: list[str] | None = None):

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0

        # fallback to 1 fps when video metadata is not available
        if fps <= 0:
            fps = 1.0

        frame_interval = int(fps * self.frame_interval)
        if frame_interval <= 0:
            frame_interval = 1

        frame_count = 0

        results = []

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            if frame_count % frame_interval == 0:
                # calculate current time in seconds
                timestamp = frame_count / fps if fps > 0 else None
                result = self.send_frame(frame, video_id=video_id, video_time=timestamp, required_items=required_items)

                if result:
                    # propagate metadata to the returned result as well
                    if video_id is not None:
                        result["video_id"] = video_id
                    if timestamp is not None:
                        result["video_time"] = timestamp
                    if required_items is not None:
                        result["required_items"] = required_items
                    results.append(result)

            frame_count += 1

        cap.release()

        return results

    def send_frame(self, frame, video_id: str | None = None, video_time: float | None = None, required_items: list[str] | None = None):

        _, img_encoded = cv2.imencode(".jpg", frame)

        files = {
            "file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
        }
        data = {}
        if video_id is not None:
            data["video_id"] = video_id
        if video_time is not None:
            data["video_time"] = video_time
        if required_items is not None:
            data["required_items"] = ",".join(required_items)

        try:
            response = requests.post(self.detection_api, files=files, data=data, timeout=30)

            if response.status_code != 200:
                print("error sending frame, status", response.status_code, "body", response.text)
                return None

            try:
                return response.json()
            except ValueError as e:
                print("error parsing JSON from detection service:", e, "body:", response.text)
                return None

        except Exception as e:
            print("error sending frame", e)
            return None