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
from .cctv_news import CCTVNewsCrawler
from state_store import StateStore
import concurrent.futures
import hashlib
from typing import Any, Dict, Iterable, List, Tuple


def _stable_item_key(it: Dict[str, Any]) -> str:
    """Build a stable de-dup key for a news item.

    Priority:
    - url (best)
    - normalized title
    - short hash of (title+content) as last resort
    """
    url = (it.get("url") or "").strip()
    if url:
        return f"url:{url}"
    title = (it.get("title") or "").strip()
    if title:
        return f"title:{title}"
    content = (it.get("content") or "").strip()
    raw = (title + "\n" + content).encode("utf-8", errors="ignore")
    digest = hashlib.sha1(raw).hexdigest()[:12]
    return f"hash:{digest}"


def _deduplicate(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for it in items:
        key = _stable_item_key(it)
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
        CCTVNewsCrawler(),     # 新闻联播内容
    ]

    def _run_one(crawler: NewsCrawler) -> Tuple[str, List[Dict[str, Any]]]:
        try:
            result = crawler.crawl()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - keep system running
            print(f"[爬虫错误] {crawler.__class__.__name__}: {exc}")
            result = []
        if not isinstance(result, list):
            result = []
        # attach source for debugging/tracing (won't break downstream)
        for it in result:
            if isinstance(it, dict):
                it.setdefault("source", crawler.__class__.__name__)
        return (crawler.__class__.__name__, result)  # type: ignore[return-value]

    news_list: List[Dict[str, Any]] = []
    store = StateStore()
    gold_snapshot = None

    # Run crawlers concurrently (IO-bound). Post-process sequentially to keep
    # StateStore operations simple and deterministic.
    max_workers = min(8, max(1, len(crawlers)))
    results_by_name: Dict[str, List[Dict[str, Any]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_run_one, c) for c in crawlers]
        for fut in concurrent.futures.as_completed(futures):
            name, result = fut.result()
            results_by_name[name] = result

    for crawler in crawlers:
        cname = crawler.__class__.__name__
        result = results_by_name.get(cname, [])
        print(f"[爬虫调试] {cname} 抓取到 {len(result)} 条")
        # 合并黄金来源：只保留一条
        if isinstance(crawler, (GoldPriceCrawler, SinaGoldPriceCrawler)):
            # 若已有黄金快照，跳过后续黄金源
            if gold_snapshot is not None:
                continue
            if result:
                gold_snapshot = result[0]
                text = f"{gold_snapshot.get('title','')}\n{gold_snapshot.get('content','')}"
                tags = gold_snapshot.get("tags") or match_keywords(text)
                if tags:
                    gold_snapshot["tags"] = tags
                key = _stable_item_key(gold_snapshot)
                if not store.seen(key):
                    store.mark(key)
                    news_list.append(gold_snapshot)
            continue
        
        # CCTV Special Handling (Always add if found, maybe skip keyword match or ensure it has tags)
        if isinstance(crawler, CCTVNewsCrawler):
            for item in result:
                # CCTV items usually already have tags assigned in crawler
                key = _stable_item_key(item)
                if not store.seen(key):
                    store.mark(key)
                    news_list.append(item)
            continue

        for item in result:
            text = f"{item.get('title','')}\n{item.get('content','')}"
            tags = item.get("tags") or match_keywords(text)
            if tags:
                item["tags"] = tags
                key = _stable_item_key(item)
                if not store.seen(key):
                    store.mark(key)
                    news_list.append(item)
    news_list = _deduplicate(news_list)
    print(f"[筛选] 关注板块：{', '.join(TARGET_SECTORS)}，产出 {len(news_list)} 条")
    store.flush()
    return news_list
