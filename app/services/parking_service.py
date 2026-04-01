from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any

from app.camera import CameraManager
from app.detector import ParkingDetector
from app.models import ParkingSlot, SystemStatus
from app.services.history_store import HistoryStore
from app.services.notifier import WeChatNotifier


class ParkingMonitorService:
    def __init__(
        self,
        settings_path: str = "config/settings.json",
        slots_path: str = "config/parking_slots.json",
    ) -> None:
        self.settings_path = Path(settings_path)
        self.slots_path = Path(slots_path)
        self.settings = self._load_settings()
        self.camera = CameraManager(settings_path=settings_path)
        self.detector = ParkingDetector(
            occupancy_threshold=self.settings.get("occupancy_threshold", 0.12)
        )
        self.history_store = HistoryStore(self.settings.get("history_db_path", "data/parking_history.sqlite3"))
        self.notifier = WeChatNotifier(self.settings)
        self.refresh_interval_ms = int(self.settings.get("refresh_interval_ms", 3000))
        self._status_lock = threading.Lock()
        self._latest_status: SystemStatus | None = None
        self._worker: threading.Thread | None = None
        self._running = False

    def _load_settings(self) -> dict[str, Any]:
        if not self.settings_path.exists():
            return {}
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def _load_slots(self) -> list[ParkingSlot]:
        if not self.slots_path.exists():
            return []
        raw = json.loads(self.slots_path.read_text(encoding="utf-8"))
        return [ParkingSlot.model_validate(item) for item in raw]

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker = threading.Thread(target=self._monitor_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._running = False
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1)

    def _monitor_loop(self) -> None:
        while self._running:
            self.refresh_status()
            sleep(max(self.refresh_interval_ms / 1000, 1))

    def refresh_status(self) -> SystemStatus:
        frame = self.camera.get_frame()
        slots = self._load_slots()

        if frame is None:
            status = SystemStatus(
                total_slots=len(slots),
                free_slots=0,
                occupied_slots=0,
                state="offline",
                slots=[],
                last_updated=datetime.now().isoformat(timespec="seconds"),
                notification_enabled=self.notifier.enabled,
            )
        else:
            statuses = self.detector.detect(frame, slots)
            occupied_count = sum(1 for item in statuses if item.occupied)
            free_count = max(len(statuses) - occupied_count, 0)
            status = SystemStatus(
                total_slots=len(statuses),
                free_slots=free_count,
                occupied_slots=occupied_count,
                state="available" if free_count > 0 else "full",
                slots=statuses,
                last_updated=datetime.now().isoformat(timespec="seconds"),
                notification_enabled=self.notifier.enabled,
            )

        self.history_store.record(status)
        self.notifier.maybe_notify(status)
        with self._status_lock:
            self._latest_status = status
        return status

    def get_status(self) -> SystemStatus:
        with self._status_lock:
            if self._latest_status is not None:
                return self._latest_status
        return self.refresh_status()

    def get_analytics(self, days: int = 30):
        return self.history_store.build_summary(days=days)
