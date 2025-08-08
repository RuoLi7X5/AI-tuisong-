from __future__ import annotations

import requests
from .base import NewsCrawler


class GoldPriceCrawler(NewsCrawler):
    """Fetch spot gold price info from a public JSON endpoint.

    We avoid retail pricing and focus on market references. As a lightweight
    approach, we use Eastmoney's precious metal quote API as an example.
    """

    def __init__(self) -> None:
        # Eastmoney precious metal quotes (example, subject to change)
        # API returns a JSONP-like payload sometimes; we attempt to parse JSON.
        self.url = (
            "https://push2.eastmoney.com/api/qt/ulist/get?"
            "fltt=2&invt=2&dect=2&np=1&fields=f2,f3,f4,f12,f13,f14&"
            "secids=103.GC00,131.YAUUSD"  # COMEX主连与伦敦金USD示例
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def crawl(self):
        items: list[dict] = []
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=10)
            data = resp.json()
            lst = data.get("data", {}).get("diff", [])
            for it in lst:
                name = it.get("f14", "黄金")
                price = it.get("f2")  # 最新价
                change_pct = it.get("f3")  # 涨跌幅%
                code = it.get("f12")
                high = it.get("f15")
                low = it.get("f16")
                open_price = it.get("f17")
                prev_close = it.get("f18")
                title = f"黄金 | {name} 现价:{price} 涨幅:{change_pct}% 开盘:{open_price} 高:{high} 低:{low} 昨收:{prev_close}"
                content = title
                url = "https://quote.eastmoney.com/"  # 引导至行情页
                items.append({"title": title, "content": content, "url": url})
        except Exception:
            # 返回空列表，让上层用新浪源兜底，不再产生“失败”推送
            return []
        return items


