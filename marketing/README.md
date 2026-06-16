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
