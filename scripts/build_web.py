#!/usr/bin/env python3
"""Build the installable web version (PWA) of the clock app as its own small site.

Each app needs its OWN site (its own GitHub Pages address). An app placed in a sub-folder of
another installed web app (e.g. Ai-Tools/apps/…) opens inside that app's window on Android and
can't be installed as a separate home-screen icon.

Usage:
  python3 scripts/build_web.py assets/clock-template.html OUT_DIR --name "Tick Clock" \
      [--back-url "https://you.github.io/Ai-Tools/index.html#apps" --back-label "Ai-Tools"] [--color "#4fd1c5"]

OUT_DIR gets: index.html (install offer on, test hooks removed), manifest.webmanifest (start_url ./?app=1),
sw.js (network-first offline copy), icons/, .nojekyll. Publish OUT_DIR with GitHub Pages.
"""
import argparse, json, re, sys, pathlib, shutil, subprocess

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_app_package import draw_icon, hex_rgb  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template"); ap.add_argument("out")
    ap.add_argument("--name", required=True)
    ap.add_argument("--back-url"); ap.add_argument("--back-label", default="Back")
    ap.add_argument("--color", default="#4fd1c5")
    a = ap.parse_args()
    out = pathlib.Path(a.out); (out / "icons").mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "", a.name.lower()) or "clock"
    s = pathlib.Path(a.template).read_text(encoding="utf-8")
    s = re.sub(r"// TEST-HOOK-START.*?// TEST-HOOK-END", "", s, flags=re.S)
    assert "__clock" not in s, "test hook still present"
    def sub(pat, rep):
        nonlocal s
        s, n = re.subn(pat, rep, s, count=1)
        assert n == 1, pat
    sub(r"serviceWorker:\s*false", "serviceWorker: true")
    sub(r"installPrompt:\s*false", "installPrompt: true")
    sub(r'title:\s*"[^"]*"', 'title: ' + json.dumps(a.name.upper()[:24]))
    sub(r'storageKey:\s*"[^"]*"', f'storageKey: "{slug}.web.v1"')
    if a.back_url:
        sub(r"backLink:\s*null", "backLink: " + json.dumps({"url": a.back_url, "label": a.back_label}))
    s = s.replace("<title>Clock</title>", f"<title>{a.name}</title>")
    s = s.replace('<meta name="theme-color"', '<link rel="manifest" href="manifest.webmanifest">\n'
                  '<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">\n'
                  '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n<meta name="theme-color"', 1)
    (out / "index.html").write_text(s, encoding="utf-8", newline="\n")
    m = re.search(r"<script>(.*)</script>", s, flags=re.S)
    if shutil.which("node") and m:
        chk = out.parent / f".{slug}-check.js"; chk.write_text(m.group(1))
        r = subprocess.run(["node", "--check", str(chk)], capture_output=True, text=True); chk.unlink()
        assert r.returncode == 0, r.stderr
    acc = hex_rgb(a.color)
    for n, sz in [("icon-192", 192), ("icon-512", 512), ("apple-touch-icon", 180)]:
        draw_icon(sz, acc).save(out / "icons" / f"{n}.png", optimize=True)
    draw_icon(512, acc, pad_frac=0.06).save(out / "icons" / "maskable-512.png", optimize=True)
    manifest = {"id": "./", "name": a.name, "short_name": a.name[:12],
                "description": "Clock, world clock, alarms, timer and stopwatch. Works offline.",
                "start_url": "./?app=1", "scope": "./", "display": "standalone", "orientation": "any",
                "background_color": "#0e1116", "theme_color": "#0e1116",
                "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
                          {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    (out / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", newline="\n")
    (out / "sw.js").write_text(f"""// Offline copy for the web version (not used inside the store apps)
const CACHE = '{slug}-v1';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png', 'icons/apple-touch-icon.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('{slug}-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
// Network first: the newest version when online, the saved copy when offline.
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(new Request(e.request.url, {{ cache: 'no-cache', credentials: 'same-origin' }}))
    .then(res => {{ if (res.ok) {{ const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }} return res; }})
    .catch(() => caches.match(e.request, {{ ignoreSearch: true }}).then(r => r || caches.match('index.html'))));
}});
""", newline="\n")
    (out / ".nojekyll").write_text("")
    print(f"Web build of {a.name} in {out}")


if __name__ == "__main__":
    main()
