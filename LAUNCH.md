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

- [ ] Verify site in Google Search Console, submit sitemap
- [ ] Build Reddit karma in r/RealEstate + r/FirstTimeHomeBuyer (no HomeSight mentions yet)
- [ ] Create Product Hunt maker account
- [ ] Start participating in Indie Hackers discussions

## Launch Week Sequence

- **Day 1:** r/dataisbeautiful + r/MapPorn posts
- **Day 2–3:** Show HN
- **Day 4:** Twitter/X launch thread
- **Day 5:** Product Hunt

## Month 2

- Begin programmatic ZIP-level SSR pages
- Submit to housing newsletters with a specific data finding as the pitch
- Post "I launched" milestone on Indie Hackers with honest traffic numbers
