from __future__ import annotations

import requests
from .base import NewsCrawler
from .config import TARGET_SECTORS


class SectorOpenCrawler(NewsCrawler):
    """Fetch opening and intraday snapshot for target sectors (industry/concept boards).

    Data source: Eastmoney push2 board list API. We query both industry (t:2)
    and concept (t:3) boards, then filter by sector keywords. The field
    mapping is based on Eastmoney common quote fields.
    """

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        self.base_url = (
            "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=200&po=1&np=1&fltt=2&fid=f3&fields=f2,f3,f4,f12,f14,f15,f16,f17,f18&fs="
        )

    def _fetch(self, fs: str):
        url = self.base_url + fs
        resp = requests.get(url, headers=self.headers, timeout=10)
        data = resp.json()
        return data.get("data", {}).get("diff", [])

    def crawl(self):
        results: list[dict] = []
        try:
            # Industry boards
            industry = self._fetch("m:90+t:2")
            # Concept boards
            concept = self._fetch("m:90+t:3")
            all_boards = (industry or []) + (concept or [])
            for it in all_boards:
                name = str(it.get("f14", ""))
                if not name:
                    continue
                if not any(sector in name for sector in TARGET_SECTORS):
                    continue
                code = it.get("f12", "")
                last = it.get("f2")  # latest
                pct = it.get("f3")  # pct change
                chg = it.get("f4")  # change amount
                high = it.get("f15")
                low = it.get("f16")
                open_price = it.get("f17")
                prev_close = it.get("f18")

                title = f"板块开盘 | {name}  开盘:{open_price}  现价:{last}  涨跌:{chg} 涨幅:{pct}%"
                content = (
                    f"高:{high}  低:{low}  昨收:{prev_close}  代码:{code}"
                )
                url = f"https://quote.eastmoney.com/bk/90.{code}.html" if code else "https://quote.eastmoney.com/"
                results.append({
                    "title": title,
                    "content": content,
                    "url": url,
                })
        except Exception as exc:  # noqa: BLE001
            results.append({
                "title": "板块开盘数据抓取失败",
                "content": f"抓取失败: {exc}",
                "url": "",
            })
        return results


