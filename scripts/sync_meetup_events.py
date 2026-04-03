#!/usr/bin/env python3
"""Sync Meetup events into _data/events.json for Jekyll rendering."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = REPO_ROOT / "_data" / "events.json"
DEFAULT_ICAL_URL = "https://www.meetup.com/genai-gurus/events/ical/"


def log(msg: str) -> None:
    print(f"[sync-meetup-events] {msg}")


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

        summary = strip_html(item.get("SUMMARY", "")).strip()
        description = strip_html(item.get("DESCRIPTION", "")).strip()
        location = strip_html(item.get("LOCATION", "")).strip()
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
    return parsed_events


def fetch_events() -> list[dict[str, str]]:
    source_url = os.environ.get("MEETUP_ICAL_URL", DEFAULT_ICAL_URL)
    headers = {"User-Agent": "genai-gurus-event-sync/1.0"}
    req = urllib.request.Request(source_url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"Meetup fetch failed with status {response.status}")
        payload = response.read().decode("utf-8", errors="replace")
    return parse_ical_events(payload)


def write_if_changed(events: list[dict[str, str]]) -> bool:
    serialized = json.dumps(events, ensure_ascii=False, indent=2) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists() and OUTPUT_FILE.read_text(encoding="utf-8") == serialized:
        return False
    OUTPUT_FILE.write_text(serialized, encoding="utf-8")
    return True


def main() -> int:
    try:
        events = fetch_events()
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        log(f"WARNING: unable to fetch Meetup events ({exc}). Keeping existing local data.")
        if not OUTPUT_FILE.exists():
            OUTPUT_FILE.write_text("[]\n", encoding="utf-8")
            log("Created empty fallback _data/events.json")
        return 0

    changed = write_if_changed(events)
    log(f"Synced {len(events)} events")
    log("Updated _data/events.json" if changed else "No event data changes detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
