from __future__ import annotations

from typing import List
from bs4 import BeautifulSoup


def parse_rss_or_atom(xml_text: str) -> List[dict]:
    """Parse RSS/Atom XML into a list of {title, url, content} dicts.

    We support common variants: RSS (<item>) and Atom (<entry>).
    """
    soup = BeautifulSoup(xml_text, "xml")
    items: List[dict] = []
    # RSS
    for item in soup.find_all("item"):
        title = (item.title.string or "").strip() if item.title else ""
        link = (item.link.string or "").strip() if item.link else ""
        description_tag = item.find("description") or item.find("summary")
        desc = (description_tag.get_text() or "").strip() if description_tag else title
        if title and link:
            items.append({"title": title, "url": link, "content": desc})
    if items:
        return items
    # Atom
    for entry in soup.find_all("entry"):
        title_tag = entry.find("title")
        link_tag = entry.find("link")
        href = link_tag.get("href") if link_tag else ""
        title = (title_tag.get_text() or "").strip() if title_tag else ""
        summary_tag = entry.find("summary") or entry.find("content")
        desc = (summary_tag.get_text() or "").strip() if summary_tag else title
        if title and href:
            items.append({"title": title, "url": href, "content": desc})
    return items


