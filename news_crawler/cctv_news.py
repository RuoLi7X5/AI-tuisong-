from .base import NewsCrawler
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class CCTVNewsCrawler(NewsCrawler):
    """CCTV News (Xinwen Lianbo) Summary Crawler"""
    def crawl(self):
        # Target: Find the latest "Xinwen Lianbo" summary
        # Usually found on news.cctv.com or news.cctv.com/china/
        urls = [
            "https://news.cctv.com/china/",
            "https://news.cctv.com/world/",
            "https://tv.cctv.com/lm/xwlb/",
            "https://news.cctv.com/lbj/", # 联播+
        ]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        found_items = []
        today_str = datetime.now().strftime("%Y%m%d")
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.encoding = resp.apparent_encoding
                soup = BeautifulSoup(resp.text, "html.parser")
                
                for a in soup.find_all('a'):
                    title = a.get_text(strip=True)
                    link = a.get('href')
                    
                    # Pattern: "《新闻联播》 20241226期 节目主要内容"
                    if title and "新闻联播" in title and "主要内容" in title:
                        # Optional: Check if it matches today's date if strict daily push is required
                        # But user said "after the end", so grabbing the latest is fine.
                        # We can filter by date if needed.
                        
                        # Fetch content
                        content = self._fetch_content(link, headers)
                        found_items.append({
                            "title": title,
                            "content": content,
                            "url": link,
                            "tags": ["政治", "新闻联播"]
                        })
            except Exception as e:
                print(f"[CCTV] Error scraping {url}: {e}")
                
        # Deduplicate by URL
        unique_items = []
        seen_urls = set()
        for item in found_items:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_items.append(item)
                
        return unique_items

    def _fetch_content(self, url, headers):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Content usually in #content_area or .content_area
            # CCTV structure varies, but often #content_body or similar
            content_div = soup.find('div', id='content_area') or \
                          soup.find('div', class_='content_area') or \
                          soup.find('div', id='text_area')
            
            if content_div:
                return content_div.get_text(separator='\n', strip=True)
            return ""
        except Exception:
            return ""
