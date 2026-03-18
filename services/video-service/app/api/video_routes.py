from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import uuid
import requests

from app.services.video_processor import VideoProcessor

router = APIRouter()

processor = VideoProcessor()


@router.post("/process-video")
async def process_video(
        file: UploadFile | None = File(None),
        video_url: str | None = Form(None),
        required_items: str | None = Form(None),
):

    if not file and not video_url:
        raise HTTPException(status_code=400, detail="Provide either a video file or a video_url.")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        if file:
            tmp.write(await file.read())
            video_filename = file.filename
        else:
            resp = requests.get(video_url, stream=True, timeout=30)
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            video_filename = video_url

        video_path = tmp.name

    video_id = str(uuid.uuid4())

    items_list = None
    if required_items:
        items_list = [i.strip() for i in required_items.split(",") if i.strip()]

    results = processor.process_video(video_path, video_id=video_id, required_items=items_list)

    return {
        "video_id": video_id,
        "frames_analyzed": len(results),
        "violations": [
            {
                "video_time": r.get("video_time"),
                "missing_items": r.get("missing_items"),
                "image_path": r.get("image_path"),
                "bounding_box": r.get("bounding_box"),
            }
            for r in results
            if r.get("compliance") is False
        ]
    }