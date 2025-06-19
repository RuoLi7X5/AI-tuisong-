# news_crawler/eastmoney_fund.py
from .base import NewsCrawler
import requests
from bs4 import BeautifulSoup

class EastMoneyFundCrawler(NewsCrawler):
    """东方财富-国内基金新闻爬虫"""
    def crawl(self):
        url = "https://finance.eastmoney.com/a/cgnjj.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[调试] {url} status: {resp.status_code}")
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        news_list = []
        # 头条
        headline = soup.select_one("div#newsList h2 a")
        if headline:
            news_list.append({
                "title": headline.get_text(strip=True),
                "content": headline.get("title", ""),
                "url": headline.get("href", "")
            })
        # 列表新闻
        for li in soup.select("div#newsList ul li a"):
            news_list.append({
                "title": li.get_text(strip=True),
                "content": li.get("title", ""),
                "url": li.get("href", "")
            })
        print(f"[调试] EastMoneyFundCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
