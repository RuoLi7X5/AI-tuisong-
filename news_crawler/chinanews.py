# news_crawler/chinanews.py
from .base import NewsCrawler
import requests
from bs4 import BeautifulSoup

class ChinaNewsCrawler(NewsCrawler):
    """中国新闻网-国内新闻爬虫（限制抓取数量，去掉调试写盘）"""
    def crawl(self, max_items: int = 50):
        url = "https://www.chinanews.com.cn/china/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[调试] {url} status: {resp.status_code}")
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        news_list = []
        # 新闻列表区域
        count = 0
        for li in soup.find_all('li'):
            a = li.find('a')
            if a and a.get('href') and a.get_text(strip=True):
                # 新增：抓取详情页正文内容
                detail_url = a.get('href', '')
                detail_content = ''
                if detail_url.startswith('http'):
                    try:
                        detail_resp = requests.get(detail_url, headers=headers, timeout=10)
                        detail_resp.encoding = detail_resp.apparent_encoding
                        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                        # 尝试多种正文选择器
                        content_tag = detail_soup.find('div', class_='left_zw') or \
                                      detail_soup.find('div', class_='content') or \
                                      detail_soup.find('div', id='content')
                        if content_tag:
                            detail_content = content_tag.get_text(separator='\n', strip=True)
                    except Exception as e:
                        detail_content = f"正文抓取失败: {e}"
                news_list.append({
                    "title": a.get_text(strip=True),
                    "content": detail_content or a.get('title', ''),
                    "url": detail_url
                })
                count += 1
                if count >= max_items:
                    break
        print(f"[调试] ChinaNewsCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
