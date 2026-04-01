from __future__ import annotations

import cv2
import numpy as np

from app.models import ParkingSlot, SlotStatus


class ParkingDetector:
    def __init__(self, occupancy_threshold: float = 0.12) -> None:
        self.occupancy_threshold = occupancy_threshold

    def detect(self, frame: np.ndarray, slots: list[ParkingSlot]) -> list[SlotStatus]:
        statuses: list[SlotStatus] = []
        for slot in slots:
            confidence = self._estimate_occupancy(frame, slot)
            occupied = confidence >= self.occupancy_threshold
            statuses.append(
                SlotStatus(
                    id=slot.id,
                    name=slot.name,
                    occupied=occupied,
                    confidence=round(confidence, 3),
                )
            )
        return statuses

    def _estimate_occupancy(self, frame: np.ndarray, slot: ParkingSlot) -> float:
        polygon = np.array([[point.x, point.y] for point in slot.polygon], dtype=np.int32)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [polygon], 255)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        masked_edges = cv2.bitwise_and(edges, edges, mask=mask)
        occupied_pixels = np.count_nonzero(masked_edges)
        total_pixels = max(np.count_nonzero(mask), 1)

        return float(occupied_pixels / total_pixels)
