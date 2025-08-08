from __future__ import annotations

import time
import requests
from bs4 import BeautifulSoup

from .base import NewsCrawler


class AINewsCrawler(NewsCrawler):
    """Fetch latest AI industry news from multiple tech portals.

    Sources:
      - 量子位 (QbitAI) 最新文章页
      - 机器之心 (Synced) 新闻列表
    We parse anchor tags generically; this is resilient to minor layout changes.
    """

    def __init__(self) -> None:
        self.sources = [
            "https://www.qbitai.com/",
            "https://www.jiqizhixin.com/news",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        self.max_per_source = 40

    def _extract(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for a in soup.select("a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if not title or not href:
                continue
            if href.startswith("/"):
                # basic join
                if base_url.endswith("/"):
                    href = base_url[:-1] + href
                else:
                    href = base_url + href
            if not href.startswith("http"):
                continue
            # Rough filter to keep AI/model posts primarily
            if any(k in title for k in ("模型", "大模型", "LLM", "AI", "多模态", "发布", "开源", "推理", "评测", "对齐", "指令")):
                results.append({"title": title, "url": href, "content": title})
                if len(results) >= self.max_per_source:
                    break
        return results

    def crawl(self):
        items: list[dict] = []
        for src in self.sources:
            try:
                resp = requests.get(src, headers=self.headers, timeout=10)
                resp.encoding = resp.apparent_encoding
                items.extend(self._extract(resp.text, src))
            except Exception as exc:  # noqa: BLE001
                items.append({
                    "title": "AI新闻抓取失败",
                    "content": f"源: {src} 错误: {exc}",
                    "url": src,
                })
            time.sleep(0.3)
        return items


