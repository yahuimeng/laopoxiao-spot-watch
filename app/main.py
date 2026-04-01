from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.services.parking_service import ParkingMonitorService

service = ParkingMonitorService()
web_dir = Path("web")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    service.start()
    try:
        yield
    finally:
        service.stop()


app = FastAPI(title="老破小车位哨兵", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.get("/api/status")
def get_status():
    return service.get_status()


@app.get("/api/analytics")
def get_analytics(days: int = Query(default=30, ge=1, le=180)):
    return service.get_analytics(days=days)


@app.get("/api/frame")
def get_frame():
    image = service.camera.get_jpeg_bytes()
    if image is None:
        raise HTTPException(status_code=503, detail="Camera is unavailable")
    return Response(content=image, media_type="image/jpeg")


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")
