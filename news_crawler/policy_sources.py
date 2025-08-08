from __future__ import annotations

import urllib.parse
from typing import List

import requests
from bs4 import BeautifulSoup

from .base import NewsCrawler
from .config import TARGET_SECTORS, POLICY_KEYWORDS


class MultiPolicyCrawler(NewsCrawler):
    """Aggregate policy/meeting/foreign-affairs news from multiple authorities.

    Sources include (home/list pages; stable selectors are not guaranteed, so we
    parse anchors generically):
      - 国家发展改革委（ndrc.gov.cn）
      - 工业和信息化部（miit.gov.cn）
      - 国家能源局（nea.gov.cn）
      - 中国证监会（csrc.gov.cn）
      - 国家药监局（nmpa.gov.cn）
      - 国家医保局（nhsa.gov.cn）
      - 外交部（fmprc.gov.cn）
      - 商务部（mofcom.gov.cn）
      - 上交所公告（sse.com.cn）
      - 深交所公告（szse.cn）

    We keep the crawler robust by:
      - limiting to same-domain links
      - requiring the anchor text to contain either sector or policy keywords
      - capping the number of items per source
    """

    def __init__(self) -> None:
        self.sources: List[str] = [
            # 政策/要闻聚合页（视网站改版可能失效，作为宽泛入口）
            "https://www.ndrc.gov.cn/xwdt/",
            "https://www.miit.gov.cn/gzcy/index.html",
            "https://www.nea.gov.cn/",
            "https://www.csrc.gov.cn/csrc/c100028/common_list.shtml",  # 要闻/公告列表入口
            "https://www.nmpa.gov.cn/",
            "https://www.nhsa.gov.cn/",
            "https://www.fmprc.gov.cn/web/wjdt_674879/",
            "https://www.mofcom.gov.cn/article/ae/",  # 经贸政策
            "https://www.sse.com.cn/disclosure/announcement/",
            "https://www.szse.cn/disclosure/notice/company/index.html",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        self.max_per_source = 60

    def _same_domain(self, href: str, base: str) -> bool:
        try:
            h = urllib.parse.urlparse(href)
            b = urllib.parse.urlparse(base)
            return bool(h.netloc) and (h.netloc.endswith(b.netloc) or b.netloc.endswith(h.netloc))
        except Exception:
            return False

    def _fix_href(self, href: str, base: str) -> str:
        return urllib.parse.urljoin(base, href)

    def _text_matches(self, text: str) -> bool:
        if not text:
            return False
        # Early filter to reduce noise; final filter仍在上层统一进行
        for kw in TARGET_SECTORS + POLICY_KEYWORDS:
            if kw in text:
                return True
        return False

    def _extract(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []
        for a in soup.select("a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if not title or not href:
                continue
            fixed = self._fix_href(href, base_url)
            if not fixed.startswith("http"):
                continue
            if not self._same_domain(fixed, base_url):
                continue
            if not self._text_matches(title):
                continue
            results.append({"title": title, "content": title, "url": fixed})
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
                    "title": "政策抓取失败",
                    "content": f"源: {src} 错误: {exc}",
                    "url": src,
                })
        return items


