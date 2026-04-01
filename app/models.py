from typing import Literal

from pydantic import BaseModel


class Point(BaseModel):
    x: int
    y: int


class ParkingSlot(BaseModel):
    id: str
    name: str
    polygon: list[Point]


class SlotStatus(BaseModel):
    id: str
    name: str
    occupied: bool
    confidence: float


class SystemStatus(BaseModel):
    total_slots: int
    free_slots: int
    occupied_slots: int
    state: Literal["available", "full", "offline"]
    slots: list[SlotStatus]
    last_updated: str
