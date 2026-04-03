# GenAI Gurus Website

This repository hosts the Jekyll-powered website for **GenAI Gurus** at <https://genai-gurus.com>.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

## Event data and maintenance

The homepage reads event data from `_data/events.json`.
Discovered Meetup event URLs are persisted in `_data/event_links.json`.

- **Automated sync:** `.github/workflows/sync-meetup-events.yml` runs every 12 hours, on manual dispatch, on pull requests targeting `main`/`master`, and on all pushes to `main`/`master`.
- **Sync script:** `scripts/sync_meetup_events.py` fetches Meetup data and writes deterministic JSON output.
  - Primary source: Meetup iCal feed.
  - Fallback source: JSON-LD event data from the Meetup events page.
- **Commit behavior:** The workflow only commits when `_data/events.json` actually changes.
  - It also commits when `_data/event_links.json` changes (new discovered event URLs).
- **Failure behavior:** If Meetup fetch fails, the script logs a warning and keeps the last successful local data file.
  - In GitHub Actions, strict mode is enabled so fetch failures fail the workflow run (instead of silently succeeding).
  - If fresh fetches contain no past events (e.g., source requires login), cached past events already in `_data/events.json` are preserved.

### Optional source overrides

- `MEETUP_ICAL_URL` (optional): override iCal endpoint used by the sync script.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/ical/`.
- `MEETUP_EVENTS_URL` (optional): override Meetup events page URL used as the JSON-LD fallback source.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/`.
- `MEETUP_PAST_EVENTS_URL` (optional): override Meetup past-events page URL used to supplement iCal with recent historical events.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/past/`.
- `MEETUP_EVENTS_API_URL` (optional): override Meetup REST events endpoint used as an additional fallback for past events.
  - If not set, the script defaults to `https://api.meetup.com/genai-gurus/events`.
- `MEETUP_SYNC_STRICT` (optional): if truthy (`1`, `true`, `yes`, `on`), the script exits non-zero when fetch fails.
  - Useful in CI to surface data-source outages immediately.
- `MEETUP_SYNC_DEBUG` (optional): if truthy, emits detailed fetch/parse diagnostics to stdout (source URLs, payload sizes, parsed counts, and sample event URLs).

By default, the GitHub Actions workflow uses the script defaults for source URLs (no secrets required).

### Manual sync

```bash
python scripts/sync_meetup_events.py
```

### GitHub Actions notes

- Scheduled (`cron`) workflows only run from the repository default branch.
- If the schedule appears not to run, use **Actions → Sync Meetup events → Run workflow** once to validate permissions and fetch behavior.

## Notes

- Generated build output (`_site/`) should not be committed.
- Keep `CNAME` intact for GitHub Pages custom domain mapping.
