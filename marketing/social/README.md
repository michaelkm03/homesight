# HomeSight Social Media Automation

Three scripts that automate Buffer scheduling for the HomeSight two-week content campaign (July 6–19, 2026).

## Scripts

| Script | Purpose |
|--------|---------|
| `buffer_schedule.py` | Schedule all 42 posts across LinkedIn, Twitter, Facebook via Buffer GraphQL API |
| `generate_post_images.py` | Screenshot homesight.live with ZIP panel open; upload to server; patch image URLs into buffer_schedule.py |
| `generate_og_concepts.py` | Generate candidate default OG images using Playwright + HTML/CSS concepts |

---

## Setup

**1. Install dependencies**
```bash
pip install requests playwright
playwright install chromium
```

**2. Set env var** (add to PowerShell `$PROFILE` or export in shell):
```powershell
$env:BUFFER_TOKEN = "your-buffer-personal-api-key"
# Get from: buffer.com/settings → API Keys
```

Buffer account: Essentials plan required (free plan caps at 10 scheduled posts per channel).

**3. SSH key** — `generate_post_images.py` uses `C:\Users\micha\.ssh\beacon.pem` to upload screenshots to the Lightsail server. This path is hardcoded; update `SSH_KEY` in the script if your key is elsewhere.

---

## Workflow

### Step 1 — Generate per-post screenshots (optional but recommended)

Each post that references a specific ZIP gets a custom screenshot of homesight.live with that ZIP's panel open:

```bash
cd marketing/social

# Preview what would happen without uploading or patching
python generate_post_images.py --dry-run

# Full run: screenshot → upload to server → patch image URLs into buffer_schedule.py
python generate_post_images.py
```

Screenshots saved to `post_images/` (gitignored). Uploaded to `/opt/homesight/static/social/` on the server. Posts with no ZIP use the default OG image (randomly selected from A or B on each run).

### Step 2 — Review the post list

```bash
python buffer_schedule.py --dry-run
```

Prints all 42 posts with platform, date, link flag, and image assignment. No API calls.

### Step 3 — Schedule to Buffer

```bash
python buffer_schedule.py
```

- Fetches currently-scheduled posts from Buffer (paginates all pages)
- Skips any post whose scheduled time is already in the queue (safe to re-run)
- Deletes any IDs listed in `EXISTING_IDS` first (only needed to force a clean slate)
- Prints ACCEPTED / REJECTED / ERROR per post with Buffer post ID

---

## Buffer API notes

**Plan: Essentials** — removes the 10-post-per-channel queue limit.

| Limit | Value |
|-------|-------|
| 15-min window | 100 requests (binding for bulk runs) |
| 24-hr window | 250 requests |
| 30-day window | 7,500 requests |

42 posts + overhead = ~45 API calls per full run. Well within all limits.

**Rate limit 429**: If hit, the `X-RateLimit-Reset` header shows when the 15-min window resets. Re-run after that timestamp — the dedup logic skips already-accepted posts automatically.

**Authentication**: Bearer token (personal API key). Never commit the key. Always read from `BUFFER_TOKEN` env var.

---

## Post structure

**Channels:**
- LinkedIn (`6a4167a85ab6d2f10680f165`) — 8 AM PT, data-heavy posts
- Twitter (`6a41645d5ab6d2f10680e433`) — 9 AM PT, short hooks + engagement questions
- Facebook (`6a41677f5ab6d2f10680f0d9`) — 10 AM PT, audience-growth format (polls, questions)

**Facebook `link` flag:**
- `link=True` — includes OG card preview (`linkAttachment`) pointing to homesight.live
- `link=False` — pure text/engagement post; `"type": "post"` is still required in metadata

**Default OG images** (both uploaded to `/opt/homesight/static/`):
- `og-default-a.png` — dark gradient overlay on live map + left-side brand block
- `og-default-b.png` — 60/40 split: Charlotte panel left, dark stats card right
- Selected randomly per run via `random.choice(OG_IMAGES)`

---

## Generating new OG image concepts

```bash
python generate_og_concepts.py
```

Screenshots homesight.live (hiding the on-page HomeSight text to avoid visual clash), then renders 4 HTML/CSS concept files and opens them for review. Output saved to `og_concepts/` (gitignored).

To use a chosen concept as the new default:
1. Upload the PNG to `/opt/homesight/static/` via scp
2. Add the URL to `OG_IMAGES` in `buffer_schedule.py`

---

## Theme distribution (July 6–19 campaign)

| Theme | Posts | Platforms |
|-------|-------|-----------|
| Data Insight | LinkedIn (all 14) | LI |
| Engagement Bait | Facebook (all 14), most Twitter | FB, TW |
| Market Spotlight | Rust Belt, Indiana, New England, South, Florida | LI |
| Momentum | Markets still moving post-pandemic | LI |
| Awareness | Tool intro, global/UK angle, rent data | All |

Goal: after July 19, compare engagement by theme to inform the next campaign's content mix.
