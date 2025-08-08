from __future__ import annotations

import requests
from .base import NewsCrawler


class SinaGoldPriceCrawler(NewsCrawler):
    """Fetch gold quotes from Sina HQ API as a robust fallback.

    Symbols:
    - hf_XAU: spot gold XAUUSD
    - AU9999: Shanghai Gold Exchange Au99.99 reference
    """

    def __init__(self) -> None:
        self.url = "https://hq.sinajs.cn/?list=hf_XAU,AU9999"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://finance.sina.com.cn/",
        }

    def _parse_line(self, line: str) -> dict | None:
        # Example: var hq_str_hf_XAU="现货黄金,2350.16,2351.00,2348.87,2353.66,2345.43,...,2024-06-20,23:59:59";
        try:
            name_start = line.find("=")
            if name_start == -1:
                return None
            payload = line[name_start + 1 :].strip().strip(";")
            payload = payload.strip('"')
            parts = payload.split(",")
            if len(parts) < 6:
                return None
            name = parts[0]
            last = parts[1]
            open_price = parts[2]
            prev_close = parts[3]
            high = parts[4]
            low = parts[5]
            date = parts[-2] if len(parts) >= 2 else ""
            time = parts[-1] if len(parts) >= 1 else ""
            title = f"黄金 | {name} 现价:{last} 开盘:{open_price} 高:{high} 低:{low}"
            content = f"昨收:{prev_close} 时间:{date} {time}"
            url = "https://finance.sina.com.cn/money/forex/hq/XAUUSD.shtml"
            return {"title": title, "content": content, "url": url}
        except Exception:
            return None

    def crawl(self):
        items: list[dict] = []
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.splitlines():
                parsed = self._parse_line(line)
                if parsed:
                    items.append(parsed)
        except Exception as exc:  # noqa: BLE001
            items.append({
                "title": "黄金价格抓取失败(新浪)",
                "content": f"失败: {exc}",
                "url": "",
            })
        return items


