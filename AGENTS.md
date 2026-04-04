# GenAI Gurus Repo Guide

## Purpose

This repository powers <https://genai-gurus.com> as a Jekyll site.
The current product is a community homepage centered on Meetup events, plus a small set of static pages and blog-style posts.

## Fast Start

- Local preview: `bundle install` then `bundle exec jekyll serve`
- Build only: `bundle exec jekyll build`
- Manual Meetup sync: `python3 scripts/sync_meetup_events.py`
- Sync script tests: `python3 -m unittest tests/test_sync_meetup_events.py`

## Repo Map

- `index.html`: custom homepage. This is the main entry point and reads from `site.data.events` and `site.data.settings`.
- `_data/settings.yml`: site-wide copy, branding, links, default images, and community text.
- `_data/events.json`: generated event data rendered on the homepage.
- `_data/event_links.json`: cache of discovered Meetup event URLs used by the sync script.
- `_pages/`: static pages using `layout: page`. Current examples are `about.md` and `courses.md`.
- `_posts/`: article/event recap posts using `layout: post`. These feed `search.json` and post pages, but they are not the homepage source of truth.
- `_layouts/`, `_includes/`, `_sass/`, `js/common.js`: theme/layout/style code.
- `scripts/sync_meetup_events.py`: fetches Meetup data and writes deterministic JSON output for Jekyll.
- `tests/test_sync_meetup_events.py`: parser/image extraction coverage for the sync script.
- `.github/workflows/sync-meetup-events.yml`: scheduled and on-demand event refresh workflow.

## Where To Edit

- Homepage copy, CTA labels, social links: `index.html` and `_data/settings.yml`
- SEO/meta tags and global CSS entrypoint: `_includes/head.html`
- Header or footer navigation: `_includes/header.html` and `_includes/footer.html`
- Shared page shell: `_layouts/default.html`
- Static page layout: `_layouts/page.html`
- Post layout/chrome: `_layouts/post.html`
- Styling: matching partials under `_sass/`
- Static pages: `_pages/`
- Blog posts: `_posts/`
- Event ingestion or event schema: `scripts/sync_meetup_events.py` and `tests/test_sync_meetup_events.py`

## Guardrails

- Do not hand-edit `_data/events.json` or `_data/event_links.json` for routine content changes. Prefer fixing the sync script or rerunning it.
- Preserve `CNAME`.
- Do not commit `_site/`.
- If you change the event object shape, update `index.html` and the sync tests together.
- Event dates are stored as UTC ISO timestamps with a trailing `Z`; homepage logic depends on that format.
- `search.json` indexes `site.posts` only. It does not index Meetup events or static pages.

## Theme Notes

This repo started from the Zolan Jekyll theme and still contains some older theme components.
Not every include or script is part of the current user experience.

- The homepage is custom and event-driven, not a default blog index.
- Search assets are still loaded, but the current header does not expose a search button/input.
- Instagram, subscribe, and some other theme modules are present in the codebase but are not core to the current site flow.
- Before editing a theme partial, confirm it is actually referenced by an active layout/include path.

## Known Quirks

- `_pages/about.md` currently publishes at `/aboutus/`.
- `_layouts/post.html` links the author name to `/about/`, which does not match the current page permalink.
- If you choose to fix that mismatch, treat it as a deliberate site change rather than incidental cleanup.

## Suggested Workflow

1. Confirm whether the task is about homepage/event data, static pages, posts, styling, or the sync pipeline.
2. Edit the smallest set of files that owns that behavior.
3. Run `python3 -m unittest tests/test_sync_meetup_events.py` for sync logic changes.
4. Run `bundle exec jekyll build` or `bundle exec jekyll serve` for template/style/content changes when available.
5. After changes are verified and committed, push the branch to the remote repository so GitHub Pages or related GitHub Actions deployment triggers can run.

## Deployment Reminder

- Do not leave finished feature work only in a local commit when the intent is to ship it.
- For changes meant to go live, push to the remote repository after verification so deployment can happen.
