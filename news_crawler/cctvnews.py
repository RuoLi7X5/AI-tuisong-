import requests
from bs4 import BeautifulSoup

class CCTVNewsCrawler:
    def __init__(self):
        self.url = "https://news.cctv.com/china/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

    def crawl(self, max_count=5):
        resp = requests.get(self.url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        news_list = []
        # 适配央视新闻结构，提取新闻链接
        for li in soup.select('ul#newslist li.borderenno')[:max_count]:
            a = li.select_one('h3.titlekapian a')
            if not a:
                continue
            title = a.get_text(strip=True)
            link = a['href']
            # 获取详情页正文
            try:
                detail_resp = requests.get(link, headers=self.headers, timeout=10)
                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                content_tag = detail_soup.find('div', class_='content_area')
                content = content_tag.get_text(separator='\n', strip=True) if content_tag else ''
            except Exception as e:
                content = f"正文抓取失败: {e}"
            news_list.append({
                "title": title,
                "url": link,
                "content": content
            })
        print(f"[调试] CCTVNewsCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
