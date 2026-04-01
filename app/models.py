from __future__ import annotations

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
    notification_enabled: bool = False


class WeekdayStat(BaseModel):
    weekday: int
    label: str
    avg_free_slots: float
    availability_rate: float
    sample_count: int


class HourlyStat(BaseModel):
    hour: int
    label: str
    avg_free_slots: float
    availability_rate: float
    sample_count: int


class AnalyticsSummary(BaseModel):
    generated_at: str
    total_records: int
    weekday_stats: list[WeekdayStat]
    hourly_stats: list[HourlyStat]
    best_weekdays: list[str]
    busiest_weekdays: list[str]
