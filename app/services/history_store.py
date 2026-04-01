from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from app.models import AnalyticsSummary, HourlyStat, SystemStatus, WeekdayStat


class HistoryStore:
    WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    def __init__(self, db_path: str = "data/parking_history.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    recorded_at TEXT NOT NULL,
                    total_slots INTEGER NOT NULL,
                    free_slots INTEGER NOT NULL,
                    occupied_slots INTEGER NOT NULL,
                    state TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def record(self, status: SystemStatus) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO snapshots (recorded_at, total_slots, free_slots, occupied_slots, state)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    status.last_updated,
                    status.total_slots,
                    status.free_slots,
                    status.occupied_slots,
                    status.state,
                ),
            )
            connection.commit()

    def build_summary(self, days: int = 30) -> AnalyticsSummary:
        cutoff = datetime.now() - timedelta(days=max(days, 1))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT recorded_at, total_slots, free_slots, occupied_slots, state
                FROM snapshots
                WHERE recorded_at >= ?
                ORDER BY recorded_at ASC
                """,
                (cutoff.isoformat(timespec="seconds"),),
            ).fetchall()

        weekday_groups: dict[int, list[tuple[int, int]]] = defaultdict(list)
        hourly_groups: dict[int, list[tuple[int, int]]] = defaultdict(list)

        for recorded_at, total_slots, free_slots, _occupied_slots, state in rows:
            if state == "offline":
                continue
            timestamp = datetime.fromisoformat(recorded_at)
            weekday_groups[timestamp.weekday()].append((free_slots, total_slots))
            hourly_groups[timestamp.hour].append((free_slots, total_slots))

        weekday_stats = [self._build_weekday_stat(day, weekday_groups.get(day, [])) for day in range(7)]
        hourly_stats = [self._build_hourly_stat(hour, hourly_groups.get(hour, [])) for hour in range(24)]

        comparable_weekdays = [item for item in weekday_stats if item.sample_count > 0]
        if comparable_weekdays:
            best_score = max(item.avg_free_slots for item in comparable_weekdays)
            busy_score = min(item.avg_free_slots for item in comparable_weekdays)
            best_weekdays = [item.label for item in comparable_weekdays if item.avg_free_slots == best_score]
            busiest_weekdays = [item.label for item in comparable_weekdays if item.avg_free_slots == busy_score]
        else:
            best_weekdays = []
            busiest_weekdays = []

        return AnalyticsSummary(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            total_records=len(rows),
            weekday_stats=weekday_stats,
            hourly_stats=hourly_stats,
            best_weekdays=best_weekdays,
            busiest_weekdays=busiest_weekdays,
        )

    def _build_weekday_stat(self, weekday: int, samples: list[tuple[int, int]]) -> WeekdayStat:
        avg_free_slots, availability_rate = self._aggregate(samples)
        return WeekdayStat(
            weekday=weekday,
            label=self.WEEKDAY_LABELS[weekday],
            avg_free_slots=avg_free_slots,
            availability_rate=availability_rate,
            sample_count=len(samples),
        )

    def _build_hourly_stat(self, hour: int, samples: list[tuple[int, int]]) -> HourlyStat:
        avg_free_slots, availability_rate = self._aggregate(samples)
        return HourlyStat(
            hour=hour,
            label=f"{hour:02d}:00",
            avg_free_slots=avg_free_slots,
            availability_rate=availability_rate,
            sample_count=len(samples),
        )

    def _aggregate(self, samples: list[tuple[int, int]]) -> tuple[float, float]:
        if not samples:
            return 0.0, 0.0

        free_avg = round(sum(free for free, _total in samples) / len(samples), 2)
        available_samples = sum(1 for free, _total in samples if free > 0)
        availability_rate = round(available_samples / len(samples), 3)
        return free_avg, availability_rate
