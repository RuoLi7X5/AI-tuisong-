from __future__ import annotations

from typing import List
import requests
import time

from .base import NewsCrawler
from .rss_utils import parse_rss_or_atom


class AIResearchCrawler(NewsCrawler):
    """Research-level feeds: arXiv + Papers with Code SOTA updates."""

    def __init__(self) -> None:
        self.feeds: List[str] = [
            # arXiv CS/AI-related categories
            "https://export.arxiv.org/rss/cs.AI",
            "https://export.arxiv.org/rss/cs.CL",
            "https://export.arxiv.org/rss/cs.LG",
            "https://export.arxiv.org/rss/stat.ML",
            "https://export.arxiv.org/rss/cs.CV",
            # Papers with Code blog
            "https://paperswithcode.com/feeds/latest",
        ]
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        self.max_items = 200

    def crawl(self):
        items: List[dict] = []
        failures: List[str] = []
        for url in self.feeds:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                parsed = parse_rss_or_atom(resp.text)
                if parsed:
                    items.extend(parsed[: self.max_items])
                else:
                    failures.append(url)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{url} 错误: {exc}")
            time.sleep(0.2)
        if failures:
            items.append({
                "title": "AI研究源抓取失败",
                "content": "; ".join(failures)[:2000],
                "url": "",
            })
        return items


