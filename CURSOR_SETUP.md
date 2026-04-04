# Cursor setup for GenAI Gurus

Status: **Setup complete.** All agent tasks below have been implemented.

## What was set up

| Item | Status |
| ---- | ------ |
| Astro (v6) + Tailwind CSS v4 via `@tailwindcss/vite` | Installed |
| `prettier` + `prettier-plugin-astro` + `prettier-plugin-tailwindcss` | Installed |
| `eslint` + `eslint-plugin-astro` (flat config) | Installed |
| `.prettierrc` formatting config for `.astro`, `.ts`, `.js`, `.json`, `.md`, `.css` | Created |
| `eslint.config.js` (flat config) | Created |
| npm scripts: `dev`, `build`, `preview`, `lint`, `format` | Added |
| `.cursor/rules/project.mdc` with design and architecture guardrails | Created |
| `.gitignore` for `node_modules/`, `dist/`, `.astro/` | Created |
| `README.md` with run/build/lint/format instructions | Created |
| `AGENTS.md` repo guide for AI-assisted development | Created |

## Manual steps for Carlos

These need to be done once in Cursor:

1. Install editor extensions:
   1. [Astro](https://marketplace.visualstudio.com/items?itemName=astro-build.astro-vscode)
   2. [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)
   3. [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
   4. [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
2. Enable **Format on Save** in settings
3. Set **Prettier** as the default formatter for `.astro`, `.ts`, `.js`, `.json`, `.md`, `.css`
4. Run `npm install` to get all dependencies
5. Run `npm run dev` to start the local dev server at `localhost:4321`

## Tech stack summary

- **Framework**: Astro v6 (static output)
- **Styling**: Tailwind CSS v4 via `@tailwindcss/vite` plugin
- **Formatting**: Prettier with Astro and Tailwind plugins
- **Linting**: ESLint with `eslint-plugin-astro` (flat config)
- **Deployment**: GitHub Pages via `.github/workflows/deploy.yml`
- **Data sync**: Monthly via `.github/workflows/sync-data.yml` running `scripts/sync_meetup_data.py`
