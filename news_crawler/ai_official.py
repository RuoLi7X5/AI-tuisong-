from __future__ import annotations

from typing import List
import time
import requests

from .base import NewsCrawler
from .rss_utils import parse_rss_or_atom


class AIOfficialBlogsCrawler(NewsCrawler):
    """Fetch AI official blog updates via RSS/Atom when available."""

    def __init__(self) -> None:
        # RSS/Atom feeds for official AI orgs; some may redirect to Atom
        self.feeds: List[str] = [
            # US/Global
            "https://openai.com/blog/rss.xml",
            "https://www.anthropic.com/feed.xml",
            "https://ai.googleblog.com/atom.xml",
            "https://www.deepmind.com/blog/rss.xml",
            "https://www.microsoft.com/en-us/research/feed/",
            "https://mistral.ai/news/feed.xml",
            "https://blog.cohere.com/rss/",
            "https://blog.cloudflare.com/tag/ai/rss/",  # infra 相关
            # China
            "https://qwenlm.github.io/feed.xml",  # 通义千问团队页
            "https://www.baai.ac.cn/rss.xml",      # 示例（根据可用性调整）
            # HF platform
            "https://huggingface.co/blog/rss",
        ]
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        self.max_items = 200

    def crawl(self):
        items: List[dict] = []
        for url in self.feeds:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                parsed = parse_rss_or_atom(resp.text)
                items.extend(parsed[: self.max_items])
            except Exception as exc:  # noqa: BLE001
                items.append({
                    "title": "AI官方博客抓取失败",
                    "content": f"源: {url} 错误: {exc}",
                    "url": url,
                })
            time.sleep(0.2)
        return items


