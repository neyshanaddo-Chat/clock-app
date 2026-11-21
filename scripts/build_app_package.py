#!/usr/bin/env python3
"""Package the clock template as a Capacitor 8 project for Google Play and the App Store.

Usage:
  python3 scripts/build_app_package.py assets/clock-template.html OUT_DIR \
      --name "Tick Clock" --app-id com.example.tickclock [--color "#4fd1c5"] [--no-screenshots]

Produces:
  OUT_DIR/www/            app (test hooks stripped, service worker on), manifest, sw.js, icons
  OUT_DIR/assets/         icon.png (1024) + splash.png (2732) for @capacitor/assets
  OUT_DIR/store/          screenshots (Android phone, 6.9" iPhone, 13" iPad), feature graphic,
                          512 Play icon, listing.md, privacy-policy.html
  OUT_DIR/scripts/patch-native.mjs   Android permissions + iOS privacy manifest (run after `cap add`)
  OUT_DIR/package.json, capacitor.config.json, RELEASE-GUIDE.md
Needs: Python 3 + Pillow; Playwright + Chrome for screenshots (skipped with a warning if missing).
"""
import argparse, json, re, shutil, subprocess, sys, pathlib, datetime

SKILL = pathlib.Path(__file__).resolve().parent.parent
APPDOCS = SKILL / "assets" / "app"


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build_www(src, www, name, app_id):
    html = src.read_text(encoding="utf-8")
    for a, b in [("// TEST-HOOK-START", "// TEST-HOOK-END")]:
        if a not in html or b not in html:
            fail(f"template is missing the {a} / {b} markers")
        html = re.sub(re.escape(a) + r".*?" + re.escape(b), "", html, flags=re.S)
    if "__clock" in html:
        fail("test hook still present after stripping")
    html, n = re.subn(r'serviceWorker:\s*false', 'serviceWorker: true', html)
    if n != 1:
        fail("could not switch CONFIG.serviceWorker on")
    title = name.upper()[:24].replace('"', "")
    html = re.sub(r'title:\s*"[^"]*"', f'title: "{title}"', html, count=1)
    key = "clock." + re.sub(r"[^a-z0-9.]", "", app_id.lower()) + ".v1"
    html = re.sub(r'storageKey:\s*"[^"]*"', f'storageKey: "{key}"', html, count=1)
    html = html.replace("<title>Clock</title>", f"<title>{name}</title>")
    html = html.replace('<meta name="theme-color"', '<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icons/icon-180.png">\n<meta name="theme-color"', 1)
    www.mkdir(parents=True, exist_ok=True)
    (www / "index.html").write_text(html, encoding="utf-8")
    # syntax-check the script with node if available
    m = re.search(r"<script>(.*)</script>", html, flags=re.S)
    if shutil.which("node") and m:
        tmp = www.parent / ".syntax-check.js"
        tmp.write_text(m.group(1), encoding="utf-8")
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        tmp.unlink()
        if r.returncode:
            fail("app script has a syntax error:\n" + r.stderr)
    manifest = {
        "name": name, "short_name": name[:12], "start_url": "./index.html", "display": "standalone",
        "background_color": "#0e1116", "theme_color": "#0e1116", "orientation": "any",
        "icons": [{"src": f"icons/icon-{s}.png", "sizes": f"{s}x{s}", "type": "image/png", "purpose": "any maskable"} for s in (192, 512)],
    }
    (www / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2))
    ver = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    (www / "sw.js").write_text(f"""const C="clock-{ver}";const F=["./","./index.html","./manifest.webmanifest","./icons/icon-192.png","./icons/icon-512.png"];
self.addEventListener("install",e=>{{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting();}});
self.addEventListener("activate",e=>{{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim();}});
self.addEventListener("fetch",e=>{{if(e.request.method!=="GET")return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));}});
""")
    return key


def draw_icon(size, accent, bg=(14, 17, 22), pad_frac=0.0):
    from PIL import Image, ImageDraw
    import math
    S = size * 4
    im = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(im)
    cx = cy = S / 2
    r = S * (0.36 - pad_frac)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(31, 37, 48), outline=accent, width=int(S * 0.03))
    for i in range(12):
        a = i * math.pi / 6
        r1, r2 = r * (0.78 if i % 3 == 0 else 0.84), r * 0.9
        d.line([cx + r1 * math.sin(a), cy - r1 * math.cos(a), cx + r2 * math.sin(a), cy - r2 * math.cos(a)],
               fill=(233, 237, 243), width=int(S * (0.018 if i % 3 == 0 else 0.009)))
    def hand(deg, length, w, col):
        a = math.radians(deg)
        d.line([cx, cy, cx + length * math.sin(a), cy - length * math.cos(a)], fill=col, width=int(w))
    hand(300, r * 0.5, S * 0.035, (233, 237, 243))   # hour ~10
    hand(60, r * 0.72, S * 0.025, (233, 237, 243))   # minute ~10 past
    hand(180, r * 0.8, S * 0.01, (246, 173, 85))
    cr = S * 0.025
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(246, 173, 85))
    return im.resize((size, size), Image.LANCZOS)


def make_images(out, www, name, accent):
    from PIL import Image, ImageDraw, ImageFont
    acc = hex_rgb(accent)
    (www / "icons").mkdir(parents=True, exist_ok=True)
    for s in (180, 192, 512):
        draw_icon(s, acc).save(www / "icons" / f"icon-{s}.png")
    (out / "assets").mkdir(exist_ok=True)
    draw_icon(1024, acc).save(out / "assets" / "icon.png")
    splash = Image.new("RGB", (2732, 2732), (14, 17, 22))
    ic = draw_icon(700, acc)
    splash.paste(ic, ((2732 - 700) // 2, (2732 - 700) // 2))
    splash.save(out / "assets" / "splash.png")
    st = out / "store"
    st.mkdir(exist_ok=True)
    draw_icon(512, acc).save(st / "play-icon-512.png")
    fg = Image.new("RGB", (1024, 500), (14, 17, 22))
    fg.paste(draw_icon(360, acc), (70, 70))
    dd = ImageDraw.Draw(fg)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        small = ImageFont.truetype("DejaVuSans.ttf", 30)
    except Exception:
        font = small = ImageFont.load_default()
    dd.text((480, 170), name, fill=(233, 237, 243), font=font)
    dd.text((482, 260), "Clock · Alarm · Timer · Stopwatch", fill=acc, font=small)
    fg.save(st / "feature-graphic-1024x500.png")


SCENES = [("clock", None), ("alarm", None), ("timer", "run"), ("stopwatch", None), ("world", None), ("clock", "settings")]
DEVICES = {"android-phone": (1080, 1920, 3), "iphone-6.9": (1320, 2868, 3), "ipad-13": (2064, 2752, 2)}


def screenshots(out, www, key):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("WARNING: Playwright not installed - store screenshots skipped")
        return
    seed = {"alarms": [{"id": "a", "h": 6, "m": 30, "days": [1, 2, 3, 4, 5], "label": "Wake up", "on": True, "sound": "chime", "createdAt": 0},
                       {"id": "b", "h": 8, "m": 0, "days": [0, 6], "label": "Sleep in", "on": True, "sound": "gentle", "createdAt": 0},
                       {"id": "c", "h": 17, "m": 45, "days": [], "label": "School pick-up", "on": False, "sound": "beep", "createdAt": 0}],
            "cities": ["Europe/London", "America/New_York", "Asia/Tokyo", "Australia/Sydney"],
            "sw": {"acc": 154230, "laps": [48110, 99870, 154230]}}
    url = (www / "index.html").resolve().as_uri()
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            b = p.chromium.launch()
        for dev, (w, h, dpr) in DEVICES.items():
            ctx = b.new_context(viewport={"width": w // dpr, "height": h // dpr}, device_scale_factor=dpr, timezone_id="Australia/Perth", has_touch=True)
            for i, (view, extra) in enumerate(SCENES, 1):
                pg = ctx.new_page()
                pg.clock.install(time=datetime.datetime(2026, 11, 23, 6, 12, 8))
                pg.add_init_script(f"localStorage.setItem({key!r}, {json.dumps(json.dumps(seed))})")
                pg.add_init_script("window.Capacitor = window.Capacitor || {}")  # show the app's look (no browser-only note)
                pg.goto(url)
                pg.wait_for_timeout(300)
                pg.click(f"nav [data-view={view}]")
                if extra == "run":
                    pg.click("#presets [data-preset='600']")
                    pg.clock.run_for(147000)
                if extra == "settings":
                    pg.click("#btnSettings")
                pg.clock.run_for(400)
                pg.screenshot(path=str(out / "store" / f"{dev}-{i}-{view}{'-' + extra if extra else ''}.png"))
                pg.close()
            ctx.close()
        b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template"); ap.add_argument("out")
    ap.add_argument("--name", required=True); ap.add_argument("--app-id", required=True)
    ap.add_argument("--color", default="#4fd1c5"); ap.add_argument("--no-screenshots", action="store_true")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){2,}", a.app_id):
        fail("--app-id must be reverse-domain, lower case, e.g. com.yourname.clock")
    if re.search(r"\b(apple|google|samsung|casio|rolex)\b", a.name, re.I):
        fail("use an original app name, not another company's brand")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", a.color):
        fail("--color must look like #4fd1c5")
    src = pathlib.Path(a.template).resolve()
    out = pathlib.Path(a.out).resolve()
    if out.exists() and any(out.iterdir()):
        fail(f"{out} is not empty - choose a new folder")
    out.mkdir(parents=True, exist_ok=True)
    www = out / "www"
    key = build_www(src, www, a.name, a.app_id)
    make_images(out, www, a.name, a.color)
    pkg = {
        "name": re.sub(r"[^a-z0-9-]", "-", a.name.lower()).strip("-") or "clock-app", "version": "1.0.0", "private": True,
        "scripts": {"sync": "npx cap sync", "patch": "node scripts/patch-native.mjs",
                    "assets": "npx @capacitor/assets generate --iconBackgroundColor '#0e1116' --splashBackgroundColor '#0e1116'"},
        "dependencies": {"@capacitor/core": "^8.0.0", "@capacitor/android": "^8.0.0", "@capacitor/ios": "^8.0.0", "@capacitor/local-notifications": "^8.0.0"},
        "devDependencies": {"@capacitor/cli": "^8.0.0", "@capacitor/assets": "^3.0.5"},
    }
    (out / "package.json").write_text(json.dumps(pkg, indent=2))
    cap = {"appId": a.app_id, "appName": a.name, "webDir": "www",
           "plugins": {"LocalNotifications": {"iconColor": a.color, "presentationOptions": ["sound", "banner", "list"]}}}
    (out / "capacitor.config.json").write_text(json.dumps(cap, indent=2))
    (out / "scripts").mkdir(exist_ok=True)
    shutil.copy(APPDOCS / "patch-native.mjs", out / "scripts" / "patch-native.mjs")
    shutil.copy(APPDOCS / "PrivacyInfo.xcprivacy", out / "scripts" / "PrivacyInfo.xcprivacy")
    today = datetime.date.today().isoformat()
    for doc, dest in [("RELEASE-GUIDE.md", out / "RELEASE-GUIDE.md"), ("listing.md", out / "store" / "listing.md"), ("privacy-policy.html", out / "store" / "privacy-policy.html")]:
        t = (APPDOCS / "docs" / doc).read_text(encoding="utf-8")
        t = t.replace("{{APP_NAME}}", a.name).replace("{{APP_ID}}", a.app_id).replace("{{DATE}}", today)
        dest.write_text(t, encoding="utf-8")
    if not a.no_screenshots:
        screenshots(out, www, key)
    print(f"Built {a.name} ({a.app_id}) in {out}")
    print("Next: read RELEASE-GUIDE.md (npm install -> npx cap add android/ios -> npm run patch -> npm run assets -> npx cap sync)")


if __name__ == "__main__":
    main()
