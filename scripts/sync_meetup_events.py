#!/usr/bin/env python3
"""Sync Meetup events into _data/events.json for Jekyll rendering."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
from urllib.parse import urljoin
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = REPO_ROOT / "_data" / "events.json"
DEFAULT_ICAL_URL = "https://www.meetup.com/genai-gurus/events/ical/"
DEFAULT_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/"
DEFAULT_PAST_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/past/"


def log(msg: str) -> None:
    print(f"[sync-meetup-events] {msg}")


def debug(msg: str) -> None:
    if os.environ.get("MEETUP_SYNC_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
        print(f"[sync-meetup-events][debug] {msg}")


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
        parsed = dt.datetime.strptime(value, "%Y%m%dT%H%M%S")
        return parsed.replace(tzinfo=dt.timezone.utc)

    parsed = dt.datetime.strptime(value, "%Y%m%d")
    return parsed.replace(tzinfo=dt.timezone.utc)


def strip_html(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value)
    normalized = re.sub(r"\s+", " ", no_tags)
    return html.unescape(normalized).strip()


def unescape_ical_text(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def extract_speaker(summary: str, description: str) -> str:
    text = f"{summary}\n{description}"
    patterns = [r"Speaker[s]?:\s*([^\n|,;]+)", r"Presented by\s*([^\n|,;]+)"]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def parse_ical_events(ical_text: str) -> list[dict[str, str]]:
    lines = unfold_ical_lines(ical_text)
    events: list[dict[str, str]] = []
    event: dict[str, str] | None = None

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
        key = key_part.split(";", 1)[0]
        event[key] = value.strip()

    now = dt.datetime.now(dt.timezone.utc)
    parsed_events: list[dict[str, str]] = []

    for item in events:
        event_dt = parse_dt(item.get("DTSTART", ""))
        if event_dt is None:
            continue

        summary = strip_html(unescape_ical_text(item.get("SUMMARY", ""))).strip()
        description = strip_html(unescape_ical_text(item.get("DESCRIPTION", ""))).strip()
        location = strip_html(unescape_ical_text(item.get("LOCATION", ""))).strip()
        meetup_url = item.get("URL", "").strip() or DEFAULT_ICAL_URL
        speaker = extract_speaker(summary, description)

        parsed_events.append(
            {
                "title": summary or "GenAI Gurus Event",
                "date": event_dt.isoformat().replace("+00:00", "Z"),
                "event_status": "upcoming" if event_dt >= now else "past",
                "speaker_name": speaker,
                "location_label": location or "Online",
                "meetup_url": meetup_url,
                "youtube_url": "",
                "image": "",
                "summary": description[:280],
            }
        )

    parsed_events.sort(key=lambda e: e["date"])
    debug(f"parse_ical_events: parsed {len(parsed_events)} events")
    return parsed_events


def to_utc_iso(value: str) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_ld_json_events(events_html: str) -> list[dict[str, str]]:
    script_pattern = re.compile(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    now = dt.datetime.now(dt.timezone.utc)
    parsed_events: list[dict[str, str]] = []

    for match in script_pattern.findall(events_html):
        candidate = match.strip()
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        nodes = payload if isinstance(payload, list) else [payload]
        expanded_nodes: list[dict[str, object]] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if isinstance(node.get("@graph"), list):
                expanded_nodes.extend([g for g in node["@graph"] if isinstance(g, dict)])
            expanded_nodes.append(node)

        for node in expanded_nodes:
            node_type = node.get("@type")
            if isinstance(node_type, list):
                is_event = "Event" in node_type
            else:
                is_event = node_type == "Event"
            if not is_event:
                continue

            date_iso = to_utc_iso(str(node.get("startDate", "")))
            if not date_iso:
                continue

            event_dt = dt.datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
            location = node.get("location", {})
            if isinstance(location, dict):
                location_name = str(location.get("name", "")).strip()
            else:
                location_name = ""
            description = strip_html(str(node.get("description", "")))
            speaker = ""
            performer = node.get("performer")
            if isinstance(performer, dict):
                speaker = str(performer.get("name", "")).strip()
            elif isinstance(performer, list):
                names = [str(p.get("name", "")).strip() for p in performer if isinstance(p, dict)]
                speaker = ", ".join([n for n in names if n])

            parsed_events.append(
                {
                    "title": strip_html(str(node.get("name", ""))) or "GenAI Gurus Event",
                    "date": date_iso,
                    "event_status": "upcoming" if event_dt >= now else "past",
                    "speaker_name": speaker or extract_speaker("", description),
                    "location_label": location_name or "Online",
                    "meetup_url": str(node.get("url", "")).strip() or DEFAULT_EVENTS_URL,
                    "youtube_url": "",
                    "image": "",
                    "summary": description[:280],
                }
            )

    deduped: dict[str, dict[str, str]] = {}
    for event in parsed_events:
        key = event.get("meetup_url") or f"{event.get('title')}|{event.get('date')}"
        deduped[key] = event
    ordered = sorted(deduped.values(), key=lambda e: e["date"])
    debug(f"parse_ld_json_events: parsed {len(ordered)} events")
    return ordered


def merge_events(*event_lists: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for events in event_lists:
        for event in events:
            key = event.get("meetup_url") or f"{event.get('title')}|{event.get('date')}"
            merged[key] = event
    return sorted(merged.values(), key=lambda e: e["date"])


def extract_event_urls_from_html(page_html: str) -> list[str]:
    href_pattern = re.compile(
        r'href=["\'](?P<href>(?:https?://www\.meetup\.com)?/[^"\']+/events/[^"\']+)["\']',
        flags=re.IGNORECASE,
    )
    text_pattern = re.compile(
        r'(?P<href>(?:https?://www\.meetup\.com)?/[^"\'\s<>]+/events/\d+/?(?:\?[^"\'\s<>]*)?)',
        flags=re.IGNORECASE,
    )
    seen: set[str] = set()
    urls: list[str] = []

    href_matches = 0
    for match in href_pattern.finditer(page_html):
        candidate = match.group("href")
        normalized = urljoin("https://www.meetup.com", candidate).split("?", 1)[0].rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)
        urls.append(normalized)
        href_matches += 1

    json_like_html = page_html.replace("\\/", "/")
    text_matches = 0
    for match in text_pattern.finditer(json_like_html):
        candidate = match.group("href")
        normalized = urljoin("https://www.meetup.com", candidate).split("?", 1)[0].rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)
        urls.append(normalized)
        text_matches += 1

    debug(
        "extract_event_urls_from_html: "
        f"{len(urls)} candidate event URLs "
        f"(href matches added={href_matches}, text/json matches added={text_matches})"
    )
    return urls


def fetch_url(url: str, headers: dict[str, str], timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Meetup fetch failed for {url} with status {response.status}")
        payload = response.read().decode("utf-8", errors="replace")
        debug(f"fetch_url: {url} -> status {response.status}, bytes={len(payload)}")
        return payload


def fetch_events() -> list[dict[str, str]]:
    source_url = getenv_or_default("MEETUP_ICAL_URL", DEFAULT_ICAL_URL)
    events_url = getenv_or_default("MEETUP_EVENTS_URL", DEFAULT_EVENTS_URL)
    past_events_url = getenv_or_default("MEETUP_PAST_EVENTS_URL", DEFAULT_PAST_EVENTS_URL)
    headers = {"User-Agent": "genai-gurus-event-sync/1.0"}
    debug(f"fetch_events: source_url={source_url}")
    debug(f"fetch_events: events_url={events_url}")
    debug(f"fetch_events: past_events_url={past_events_url}")

    errors: list[str] = []

    ical_events: list[dict[str, str]] = []
    past_events: list[dict[str, str]] = []

    try:
        payload = fetch_url(source_url, headers=headers)
        ical_events = parse_ical_events(payload)
        if ical_events:
            log(f"Fetched {len(ical_events)} events from iCal")
            debug(f"iCal sample URLs: {[e.get('meetup_url') for e in ical_events[:3]]}")
        else:
            errors.append("Meetup iCal response contained no events")
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        errors.append(f"iCal source failed: {exc}")

    try:
        payload = fetch_url(past_events_url, headers=headers)
        past_events = [event for event in parse_ld_json_events(payload) if event.get("event_status") == "past"]
        if not past_events:
            for event_url in extract_event_urls_from_html(payload)[:12]:
                event_html = fetch_url(event_url, headers=headers, timeout=20)
                detailed = parse_ld_json_events(event_html)
                past_events.extend([event for event in detailed if event.get("event_status") == "past"])
            debug(f"past-event detail crawl produced {len(past_events)} past events before merge")
        if past_events:
            log(f"Fetched {len(past_events)} past events from events/past page")
            debug(f"Past sample URLs: {[e.get('meetup_url') for e in past_events[:5]]}")
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        errors.append(f"past events source failed: {exc}")

    merged_events = merge_events(ical_events, past_events)
    debug(
        "Merged counts: "
        f"ical={len(ical_events)}, past={len(past_events)}, merged={len(merged_events)}, "
        f"upcoming={sum(1 for e in merged_events if e.get('event_status') == 'upcoming')}, "
        f"past={sum(1 for e in merged_events if e.get('event_status') == 'past')}"
    )
    if merged_events:
        return merged_events

    try:
        payload = fetch_url(events_url, headers=headers)
        events = parse_ld_json_events(payload)
        if events:
            return events
        errors.append("Meetup events page contained no parseable JSON-LD events")
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        errors.append(f"events page source failed: {exc}")

    raise RuntimeError("; ".join(errors))


def write_if_changed(events: list[dict[str, str]]) -> bool:
    serialized = json.dumps(events, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists() and OUTPUT_FILE.read_text(encoding="utf-8") == serialized:
        return False
    OUTPUT_FILE.write_text(serialized, encoding="utf-8")
    return True


def is_truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def getenv_or_default(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    return value or default


def main() -> int:
    debug("Debug logging enabled via MEETUP_SYNC_DEBUG")
    try:
        events = fetch_events()
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        log(f"WARNING: unable to fetch Meetup events ({exc}). Keeping existing local data.")
        if not OUTPUT_FILE.exists():
            OUTPUT_FILE.write_text("[]\n", encoding="utf-8")
            log("Created empty fallback _data/events.json")
        if is_truthy_env("MEETUP_SYNC_STRICT", default=False):
            log("Strict mode enabled; failing job so fetch issues are visible in CI.")
            return 1
        return 0

    changed = write_if_changed(events)
    upcoming_count = sum(1 for event in events if event.get("event_status") == "upcoming")
    past_count = sum(1 for event in events if event.get("event_status") == "past")
    log(f"Synced {len(events)} events ({upcoming_count} upcoming, {past_count} past)")
    log("Updated _data/events.json" if changed else "No event data changes detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
