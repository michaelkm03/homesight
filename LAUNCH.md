# HomeSight Launch Gameplan

## Channel Priority

| Channel | Effort | Impact | When |
|---------|--------|--------|------|
| Reddit | Low–Med | High — immediate traffic | Week 1–2 |
| Show HN | Low | High — thousands of visits if it lands | Week 2–3 |
| Twitter/X | Med | Medium — compounds over time | Ongoing |
| Product Hunt | Med | Low–Med — credibility + directory | Week 3 |
| Programmatic SEO | High | Very High — long-term | Month 2+ |

---

## Reddit

**Best subreddits (priority order):**

1. `r/dataisbeautiful` — post map screenshot as [OC], credit Zillow Research, mention tool in comments
2. `r/MapPorn` — the national ZIP choropleth is exactly what this sub is for
3. `r/FirstTimeHomeBuyer` — answer questions with HomeSight data first, then disclose you built it
4. `r/RealEstate` — same approach
5. `r/realestateinvesting` — appreciation trends + rent data directly relevant
6. `r/REBubble` — data-hungry audience that loves raw charts
7. `r/personalfinance` — massive audience, rent vs. buy threads

**Rules:**
- Lead with a data finding, never "I built a tool"
- Always disclose you're the maker — Reddit punishes hidden affiliation more than disclosed
- Build karma by answering real questions before posting directly

---

## Show HN (Hacker News)

**Title:**
```
Show HN: HomeSight – Home values and rent trends across 26K U.S. ZIP codes
```

- No exclamation marks, no marketing language — describe exactly what it does
- **Timing:** Tuesday–Thursday, 9–11 AM ET
- Line up 5–10 people to upvote within the first 60 minutes
- Post your own comment within 60 seconds of submitting: why you built it, one interesting data finding, open Q&A invite
- Reply to every comment for the first 2 hours

---

## Twitter/X

**Zero-follower strategy — reply farming beats broadcast posting:**
- Find housing market tweets from large accounts
- Reply within 30–60 minutes with a relevant HomeSight screenshot
- Early replies on viral threads get massive exposure before the thread gets crowded

**Launch thread format:**
1. Hook tweet — screenshot + one sentence, no link
2–5. Data findings with screenshots
6. Link + CTA

Never lead with the link — algorithms suppress link-first posts.

---

## Product Hunt

**Tagline:** `Zillow data for every U.S. ZIP code — mapped, trended, ranked`

- Launch Tuesday–Thursday at 12:01 AM Pacific
- Create maker account 30+ days before launch
- Post maker comment immediately on launch day
- Reply to every comment within 15–30 minutes for the first 6 hours

**Alternative:** Indie Hackers converts better than Product Hunt but requires 4–6 weeks of genuine community participation first. Post in the "Milestones" category with specific numbers.

**Free directories to submit to:** BetaList, Uneed, TinyLaunch, Smol Launch

---

## Programmatic SEO (Month 2+)

HomeSight's biggest long-term opportunity. Zillow built 33M monthly visits largely through programmatic location pages — HomeSight can mirror this at ZIP-code level where there is almost zero competition.

**Page structure to build:**
```
/housing-market/{state}/
/housing-market/{state}/{city}/
/housing-market/{zip}/        ← 26,000+ pages
```

Each page must:
- Return full HTML with real data on first response (not JS-rendered)
- Have a unique `<title>` and meta description per location
- Be linked via state → city → ZIP internal hierarchy

**Critical blocker:** HomeSight is currently a single-page app. AI crawlers (Perplexity, ChatGPT, Claude) and some Googlebot passes cannot execute JS and see a blank shell. SSR must be implemented before investing in SEO.

---

## Pre-Launch Checklist

### SEO & Discoverability
- [x] **S1** — Add `sitemap.xml` route to server — deployed to homesight.live 2026-06-12 (commit 92f6129)
- [x] **S2** — Verify homesight.live in Google Search Console — auto-verified via GA4 tag (G-47JL6EME24) on 2026-06-12
- [x] **S3** — Submit sitemap in Search Console: `https://homesight.live/sitemap.xml` — submitted and confirmed 2026-06-12

### Community Accounts
- [x] **C1** — Create Product Hunt maker account — clock started 2026-06-12; earliest launch date: **2026-07-12**
- [ ] **C2** — Start participating in Indie Hackers discussions (need 4–6 weeks before posting milestone)
  - Go to indiehackers.com → find active threads in "Ask IH" or "Growth"
  - Answer 2–3 questions genuinely per week — no HomeSight mentions yet
  - Goal: 4–6 weeks of participation before posting milestone

### Free Directory Submissions
- [ ] **D1** — BetaList — betalist.com/submit
  - Fill out: name, URL, tagline, description, category (Real Estate / Data)
  - Tagline: `Zillow data for every U.S. ZIP code — mapped, trended, ranked`
  - Takes 1–2 weeks to go live; submit now
- [x] **D2** — Uneed — uneed.best/submit-a-tool
  - Same info as BetaList; goes live same day or next day
  - Note: currently running a $600 giveaway — upvotes earn raffle tickets
- [x] **D3** — TinyLaunch — tinylaunch.com
  - Submit product page; minimal friction
- [x] **D4** — Smol Launch — smollaunch.com
  - Submit product page; minimal friction

### Reddit Karma Building (no HomeSight mentions yet)
- [ ] **R1** — Answer 10+ real questions in r/RealEstate
  - Go to r/RealEstate → sort by "New" → find questions you can answer with real housing data knowledge
  - Track count: 0 / 10
- [ ] **R2** — Answer 10+ real questions in r/FirstTimeHomeBuyer
  - Same approach — focus on first-timer questions (down payment, market timing, rates)
  - Track count: 0 / 10
- [ ] **R3** — Participate in r/personalfinance rent vs. buy threads
  - Search: `subreddit:personalfinance rent vs buy` → reply to active threads with data-driven takes
  - No tool promotion — just be genuinely useful

### Site Readiness
- [x] **P1** — Favicon — confirmed present
- [x] **P2** — OG/social meta tags — deployed 2026-06-12, verified at opengraph.xyz
- [x] **P3** — Uptime monitoring — AWS Lambda + EventBridge + SNS, runs every 5 min, emails michaelkm03@gmail.com on failure (deployed 2026-06-12)
  - Lambda: `homesight-monitor` (us-west-2)
  - SNS topic: `arn:aws:sns:us-west-2:005097885341:homesight-alerts`
  - Checks: /health, /api/zip/98101, /api/heatmap
- [x] **P4** — Bing Webmaster Tools — verified 2026-06-12, homesight.live indexed for Bing/DuckDuckGo
- [x] **P5** — GA4 event tracking — deployed 2026-06-12; tracks zip_search (landing + header), zip_click (map), metric_change, metro_search
- [x] **P6** — Content platform posts
  - Medium Article 1 published 2026-06-16: https://medium.com/@michaelkm03/i-mapped-26-000-u-s-zip-codes-heres-what-city-averages-are-hiding-0f398e729a70
  - Medium Article 2 scheduled 2026-06-24 8AM EST
  - Medium Article 3 scheduled 2026-07-01 8AM EST
  - Medium Article 4 (Sun Belt) — schedule for 2026-07-08 8AM EST
  - Dev.to Article 1 published 2026-06-16: https://dev.to/michael_montgomery/i-mapped-home-prices-across-26000-us-zip-codes-heres-what-city-averages-are-hiding-1ej0
  - Hashnode — removed (API paid-only since May 2026; content removed by their moderation)
  - LinkedIn post — ready, post 2026-06-17 8-9AM EST (first comment links to Medium)
  - r/dataisbeautiful, Show HN, Twitter thread — not yet written
- [x] **P7** — Cross-post automation script
  - `marketing/crosspost.py` — publishes to Dev.to; Hashnode removed (paid API)
  - Article configs in `marketing/articles/`
  - Run: `python crosspost.py articles/articleN.json`
  - Requires env vars: DEVTO_API_KEY (HASHNODE vars no longer needed)

### Twitter/X Setup
- [ ] **T1** — Set up alerts/monitoring for: @nickgerli1, @zillow, @redfin, @NAR_Research
  - On Twitter/X: follow all four accounts
  - Enable notifications for their tweets (bell icon)
  - Optional: create a private Twitter List called "Housing" with these accounts for easy monitoring
- [ ] **T2** — Reply farm: respond to 5+ housing market tweets with data from HomeSight (no promo, just value)
  - Find tweet → pull relevant HomeSight data or screenshot → reply with the data point
  - No link to HomeSight yet — just be the person with good data
  - Track count: 0 / 5

---

## Launch Week Sequence

- [ ] **L1** — **Day 1:** r/dataisbeautiful + r/MapPorn posts
  - Take a high-quality screenshot of the national ZIP choropleth map
  - r/dataisbeautiful post: title starts with `[OC]`, credit Zillow Research in body, link HomeSight in comments (not title)
  - r/MapPorn post: same screenshot, different title framing (geography angle)
  - Post Tuesday–Thursday, 9–11 AM ET for best visibility
- [ ] **L2** — **Day 2–3:** Show HN — `Show HN: HomeSight – Home values and rent trends across 26K U.S. ZIP codes`
  - Post at news.ycombinator.com/submit — select "Show HN" in title
  - Post your own comment within 60 seconds: why you built it + one interesting data finding + open Q&A
  - Line up 5–10 people to upvote within the first 60 minutes
  - Reply to every comment for the first 2 hours
  - Post Tuesday–Thursday, 9–11 AM ET
- [ ] **L3** — **Day 4:** Twitter/X launch thread
  - Tweet 1: screenshot + one sentence, no link
  - Tweets 2–5: data findings with screenshots
  - Tweet 6: link + CTA
  - Never lead with the link — algorithms suppress link-first posts
- [ ] **L4** — **Day 5:** Product Hunt (requires maker account 30+ days old — earliest 2026-07-12)
  - Launch at 12:01 AM Pacific on a Tuesday–Thursday
  - Post maker comment immediately on launch day
  - Reply to every comment within 15–30 min for first 6 hours

---

## Month 2

- [ ] **M1** — Begin programmatic ZIP-level SSR pages (`/housing-market/{zip}`)
  - Requires SSR implementation (FastAPI Jinja2 templates or Next.js wrapper)
  - Each page needs: unique `<title>`, meta description, real data on first response (not JS-rendered)
  - Start with state-level pages → city → ZIP hierarchy
- [ ] **M2** — Submit to housing newsletters with a specific data finding as the pitch
  - Find 3–5 housing/real estate newsletters
  - Pitch email: lead with a specific data finding (e.g., "ZIP codes with highest 5-year appreciation in Seattle metro"), offer it as a guest data insight
- [ ] **M3** — Post "I launched" milestone on Indie Hackers with honest traffic numbers
  - Write in "Milestones" category
  - Include: what you built, launch channels used, traffic numbers, what worked / what didn't
