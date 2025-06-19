# news_crawler/base.py
class NewsCrawler:
    """新闻爬虫基类，所有爬虫需继承此类"""
    def crawl(self):
        raise NotImplementedError("子类需实现 crawl 方法")
