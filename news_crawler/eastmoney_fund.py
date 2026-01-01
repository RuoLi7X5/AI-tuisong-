# news_crawler/eastmoney_fund.py
from .base import NewsCrawler
import requests


class EastMoneyFundCrawler(NewsCrawler):
    """东方财富-基金资讯（聚焦指定板块/关键词）"""

    def __init__(self) -> None:
        # 使用东方财富快讯接口获取更多结构化资讯，再在上层用关键词过滤
        # 注意: sortEnd 为空获取最新
        self.base_url = (
            "https://np-weblist.eastmoney.com/comm/web/getFastNewsList?"
            "client=web&biz=web_724&fastColumn=103&pageSize=50&sortEnd="
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://kuaixun.eastmoney.com/'
        }

    def crawl(self):
        news_list = []
        try:
            # 增加 req_trace，减少CDN缓存导致的“滞后”
            import time
            ts = int(time.time() * 1000)
            url = self.base_url + f"&req_trace={ts}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            items = data.get('data', {}).get('fastNewsList', [])
            if not items:
                items = data.get('data', {}).get('list', [])
                
            for item in items:
                news_list.append({
                    "title": item.get("title", ""),
                    "content": item.get("summary", ""),
                    "url": item.get("url", ""),
                })
        except Exception as exc:  # noqa: BLE001
            print(f"[调试] EastMoneyFundCrawler 解析失败: {exc}")
        print(f"[调试] EastMoneyFundCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
