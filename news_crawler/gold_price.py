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
        # 补全 fields: f15(high), f16(low), f17(open), f18(prev_close)
        self.url = (
            "https://push2.eastmoney.com/api/qt/ulist/get?"
            "fltt=2&invt=2&dect=2&np=1&fields=f2,f3,f4,f12,f13,f14,f15,f16,f17,f18&"
            "secids=100.GC00,103.GC00,113.GC00,123.GC00,131.YAUUSD"  # 尝试多种市场代码
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
            if isinstance(lst, dict): # 有时候 diff 是 dict (id做key)
                 lst = list(lst.values())
            
            for it in lst:
                name = it.get("f14", "黄金")
                price = it.get("f2")  # 最新价
                change_pct = it.get("f3")  # 涨跌幅%
                # 过滤无效数据
                if price == "-" or not price:
                    continue

                code = it.get("f12")
                high = it.get("f15")
                low = it.get("f16")
                open_price = it.get("f17")
                prev_close = it.get("f18")
                title = f"黄金 | {name} 现价:{price} 涨幅:{change_pct}%"
                content = f"开盘:{open_price} 高:{high} 低:{low} 昨收:{prev_close}"
                url = "https://quote.eastmoney.com/"  # 引导至行情页
                items.append({"title": title, "content": content, "url": url})
        except Exception as e:
            print(f"[GoldPriceCrawler] Error: {e}")
            return []
        return items


