## Updated minimal spec for the GenAI Gurus landing page

### 1. Product goal

Create an original, simple, professional English landing page for GenAI Gurus that maximizes prestige and makes the community feel active, serious, and growing.

The page should optimize for 3 outcomes:

1. Drive visitors to the next Meetup event
2. Build prestige through selected flagship talks and visible community credibility
3. Strengthen the GenAI Gurus ecosystem through Meetup, LinkedIn, and YouTube, while making the Core Team highly visible

Internal success metrics:

1. Overall prestige of the community
2. Growth of Carlos’s personal LinkedIn followers
3. Growth of the LinkedIn page, Meetup group, and YouTube channel

---

### 2. Product scope

1. Main deliverable is a single landing page
2. Minor extra pages are allowed only when clearly needed, such as:

   1. `/leaderboard`
   2. External form pages for speaking and partnership inquiries via Google Forms
3. No newsletter or email capture
4. No testimonials section
5. No blog archive emphasis on the landing page
6. No pricing, product, or startup style sales sections unless they are fully repurposed for community use

---

### 3. Technology and implementation direction

1. The site must remain fully compatible with GitHub Pages
2. The implementation should stay minimal and static first
3. Manual content should live in git
4. Dynamic numbers should be refreshed by GitHub Actions on a monthly cadence
5. Meetup data should be derived from crawling provided public event URLs, not from Meetup Pro or paid infrastructure
6. A starter such as AstroWind can be used as a scaffold, but only as a base to customize heavily
7. Any starter chosen must be stripped of irrelevant starter sections and visually reshaped to feel custom to GenAI Gurus

---

### 4. Visual direction

1. English only
2. Design must feel original, clean, and professional
3. Match the visual identity to the GenAI Gurus logo
4. The visual style must communicate:

   1. technical depth
   2. strategic AI leadership
   3. responsible and safety focused AI
5. The site should feel like a respected AI community and event platform, not like a generic SaaS product site
6. The site should feel editorial and community driven, with a light institutional credibility

---

### 5. Design restrictions and style guardrails

These restrictions are mandatory.

1. Do **not** make the site look like another generic AI startup landing page
2. Do **not** use clichéd AI visuals such as:

   1. robot heads
   2. glowing brains
   3. generic circuits
   4. excessive neon effects
   5. sci fi crypto aesthetics
   6. meaningless abstract AI art
3. Do **not** rely on generic SaaS sections such as:

   1. pricing
   2. fake feature grids
   3. app screenshots
   4. ROI product copy
   5. startup jargon
4. Do **not** use testimonial blocks
5. Do **not** let the page feel like a template demo with many unrelated sections
6. Do **not** make one organizer dominate the identity of the page, even if Carlos is the top contributor
7. Do **not** hide the community behind abstract branding. The page should foreground real talks, real people, real milestones, and real channels
8. Keep visual complexity controlled. The page should feel premium through hierarchy, typography, spacing, and curation, not through visual noise
9. Prefer a restrained, polished, editorial aesthetic over flashy motion heavy design
10. Any template used must be treated as a scaffold only. Remove or redesign whatever feels generic, startup oriented, or visually off brand

---

### 6. Content and hierarchy principles

1. Upcoming event should be the strongest conversion area
2. Highlighted talks should be the strongest prestige area
3. Core Team should be highly visible and motivating
4. Milestones should show growth over time
5. The page should communicate that GenAI Gurus is larger than any one individual
6. The design should make it easy to understand the community in under 10 seconds

---

### 7. Information architecture of the landing page

#### 7.1 Hero section

Purpose: immediate prestige and orientation

Must include:

1. Strong community headline
2. Short supporting value proposition mixing:

   1. technical expertise
   2. strategic AI leadership
   3. responsible and safety focused AI
3. Primary CTA: **Join next event on Meetup**
4. Secondary CTAs:

   1. **Follow on LinkedIn**
   2. **Watch on YouTube**
5. Optional lightweight community stats strip below hero

Restrictions:

1. Do not make this section about one person only
2. Do not make it read like a startup product pitch
3. It should feel like the front door to a respected community

---

#### 7.2 Upcoming event section

Purpose: strongest conversion area on the page

Rules:

1. Show only the next immediate upcoming Meetup event
2. This section must be more prominent than the highlighted past talks section
3. All visible data should be parsed automatically from the Meetup page where possible

Required content:

1. event title
2. date
3. event image
4. short abstract
5. speaker name
6. speaker role and company where available
7. button to register on Meetup

CTA:

1. **Register on Meetup**

---

#### 7.3 Highlighted talks section

Purpose: prestige and proof of speaker quality

Rules:

1. Show exactly 6 highlighted past events
2. Layout should be two rows of three on desktop
3. The 6 events must be manually selectable by editing a list in git
4. These are curated, not automatically chosen
5. These are past events only

For each card show:

1. event title
2. date
3. event image
4. short abstract
5. speaker photo
6. speaker name
7. speaker role and company where available
8. optional company logo when manually provided
9. total reach as the main metric
10. smaller breakdown below total reach:
11. Meetup participants
12. YouTube views
13. button or clickable thumbnail that opens the YouTube recording

Video behavior:

1. Use thumbnail style presentation only
2. Do not embed full YouTube players directly in the page
3. Thumbnail image can come from the Meetup event image or a manually provided visual

Below or near this section add three ecosystem buttons:

1. **Join Meetup group**
2. **Follow LinkedIn page**
3. **Visit YouTube channel**

Design intent:

1. This section should feel curated and premium
2. It should look more like a selected conference archive than a generic content grid

---

#### 7.4 Core Team section

Purpose: visible recognition, prestige, and contributor incentive

Section title:

**Core Team**

Rules:

1. Show exactly 4 cards, one per Core Team member
2. All 4 cards must have equal visual weight
3. Sort cards by participation score descending
4. No manual override
5. Ranking is purely data driven

For each Core Team card show:

1. photo
2. full name
3. one line role description
4. LinkedIn logo button only
5. member since date, defined as first date they joined on Meetup
6. participation score

Scoring formula:

`score = hosted_events × 5 + joined_events × 1`

Definitions:

1. `hosted_events` means events hosted as represented in Meetup
2. `joined_events` means RSVP joined on Meetup

Additional requirement:

1. Add a visible link to **See full top 100 leaderboard**

Design intent:

1. Make the top 4 visible and respected
2. Signal that the community is bigger than these 4 people
3. Encourage future contribution through visible recognition

---

#### 7.5 Leaderboard page

Purpose: reinforce that the community is broader than the Core Team and visibly active

Route:

`/leaderboard`

Rules:

1. Show top 100 participants by score descending
2. Public names only
3. No LinkedIn links or other profile links
4. Show only:

   1. rank
   2. name
   3. score
5. Use the same score formula as the Core Team
6. This page can be visually simple

---

#### 7.6 Community milestones section

Purpose: show growth over time and make the community feel alive

Display 5 milestones in a visual timeline or other compact visual format.

Milestones:

1. **June 2023**
   GenAI Gurus created

2. **May 2024 to October 2024**
   Project incubator organized

3. **Beginning of 2025**
   Passed 1000 Meetup members

4. **April 2026**
   Reached 50 events and total participant reach
   Total participant reach is defined as:
   sum of Meetup participants across all events plus total YouTube views across all recordings

5. **Today**
   Current Meetup member count
   This fifth milestone should make the growth feel current and ongoing

Rules:

1. The fifth milestone should be refreshed automatically through monthly data updates
2. The visual should feel like community progress, not corporate KPI reporting

---

#### 7.7 About section

Purpose: explain identity and differentiate the community

Must communicate:

1. who the community is for
2. what topics it covers
3. how it combines:

   1. technical depth
   2. strategic AI leadership
   3. responsible and safety focused AI
4. a short community origin story

Design intent:

1. This section should support the premium positioning of the community
2. It should feel human, credible, and specific
3. Avoid fluffy AI manifesto language

---

#### 7.8 Speak and partner section

Purpose: attract valuable inbound opportunities

Two visible CTAs:

1. **Apply to speak**
2. **Partner with the community**

Speaking inquiry:

1. Use Google Form
2. Trigger email notification to `talks@genai-gurus.com`
3. Do not rely only on a Google Sheet entry

Partnership inquiry:

1. Use Google Form
2. Trigger email notification to `partners@genai-gurus.com`
3. Do not rely only on a Google Sheet entry

Target partner types:

1. sponsors
2. enterprise collaborators
3. startup collaborators
4. recruiters

Implementation proposal:

1. Keep the landing page simple
2. Open Google Forms in a new tab
3. Use email notification workflow so each submission actively notifies Carlos

---

#### 7.9 Footer

Must include:

1. GenAI Gurus logo
2. Meetup link
3. LinkedIn page link
4. YouTube channel link
5. contact links to speaking and partner forms
6. optional copyright and minimal legal links

---

### 8. Data model and content ownership

#### 8.1 Manual content in git

These items must be manually editable via simple files in the repo:

1. list of 6 highlighted talks
2. optional company logos for highlighted talks
3. Core Team member metadata:

   1. name
   2. role line
   3. LinkedIn URL
   4. photo
4. milestone text content where needed
5. About section copy

Recommended simple files:

1. `data/featured_talks.json`
2. `data/core_team.json`
3. `data/milestones.json`
4. `content/about.md`

#### 8.2 Generated monthly data

These values should be refreshed by GitHub Actions once per month:

1. Meetup member count
2. total number of Meetup events
3. total Meetup participants across all events
4. total YouTube views across selected recordings or all community recordings, depending on implementation choice
5. Core Team scores
6. top 100 leaderboard
7. current upcoming event data

Recommended generated files:

1. `data/community_stats.json`
2. `data/leaderboard.json`
3. `data/upcoming_event.json`

---

### 9. Automation rules

Use GitHub Actions once per month to update generated data.

The automation should:

1. crawl Meetup community data
2. compute participation score using:

   1. hosted events × 5
   2. RSVP joined × 1
3. generate leaderboard data
4. fetch current upcoming event
5. fetch latest community level metrics
6. commit the refreshed generated JSON files back into the repo

Important:

1. Highlighted talks remain manually curated
2. Prestige content is curated by Carlos
3. Growth and participation numbers are automated

---

### 10. Functional rules

1. Upcoming event is automatic and singular
2. Highlighted talks are manual and exactly 6
3. Core Team order is automatic based on score
4. Leaderboard is automatic based on score
5. All clickable personal networking from Core Team goes only through LinkedIn logo buttons
6. No testimonials
7. No newsletter
8. No blog archive emphasis on the landing page
9. Page must be mobile friendly and fast
10. The final page must feel custom made, not template driven

---

### 11. Content tone

1. confident
2. serious
3. community driven
4. technically credible
5. strategically relevant
6. responsible in its AI framing

The voice should make GenAI Gurus feel like a respected meeting point for strong AI practitioners and leaders.

---

### 12. What the AI building this should optimize for

1. Make the community look prestigious without becoming cluttered
2. Make the Core Team visible and motivating
3. Make the highlighted talks feel like proof of quality
4. Keep the page simple enough that Carlos can maintain it easily
5. Use automation only where it reduces manual work and keeps the site feeling alive
6. Transform any starter template into something that feels distinctly GenAI Gurus
7. Avoid generic AI startup aesthetics at all costs

The best implementation will feel like a carefully curated AI community home, not like a repurposed SaaS landing page.