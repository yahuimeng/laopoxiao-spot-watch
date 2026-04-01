from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from urllib import error, parse, request

from app.models import SystemStatus


class WeChatNotifier:
    def __init__(self, settings: dict[str, Any]) -> None:
        self.webhook_url = settings.get("wechat_webhook_url", "")
        self.serverchan_sendkey = settings.get("serverchan_sendkey", "")
        self.cooldown_seconds = int(settings.get("notification_cooldown_seconds", 1800))
        self.last_sent_at: datetime | None = None
        self.last_available = False

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url or self.serverchan_sendkey)

    def maybe_notify(self, status: SystemStatus) -> None:
        currently_available = status.state == "available" and status.free_slots > 0
        should_send = (
            self.enabled
            and currently_available
            and not self.last_available
            and not self._in_cooldown()
        )

        if should_send:
            self._send(status)
            self.last_sent_at = datetime.now()

        self.last_available = currently_available

    def _in_cooldown(self) -> bool:
        if self.last_sent_at is None:
            return False
        return datetime.now() - self.last_sent_at < timedelta(seconds=self.cooldown_seconds)

    def _send(self, status: SystemStatus) -> None:
        title = "老破小车位哨兵提醒"
        body = (
            f"检测到楼下出现空位。\\n"
            f"空位数：{status.free_slots}/{status.total_slots}\\n"
            f"时间：{status.last_updated}\\n"
            f"建议你现在出门前再看一眼页面确认。"
        )

        if self.webhook_url:
            payload = json.dumps({"msgtype": "text", "text": {"content": f"{title}\\n{body}"}}).encode("utf-8")
            req = request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            self._safe_open(req)

        if self.serverchan_sendkey:
            url = f"https://sctapi.ftqq.com/{self.serverchan_sendkey}.send"
            form = parse.urlencode({"title": title, "desp": body}).encode("utf-8")
            req = request.Request(url, data=form, method="POST")
            self._safe_open(req)

    def _safe_open(self, req: request.Request) -> None:
        try:
            with request.urlopen(req, timeout=10):
                return
        except error.URLError:
            return
