from __future__ import annotations

import json
import os
import time
from typing import Dict, Tuple


class StateStore:
    """Simple JSON-based store to de-duplicate items across runs.

    We persist a dict of {key: last_seen_ts}. Keys should be stable, e.g., url
    or (title+domain). Items older than retention_days will be purged.
    """

    def __init__(self, path: str = "data/state.json", retention_days: int = 7) -> None:
        self.path = path
        self.retention_days = retention_days
        self.data: Dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
        except Exception:
            self.data = {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _purge(self) -> None:
        now = time.time()
        ttl = self.retention_days * 86400
        keys_to_delete = [k for k, ts in self.data.items() if now - float(ts) > ttl]
        for k in keys_to_delete:
            self.data.pop(k, None)

    def seen(self, key: str) -> bool:
        return key in self.data

    def mark(self, key: str) -> None:
        self.data[key] = time.time()

    def flush(self) -> None:
        self._purge()
        self._save()


