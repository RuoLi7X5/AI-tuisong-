# news_crawler/eastmoney_flash.py
from .base import NewsCrawler
import requests
import time

class EastMoneyFlashCrawler(NewsCrawler):
    """东方财富-快讯API爬虫，直接请求新闻接口，抓取最新快讯"""
    def crawl(self):
        ts = int(time.time() * 1000)
        # sortEnd 为空获取最新
        url = f"https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&pageSize=20&sortEnd=&req_trace={ts}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://kuaixun.eastmoney.com/'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[调试] {url} status: {resp.status_code}")
        news_list = []
        try:
            data = resp.json()
            # API 结构变更: list -> fastNewsList
            items = data.get('data', {}).get('fastNewsList', [])
            if not items:
                # 兼容旧字段名，以防万一
                items = data.get('data', {}).get('list', [])
            
            for item in items:
                news_list.append({
                    "title": item.get("title", ""),
                    "content": item.get("summary", ""),
                    "url": item.get("url", "")
                })
        except Exception as e:
            print(f"[调试] EastMoneyFlashCrawler 解析失败: {e}")
        print(f"[调试] EastMoneyFlashCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
