# Cursor setup for GenAI Gurus

Please prepare this repo for development in Cursor with a minimal Astro + Tailwind + GitHub Pages workflow.

## Goals

1. Keep the setup minimal
2. Make `.astro` development smooth
3. Enable formatting, linting, and class sorting
4. Add project rules so AI edits stay aligned with the site spec
5. Do not introduce unnecessary frameworks, CMSs, databases, or server features

## Agent tasks

1. Detect whether this project already uses Astro and Tailwind
2. If missing, install and configure:
   1. `prettier`
   2. `prettier-plugin-astro`
   3. `prettier-plugin-tailwindcss`
   4. `eslint`
3. Create or update formatting config so `.astro`, `.ts`, `.js`, `.json`, `.md`, `.css` are formatted consistently
4. Add npm scripts if missing:
   1. `dev`
   2. `build`
   3. `preview`
   4. `lint`
   5. `format`
5. Create `.cursor/rules` with short project rules covering:
   1. no generic AI startup design
   2. no pricing section
   3. no testimonials
   4. no clichéd AI visuals
   5. preserve the GenAI Gurus information architecture
   6. keep implementation static first and GitHub Pages compatible
6. Add minimal repo docs explaining how to run, build, lint, and format
7. Do not break existing project structure unless clearly necessary

## Manual steps for Carlos

These likely need to be done manually in Cursor:

1. Install editor extensions:
   1. Astro
   2. Tailwind CSS IntelliSense
   3. ESLint
   4. Prettier
2. Enable format on save
3. Set Prettier as default formatter where appropriate
4. Sign in to any tools or services if prompted

## Constraints

1. Keep the result simple and maintainable
2. Prefer editing existing files over introducing many new abstractions
3. Ask for confirmation only if a destructive change is required
4. Output a short summary of what was installed, configured, and what still needs manual action