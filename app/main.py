from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.services.parking_service import ParkingMonitorService

app = FastAPI(title="Parking Monitor")
service = ParkingMonitorService()
web_dir = Path("web")

app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.get("/api/status")
def get_status():
    return service.get_status()


@app.get("/api/frame")
def get_frame():
    image = service.camera.get_jpeg_bytes()
    if image is None:
        raise HTTPException(status_code=503, detail="Camera is unavailable")
    return Response(content=image, media_type="image/jpeg")


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")
