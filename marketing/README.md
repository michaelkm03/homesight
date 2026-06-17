# HomeSight Content Marketing

## crosspost.py

Publishes a Markdown article to **Dev.to** and **Hashnode** simultaneously, or audits both accounts to surface optimization suggestions.

### Setup

Set env vars once in your PowerShell profile (`notepad $PROFILE`):

```powershell
$env:DEVTO_API_KEY    = "your-key"      # dev.to/settings/extensions
$env:HASHNODE_API_KEY = "your-key"      # hashnode.com/settings/developer
$env:HASHNODE_PUB_ID  = "your-pub-id"  # Settings > General, ID is in the URL
```

Install dependency: `pip install requests`

---

### GA4 Stats setup (one-time, ~10 min)

Required for `--stats` mode. Skip if you only need crosspost/audit.

**1. Install the library**
```powershell
pip install google-analytics-data
```

**2. Enable the API in Google Cloud**
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Select or create a project (any name, e.g. "HomeSight Scripts")
- Search for "Google Analytics Data API" → Enable it

**3. Create a service account**
- IAM & Admin → Service Accounts → Create Service Account
- Name: `homesight-stats` (any name)
- Skip role assignment → Done
- Click the service account → Keys → Add Key → JSON → download the file
- Save it somewhere permanent, e.g. `C:\Users\micha\.gcp\homesight-stats.json`

**4. Grant the service account access to GA4**
- Go to [analytics.google.com](https://analytics.google.com) → Admin
- Property Access Management → Add users
- Paste the service account email (looks like `homesight-stats@your-project.iam.gserviceaccount.com`)
- Role: **Viewer** → Add

**5. Find your GA4 numeric property ID**
- GA4 Admin → Property Settings
- Copy the **Property ID** (a plain number like `123456789`) — NOT the `G-XXXXXX` measurement ID

**6. Set the remaining env vars** (add to `$PROFILE`):
```powershell
$env:GA4_PROPERTY_ID              = "123456789"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\micha\.gcp\homesight-stats.json"
```

---

### Crosspost scenario (typical flow)

1. Write article → publish on Medium → copy the final published URL.
2. Edit the article's JSON config and update `canonical_url` to that URL.
3. Run:

```
cd marketing
python crosspost.py articles/article2.json
```

**Output:**
```
Dev.to:   https://dev.to/michael_montgomery/5-us-housing-markets-quietly-outperforming-...
Hashnode: https://michaelkm.hashnode.dev/5-us-housing-markets-quietly-outperforming-...
```

The canonical URL on both posts points back to Medium, so all SEO credit stays there. Dev.to and Hashnode become distribution channels only.

---

### Stats scenario

```powershell
python crosspost.py --stats          # last 30 days
python crosspost.py --stats --days 7 # last 7 days
```

Prints four sections:
1. **Summary** — sessions, users, avg engagement time, engagement rate
2. **Traffic sources** — top 12 by sessions; content platforms (medium.com, dev.to, hashnode) flagged with `*`
3. **Landing pages** — which pages users land on first (shows if blog traffic hits `/` or bounces)
4. **Events** — GA4 events (zip_search, zip_click, metric_change, metro_search)

Use this weekly after each article publishes to see which platform and article actually drove visits.

**Metrics that matter:**

| Metric | Signal |
|---|---|
| `zip_click` | Core engagement — users clicking ZIPs on the map |
| `zip_search` | Intent-driven users — they came with a specific ZIP in mind |
| Content platform sessions | medium.com / dev.to referrals — shows which articles drive real traffic |
| Engagement rate | Target 60%+ — means users interact, not just land and leave |

**Ignore:** `page_view`, `scroll`, `session_start`, `first_visit`, `user_engagement` — GA4 auto-events, not actionable.

**Workflow:** run `--stats --days 7` the day after each LinkedIn/Medium post to measure immediate impact, then `--stats` (30-day) weekly to track trends.

---

### Audit scenario

```
python crosspost.py --audit
```

Pulls live data from both platforms and prints:

- Profile completeness (bio, website, avatar)
- Per-article table: views, reactions, cover image, canonical URL
- Actionable suggestions for anything missing

**Example output:**
```
=== Dev.to ===
Username : @michael_montgomery
Bio      : MISSING
Website  : MISSING

Articles : 1 published | 124 total views | 2 total reactions

  Title                                            Views  Reacts  Cover  Canonical
  ──────────────────────────────────────────────────────────────────────────────────
  I Mapped Home Prices Across 26,000 US ZIP Codes    124       2    YES        YES

  Top tags: webdev(1), datascience(1), javascript(1), discuss(1)

Suggestions:
  • Add a bio at dev.to/settings — appears on every article byline
  • Add website (homesight.live) in dev.to/settings — free backlink on every article
```

Run this before scheduling each new article drop.

---

### Article config format

Each article needs a JSON config + a Markdown body in `articles/`:

```
articles/
  article2.json    ← config (title, tags, canonical URL)
  article2.md      ← raw Markdown body (copy from Medium draft, no front matter)
  article3.json
  article3.md
  ...
```

**JSON fields:**

| Field | Required | Notes |
|---|---|---|
| `title` | yes | Must match what you published on Medium |
| `body_file` | yes | Filename of the .md file, relative to the articles/ folder |
| `tags_devto` | yes | Max 4. Use high-follower tags: `webdev`, `datascience`, `javascript`, `discuss` |
| `tags_hashnode` | yes | No hard limit; keep it focused |
| `canonical_url` | yes | **Full Medium URL** — update this before running the script |
| `cover_image` | no | Public image URL, or null |

**Template:**
```json
{
    "title":         "Your Article Title",
    "body_file":     "article3.md",
    "tags_devto":    ["webdev", "datascience", "javascript", "discuss"],
    "tags_hashnode": ["webdev", "datascience"],
    "canonical_url": "https://medium.com/@michaelkm03/YOUR-SLUG-HERE",
    "cover_image":   null
}
```

---

### Article schedule

| Config | Title | Medium Publish | Crosspost |
|---|---|---|---|
| article1 | I Mapped 26K U.S. ZIP Codes | 2026-06-16 LIVE | Dev.to LIVE; Hashnode pending |
| article2.json | 5 Markets Quietly Outperforming | 2026-06-24 8AM EST | After publish, update canonical_url then run |
| article3.json | Interest Rates & ZIP-Level Appreciation | 2026-07-01 8AM EST | Same |
| article4.json | Is the Sun Belt Housing Boom Actually Over? | 2026-07-08 8AM EST | Same — not written yet |
