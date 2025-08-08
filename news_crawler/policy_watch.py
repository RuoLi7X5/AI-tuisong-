from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from .base import NewsCrawler


class PolicyWatchCrawler(NewsCrawler):
    """Crawl policy/meeting/foreign-affairs news from gov.cn as a primary source.

    We target the Policy/News sections and extract title+link+snippet. Detailed
    impact analysis is delegated to the summarizer.
    """

    def __init__(self) -> None:
        self.url_list = [
            # 国务院门户要闻/政策
            "https://www.gov.cn/yaowen/index.htm",
            "https://www.gov.cn/zhengce/index.htm",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def _extract(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict] = []
        for a in soup.select("a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if not title or not href:
                continue
            if href.startswith("/"):
                href = "https://www.gov.cn" + href
            if href.startswith("http") and len(title) >= 6:
                items.append({"title": title, "url": href, "content": title})
        return items[:80]

    def crawl(self):
        results: list[dict] = []
        for url in self.url_list:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.encoding = resp.apparent_encoding
                results.extend(self._extract(resp.text))
            except Exception as exc:  # noqa: BLE001
                results.append({
                    "title": "政策抓取失败",
                    "content": f"源: {url} 错误: {exc}",
                    "url": url,
                })
        return results


