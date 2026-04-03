# GenAI Gurus Website

This repository hosts the Jekyll-powered website for **GenAI Gurus** at <https://genai-gurus.com>.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

## Event data and maintenance

The homepage reads event data from `_data/events.json`.

- **Automated sync:** `.github/workflows/sync-meetup-events.yml` runs every 12 hours and on manual dispatch.
  - It also runs on pushes to `main`/`master` that touch the workflow, sync script, or `_data/events.json` so first-time setup is easier to verify.
- **Sync script:** `scripts/sync_meetup_events.py` fetches Meetup data and writes deterministic JSON output.
  - Primary source: Meetup iCal feed.
  - Fallback source: JSON-LD event data from the Meetup events page.
- **Commit behavior:** The workflow only commits when `_data/events.json` actually changes.
- **Failure behavior:** If Meetup fetch fails, the script logs a warning and keeps the last successful local data file.

### Optional secret

- `MEETUP_ICAL_URL` (optional): override iCal endpoint used by the sync job.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/ical/`.
- `MEETUP_EVENTS_URL` (optional): override Meetup events page URL used as the JSON-LD fallback source.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/`.

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
