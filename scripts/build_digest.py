#!/usr/bin/env python3
import datetime as dt
import email.utils
import html
import json
import os
import re
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "feeds.json"
DIST_DIR = ROOT / "dist"


CATEGORIES = {
    "hard_signal": [
        "contract",
        "order",
        "backlog",
        "purchase agreement",
        "supply agreement",
        "power purchase",
        "ppa",
        "financing",
        "prepayment",
        "customer advance",
        "shipment",
        "production",
        "capacity",
        "lease",
    ],
    "risk_signal": [
        "delay",
        "cancel",
        "cut",
        "restriction",
        "export control",
        "inventory",
        "write-down",
        "shortage",
        "oversupply",
        "tariff",
        "margin pressure",
        "slowing",
    ],
    "ai_value_chain": [
        "gpu",
        "hbm",
        "cowos",
        "packaging",
        "optical",
        "ethernet",
        "infiniband",
        "liquid cooling",
        "data center",
        "power",
        "cloud",
        "inference",
        "agent",
        "enterprise ai",
    ],
}


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ai-investment-radar/0.1 contact@example.com",
            "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            return parsed.astimezone(dt.timezone.utc).isoformat()
    except Exception:
        pass
    return value.strip()


def child_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def atom_link(entry: ET.Element) -> str:
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        href = link.attrib.get("href")
        if href:
            return href
    return ""


def parse_feed(feed_name: str, tags: list[str], data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    items = []

    if root.tag.endswith("rss") or root.find("channel") is not None:
        for item in root.findall("./channel/item"):
            title = child_text(item, ["title"])
            link = child_text(item, ["link"])
            published = child_text(item, ["pubDate", "date"])
            summary = child_text(item, ["description", "summary"])
            items.append(build_item(feed_name, tags, title, link, published, summary))
        return items

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{atom_ns}entry"):
        title = child_text(entry, [f"{atom_ns}title"])
        link = atom_link(entry)
        published = child_text(entry, [f"{atom_ns}published", f"{atom_ns}updated"])
        summary = child_text(entry, [f"{atom_ns}summary", f"{atom_ns}content"])
        items.append(build_item(feed_name, tags, title, link, published, summary))
    return items


def score_text(text: str) -> dict:
    lower = text.lower()
    scores = {}
    for category, keywords in CATEGORIES.items():
        hits = [keyword for keyword in keywords if keyword in lower]
        scores[category] = hits
    return scores


def build_item(feed_name: str, tags: list[str], title: str, link: str, published: str, summary: str) -> dict:
    title = strip_html(title)
    summary = strip_html(summary)
    signals = score_text(f"{title} {summary}")
    return {
        "feed": feed_name,
        "tags": tags,
        "title": title,
        "link": link,
        "published": parse_date(published),
        "summary": summary[:500],
        "signals": signals,
        "signal_score": sum(len(values) for values in signals.values()),
    }


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def markdown_item(item: dict) -> str:
    signal_bits = []
    for category, hits in item["signals"].items():
        if hits:
            signal_bits.append(f"{category}: {', '.join(hits[:5])}")
    signal_text = "; ".join(signal_bits) if signal_bits else "no matched signal keywords"
    summary = textwrap.shorten(item["summary"], width=260, placeholder="...")
    return "\n".join(
        [
            f"### [{item['title']}]({item['link']})",
            f"- Feed: {item['feed']}",
            f"- Published: {item['published'] or 'unknown'}",
            f"- Tags: {', '.join(item['tags'])}",
            f"- Signals: {signal_text}",
            f"- Summary: {summary}",
        ]
    )


def write_outputs(items: list[dict], errors: list[dict]) -> None:
    DIST_DIR.mkdir(exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", "14"))
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
    recent_items = [item for item in items if is_recent(item.get("published", ""), cutoff)]
    sorted_items = sorted(recent_items, key=lambda item: item["signal_score"], reverse=True)

    digest_lines = [
        f"# AI Investment Radar - {today}",
        "",
        f"Lookback window: {lookback_days} days",
        f"Items fetched: {len(items)}",
        f"Items in window: {len(sorted_items)}",
        "",
        "## Top Signal Items",
        "",
    ]
    for item in sorted_items[:30]:
        digest_lines.append(markdown_item(item))
        digest_lines.append("")

    if errors:
        digest_lines.extend(["## Fetch Errors", ""])
        for error in errors:
            digest_lines.append(f"- {error['feed']}: {error['error']}")

    (DIST_DIR / "daily-digest.md").write_text("\n".join(digest_lines), encoding="utf-8")
    (DIST_DIR / "daily-items.json").write_text(
        json.dumps(
            {"items": sorted_items, "errors": errors, "lookback_days": lookback_days},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def is_recent(value: str, cutoff: dt.datetime) -> bool:
    if not value:
        return True
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed >= cutoff
    except Exception:
        return True


def main() -> None:
    config = load_config()
    items = []
    errors = []
    for feed in config["feeds"]:
        try:
            data = fetch_url(feed["url"])
            items.extend(parse_feed(feed["name"], feed.get("tags", []), data))
        except Exception as exc:
            errors.append({"feed": feed["name"], "url": feed["url"], "error": str(exc)})
    write_outputs(items, errors)
    print(f"Wrote {len(items)} items with {len(errors)} errors to {DIST_DIR}")


if __name__ == "__main__":
    main()

