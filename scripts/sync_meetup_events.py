#!/usr/bin/env python3
"""Sync Meetup events into _data/events.json for Jekyll rendering."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
from urllib.parse import urlencode, urljoin
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = REPO_ROOT / "_data" / "events.json"
EVENT_LINKS_FILE = REPO_ROOT / "_data" / "event_links.json"
DEFAULT_ICAL_URL = "https://www.meetup.com/genai-gurus/events/ical/"
DEFAULT_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/"
DEFAULT_PAST_EVENTS_URL = "https://www.meetup.com/genai-gurus/events/past/"
DEFAULT_EVENTS_API_URL = "https://api.meetup.com/genai-gurus/events"


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


def extract_image_from_event_html(event_html: str) -> str:
    og_image_pattern = re.compile(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        flags=re.IGNORECASE,
    )
    og_match = og_image_pattern.search(event_html)
    if og_match:
        return html.unescape(og_match.group(1)).strip()

    script_pattern = re.compile(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in script_pattern.findall(event_html):
        candidate = match.strip()
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        nodes = payload if isinstance(payload, list) else [payload]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            image = node.get("image")
            if isinstance(image, str) and image.strip():
                return image.strip()
            if isinstance(image, list):
                for value in image:
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    return ""


def fill_event_images(events: list[dict[str, str]], headers: dict[str, str]) -> list[dict[str, str]]:
    updated_events: list[dict[str, str]] = []
    image_cache: dict[str, str] = {}
    for event in events:
        normalized_event = dict(event)
        meetup_url = str(normalized_event.get("meetup_url", "")).strip()
        existing_image = str(normalized_event.get("image", "")).strip()
        if existing_image or not meetup_url:
            updated_events.append(normalized_event)
            continue

        if meetup_url in image_cache:
            normalized_event["image"] = image_cache[meetup_url]
            updated_events.append(normalized_event)
            continue

        try:
            event_html = fetch_url(meetup_url, headers=headers, timeout=20)
            image_url = extract_image_from_event_html(event_html)
        except (urllib.error.URLError, RuntimeError, ValueError) as exc:
            debug(f"fill_event_images: failed to fetch {meetup_url}: {exc}")
            image_url = ""

        image_cache[meetup_url] = image_url
        normalized_event["image"] = image_url
        updated_events.append(normalized_event)

    return updated_events


def merge_events(*event_lists: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for events in event_lists:
        for event in events:
            key = event.get("meetup_url") or f"{event.get('title')}|{event.get('date')}"
            merged[key] = event
    return sorted(merged.values(), key=lambda e: e["date"])


def normalize_event_url(url: str) -> str:
    return (url or "").strip().split("?", 1)[0].rstrip("/")


def load_event_links() -> list[str]:
    if not EVENT_LINKS_FILE.exists():
        return []
    try:
        payload = json.loads(EVENT_LINKS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(payload, list):
        return []
    return [normalize_event_url(str(item)) for item in payload if normalize_event_url(str(item))]


def write_event_links_if_changed(links: list[str]) -> bool:
    deduped = sorted({normalize_event_url(link) for link in links if normalize_event_url(link)})
    serialized = json.dumps(deduped, ensure_ascii=False, indent=2) + "\n"
    EVENT_LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if EVENT_LINKS_FILE.exists() and EVENT_LINKS_FILE.read_text(encoding="utf-8") == serialized:
        return False
    EVENT_LINKS_FILE.write_text(serialized, encoding="utf-8")
    return True


def discover_links_from_visible_sources(headers: dict[str, str], source_url: str, events_url: str) -> list[str]:
    discovered: set[str] = set()
    try:
        payload = fetch_url(source_url, headers=headers)
        for event in parse_ical_events(payload):
            discovered.add(normalize_event_url(event.get("meetup_url", "")))
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        debug(f"discover_links: iCal source failed: {exc}")

    try:
        payload = fetch_url(events_url, headers=headers)
        for event in parse_ld_json_events(payload):
            discovered.add(normalize_event_url(event.get("meetup_url", "")))
        for link in extract_event_urls_from_html(payload):
            discovered.add(normalize_event_url(link))
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        debug(f"discover_links: events page source failed: {exc}")

    links = sorted([link for link in discovered if link])
    debug(f"discover_links: found {len(links)} links from visible sources")
    return links


def hydrate_events_from_links(
    links: list[str],
    headers: dict[str, str],
    fallback_events_by_url: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    hydrated: list[dict[str, str]] = []
    for link in links:
        normalized = normalize_event_url(link)
        if not normalized:
            continue
        parsed_for_link: list[dict[str, str]] = []
        try:
            payload = fetch_url(normalized, headers=headers, timeout=20)
            parsed_for_link = parse_ld_json_events(payload)
        except (urllib.error.URLError, RuntimeError, ValueError) as exc:
            debug(f"hydrate_events_from_links: failed to fetch {normalized}: {exc}")

        chosen: dict[str, str] | None = None
        for item in parsed_for_link:
            if normalize_event_url(item.get("meetup_url", "")) == normalized:
                chosen = item
                break
        if chosen is None and parsed_for_link:
            chosen = parsed_for_link[0]

        if chosen is None:
            chosen = fallback_events_by_url.get(normalized)

        if chosen is not None:
            hydrated.append(chosen)

    debug(f"hydrate_events_from_links: produced {len(hydrated)} events from {len(links)} links")
    return hydrated


def parse_api_events(events_payload: str) -> list[dict[str, str]]:
    try:
        payload = json.loads(events_payload)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    now = dt.datetime.now(dt.timezone.utc)
    parsed_events: list[dict[str, str]] = []
    for event in payload:
        if not isinstance(event, dict):
            continue
        event_time_ms = event.get("time")
        if not isinstance(event_time_ms, (int, float)):
            continue

        event_dt = dt.datetime.fromtimestamp(event_time_ms / 1000, tz=dt.timezone.utc)
        venue = event.get("venue")
        location_name = ""
        if isinstance(venue, dict):
            location_name = str(venue.get("name", "")).strip()
        if not location_name:
            location_name = "Online" if bool(event.get("is_online")) else "TBD"

        description = strip_html(str(event.get("description", "")))
        parsed_events.append(
            {
                "title": strip_html(str(event.get("name", ""))) or "GenAI Gurus Event",
                "date": event_dt.isoformat().replace("+00:00", "Z"),
                "event_status": "upcoming" if event_dt >= now else "past",
                "speaker_name": extract_speaker("", description),
                "location_label": location_name,
                "meetup_url": str(event.get("link", "")).strip() or DEFAULT_EVENTS_URL,
                "youtube_url": "",
                "image": "",
                "summary": description[:280],
            }
        )

    ordered = sorted(parsed_events, key=lambda e: e["date"])
    debug(f"parse_api_events: parsed {len(ordered)} events")
    return ordered


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
    events_api_url = getenv_or_default("MEETUP_EVENTS_API_URL", DEFAULT_EVENTS_API_URL)
    headers = {"User-Agent": "genai-gurus-event-sync/1.0"}
    debug(f"fetch_events: source_url={source_url}")
    debug(f"fetch_events: events_url={events_url}")
    debug(f"fetch_events: past_events_url={past_events_url}")
    debug(f"fetch_events: events_api_url={events_api_url}")

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
        message = f"iCal source failed: {exc}"
        errors.append(message)
        debug(message)

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
        message = f"past events source failed: {exc}"
        errors.append(message)
        debug(message)

    if not past_events:
        try:
            query = urlencode(
                {
                    "status": "past",
                    "page": 20,
                    "desc": "true",
                    "only": "name,time,link,description,is_online,venue",
                }
            )
            api_url = f"{events_api_url}?{query}"
            debug(f"Trying Meetup API fallback URL: {api_url}")
            api_payload = fetch_url(api_url, headers=headers)
            api_events = [event for event in parse_api_events(api_payload) if event.get("event_status") == "past"]
            if api_events:
                past_events = api_events
                log(f"Fetched {len(past_events)} past events from Meetup API")
                debug(f"API past sample URLs: {[e.get('meetup_url') for e in past_events[:5]]}")
            else:
                message = "Meetup API returned no parseable past events"
                errors.append(message)
                debug(message)
        except (urllib.error.URLError, RuntimeError, ValueError) as exc:
            message = f"events API source failed: {exc}"
            errors.append(message)
            debug(message)

    merged_events = merge_events(ical_events, past_events)
    merged_events = fill_event_images(merged_events, headers=headers)
    debug(
        "Merged counts: "
        f"ical={len(ical_events)}, past={len(past_events)}, merged={len(merged_events)}, "
        f"upcoming={sum(1 for e in merged_events if e.get('event_status') == 'upcoming')}, "
        f"past={sum(1 for e in merged_events if e.get('event_status') == 'past')}"
    )
    if not past_events:
        debug("No past events recovered from any source")
        for source_error in errors:
            if "past events source failed" in source_error or "events API source failed" in source_error:
                debug(f"Past-source diagnostic: {source_error}")
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


def load_existing_events() -> list[dict[str, str]]:
    if not OUTPUT_FILE.exists():
        return []
    try:
        payload = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(payload, list):
        return []
    return [event for event in payload if isinstance(event, dict)]


def preserve_existing_past_events(fetched_events: list[dict[str, str]]) -> list[dict[str, str]]:
    fetched_past_count = sum(1 for event in fetched_events if event.get("event_status") == "past")
    if fetched_past_count > 0:
        return fetched_events

    existing_events = load_existing_events()
    existing_past = [event for event in existing_events if event.get("event_status") == "past"]
    if not existing_past:
        return fetched_events

    merged = merge_events(fetched_events, existing_past)
    log(
        "No past events fetched from Meetup sources; "
        f"preserved {len(existing_past)} cached past events from _data/events.json"
    )
    return merged


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

    existing_events = load_existing_events()
    headers = {"User-Agent": "genai-gurus-event-sync/1.0"}
    discovered_links = discover_links_from_visible_sources(headers, DEFAULT_ICAL_URL, DEFAULT_EVENTS_URL)
    existing_links = load_event_links()
    cached_links = [normalize_event_url(event.get("meetup_url", "")) for event in existing_events]
    fetched_links = [normalize_event_url(event.get("meetup_url", "")) for event in events]
    all_links = sorted({link for link in [*existing_links, *cached_links, *fetched_links, *discovered_links] if link})
    links_changed = write_event_links_if_changed(all_links)

    fallback_map = {
        normalize_event_url(event.get("meetup_url", "")): event
        for event in merge_events(existing_events, events)
        if normalize_event_url(event.get("meetup_url", ""))
    }
    hydrated_events = hydrate_events_from_links(all_links, headers=headers, fallback_events_by_url=fallback_map)
    events = merge_events(events, hydrated_events)
    events = preserve_existing_past_events(events)
    changed = write_if_changed(events)
    upcoming_count = sum(1 for event in events if event.get("event_status") == "upcoming")
    past_count = sum(1 for event in events if event.get("event_status") == "past")
    log(f"Synced {len(events)} events ({upcoming_count} upcoming, {past_count} past)")
    if changed or links_changed:
        log("Updated event data files" if changed and links_changed else ("Updated _data/events.json" if changed else "Updated _data/event_links.json"))
    else:
        log("No event data changes detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
