from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

import cv2
import numpy as np


class CameraManager:
    def __init__(self, settings_path: str = "config/settings.json") -> None:
        self.settings_path = Path(settings_path)
        self._lock = Lock()
        self._capture = None
        self._source = self._load_source()

    def _load_source(self):
        if not self.settings_path.exists():
            return 0

        settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
        source = settings.get("camera_source", 0)
        if isinstance(source, str) and source.isdigit():
            return int(source)
        return source

    def _ensure_capture(self) -> cv2.VideoCapture:
        with self._lock:
            if self._capture is None or not self._capture.isOpened():
                self._capture = cv2.VideoCapture(self._source)
            return self._capture

    def get_frame(self) -> np.ndarray | None:
        capture = self._ensure_capture()
        ok, frame = capture.read()
        if not ok:
            return None
        return frame

    def get_jpeg_bytes(self) -> bytes | None:
        frame = self.get_frame()
        if frame is None:
            return None
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        return encoded.tobytes()
