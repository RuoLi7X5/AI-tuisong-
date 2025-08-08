# news_crawler/__init__.py
from .base import NewsCrawler
from .eastmoney_fund import EastMoneyFundCrawler
from .chinanews import ChinaNewsCrawler
from .eastmoney_flash import EastMoneyFlashCrawler
from .gold_price import GoldPriceCrawler
from .gold_price_sina import SinaGoldPriceCrawler
from .config import match_keywords, TARGET_SECTORS
from .sector_open import SectorOpenCrawler
from .policy_watch import PolicyWatchCrawler
from .policy_sources import MultiPolicyCrawler
from .ai_news import AINewsCrawler
from .ai_official import AIOfficialBlogsCrawler
from .ai_research import AIResearchCrawler
from .ai_platforms import AIPlatformCrawler
from state_store import StateStore


def _deduplicate(items):
    seen = set()
    deduped = []
    for it in items:
        key = (it.get("url") or "", it.get("title") or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)
    return deduped


def run_all_crawlers():
    """Run all crawlers, then filter by target sectors/keywords.

    Returns list of dicts with optional field 'tags' indicating matched keywords.
    """
    crawlers = [
        EastMoneyFlashCrawler(),
        EastMoneyFundCrawler(),
        ChinaNewsCrawler(),
        GoldPriceCrawler(),  # 黄金价格监测（东财）
        SinaGoldPriceCrawler(),  # 黄金价格监测（新浪）
        SectorOpenCrawler(),  # 关注板块的当日开盘/盘中快照
        PolicyWatchCrawler(),  # 重大会议/政策/外交要闻
        MultiPolicyCrawler(),  # 多部委/交易所等政策/公告源
        AINewsCrawler(),             # AI 行业媒体
        AIOfficialBlogsCrawler(),    # 官方博客（OpenAI/Anthropic/Google/Meta/HF等）
        AIResearchCrawler(),         # arXiv + PwC
        AIPlatformCrawler(),         # 云平台/框架/GitHub Releases
    ]
    news_list = []
    store = StateStore()
    gold_snapshot = None
    for crawler in crawlers:
        try:
            result = crawler.crawl()
        except Exception as exc:  # noqa: BLE001 - keep system running
            print(f"[爬虫错误] {crawler.__class__.__name__}: {exc}")
            result = []
        print(f"[爬虫调试] {crawler.__class__.__name__} 抓取到 {len(result)} 条")
        # 合并黄金来源：只保留一条
        if isinstance(crawler, (GoldPriceCrawler, SinaGoldPriceCrawler)):
            # 若已有黄金快照，跳过后续黄金源
            if gold_snapshot is not None:
                continue
            if result:
                gold_snapshot = result[0]
                text = f"{gold_snapshot.get('title','')}\n{gold_snapshot.get('content','')}"
                tags = match_keywords(text)
                if tags:
                    gold_snapshot["tags"] = tags
                key = gold_snapshot.get("url") or gold_snapshot.get("title", "")
                if not store.seen(key):
                    store.mark(key)
                    news_list.append(gold_snapshot)
            continue

        for item in result:
            text = f"{item.get('title','')}\n{item.get('content','')}"
            tags = match_keywords(text)
            if tags:
                item["tags"] = tags
                key = item.get("url") or item.get("title", "")
                if not store.seen(key):
                    store.mark(key)
                    news_list.append(item)
    news_list = _deduplicate(news_list)
    print(f"[筛选] 关注板块：{', '.join(TARGET_SECTORS)}，产出 {len(news_list)} 条")
    store.flush()
    return news_list
