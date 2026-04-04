# GenAI Gurus Repo Guide

## Purpose

This repository powers <https://genai-gurus.com> as an Astro static site deployed to GitHub Pages.
The product is a community landing page with a leaderboard subpage.

## Fast Start

- Install: `npm install`
- Dev server: `npm run dev`
- Production build: `npm run build`
- Meetup data sync: `python scripts/sync_meetup_data.py`

## Repo Map

### Pages

- `src/pages/index.astro` — landing page, composes section components in spec order.
- `src/pages/leaderboard.astro` — `/leaderboard`, reads `leaderboard.json`.

### Layouts and Components

- `src/layouts/Base.astro` — HTML shell, `<head>`, font loading, wraps Header + Footer.
- `src/components/Header.astro` — fixed nav bar with logo and section anchors.
- `src/components/Hero.astro` — headline, value prop, CTAs, stats strip.
- `src/components/UpcomingEvent.astro` — next Meetup event card.
- `src/components/HighlightedTalks.astro` — 2×3 grid of curated past talks.
- `src/components/CoreTeam.astro` — 4 team member cards sorted by participation score.
- `src/components/Milestones.astro` — timeline of community milestones.
- `src/components/About.astro` — community identity and pillars.
- `src/components/SpeakAndPartner.astro` — CTAs linking to Google Forms.
- `src/components/Footer.astro` — logo, social links, engagement links, copyright.

### Data

- `src/data/site.json` — site-wide config: title, social URLs, form URLs.
- `src/data/upcoming_event.json` — **generated** — next Meetup event.
- `src/data/featured_talks.json` — **manual** — 6 curated highlighted talks.
- `src/data/core_team.json` — **manual** — 4 Core Team members with score inputs.
- `src/data/milestones.json` — **manual** — 5 community milestones.
- `src/data/community_stats.json` — **generated** — aggregate community numbers.
- `src/data/leaderboard.json` — **generated** — top 100 ranked participants.
- `src/content/about.md` — **manual** — about section long-form copy.

### Scripts and CI

- `scripts/sync_meetup_data.py` — crawls Meetup (iCal + HTML + LD+JSON), writes generated data files.
- `.github/workflows/deploy.yml` — builds Astro and deploys to GitHub Pages on push to `main`.
- `.github/workflows/sync-data.yml` — runs sync script monthly, commits updated JSON.

### Styling

- `src/styles/global.css` — Tailwind v4 import, brand color tokens (`brand-*`, `accent-*`), font config.
- Brand palette: dark navy backgrounds (`brand-950` to `brand-50`), amber/gold accents (`accent-500: #F6B141`).

### Config

- `astro.config.mjs` — Astro config, Tailwind via `@tailwindcss/vite` plugin.
- `tsconfig.json` — strict mode, `@/*` path alias to `src/*`.
- `.prettierrc` — Prettier with `prettier-plugin-astro` and `prettier-plugin-tailwindcss`.
- `eslint.config.js` — flat config with `eslint-plugin-astro`.
- `.cursor/rules/project.mdc` — AI guardrails (no startup aesthetics, preserve IA, static-first).

## Where To Edit

- **Landing page section order** — `src/pages/index.astro` (component composition order).
- **Section content and layout** — matching component in `src/components/`.
- **Social links, form URLs** — `src/data/site.json`.
- **Curated talks** — `src/data/featured_talks.json`.
- **Team members** — `src/data/core_team.json`.
- **Theme colors, fonts** — `src/styles/global.css` `@theme` block.
- **Meta tags, fonts** — `src/layouts/Base.astro` `<head>`.
- **Meetup crawl logic** — `scripts/sync_meetup_data.py`.

## Guardrails

- Do not hand-edit `upcoming_event.json`, `community_stats.json`, or `leaderboard.json` for routine updates — run the sync script or wait for the monthly Action.
- Preserve `public/CNAME`.
- Do not commit `node_modules/`, `dist/`, or `.astro/`.
- The spec of record is `site-functional-spec.md` — consult it for information architecture and design rules.
- Highlighted talks are always manually curated (exactly 6). Never auto-select them.
- Core Team card order is computed by score (`hosted_events × 5 + joined_events × 1`) — do not manually reorder.

## Score Formula

```
score = hosted_events × 5 + joined_events × 1
```

- `hosted_events` — events hosted as shown on Meetup.
- `joined_events` — RSVP joined on Meetup.

Applied to Core Team cards (sorted descending) and the leaderboard.
