# GenAI Gurus — genai-gurus.com

Community landing page for [GenAI Gurus](https://genai-gurus.com), a global community for builders, researchers, and leaders exploring applied Generative AI.

Built with **Astro** + **Tailwind CSS v4**, deployed to **GitHub Pages**.

## Quick start

```bash
npm install
npm run dev        # local dev server at localhost:4321
```

## Scripts

| Command            | What it does                                              |
| ------------------ | --------------------------------------------------------- |
| `npm run dev`      | Start the Astro dev server with hot reload                |
| `npm run build`    | Production build into `dist/`                             |
| `npm run preview`  | Preview the production build locally                      |
| `npm run lint`     | Run ESLint across the project                             |
| `npm run format`   | Format all source files with Prettier                     |

## Project structure

```
public/                 Static assets copied as-is into the build
  CNAME                 Custom domain for GitHub Pages
  images/logo.svg       GenAI Gurus logo

src/
  components/           Astro components (one per landing page section)
    Header.astro
    Hero.astro
    UpcomingEvent.astro
    HighlightedTalks.astro
    CoreTeam.astro
    Milestones.astro
    About.astro
    SpeakAndPartner.astro
    Footer.astro
  content/
    about.md            About section copy
  data/                 JSON data consumed at build time
    site.json           Site-wide metadata and social links
    upcoming_event.json Next Meetup event (auto-updated monthly)
    featured_talks.json 6 curated past talks (manually edited)
    core_team.json      4 Core Team members (manually edited)
    milestones.json     Community milestones (manually edited)
    community_stats.json Aggregate stats (auto-updated monthly)
    leaderboard.json    Top 100 by participation score (auto-updated monthly)
  layouts/
    Base.astro          HTML shell, meta tags, font loading
  pages/
    index.astro         Landing page (composes all section components)
    leaderboard.astro   /leaderboard — ranked table of top 100
  styles/
    global.css          Tailwind v4 import and brand theme tokens

scripts/
  sync_meetup_data.py   Python script that crawls Meetup and writes data JSON files

.github/workflows/
  deploy.yml            Build and deploy to GitHub Pages on push to main
  sync-data.yml         Run sync script monthly and commit updated data
```

## Editing content

### Manual content (edit directly in git)

- **Featured talks** — edit `src/data/featured_talks.json` (exactly 6 curated entries).
- **Core Team** — edit `src/data/core_team.json` (4 members; order is computed by score at build time).
- **Milestones** — edit `src/data/milestones.json`.
- **About copy** — edit `src/content/about.md`.
- **Social links and form URLs** — edit `src/data/site.json`.

### Auto-generated content

These files are updated monthly by the `sync-data.yml` GitHub Action:

- `src/data/upcoming_event.json`
- `src/data/community_stats.json`
- `src/data/leaderboard.json`

You can also run the sync manually:

```bash
python scripts/sync_meetup_data.py
```

## Deployment

Push to `main` triggers the `deploy.yml` workflow, which builds the Astro site and deploys it to GitHub Pages. The custom domain `genai-gurus.com` is set via `public/CNAME`.

## Recommended editor extensions (Cursor / VS Code)

1. [Astro](https://marketplace.visualstudio.com/items?itemName=astro-build.astro-vscode)
2. [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)
3. [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
4. [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

Enable **Format on Save** and set Prettier as the default formatter.
