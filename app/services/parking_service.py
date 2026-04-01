from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.camera import CameraManager
from app.detector import ParkingDetector
from app.models import ParkingSlot, SystemStatus


class ParkingMonitorService:
    def __init__(
        self,
        settings_path: str = "config/settings.json",
        slots_path: str = "config/parking_slots.json",
    ) -> None:
        self.settings_path = Path(settings_path)
        self.slots_path = Path(slots_path)
        self.camera = CameraManager(settings_path=settings_path)
        self.detector = ParkingDetector(
            occupancy_threshold=self._load_settings().get("occupancy_threshold", 0.12)
        )

    def _load_settings(self) -> dict:
        if not self.settings_path.exists():
            return {}
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def _load_slots(self) -> list[ParkingSlot]:
        if not self.slots_path.exists():
            return []
        raw = json.loads(self.slots_path.read_text(encoding="utf-8"))
        return [ParkingSlot.model_validate(item) for item in raw]

    def get_status(self) -> SystemStatus:
        frame = self.camera.get_frame()
        slots = self._load_slots()

        if frame is None:
            return SystemStatus(
                total_slots=len(slots),
                free_slots=0,
                occupied_slots=0,
                state="offline",
                slots=[],
                last_updated=datetime.now().isoformat(timespec="seconds"),
            )

        statuses = self.detector.detect(frame, slots)
        occupied_count = sum(1 for item in statuses if item.occupied)
        free_count = max(len(statuses) - occupied_count, 0)

        return SystemStatus(
            total_slots=len(statuses),
            free_slots=free_count,
            occupied_slots=occupied_count,
            state="available" if free_count > 0 else "full",
            slots=statuses,
            last_updated=datetime.now().isoformat(timespec="seconds"),
        )
