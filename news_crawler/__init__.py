# news_crawler/__init__.py
from .base import NewsCrawler
from .example_site import ExampleSiteCrawler
from .eastmoney import EastMoneyCrawler
from .eastmoney_fund import EastMoneyFundCrawler
from .chinanews import ChinaNewsCrawler
from .eastmoney_flash import EastMoneyFlashCrawler
from .cctvnews import CCTVNewsCrawler

def run_all_crawlers():
    # 预留：可扩展多个网站爬虫
    crawlers = [
        # ExampleSiteCrawler(),  # 可注释掉示例爬虫
        EastMoneyCrawler(),
        EastMoneyFundCrawler(),
        ChinaNewsCrawler(),
        EastMoneyFlashCrawler(),
        CCTVNewsCrawler()
    ]
    news_list = []
    for crawler in crawlers:
        result = crawler.crawl()
        print(f"[爬虫调试] {crawler.__class__.__name__} 抓取到 {len(result)} 条新闻")
        news_list.extend(result)
    return news_list
