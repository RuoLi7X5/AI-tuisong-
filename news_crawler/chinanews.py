# news_crawler/chinanews.py
from .base import NewsCrawler
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import urllib.parse

from .config import match_keywords

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
        # 优化点：原实现会对列表页每一条都抓详情页，网络请求量巨大且串行。
        # 这里改为：先用标题做一次关键词命中筛选，再并发抓取少量详情页。
        candidates = []
        seen_urls = set()
        for a in soup.select("a[href]"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or not href:
                continue
            # normalize url
            if href.startswith("//"):
                href = "https:" + href
            href = urllib.parse.urljoin(url, href)
            if not href.startswith("http"):
                continue
            # 过滤非新闻详情的噪音链接
            if "chinanews.com.cn" not in href:
                continue
            if href in seen_urls:
                continue
            tags = match_keywords(title)
            if not tags:
                continue
            seen_urls.add(href)
            candidates.append({"title": title, "url": href, "tags": tags})
            if len(candidates) >= max_items:
                break

        def _fetch_detail(item):
            detail_url = item["url"]
            detail_content = ""
            try:
                detail_resp = requests.get(detail_url, headers=headers, timeout=10)
                detail_resp.encoding = detail_resp.apparent_encoding
                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                content_tag = (
                    detail_soup.find("div", class_="left_zw")
                    or detail_soup.find("div", class_="content")
                    or detail_soup.find("div", id="content")
                )
                if content_tag:
                    detail_content = content_tag.get_text(separator="\n", strip=True)
            except Exception as e:  # noqa: BLE001
                detail_content = f"正文抓取失败: {e}"
            # 控制正文长度，避免后续AI摘要prompt过大
            if detail_content and len(detail_content) > 2500:
                detail_content = detail_content[:2500]
            return {
                "title": item["title"],
                "content": detail_content or item["title"],
                "url": detail_url,
                "tags": item.get("tags", []),
            }

        news_list = []
        if candidates:
            max_workers = min(10, max(1, len(candidates)))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = [ex.submit(_fetch_detail, it) for it in candidates]
                for fut in concurrent.futures.as_completed(futures):
                    try:
                        news_list.append(fut.result())
                    except Exception as e:  # noqa: BLE001
                        print(f"[调试] ChinaNewsCrawler 详情抓取失败: {e}")
        print(f"[调试] ChinaNewsCrawler 抓取到 {len(news_list)} 条新闻")
        return news_list
