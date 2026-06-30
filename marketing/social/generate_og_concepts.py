"""
generate_og_concepts.py — Render 4 HomeSight OG image concepts and open them for review.
"""
import asyncio, base64, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).parent / "og_concepts"
OUT_DIR.mkdir(exist_ok=True)
SITE = "https://homesight.live"

# ── Concept A: Dark gradient overlay on live map ──────────────────────────────

def concept_a(map_b64):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;
     font-family:-apple-system,'Segoe UI',sans-serif}}
.bg{{position:absolute;inset:0;
     background:url('data:image/png;base64,{map_b64}') center/cover no-repeat}}
.grad{{position:absolute;inset:0;
       background:linear-gradient(105deg,
         rgba(7,9,18,0.97) 0%,
         rgba(7,9,18,0.92) 28%,
         rgba(7,9,18,0.65) 52%,
         rgba(7,9,18,0.15) 72%,
         transparent 88%)}}
.content{{position:absolute;left:64px;top:50%;transform:translateY(-50%)}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:0.18em;
          text-transform:uppercase;color:#22c55e;margin-bottom:16px}}
.name{{font-size:80px;font-weight:800;letter-spacing:-3px;line-height:1;
       color:#fff;white-space:nowrap}}
.bar{{width:64px;height:4px;background:#22c55e;border-radius:2px;margin:22px 0}}
.tag{{font-size:20px;font-weight:400;color:rgba(255,255,255,0.68);
      line-height:1.55;max-width:360px}}
.url{{margin-top:28px;font-size:15px;font-weight:600;
      color:#22c55e;letter-spacing:0.06em}}
</style></head><body>
<div class="bg"></div>
<div class="grad"></div>
<div class="content">
  <div class="eyebrow">Real estate data, simplified</div>
  <div class="name">HomeSight</div>
  <div class="bar"></div>
  <div class="tag">26,000+ ZIP codes.<br>10 years of home value history.<br>Free. No account.</div>
  <div class="url">homesight.live</div>
</div>
</body></html>"""


# ── Concept B: 60/40 split — live panel left, dark stats right ────────────────

def concept_b(panel_b64):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:630px;overflow:hidden;display:flex;
     font-family:-apple-system,'Segoe UI',sans-serif}}
.left{{width:62%;position:relative;
       background:url('data:image/png;base64,{panel_b64}') left center/cover no-repeat}}
.left-grad{{position:absolute;inset:0;
            background:linear-gradient(to right,transparent 70%,#0a0d1a 100%)}}
.right{{width:38%;background:#0a0d1a;
        display:flex;flex-direction:column;justify-content:center;padding:52px 48px}}
.logo{{font-size:34px;font-weight:800;letter-spacing:-1px;color:#fff}}
.logo span{{color:#22c55e}}
.divider{{width:36px;height:3px;background:#22c55e;border-radius:2px;margin:18px 0}}
.tagline{{font-size:15px;color:rgba(255,255,255,0.58);line-height:1.7;
          max-width:260px}}
.stat-box{{margin-top:28px;padding:16px 18px;
           background:rgba(34,197,94,0.08);
           border:1px solid rgba(34,197,94,0.25);border-radius:10px}}
.stat-num{{font-size:38px;font-weight:800;color:#22c55e;letter-spacing:-1px}}
.stat-label{{font-size:11px;color:rgba(255,255,255,0.42);
             margin-top:3px;letter-spacing:0.04em;text-transform:uppercase}}
.url{{margin-top:28px;font-size:13px;font-weight:700;
      color:rgba(255,255,255,0.32);letter-spacing:0.08em}}
.arrow{{color:#22c55e;margin-left:4px}}
</style></head><body>
<div class="left">
  <div class="left-grad"></div>
</div>
<div class="right">
  <div class="logo">Home<span>Sight</span></div>
  <div class="divider"></div>
  <div class="tagline">ZIP-level home values for every US market and UK postcode. Free. No account.</div>
  <div class="stat-box">
    <div class="stat-num">+83.2%</div>
    <div class="stat-label">national median 10yr appreciation</div>
  </div>
  <div class="url">homesight.live <span class="arrow">→</span></div>
</div>
</body></html>"""


# ── Concept C: Minimal dark typographic (Linear / Vercel style) ───────────────

def concept_c():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;background:#070912;
     font-family:-apple-system,'Segoe UI',sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;
     position:relative}
/* dot grid */
.grid{position:absolute;inset:0;
      background-image:radial-gradient(circle,rgba(255,255,255,0.07) 1px,transparent 1px);
      background-size:32px 32px}
/* green center glow */
.glow{position:absolute;width:700px;height:500px;
      background:radial-gradient(ellipse at center,rgba(34,197,94,0.09) 0%,transparent 68%);
      top:50%;left:50%;transform:translate(-50%,-50%)}
/* corner accents */
.corner{position:absolute;width:32px;height:32px;border-color:rgba(34,197,94,0.35);border-style:solid}
.tl{top:36px;left:36px;border-width:2px 0 0 2px}
.tr{top:36px;right:36px;border-width:2px 2px 0 0}
.bl{bottom:36px;left:36px;border-width:0 0 2px 2px}
.br{bottom:36px;right:36px;border-width:0 2px 2px 0}
.wordmark{position:relative;z-index:10;text-align:center}
.word{font-size:96px;font-weight:800;letter-spacing:-4px;line-height:1;color:#fff}
.word em{font-style:normal;color:#22c55e}
.sep{position:relative;z-index:10;
     width:480px;height:1px;margin:24px auto;
     background:linear-gradient(to right,transparent,rgba(255,255,255,0.15),transparent)}
.sub{position:relative;z-index:10;text-align:center;
     font-size:17px;font-weight:400;color:rgba(255,255,255,0.38);
     letter-spacing:0.14em;text-transform:uppercase}
.sub span{color:rgba(34,197,94,0.7)}
.badge{position:absolute;bottom:40px;right:50px;z-index:10;
       padding:8px 16px;border:1px solid rgba(255,255,255,0.1);border-radius:20px;
       font-size:12px;color:rgba(255,255,255,0.35);letter-spacing:0.06em}
</style></head><body>
<div class="grid"></div>
<div class="glow"></div>
<div class="corner tl"></div>
<div class="corner tr"></div>
<div class="corner bl"></div>
<div class="corner br"></div>
<div class="wordmark"><div class="word">Home<em>Sight</em></div></div>
<div class="sep"></div>
<div class="sub">Home values &nbsp;<span>·</span>&nbsp; Any ZIP &nbsp;<span>·</span>&nbsp; Free</div>
<div class="badge">homesight.live</div>
</body></html>"""


# ── Concept D: Map screenshot with heat-map filter + bottom brand bar ─────────

def concept_d(map_b64):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;
     font-family:-apple-system,'Segoe UI',sans-serif}}
/* map with vivid colour grading to suggest choropleth */
.bg{{position:absolute;inset:0;
     background:url('data:image/png;base64,{map_b64}') center/cover no-repeat;
     filter:saturate(2.2) hue-rotate(20deg) brightness(0.85) contrast(1.15)}}
/* vignette */
.vignette{{position:absolute;inset:0;
           background:radial-gradient(ellipse at 50% 40%,transparent 40%,rgba(0,0,0,0.55) 100%)}}
/* heavy bottom dark bar */
.bottom-grad{{position:absolute;inset:0;
              background:linear-gradient(to top,rgba(5,7,15,0.92) 0%,rgba(5,7,15,0.5) 30%,transparent 55%)}}
/* branding row */
.brand{{position:absolute;bottom:0;left:0;right:0;
        padding:28px 52px;display:flex;justify-content:space-between;align-items:flex-end}}
.name{{font-size:58px;font-weight:800;letter-spacing:-2px;color:#fff;
       text-shadow:0 2px 24px rgba(0,0,0,0.6)}}
.tagline{{font-size:16px;color:rgba(255,255,255,0.55);margin-top:4px}}
.legend{{display:flex;flex-direction:column;gap:7px;align-items:flex-end;
         padding-bottom:6px}}
.legend-row{{display:flex;gap:12px}}
.chip{{display:flex;align-items:center;gap:6px;
       font-size:12px;font-weight:600;color:rgba(255,255,255,0.65)}}
.dot{{width:9px;height:9px;border-radius:50%}}
.legend-title{{font-size:11px;color:rgba(255,255,255,0.3);
               letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;text-align:right}}
</style></head><body>
<div class="bg"></div>
<div class="vignette"></div>
<div class="bottom-grad"></div>
<div class="brand">
  <div>
    <div class="name">HomeSight</div>
    <div class="tagline">ZIP-level home value appreciation &nbsp;·&nbsp; Free &nbsp;·&nbsp; No account</div>
  </div>
  <div class="legend">
    <div class="legend-title">10yr appreciation</div>
    <div class="legend-row">
      <div class="chip"><div class="dot" style="background:#3b82f6"></div>+50%</div>
      <div class="chip"><div class="dot" style="background:#22c55e"></div>+100%</div>
      <div class="chip"><div class="dot" style="background:#eab308"></div>+200%</div>
      <div class="chip"><div class="dot" style="background:#ef4444"></div>+300%</div>
    </div>
  </div>
</div>
</body></html>"""


# ── Runner ────────────────────────────────────────────────────────────────────

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()

        HIDE_BRAND_JS = """
            const s = document.createElement('style');
            s.textContent = '#header h1, #landing-brand { opacity: 0 !important; }';
            document.head.appendChild(s);
        """

        print("Loading homesight.live for map screenshots...")
        await page.set_viewport_size({"width": 1200, "height": 630})
        await page.goto(SITE, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4500)  # let map tiles load
        await page.evaluate(HIDE_BRAND_JS)

        map_bytes = await page.screenshot(full_page=False)
        map_b64   = base64.b64encode(map_bytes).decode()
        print("  map screenshot done")

        await page.wait_for_function("typeof openPanel === 'function'", timeout=15000)
        await page.evaluate("openPanel('28208')")
        await page.wait_for_function(
            "document.getElementById('panel-loc') && "
            "document.getElementById('panel-loc').textContent.trim().length > 0",
            timeout=15000
        )
        await page.wait_for_timeout(3500)
        panel_bytes = await page.screenshot(full_page=False)
        panel_b64   = base64.b64encode(panel_bytes).decode()
        print("  panel screenshot done (ZIP 28208 - Charlotte)\n")

        concepts = [
            ("A", concept_a(map_b64),   "Dark gradient overlay + left-side brand"),
            ("B", concept_b(panel_b64), "60/40 split — live panel + dark stats card"),
            ("C", concept_c(),          "Minimal dark typographic (Linear/Vercel style)"),
            ("D", concept_d(map_b64),   "Heat-map filter + bottom brand bar"),
        ]

        generated = []
        for letter, html, desc in concepts:
            html_path = OUT_DIR / f"concept_{letter}.html"
            img_path  = OUT_DIR / f"concept_{letter}.png"

            html_path.write_text(html, encoding="utf-8")
            abs_path = str(html_path.resolve()).replace("\\", "/")

            await page.set_viewport_size({"width": 1200, "height": 630})
            await page.goto(f"file:///{abs_path}", wait_until="load")
            await page.wait_for_timeout(400)
            await page.screenshot(path=str(img_path), full_page=False)
            print(f"  Concept {letter}: {desc}")
            print(f"    -> {img_path}")
            generated.append(img_path)

        await browser.close()

    print("\nOpening all 4 concepts...")
    for img_path in generated:
        subprocess.Popen(["explorer", str(img_path)])

if __name__ == "__main__":
    asyncio.run(main())
