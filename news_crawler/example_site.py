# news_crawler/example_site.py
from .base import NewsCrawler

class ExampleSiteCrawler(NewsCrawler):
    """示例网站爬虫，实际使用时请扩展为真实新闻网站"""
    def crawl(self):
        # TODO: 实现真实爬虫逻辑
        return [
            {"title": "示例新闻标题", "content": "示例新闻内容", "url": "http://example.com/news/1"}
        ]
