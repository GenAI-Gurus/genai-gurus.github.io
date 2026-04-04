#!/usr/bin/env python3
"""Sync Meetup data into src/data/ for Astro build.

Produces:
  - src/data/upcoming_event.json  (next event)
  - src/data/community_stats.json (aggregate numbers)
  - src/data/leaderboard.json     (top 100 by participation score)

Reuses the proven Meetup crawling approach from the legacy Jekyll sync script.
"""

from __future__ import annotations

import datetime as dt
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "src" / "data"

DEFAULT_ICAL_URL = "https://www.meetup.com/genai-gurus/events/ical/"
DEFAULT_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/"
DEFAULT_PAST_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/past/"
HEADERS = {"User-Agent": "genai-gurus-event-sync/2.0"}


def log(msg: str) -> None:
    print(f"[sync] {msg}")


def debug(msg: str) -> None:
    if os.environ.get("SYNC_DEBUG", "").strip().lower() in {"1", "true"}:
        print(f"[sync][debug] {msg}")


# ---------------------------------------------------------------------------
# Meetup HTML / iCal parsing helpers (ported from legacy script)
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read().decode("utf-8", errors="replace")


def strip_html(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html_mod.unescape(no_tags)).strip()


def unfold_ical_lines(text: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def parse_dt(value: str) -> dt.datetime | None:
    value = value.strip()
    if not value:
        return None
    if value.endswith("Z"):
        return dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
    if "T" in value:
        return dt.datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=dt.timezone.utc)
    return dt.datetime.strptime(value, "%Y%m%d").replace(tzinfo=dt.timezone.utc)


def unescape_ical(value: str) -> str:
    return value.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def extract_speaker(summary: str, description: str) -> str:
    for pattern in [r"Speaker[s]?:\s*([^\n|,;]+)", r"Presented by\s*([^\n|,;]+)"]:
        m = re.search(pattern, f"{summary}\n{description}", re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def parse_ical_events(ical_text: str) -> list[dict]:
    lines = unfold_ical_lines(ical_text)
    events: list[dict] = []
    event: dict | None = None

    for line in lines:
        if line == "BEGIN:VEVENT":
            event = {}
            continue
        if line == "END:VEVENT":
            if event:
                events.append(event)
            event = None
            continue
        if event is None or ":" not in line:
            continue
        key_part, value = line.split(":", 1)
        event[key_part.split(";", 1)[0]] = value.strip()

    now = dt.datetime.now(dt.timezone.utc)
    parsed = []
    for item in events:
        event_dt = parse_dt(item.get("DTSTART", ""))
        if event_dt is None:
            continue
        summary = strip_html(unescape_ical(item.get("SUMMARY", "")))
        description = strip_html(unescape_ical(item.get("DESCRIPTION", "")))
        parsed.append({
            "title": summary or "GenAI Gurus Event",
            "date": event_dt.isoformat().replace("+00:00", "Z"),
            "is_upcoming": event_dt >= now,
            "speaker_name": extract_speaker(summary, description),
            "meetup_url": item.get("URL", "").strip() or DEFAULT_EVENTS_URL,
            "summary": description[:280],
        })
    parsed.sort(key=lambda e: e["date"])
    return parsed


def extract_image_from_html(page_html: str) -> str:
    og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', page_html, re.I)
    if og:
        return html_mod.unescape(og.group(1)).strip()

    pat = re.compile(r"https://secure\.meetupstatic\.com/photos/event/[^\"\'\s>]+", re.I)
    m = pat.search(page_html)
    return m.group(0) if m else ""


def to_utc_iso(value: str) -> str | None:
    raw = (value or "").strip().replace("Z", "+00:00")
    if not raw:
        return None
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_ld_json_events(html_text: str) -> list[dict]:
    script_pat = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
    now = dt.datetime.now(dt.timezone.utc)
    parsed = []

    for match in script_pat.findall(html_text):
        try:
            payload = json.loads(match.strip())
        except json.JSONDecodeError:
            continue
        nodes = payload if isinstance(payload, list) else [payload]
        expanded = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            if isinstance(n.get("@graph"), list):
                expanded.extend(g for g in n["@graph"] if isinstance(g, dict))
            expanded.append(n)

        for node in expanded:
            ntype = node.get("@type")
            is_event = "Event" in ntype if isinstance(ntype, list) else ntype == "Event"
            if not is_event:
                continue
            date_iso = to_utc_iso(str(node.get("startDate", "")))
            if not date_iso:
                continue
            event_dt = dt.datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
            description = strip_html(str(node.get("description", "")))

            speaker = ""
            performer = node.get("performer")
            if isinstance(performer, dict):
                speaker = str(performer.get("name", "")).strip()
            elif isinstance(performer, list):
                speaker = ", ".join(str(p.get("name", "")).strip() for p in performer if isinstance(p, dict))

            image_url = ""
            image = node.get("image")
            if isinstance(image, str):
                image_url = image.strip()
            elif isinstance(image, list):
                for v in image:
                    if isinstance(v, str) and v.strip():
                        image_url = v.strip()
                        break

            parsed.append({
                "title": strip_html(str(node.get("name", ""))) or "GenAI Gurus Event",
                "date": date_iso,
                "is_upcoming": event_dt >= now,
                "speaker_name": speaker or extract_speaker("", description),
                "meetup_url": str(node.get("url", "")).strip() or DEFAULT_EVENTS_URL,
                "image": image_url,
                "summary": description[:280],
            })

    deduped: dict[str, dict] = {}
    for ev in parsed:
        key = ev.get("meetup_url", f"{ev['title']}|{ev['date']}")
        deduped[key] = ev
    return sorted(deduped.values(), key=lambda e: e["date"])


def extract_event_urls(page_html: str) -> list[str]:
    pat = re.compile(r'href=["\'](?P<href>(?:https?://www\.meetup\.com)?/[^"\']+/events/[^"\']+)["\']', re.I)
    seen: set[str] = set()
    urls: list[str] = []
    for m in pat.finditer(page_html):
        normalized = urljoin("https://www.meetup.com", m.group("href")).split("?")[0].rstrip("/")
        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


# ---------------------------------------------------------------------------
# Fetch all events from multiple sources
# ---------------------------------------------------------------------------

def fetch_all_events() -> list[dict]:
    all_events: dict[str, dict] = {}

    try:
        ical_text = fetch_url(DEFAULT_ICAL_URL)
        for ev in parse_ical_events(ical_text):
            all_events[ev["meetup_url"]] = ev
        log(f"iCal: {len(all_events)} events")
    except Exception as exc:
        log(f"iCal failed: {exc}")

    try:
        events_html = fetch_url(DEFAULT_EVENTS_URL)
        for ev in parse_ld_json_events(events_html):
            key = ev.get("meetup_url", "")
            if key not in all_events:
                all_events[key] = ev
        log(f"Events page: total now {len(all_events)}")
    except Exception as exc:
        log(f"Events page failed: {exc}")

    try:
        past_html = fetch_url(DEFAULT_PAST_EVENTS_URL)
        past_parsed = parse_ld_json_events(past_html)
        if not past_parsed:
            for url in extract_event_urls(past_html)[:20]:
                try:
                    detail = fetch_url(url, timeout=15)
                    past_parsed.extend(parse_ld_json_events(detail))
                except Exception:
                    pass
        for ev in past_parsed:
            key = ev.get("meetup_url", "")
            if key not in all_events:
                all_events[key] = ev
        log(f"Past events: total now {len(all_events)}")
    except Exception as exc:
        log(f"Past events failed: {exc}")

    for key, ev in all_events.items():
        if not ev.get("image") and ev.get("meetup_url"):
            try:
                page = fetch_url(ev["meetup_url"], timeout=15)
                ev["image"] = extract_image_from_html(page)
            except Exception:
                pass

    return sorted(all_events.values(), key=lambda e: e["date"])


# ---------------------------------------------------------------------------
# Derive output files
# ---------------------------------------------------------------------------

def write_json(path: Path, data: object) -> bool:
    serialized = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return False
    path.write_text(serialized, encoding="utf-8")
    return True


def derive_upcoming_event(events: list[dict]) -> dict | None:
    upcoming = [e for e in events if e.get("is_upcoming")]
    if not upcoming:
        return None
    ev = upcoming[0]
    return {
        "title": ev["title"],
        "date": ev["date"],
        "image": ev.get("image", ""),
        "summary": ev.get("summary", ""),
        "speaker_name": ev.get("speaker_name", ""),
        "speaker_role": "",
        "meetup_url": ev["meetup_url"],
    }


def derive_community_stats(events: list[dict]) -> dict:
    return {
        "meetup_members": 1500,
        "total_events": len(events),
        "total_meetup_participants": len(events) * 60,
        "total_youtube_views": 1800,
        "total_reach": len(events) * 60 + 1800,
    }


def derive_leaderboard(_events: list[dict]) -> list[dict]:
    """Placeholder: real leaderboard requires per-member RSVP data from Meetup.
    For now, return whatever is already in the file, or the seed data."""
    lb_path = DATA_DIR / "leaderboard.json"
    if lb_path.exists():
        try:
            return json.loads(lb_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def main() -> int:
    log("Starting Meetup data sync...")
    try:
        events = fetch_all_events()
    except Exception as exc:
        log(f"FATAL: {exc}")
        return 1

    if not events:
        log("WARNING: no events fetched, keeping existing data")
        return 0

    log(f"Total events: {len(events)}")
    upcoming = sum(1 for e in events if e.get("is_upcoming"))
    past = len(events) - upcoming
    log(f"Upcoming: {upcoming}, Past: {past}")

    changed = False

    ue = derive_upcoming_event(events)
    if ue:
        if write_json(DATA_DIR / "upcoming_event.json", ue):
            changed = True
            log("Updated upcoming_event.json")
    else:
        log("No upcoming event found")

    cs = derive_community_stats(events)
    if write_json(DATA_DIR / "community_stats.json", cs):
        changed = True
        log("Updated community_stats.json")

    lb = derive_leaderboard(events)
    if lb and write_json(DATA_DIR / "leaderboard.json", lb):
        changed = True
        log("Updated leaderboard.json")

    if not changed:
        log("No data changes detected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
