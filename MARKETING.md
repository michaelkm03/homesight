# HomeSight Marketing Gameplan

---

## Section 1 — Free / Organic

### 1. Reddit (highest short-term ROI)

Reddit is the best immediate channel. The audience in these subs is exactly who uses HomeSight — active home buyers, investors, and data enthusiasts.

**Subreddit priority order:**

| Subreddit | Audience | Approach |
|-----------|----------|----------|
| r/dataisbeautiful | Data enthusiasts | Post choropleth map screenshot as [OC], credit Zillow Research in post body |
| r/MapPorn | Map lovers | National ZIP choropleth is exactly the content format this sub upvotes |
| r/FirstTimeHomeBuyer | Active buyers | Answer real questions using HomeSight data first; mention you built the tool as a footnote |
| r/RealEstate | Broad RE audience | Answer first, promote second |
| r/realestateinvesting | Investors | Lead with appreciation trends or top-10 ZIPs for a metro; data-first angle |
| r/REBubble | Skeptical data crowd | Lean into raw data, no spin — this audience distrusts marketing but loves charts |
| r/personalfinance | Mass audience | Rent vs. buy threads are evergreen; HomeSight rent data is directly relevant |

**Rules that determine success or failure:**
- Never lead with "I built a tool" — Reddit punishes this. Lead with a data finding (e.g. "The ZIP codes with the highest 5-year appreciation in Phoenix might surprise you")
- Always disclose you're the maker — hidden affiliation gets reported and kills the post
- Build 10–15 karma comments answering real questions in each sub before posting anything about HomeSight
- Best posting time: Tuesday–Thursday, 8–10 AM ET

**Expected result:** A well-timed r/dataisbeautiful or r/MapPorn post that lands on the front page can drive 5,000–20,000 visitors in 48 hours.

---

### 2. Hacker News — Show HN

High upside but unpredictable. One strong Show HN post can drive as much traffic as months of SEO.

**Title to use:**
```
Show HN: HomeSight – Home values and rent trends for every U.S. ZIP code
```

**Execution:**
- Post Tuesday–Thursday, 9–11 AM ET only
- Post your own comment within 60 seconds of submitting — explain why you built it, drop one interesting data finding (e.g. "The median home value in 90210 peaked in 2022 and has dropped 12% since"), and invite questions
- Reply to every comment within the first 2 hours — HN readers reward builders who engage
- Do NOT ask friends to mass-upvote. HN's anti-abuse system detects coordinated voting and will shadowban the post

**What makes HomeSight HN-friendly:** It's a real dataset (Zillow), a real technical problem (26K ZIPs, geopandas, Parquet), and it produces a visible artifact (the map). HN loves this combination.

**Expected result:** If it catches, 2,000–15,000 visits on launch day. If it doesn't land on the front page, still ~200–500 from the Show tab.

---

### 3. Product Hunt + Free Directories

**Product Hunt:**
- Create a maker account now (needs 30+ days of history before launch day matters)
- Launch Tuesday–Thursday at 12:01 AM Pacific
- Tagline: `Zillow data for every U.S. ZIP code — mapped, trended, ranked`
- Post your maker comment immediately on launch morning
- Reply to every comment within 15–30 min for the first 6 hours

**Free directories to submit to (1-hour total effort):**
- **BetaList** — submit now, has a queue but surfaces to early adopters
- **Uneed** — active community, free submission
- **TinyLaunch** — small but targeted indie tool audience
- **Smol Launch** — similar, 2-minute submission

**Expected result:** Product Hunt creates permanent directory listings that feed SEO and discovery over time.

---

### 4. Twitter / X — Organic

Zero followers makes broadcast posting useless. The play is reply farming.

**Reply farming strategy:**
- Follow and monitor: @zillow, @redfin, @NAR_Research, @nickgerli1 (housing bubble analyst, 200K+ followers), @HousingWire
- When any of these post housing data, reply within 30 minutes with a relevant HomeSight screenshot and a short observation — you get early-reply visibility before the thread gets crowded
- Never drop the link in the reply itself. Drop it in a reply to your own reply

**Launch thread format:**
1. Tweet 1: Hook — striking choropleth screenshot, one sentence, no link
2. Tweets 2–5: Data findings with charts ("Austin ZIPs that peaked in 2022 are now...")
3. Tweet 6: Link + brief CTA

**Expected result:** Slow build over weeks. Reply farming to large accounts can get individual tweets 5K–50K impressions organically.

---

### 5. Programmatic SEO (Month 2+ — highest long-term ceiling)

HomeSight's biggest long-term lever. Zillow's 33M monthly visits are built largely on location pages. The ZIP-code level is nearly uncontested.

**Target URL structure:**
```
/housing-market/ca/los-angeles/90210
/housing-market/tx/austin/78701
```

Each page needs:
- Unique `<title>` and meta description per location
- Real data baked into the HTML on first response (not JS-rendered — crawlers can't execute JS)
- State → city → ZIP internal link hierarchy for crawlability

**What to target:** "[ZIP code] housing market", "90210 home values", "home prices in [city] 78701" — most have fewer than 100 competing pages.

**Critical prerequisite:** HomeSight is currently a SPA. SSR must be implemented before investing time here or pages won't rank.

**Expected result:** 6–12 months to meaningful traffic, but compounding and essentially free once built.

---

### 6. Indie Hackers — Build in Public

Post honest milestone updates in the Milestones section with real numbers: launched, first 100 users, first 1,000 users, GA4 data, what worked and didn't. This audience shares, comments, and links — each post is a small SEO and distribution hit.

---

## Section 2 — Paid Advertising

> Run paid only after organic has validated the product. You need to know what message resonates and what pages convert before spending money on ads.

**Suggested starting budget:** $500–700/mo total across 2 channels.

---

### 1. Google Search Ads (highest intent — start here)

Users searching for housing data are already in the mindset to use HomeSight. This is the only paid channel where demand exists before you create it.

**Keywords to target:**

| Keyword Type | Examples | Est. CPC |
|-------------|----------|----------|
| Data-specific (low competition) | "housing market data by zip code", "home value trends map" | $1–3 |
| Buyer research | "zip code home prices", "housing market [city]" | $3–6 |
| Avoid | "homes for sale", "buy a house" | $5–20+ — wrong intent, too expensive |

**Campaign setup:**
- Search campaign only — no Display to start
- Exact and phrase match keywords only — broad match wastes budget
- Landing page: direct to homesight.live, ideally with a ZIP pre-loaded
- Budget: $300–400/mo to start (~100–200 clicks/day at low CPCs)

**Expected result:** At $2 avg CPC and $300/mo, ~150 targeted visitors/day.

---

### 2. Reddit Ads (cheapest targeted reach)

Reddit Ads let you target specific subreddits directly. You can put HomeSight in front of r/FirstTimeHomeBuyer readers for $0.75–2.00 per click — far cheaper than Google for this audience.

**Setup:**
- Format: Promoted Posts (look native, lower resistance)
- Target subreddits: r/FirstTimeHomeBuyer, r/RealEstate, r/realestateinvesting, r/personalfinance
- Creative: choropleth map screenshot — strongest visual hook
- Headline: "What's happening to home prices in your ZIP code?"
- Budget: $150–200/mo test phase

**Expected result:** CPCs of $1–2 for this audience. Reddit converts skeptically but users who engage tend to share.

---

### 3. Meta (Facebook + Instagram) Ads

Best for awareness and retargeting. Not as high intent as Google, but the visual format of HomeSight (map screenshots, trend charts) works well in feed and story ads.

**Phase A — Retargeting (start here, cheapest):**
- Install Meta Pixel on homesight.live
- Retarget visitors who didn't engage with the ZIP panel
- Budget: $100–150/mo

**Phase B — Cold prospecting:**
- Demographics: Age 28–55, homeowners + renters interested in buying, income $60K+
- Creative: choropleth map screenshot or before/after ZIP value chart
- Average CPC for real estate on Meta: ~$1.18 (2026 benchmark)
- Budget: $200–300/mo

**Expected result:** Lower intent than Google, higher volume. Best use is retargeting visitors already familiar with HomeSight.

---

### 4. Newsletter Sponsorships

One-time placements in housing/data newsletters deliver highly targeted readers at $0.10–0.50 per reader.

**Newsletters to approach:**
- **Calculated Risk** — macro housing data audience
- **Apartment List Research** — renter/buyer audience, data-forward
- **HousingWire Daily** — RE professional audience, larger list
- **The Data Viz Newsletter** — r/dataisbeautiful crowd in email form

**Approach:** Email the owner with a flat-fee sponsorship offer ($100–300 per send), or propose a "featured ZIP analysis" barter.

---

### Paid Channel Comparison

| Channel | CPC | Min Budget/mo | Best For |
|---------|-----|--------------|----------|
| Google Search | $1–6 | $300 | High-intent users actively searching |
| Reddit Ads | $0.75–2 | $150 | Targeted community reach |
| Meta Ads | $1–2 | $150 (retarget) | Awareness + retargeting |
| Newsletter | $0.10–0.50/reader | $100–300/send | Trust, niche audience |

---

## Launch Sequence

```
Now (Week 1–2)
├── Build Reddit karma in target subs (answer questions, no HomeSight mentions yet)
├── Create Product Hunt maker account
├── Submit to free directories: BetaList, Uneed, TinyLaunch, Smol Launch
└── Set up Google Search Console, verify homesight.live, submit sitemap

Launch Week
├── Day 1: r/dataisbeautiful + r/MapPorn posts
├── Day 2–3: Show HN
├── Day 4: Twitter/X launch thread
└── Day 5: Product Hunt

Month 2 (after organic validates the product)
├── Start Google Search Ads ($300/mo)
├── Start Reddit Ads ($150/mo)
└── Begin SSR work for programmatic SEO

Month 3+
├── Add Meta retargeting ($100/mo)
├── Reach out to newsletters
└── Scale winning paid channels, cut losers
```
