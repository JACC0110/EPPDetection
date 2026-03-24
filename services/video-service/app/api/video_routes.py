from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import uuid
import requests
import os

from yt_dlp import YoutubeDL
from app.services.video_processor import VideoProcessor

router = APIRouter()

processor = VideoProcessor()


@router.post('/process-video')
async def process_video(
        file: UploadFile | None = File(None),
        video_url: str | None = Form(None),
        required_items: str | None = Form(None),
):
    if not file and not video_url:
        raise HTTPException(status_code=400, detail='Provide either a video file or a video_url.')

    video_path = None

    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(await file.read())
            video_path = tmp.name
    else:
        try:
            if video_url and ('youtube.com' in video_url or 'youtu.be' in video_url):
                tmpdir = tempfile.mkdtemp()
                outtmpl = os.path.join(tmpdir, 'video.%(ext)s')
                ydl_opts = {'outtmpl': outtmpl, 'format': 'best'}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    video_path = ydl.prepare_filename(info)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                    resp = requests.get(video_url, stream=True, timeout=30)
                    resp.raise_for_status()
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            tmp.write(chunk)
                    video_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Unable to download video: {e}')

    video_id = str(uuid.uuid4())

    items_list = None
    if required_items:
        items_list = [i.strip() for i in required_items.split(',') if i.strip()]

    try:
        results = processor.process_video(video_path, video_id=video_id, required_items=items_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not results:
        raise HTTPException(status_code=400, detail='No hay frames procesados o todos fallaron en la detección.')

    violations = [
        {
            'video_time': r.get('video_time'),
            'cumplidos': r.get('cumplidos'),
            'faltantes': r.get('faltantes'),
            'image_url': r.get('image_url') or r.get('image_path'),
        }
        for r in results
        if r and r.get('cumplimiento') is False
    ]

    return {
        'video_id': video_id,
        'frames_analyzed': len(results),
        'processed_frames': len(results),
        'violations': violations,
        'violation_count': len(violations),
    }
