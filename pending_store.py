from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List


def _stable_item_key(it: Dict[str, Any]) -> str:
    """Stable key used for pending queue de-duplication."""
    url = (it.get("url") or "").strip()
    if url:
        return f"url:{url}"
    title = (it.get("title") or "").strip()
    if title:
        return f"title:{title}"
    # fallback: best-effort hash-like key without extra deps
    content = (it.get("content") or "").strip()
    return f"raw:{title[:50]}|{content[:50]}"


class PendingStore:
    """JSON-based queue for items waiting for deep analysis (AI summarization)."""

    def __init__(self, path: str = "data/pending.json", retention_days: int = 2) -> None:
        self.path = path
        self.retention_days = retention_days
        self.items: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.items = data
        except Exception:
            self.items = []

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _purge(self) -> None:
        """Drop very old items (best-effort)."""
        now = time.time()
        ttl = self.retention_days * 86400
        kept: List[Dict[str, Any]] = []
        for it in self.items:
            ts = it.get("_queued_at")
            try:
                tsf = float(ts) if ts is not None else now
            except Exception:
                tsf = now
            if now - tsf <= ttl:
                kept.append(it)
        self.items = kept

    def add_many(self, items: List[Dict[str, Any]]) -> int:
        """Append new items to pending queue; returns number of newly added."""
        self._purge()
        existing = {_stable_item_key(it) for it in self.items if isinstance(it, dict)}
        added = 0
        now = time.time()
        for it in items:
            if not isinstance(it, dict):
                continue
            key = _stable_item_key(it)
            if key in existing:
                continue
            it = dict(it)
            it["_queued_at"] = now
            self.items.append(it)
            existing.add(key)
            added += 1
        if added:
            self._save()
        return added

    def pop_all(self) -> List[Dict[str, Any]]:
        """Pop and clear all pending items."""
        self._purge()
        items = list(self.items)
        self.items = []
        self._save()
        return items

    def pop_many(self, limit: int) -> List[Dict[str, Any]]:
        """Pop up to `limit` items, keeping the rest for next analysis run."""
        self._purge()
        if limit <= 0:
            return []
        items = self.items[:limit]
        self.items = self.items[limit:]
        self._save()
        return list(items)

