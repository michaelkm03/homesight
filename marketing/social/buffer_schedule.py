# buffer_schedule.py — schedule HomeSight posts to Buffer via GraphQL API
#
# Usage:
#   python buffer_schedule.py --dry-run   # print all posts without making API calls
#   python buffer_schedule.py             # schedule all posts not already in Buffer
#
# Required env var:
#   BUFFER_TOKEN — personal API key from buffer.com/settings
#
# Buffer plan notes (Essentials):
#   15-min limit: 100 requests — binding constraint for bulk runs
#   24-hr limit:  250 requests
#   30-day limit: 7,500 requests
#
# Post timing (Pacific Time):
#   LinkedIn  8 AM  → UTC 15:00
#   Twitter   9 AM  → UTC 16:00
#   Facebook 10 AM  → UTC 17:00
#
# Facebook posts:
#   link=True  → includes linkAttachment OG card (homesight.live preview)
#   link=False → pure engagement post (question/poll format); still requires type="post"

import os, requests, json, time, random
from datetime import datetime, timezone, timedelta

TOKEN = os.environ.get("BUFFER_TOKEN", "")
if not TOKEN:
    raise RuntimeError("BUFFER_TOKEN env var not set — export BUFFER_TOKEN=<your key>")

API = "https://api.buffer.com/"
HDR = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Buffer channel IDs (organization: 6a416406d0bf4334f89575df)
TWITTER  = "6a41645d5ab6d2f10680e433"
FACEBOOK = "6a41677f5ab6d2f10680f0d9"
LINKEDIN = "6a4167a85ab6d2f10680f165"
ORG_ID   = "6a416406d0bf4334f89575df"

# Default OG images — randomly selected per run; both uploaded to /opt/homesight/static/
OG_IMAGES = [
    "https://homesight.live/static/og-default-a.png",
    "https://homesight.live/static/og-default-b.png",
]
OG_IMAGE = random.choice(OG_IMAGES)
OG_ALT   = "HomeSight map showing ZIP-level home value appreciation across the US"
SITE_URL = "https://homesight.live"

EXISTING_IDS = [
    # Posts to delete before re-running. Add IDs here only to force a clean slate.
    # Normally leave empty — the script skips already-scheduled posts automatically.
]


def pt(date_str, hour):
    """Convert a Pacific Time hour to a UTC ISO string (PT = UTC-7)."""
    dt = datetime(int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10]),
                  hour, 0, 0, tzinfo=timezone.utc)
    return (dt + timedelta(hours=7)).isoformat()


# ── Post content ──────────────────────────────────────────────────────────────
# Themes: Data Insight, Engagement Bait, Market Spotlight, Momentum, Awareness
# LinkedIn: data-heavy, analytical audience
# Twitter: short hooks, engagement questions, ZIP lookup invitations
# Facebook: audience-growth format — polls, questions, broad hooks (low follower count)

POSTS = [
    # ── Jul 6–19: all 3 platforms ──

    # ── Sun 7/6 ──
    {
        "channel": TWITTER,
        "text": "I built a free tool to look up home value appreciation for any US ZIP code.\n\nNo login. No paywall. No catch.\n\nhomesight.live\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-06", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "The Rust Belt story the housing media isn't writing.\n\nSchenectady NY 12307: +313.7% over 10 years.\nBuffalo NY 14210: +200.9%.\nDetroit MI 48219: +204.9%.\n\nThe national median ZIP appreciation over this same period: +83.2%.\n\nThese markets are at 2–4x that. They never made a list. They just compounded.\n\nI built HomeSight to surface data like this — 26,000+ US ZIP codes, 10 years, free.\n\nWhat's the most underrated market you've found in the data?\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-06", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "What would you guess the average US home has appreciated in the last 10 years?\n\nDrop your guess below — I'll share the real number in the comments 👇\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-06", 10),
        "link": False,
    },

    # ── Mon 7/7 ──
    {
        "channel": TWITTER,
        "text": "Reply with your ZIP code.\n\nI'll tell you the 10-year appreciation rate.\n\n(Yes, the tool is free — homesight.live)",
        "scheduled_at": pt("2026-07-07", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Most markets that ran hard over the last decade have softened in the last year.\n\nA few haven't.\n\nRockford IL 61101: +281.7% over 10 years. Still up +14.2% over the last 12 months.\nMilwaukee WI 53206: +327.9% over 10 years. Still up +13.5%.\n\nThese markets weren't driven by a pandemic spike. They were moving before, and they're still moving. Stable employment, affordable entry points, consistent demand.\n\nI built HomeSight to track this across 26,000+ ZIP codes — 1 year, 5 year, 10 year, all in one place.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-07", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "The national median ZIP code appreciated +83.2% in home values over the last decade.\n\nDoes that number surprise you?\n\n#RealEstate #HousingMarket",
        "scheduled_at": pt("2026-07-07", 10),
        "link": False,
    },

    # ── Tue 7/8 ──
    {
        "channel": TWITTER,
        "text": "Have home values in your city doubled in the last decade?\n\nYes, no, or no idea — drop your answer below 👇\n\n(You can actually look it up: homesight.live)",
        "scheduled_at": pt("2026-07-08", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Indiana isn't a housing headline state.\n\nThe data:\n\nFort Wayne 46803: +283.7% over 10 years.\nSouth Bend 46613: +279.7%.\nIndianapolis 46218: +306.9%.\n\nAffordable entry points. Stable employers. ZIP codes that have quietly tripled in a decade.\n\nNone of them were in a housing article. All of them are in the data.\n\nI built HomeSight to surface exactly this — 26,000+ ZIP codes, free, no account.\n\nWhat's your underrated market?\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-08", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Comment your city below — I'll look up the 10-year home value trend for your area 👇\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-08", 10),
        "link": False,
    },

    # ── Wed 7/9 ──
    {
        "channel": TWITTER,
        "text": "The most underrated housing markets in the US aren't where you'd expect.\n\nHere's how to find them: homesight.live\n\n#RealEstate #Housing",
        "scheduled_at": pt("2026-07-09", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Everyone talks about Boston real estate.\n\nThe data says look west.\n\nWorcester MA 01608: +232.9% over 10 years. +72.2% in the last 5 alone.\nHartford CT 06112: +125.0% over 10 years. +56.5% in 5.\nProvidence RI 02909: +170.4% over 10 years. +45.6% in 5.\n\nSecond-tier New England cities — 40–60 miles inland, fraction of the coastal price — have been among the most consistent housing performers in the country.\n\nThe national median was +83.2% over this same period.\n\nI built HomeSight to make this visible. 26,000+ ZIP codes, 10 years, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-09", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Do you feel like your home (or your rental) has outperformed or underperformed the broader market over the last 10 years?\n\n#RealEstate #Housing",
        "scheduled_at": pt("2026-07-09", 10),
        "link": False,
    },

    # ── Thu 7/10 ──
    {
        "channel": TWITTER,
        "text": "Two homes in the same city, same year purchased. Different ZIP codes.\n\nThe difference in 10-year appreciation can be dramatic.\n\nLocation within a city matters more than most people realize.\n\nhomesight.live\n\n#RealEstate",
        "scheduled_at": pt("2026-07-10", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Florida has been one of the most discussed housing markets in the country.\n\nBut within Florida, the variance is extreme.\n\nTampa 33605: +245.2% over 10 years.\nMiami-area 33142: +258.6%.\n\nThe state average tells you almost nothing. The same ZIP-level problem that exists in every major market exists in Florida — the city number isn't the neighborhood number.\n\nI built HomeSight to surface it — 26,000+ US ZIP codes, free.\n\nhomesight.live\n\n#RealEstate #Housing #Florida #Investing",
        "scheduled_at": pt("2026-07-10", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Fun experiment: look up your current ZIP on homesight.live — then look up the city you grew up in.\n\nCompare what each has done over the last 10 years.\n\n👇 Free, no account needed\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-10", 10),
        "link": True,
    },

    # ── Fri 7/11 ──
    {
        "channel": TWITTER,
        "text": "What's the most surprising city you've seen outperform in housing?\n\nDrop it below and I'll pull the 10-year data 👇",
        "scheduled_at": pt("2026-07-11", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "The cities with the highest ZIP-level appreciation over the last decade aren't in the articles.\n\nReading PA 19602: +345.1% over 10 years.\nSchenectady NY 12307: +313.7%.\n\nLegacy manufacturing cities. Affordable housing stock. Proximity to major corridors. A decade of compounding that almost no one covered.\n\nNational median over the same period: +83.2%.\n\nI built HomeSight to find the gaps — 26,000+ ZIP codes, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-11", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "The cities you'd expect to top the housing appreciation charts aren't the ones at the top.\n\nWhat city do you think is #1 in the US over the last decade? Drop it below 👇\n\n#RealEstate #HousingMarket",
        "scheduled_at": pt("2026-07-11", 10),
        "link": False,
    },

    # ── Sat 7/12 ──
    {
        "channel": TWITTER,
        "text": "26,000+ US ZIP codes. UK postcodes back to 1995.\n\nFree. No account.\n\nhomesight.live\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-12", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "The cities that dominated housing coverage last decade:\nAustin. Phoenix. Miami. Nashville.\n\nThe cities that dominated actual ZIP-level appreciation:\nReading. Schenectady. Rockford. Fort Wayne. South Bend. Worcester.\n\nThe gap between what gets written about and what the data shows is the whole reason I built HomeSight.\n\n26,000+ ZIP codes. 10 years of data. Free.\n\nhomesight.live\n\n#RealEstate #Housing #Data #PersonalFinance",
        "scheduled_at": pt("2026-07-12", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "I wanted to know what homes in my target ZIP codes had done over the last 10 years.\n\nNo free tool existed that showed that — so I built one.\n\nhomesight.live — 26,000+ US ZIP codes, free, no account.\n\n#RealEstate #HomeValues #SideProject",
        "scheduled_at": pt("2026-07-12", 10),
        "link": True,
    },

    # ── Sun 7/13 ──
    {
        "channel": TWITTER,
        "text": "Name a city most people write off for housing.\n\nI'll look it up and share the data 👇",
        "scheduled_at": pt("2026-07-13", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Post-pandemic, most markets that ran hard have softened.\n\nA few haven't.\n\nRockford IL 61101: +281.7% over 10 years. +14.2% in the last 12 months.\nMilwaukee WI 53206: +327.9% over 10 years. +13.5%.\nBirmingham AL 35061: +184.9% over 10 years. +9.9%.\n\nThese markets share a profile: affordable entry points, stable local employment, and demand that wasn't driven by remote-work speculation. They didn't need a boom — so they don't have a bust.\n\nI built HomeSight to track this across 26,000+ ZIP codes, every timeframe.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-13", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Which of these describes you right now?\n\n🏠 I own a home\n🏢 I rent\n🔍 Looking to buy\n💭 Just here for the data\n\nDrop it below 👇\n\n#RealEstate #Housing",
        "scheduled_at": pt("2026-07-13", 10),
        "link": False,
    },

    # ── Mon 7/14 ──
    {
        "channel": TWITTER,
        "text": "Most markets that spiked in 2021 have cooled.\n\nA few haven't.\n\nWhat's your market done in the last year?\n\nhomesight.live\n\n#RealEstate #Housing",
        "scheduled_at": pt("2026-07-14", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "A consistent track record across every timeframe is rare.\n\nMilwaukee WI 53206:\n→ +327.9% over 10 years\n→ +76.2% over 5 years\n→ +13.5% over the last 12 months\n\nThis market didn't spike in 2021 and crash. It has been compounding steadily for a decade and is still moving. Most ZIPs with a strong 10-year number have cooled at the 1-year level. This one hasn't.\n\nI built HomeSight to surface data like this — 26,000+ ZIP codes, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-14", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "If you could move anywhere in the US right now for the best housing value, where would you go?\n\n👇\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-14", 10),
        "link": False,
    },

    # ── Tue 7/15 ──
    {
        "channel": TWITTER,
        "text": "The South has some of the most consistent housing performers of the last decade.\n\nNone of them are in Atlanta.\n\nWhat cities come to mind? 👇",
        "scheduled_at": pt("2026-07-15", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Atlanta gets every headline from the South.\n\nThe data shows a bigger picture.\n\nBirmingham AL 35061: +184.9% over 10 years. Still up +9.9% last year.\nRichmond VA 23224: +178.6% over 10 years. +49.9% in just the last 5.\nMemphis TN 38126: +201.3% over 10 years.\n\nAffordable entry points. Growing local economies. ZIP codes that have compounded through two cycles without landing in a single housing article.\n\nI built HomeSight to surface them — 26,000+ US ZIP codes, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-15", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Birmingham, AL. Richmond, VA. Memphis, TN.\n\nThree Southern cities that have quietly outperformed the national housing average for a decade — with no headlines to show for it.\n\nDid your city make the list? 👇 homesight.live\n\n#RealEstate #HomeValues #HousingMarket",
        "scheduled_at": pt("2026-07-15", 10),
        "link": True,
    },

    # ── Wed 7/16 ──
    {
        "channel": TWITTER,
        "text": "The median US ZIP code appreciated +83.2% in home values from 2014–2026.\n\nDid your neighborhood beat that?\n\nhomesight.live — free, no account.\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-16", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "The national median ZIP-code home appreciation, April 2014 to April 2026: +83.2%.\n\nThat number hides everything.\n\nReading PA 19602: +345.1%.\nMilwaukee WI 53206: +327.9%.\nSchenectady NY 12307: +313.7%.\nFort Wayne IN 46803: +283.7%.\n\nThese aren't isolated cases. Scores of ZIP codes have hit 200–300%+ while the national figure sat at 83%.\n\nThe median is where the story ends. ZIP-level data is where it starts.\n\nI built HomeSight to show you where they are. 26,000+ ZIP codes. Free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #Data",
        "scheduled_at": pt("2026-07-16", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "The national home appreciation average over the last 10 years was +83.2%.\n\nDo you think your home (or your city) beat that?\n\n👇 Look it up free — homesight.live\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-16", 10),
        "link": True,
    },

    # ── Thu 7/17 ──
    {
        "channel": TWITTER,
        "text": "Rent has risen — but not equally across ZIP codes.\n\nHomeSight tracks rent by ZIP, free.\n\nhomesight.live\n\n#RealEstate #Rent",
        "scheduled_at": pt("2026-07-17", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "Everyone tracks home value appreciation.\n\nFewer people track rent.\n\nNational median ZIP-code rent increase over the last 10 years: +64.8%.\n\nSome markets ran much harder:\n\nNewport RI 02840: +151.5%.\nAtlanta GA 30310: +146.3%.\nDelray Beach FL 33483: +139.8%.\nSt. Petersburg FL 33703: +133.5%.\n\nFor investors evaluating yield, or renters deciding where to move next, rent trends by ZIP are often more actionable than home appreciation figures.\n\nHomeSight tracks both — home values and rent, by ZIP code, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-17", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Renters: do you feel like rent in your area has gotten out of control in the last 5 years?\n\nWhat city are you in? 👇\n\n#Rent #RealEstate #HousingMarket",
        "scheduled_at": pt("2026-07-17", 10),
        "link": False,
    },

    # ── Fri 7/18 ──
    {
        "channel": TWITTER,
        "text": "Drop your ZIP code below.\n\nI'll pull the 10-year appreciation rate 👇\n\n(homesight.live has it for 26,000+ ZIPs)",
        "scheduled_at": pt("2026-07-18", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "The same ZIP-level story exists in the UK.\n\nLondon gets every housing headline. The data shows a much wider picture.\n\nHomeSight now covers UK postcode sectors going back to 1995 — millions of Land Registry transactions. The variance between postcode sectors within Manchester, Leeds, or Birmingham rivals what you see between ZIP codes in a US metro.\n\nThe national UK narrative is just as misleading as the US one.\n\nSame tool. Same idea. Now global.\n\nhomesight.live\n\n#UKProperty #RealEstate #HousingMarket #DataScience",
        "scheduled_at": pt("2026-07-18", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "Before you buy a home, it's worth knowing what that ZIP code has done over the last decade — not just what it costs today.\n\nThe 10-year trend tells you things the listing price can't.\n\n👇 homesight.live — free, no account\n\n#RealEstate #HomeValues #HomeBuying",
        "scheduled_at": pt("2026-07-18", 10),
        "link": True,
    },

    # ── Sat 7/19 ──
    {
        "channel": TWITTER,
        "text": "Free tool. No ads. Just data.\n\nHome values for 26,000+ US ZIP codes — search any area in seconds.\n\nhomesight.live\n\n#RealEstate #HomeValues",
        "scheduled_at": pt("2026-07-19", 9),
    },
    {
        "channel": LINKEDIN,
        "text": "One thing worth doing before evaluating any market: look at ZIP-level appreciation across the entire metro.\n\nThe variance is almost always more informative than the city average.\n\nIn Charlotte: some ZIPs as high as +209.8% over 10 years. Same city.\nIn Indianapolis: some as high as +306.9%. Same metro.\n\nWhere you buy within a city can matter as much as which city you choose.\n\nHomeSight makes this visible — 26,000+ ZIPs, free.\n\nhomesight.live\n\n#RealEstate #Housing #Investing #PersonalFinance",
        "scheduled_at": pt("2026-07-19", 8),
    },
    {
        "channel": FACEBOOK,
        "text": "What's one thing you wish you'd known about the housing market before buying — or before deciding not to buy?\n\n👇\n\n#RealEstate #Housing #PersonalFinance",
        "scheduled_at": pt("2026-07-19", 10),
        "link": False,
    },
]


# ── GraphQL mutations ─────────────────────────────────────────────────────────

DELETE_MUTATION = """
mutation DeletePost($input: DeletePostInput!) {
  deletePost(input: $input) {
    ... on DeletePostSuccess { id }
    ... on VoidMutationError { message }
  }
}
"""

CREATE_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id status }
    }
    ... on NotFoundError     { message }
    ... on UnauthorizedError { message }
    ... on UnexpectedError   { message }
    ... on LimitReachedError { message }
    ... on InvalidInputError { message }
    ... on RestProxyError    { message code }
  }
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_dt(s):
    s = s.replace("Z", "+00:00").replace(".000", "")
    return datetime.fromisoformat(s).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def get_scheduled_times():
    """Fetch all currently-scheduled dueAt times from Buffer (paginates automatically)."""
    times = set()
    cursor = None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        q = (
            f'{{ posts(input: {{ organizationId: "{ORG_ID}"{after}, '
            f'filter: {{ status: [scheduled] }} }}) '
            f'{{ edges {{ node {{ dueAt }} }} pageInfo {{ hasNextPage endCursor }} }} }}'
        )
        r = requests.post(API, headers=HDR, json={"query": q})
        data = r.json().get("data", {}).get("posts", {})
        for edge in data.get("edges", []):
            times.add(_normalize_dt(edge["node"]["dueAt"]))
        pi = data.get("pageInfo", {})
        if not pi.get("hasNextPage"):
            break
        cursor = pi.get("endCursor")
    return times


def check_rate_limit():
    r = requests.post(API, headers=HDR, json={"query": "{ __typename }"})
    remaining   = int(r.headers.get("X-RateLimit-Remaining", -1))
    reset_ts    = int(r.headers.get("X-RateLimit-Reset", 0))
    retry_after = int(r.headers.get("Retry-After", 0))
    print(f"  HTTP {r.status_code}  remaining={remaining}  reset_ts={reset_ts}  retry_after={retry_after}s")
    if r.status_code != 200:
        print(f"  body: {r.text[:300]}")
    return remaining, reset_ts


def _raw(r):
    return f"HTTP {r.status_code} | remaining={r.headers.get('X-RateLimit-Remaining','?')} | {r.text[:400]}"


def delete_post(post_id):
    r = requests.post(API, headers=HDR, json={
        "query": DELETE_MUTATION,
        "variables": {"input": {"id": post_id}}
    })
    if r.status_code != 200:
        return {"_raw": _raw(r), "errors": [{"message": f"HTTP {r.status_code}"}]}
    return r.json()


def schedule_post(channel_id, text, scheduled_at, link=True, image=None):
    image_asset = {
        "image": {
            "url": image or OG_IMAGE,
            "metadata": {"altText": OG_ALT}
        }
    }

    metadata = {}
    if channel_id == FACEBOOK:
        if link:
            metadata["facebook"] = {"type": "post", "linkAttachment": {"url": SITE_URL}}
        else:
            # "type" is required even for non-link Facebook posts
            metadata["facebook"] = {"type": "post"}

    inp = {
        "channelId": channel_id,
        "text": text,
        "assets": [image_asset],
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": scheduled_at,
    }
    if metadata:
        inp["metadata"] = metadata

    r = requests.post(API, headers=HDR, json={
        "query": CREATE_MUTATION,
        "variables": {"input": inp}
    })
    if r.status_code != 200:
        return {"_raw": _raw(r), "errors": [{"message": f"HTTP {r.status_code}"}]}
    return r.json()


CHANNEL_NAME = {TWITTER: "Twitter", FACEBOOK: "Facebook", LINKEDIN: "LinkedIn"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN — no API calls will be made ===\n")
        for i, post in enumerate(POSTS):
            name = CHANNEL_NAME[post["channel"]]
            print(f"[{i+1}] {name} {post['scheduled_at'][:10]}  link={post.get('link', True)}  image={'custom' if post.get('image') else 'default'}")
        print(f"\nTotal: {len(POSTS)} posts. Run without --dry-run to schedule.")
        exit(0)

    print("Fetching already-scheduled posts from Buffer...")
    already_scheduled = get_scheduled_times()
    print(f"  {len(already_scheduled)} posts already in queue.\n")

    to_create = [p for p in POSTS if _normalize_dt(p["scheduled_at"]) not in already_scheduled]
    to_skip   = len(POSTS) - len(to_create)
    print(f"  {to_skip} posts already scheduled — skipping.")
    print(f"  {len(to_create)} posts to create.\n")

    NEEDED = len(EXISTING_IDS) + len(to_create)
    print("Checking rate limit...")
    remaining, reset_ts = check_rate_limit()
    if remaining != -1 and remaining < NEEDED:
        reset_local = datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"\nABORTED — only {remaining} requests remaining (need {NEEDED}). Resets at {reset_local}.")
        exit(1)
    print(f"Rate limit OK: {remaining} remaining, need {NEEDED}.\n")

    print(f"Deleting {len(EXISTING_IDS)} existing posts...")
    delete_failures = []
    for post_id in EXISTING_IDS:
        result = delete_post(post_id)
        dp = result.get("data", {}).get("deletePost", {})
        if "errors" in result:
            print(f"  DELETE {post_id} — ERROR: {result['errors'][0]['message']}")
            delete_failures.append(post_id)
        elif dp.get("id"):
            print(f"  DELETE {post_id} — OK")
        elif "not found" in dp.get("message", "").lower() or "not allowed" in dp.get("message", "").lower():
            print(f"  DELETE {post_id} — already sent/gone (skipped)")
        elif dp.get("message"):
            print(f"  DELETE {post_id} — REJECTED: {dp['message']}")
            delete_failures.append(post_id)
        else:
            print(f"  DELETE {post_id} — UNKNOWN: {json.dumps(result)[:300]}")
            delete_failures.append(post_id)
        time.sleep(2)

    if delete_failures:
        print(f"\nABORTED — {len(delete_failures)} delete(s) failed.")
        exit(1)

    print(f"\nScheduling {len(to_create)} posts...")
    for i, post in enumerate(to_create):
        name = CHANNEL_NAME[post["channel"]]
        result = schedule_post(
            post["channel"], post["text"], post["scheduled_at"],
            post.get("link", True), post.get("image")
        )
        cp = result.get("data", {}).get("createPost", {})
        if "errors" in result:
            print(f"[{i+1}] {name} {post['scheduled_at'][:10]} — ERROR: {result['errors'][0]['message']}")
            print(f"     raw: {result.get('_raw', '')[:400]}")
        elif cp.get("message"):
            print(f"[{i+1}] {name} {post['scheduled_at'][:10]} — REJECTED: {cp['message']}")
        elif cp.get("post"):
            p = cp["post"]
            print(f"[{i+1}] {name} {post['scheduled_at'][:10]} — ACCEPTED (id: {p.get('id')} status: {p.get('status')})")
        else:
            print(f"[{i+1}] {name} {post['scheduled_at'][:10]} — UNKNOWN: {json.dumps(result)[:400]}")
        time.sleep(2)

    print("\nDone.")
