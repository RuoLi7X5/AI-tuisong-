from __future__ import annotations

from typing import List
import requests
import time

from .base import NewsCrawler
from .rss_utils import parse_rss_or_atom


class AIPlatformCrawler(NewsCrawler):
    """Cloud AI platform and framework releases."""

    def __init__(self) -> None:
        self.feeds: List[str] = [
            # Cloud AI services
            "https://azure.microsoft.com/en-us/blog/feed/",
            "https://cloud.google.com/feeds/gcp-release-notes.xml",
            "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
            # Frameworks / inference stacks
            "https://github.com/vllm-project/vllm/releases.atom",
            "https://github.com/ggerganov/llama.cpp/releases.atom",
            "https://github.com/ollama/ollama/releases.atom",
            "https://github.com/huggingface/transformers/releases.atom",
            "https://github.com/huggingface/text-generation-inference/releases.atom",
        ]
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        self.max_items = 100

    def crawl(self):
        items: List[dict] = []
        for url in self.feeds:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                parsed = parse_rss_or_atom(resp.text)
                items.extend(parsed[: self.max_items])
            except Exception as exc:  # noqa: BLE001
                items.append({
                    "title": "AI平台/框架抓取失败",
                    "content": f"源: {url} 错误: {exc}",
                    "url": url,
                })
            time.sleep(0.2)
        return items


