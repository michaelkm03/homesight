"""
crosspost.py — publish or audit your Dev.to / Hashnode accounts

Modes:
    python crosspost.py articles/article2.json   # crosspost to both platforms
    python crosspost.py --audit                  # audit both accounts for optimizations

Required env vars (set once in PowerShell $PROFILE):
    DEVTO_API_KEY      — dev.to/settings/extensions
    HASHNODE_API_KEY   — hashnode.com/settings/developer
    HASHNODE_PUB_ID    — your Hashnode publication ID (Settings > General, ID in URL)
"""

import os, sys, json, argparse, requests

DEVTO_KEY = os.environ.get("DEVTO_API_KEY", "")
HN_KEY    = os.environ.get("HASHNODE_API_KEY", "")
HN_PUB_ID = os.environ.get("HASHNODE_PUB_ID", "")


# ── Crosspost ─────────────────────────────────────────────────────────────────

def post_devto(title, body, tags, canonical_url, cover_image=None):
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "tags": tags[:4],
            "canonical_url": canonical_url,
        }
    }
    if cover_image:
        payload["article"]["main_image"] = cover_image
    r = requests.post(
        "https://dev.to/api/articles",
        headers={"api-key": DEVTO_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if r.status_code in (200, 201):
        print(f"Dev.to:   {r.json().get('url')}")
    else:
        print(f"Dev.to FAILED {r.status_code}: {r.text[:300]}")


def post_hashnode(title, body, tags, canonical_url, cover_image=None):
    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) { post { id title url } }
    }
    """
    hn_tags = [{"name": t, "slug": t.lower().replace(" ", "-")} for t in tags]
    inp = {
        "title": title,
        "contentMarkdown": body,
        "publicationId": HN_PUB_ID,
        "tags": hn_tags,
        "originalArticleURL": canonical_url,
    }
    if cover_image:
        inp["coverImageOptions"] = {"coverImageURL": cover_image}
    r = requests.post(
        "https://gql.hashnode.com/",
        headers={"Authorization": f"Bearer {HN_KEY}", "Content-Type": "application/json"},
        json={"query": mutation, "variables": {"input": inp}},
        timeout=30,
    )
    data = r.json()
    if "errors" in data:
        print(f"Hashnode FAILED: {data['errors']}")
    else:
        post = data.get("data", {}).get("publishPost", {}).get("post", {})
        print(f"Hashnode: {post.get('url')}")


# ── Audit ─────────────────────────────────────────────────────────────────────

def audit_devto():
    if not DEVTO_KEY:
        print("Missing DEVTO_API_KEY — skipping Dev.to audit")
        return

    auth = {"api-key": DEVTO_KEY}
    profile_r  = requests.get("https://dev.to/api/users/me", headers=auth, timeout=30)
    articles_r = requests.get("https://dev.to/api/articles/me?per_page=30&state=published", headers=auth, timeout=30)

    if profile_r.status_code != 200:
        print(f"Dev.to profile fetch failed: {profile_r.status_code}")
        return

    profile  = profile_r.json()
    articles = articles_r.json() if articles_r.status_code == 200 else []

    print("\n=== Dev.to ===")
    print(f"Username : @{profile.get('username')}")
    print(f"Bio      : {'set' if profile.get('summary') else 'MISSING'}")
    print(f"Website  : {profile.get('website_url') or 'MISSING'}")
    print(f"Twitter  : {profile.get('twitter_username') or 'not set'}")
    print(f"GitHub   : {profile.get('github_username') or 'not set'}")

    suggestions = []
    if not profile.get('summary'):
        suggestions.append("Add a bio at dev.to/settings — appears on every article byline")
    if not profile.get('website_url'):
        suggestions.append("Add website (homesight.live) in dev.to/settings — free backlink on every article")

    articles = [a for a in articles if not a.get('title', '').startswith('[')]
    if articles:
        total_views     = sum(a.get('page_views_count', 0) for a in articles)
        total_reactions = sum(a.get('reactions_count', 0) for a in articles)
        print(f"\nArticles : {len(articles)} published | {total_views} total views | {total_reactions} total reactions\n")
        print(f"  {'Title':<48} {'Views':>6} {'Reacts':>7} {'Cover':>6} {'Canonical':>10}")
        print("  " + "-" * 82)
        for a in articles:
            title        = a.get('title', '')[:46]
            views        = a.get('page_views_count', 0)
            reactions    = a.get('reactions_count', 0)
            has_cover    = bool(a.get('cover_image'))
            has_canonical = bool(a.get('canonical_url'))
            print(f"  {title:<48} {views:>6} {reactions:>7} {'YES' if has_cover else 'NO':>6} {'YES' if has_canonical else 'NO':>10}")
            if not has_cover:
                suggestions.append(f"'{title[:36]}' — add cover image (higher CTR)")
            if not has_canonical:
                suggestions.append(f"'{title[:36]}' — set canonical_url to Medium article URL (SEO)")

        tag_counts = {}
        for a in articles:
            for tag in a.get('tag_list', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_tags:
            print(f"\n  Top tags: {', '.join(f'{t}({c})' for t, c in top_tags)}")
    else:
        print("\n  No published articles found.")

    if suggestions:
        print("\nSuggestions:")
        for s in suggestions:
            print(f"  • {s}")
    else:
        print("\nAll clear.")


def audit_hashnode():
    if not HN_KEY or not HN_PUB_ID:
        print("\nMissing HASHNODE_API_KEY or HASHNODE_PUB_ID — skipping Hashnode audit")
        return

    query = """
    query AuditPub($pubId: ObjectId!) {
      publication(id: $pubId) {
        posts(first: 20) {
          edges {
            node {
              title
              views
              reactionCount
              coverImage { url }
              canonicalUrl
            }
          }
        }
      }
      me {
        username
        bio { text }
        profilePicture
        socialMediaLinks { website }
      }
    }
    """
    r = requests.post(
        "https://gql.hashnode.com/",
        headers={"Authorization": f"Bearer {HN_KEY}", "Content-Type": "application/json"},
        json={"query": query, "variables": {"pubId": HN_PUB_ID}},
        timeout=30,
    )
    if not r.text.strip():
        print(f"\n=== Hashnode ===\nEmpty response (HTTP {r.status_code}) — check HASHNODE_API_KEY")
        return
    try:
        data = r.json()
    except Exception:
        print(f"\n=== Hashnode ===\nHTTP {r.status_code} — got HTML instead of JSON (auth rejected or wrong endpoint)")
        print("Check: hashnode.com/settings/developer → regenerate token, update HASHNODE_API_KEY")
        return
    if "errors" in data:
        print(f"\n=== Hashnode ===\nAudit query failed: {data['errors']}")
        return

    me   = data.get("data", {}).get("me", {})
    pub  = data.get("data", {}).get("publication", {})
    posts = [e["node"] for e in (pub.get("posts", {}).get("edges") or [])]

    print("\n=== Hashnode ===")
    print(f"Username : @{me.get('username')}")
    bio_text = (me.get("bio") or {}).get("text", "")
    print(f"Bio      : {'set' if bio_text else 'MISSING'}")
    print(f"Avatar   : {'set' if me.get('profilePicture') else 'MISSING'}")
    website = (me.get("socialMediaLinks") or {}).get("website", "")
    print(f"Website  : {website or 'MISSING'}")

    suggestions = []
    if not bio_text:
        suggestions.append("Add bio at hashnode.com/settings")
    if not me.get("profilePicture"):
        suggestions.append("Add profile photo at hashnode.com/settings")
    if not website:
        suggestions.append("Add website (homesight.live) at hashnode.com/settings")

    if posts:
        total_views     = sum(p.get('views', 0) for p in posts)
        total_reactions = sum(p.get('reactionCount', 0) for p in posts)
        print(f"\nArticles : {len(posts)} | {total_views} total views | {total_reactions} total reactions\n")
        print(f"  {'Title':<48} {'Views':>6} {'Reacts':>7} {'Cover':>6} {'Canonical':>10}")
        print("  " + "-" * 82)
        for p in posts:
            title         = p.get('title', '')[:46]
            views         = p.get('views', 0)
            reactions     = p.get('reactionCount', 0)
            has_cover     = bool((p.get('coverImage') or {}).get('url'))
            has_canonical = bool(p.get('canonicalUrl'))
            print(f"  {title:<48} {views:>6} {reactions:>7} {'YES' if has_cover else 'NO':>6} {'YES' if has_canonical else 'NO':>10}")
            if not has_cover:
                suggestions.append(f"'{title[:36]}' — add cover image")
            if not has_canonical:
                suggestions.append(f"'{title[:36]}' — set canonicalUrl to Medium article URL (SEO)")
    else:
        print("\n  No posts found.")

    if suggestions:
        print("\nSuggestions:")
        for s in suggestions:
            print(f"  • {s}")
    else:
        print("\nAll clear.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crosspost articles to Dev.to + Hashnode, or audit both accounts"
    )
    parser.add_argument("config", nargs="?", help="Path to article JSON config (crosspost mode)")
    parser.add_argument("--audit", "-a", action="store_true", help="Audit both accounts for optimization opportunities")
    args = parser.parse_args()

    if args.audit:
        audit_devto()
        audit_hashnode()
        return

    if not args.config:
        parser.print_help()
        sys.exit(1)

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    body_dir  = os.path.dirname(args.config) or "."
    body_path = os.path.join(body_dir, cfg["body_file"])
    with open(body_path, encoding="utf-8") as f:
        body = f.read()

    title         = cfg["title"]
    canonical     = cfg["canonical_url"]
    cover_image   = cfg.get("cover_image")
    tags_devto    = cfg.get("tags_devto", [])
    tags_hashnode = cfg.get("tags_hashnode", [])

    if not DEVTO_KEY:
        print("Missing DEVTO_API_KEY — skipping Dev.to")
    else:
        post_devto(title, body, tags_devto, canonical, cover_image)

    if not HN_KEY or not HN_PUB_ID:
        print("Missing HASHNODE_API_KEY or HASHNODE_PUB_ID — skipping Hashnode")
    else:
        post_hashnode(title, body, tags_hashnode, canonical, cover_image)


if __name__ == "__main__":
    main()
