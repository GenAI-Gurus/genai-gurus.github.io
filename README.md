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
- **Sync script:** `scripts/sync_meetup_events.py` fetches Meetup iCal data and writes deterministic JSON output.
- **Commit behavior:** The workflow only commits when `_data/events.json` actually changes.
- **Failure behavior:** If Meetup fetch fails, the script logs a warning and keeps the last successful local data file.

### Optional secret

- `MEETUP_ICAL_URL` (optional): override iCal endpoint used by the sync job.
  - If not set, the script defaults to `https://www.meetup.com/genai-gurus/events/ical/`.

### Manual sync

```bash
python scripts/sync_meetup_events.py
```

## Notes

- Generated build output (`_site/`) should not be committed.
- Keep `CNAME` intact for GitHub Pages custom domain mapping.
