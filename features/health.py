from __future__ import annotations

import os
import time

HEALTH_FILE = "/tmp/healthy"
MAX_HEARTBEAT_AGE = 30


class HealthCheck:
    def __init__(self, file_path: str = HEALTH_FILE):
        self.file_path = file_path

    def mark_healthy(self) -> None:
        try:
            with open(self.file_path, "w") as f:
                f.write(str(time.time()))
        except OSError:
            pass

    def mark_unhealthy(self) -> None:
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
        except OSError:
            pass

    @classmethod
    def is_healthy(cls, file_path: str = HEALTH_FILE, max_age: int = MAX_HEARTBEAT_AGE) -> bool:
        if not os.path.exists(file_path):
            return False
        try:
            age = time.time() - os.path.getmtime(file_path)
            return age < max_age
        except OSError:
            return False
