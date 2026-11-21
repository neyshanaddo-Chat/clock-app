"""Tests for the web (PWA) build: install offer, Download link, back link.
Run: python3 scripts/build_web.py assets/clock-template.html /tmp/webtest --name "Tick Clock" --back-url "https://example.com/Ai-Tools/index.html#apps" --back-label "Ai-Tools"
     python3 tests/test_web.py /tmp/webtest
"""
import sys, subprocess, time, pathlib
from playwright.sync_api import sync_playwright
DIR = pathlib.Path(sys.argv[1]).resolve()
AND = "Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"
IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
res = []
def check(n, c): res.append(c); print(("PASS " if c else "FAIL ") + n)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8791", "--directory", str(DIR)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
U = "http://localhost:8791/"
FAKE_PROMPT = """window.__prompted=0; window.addEventListener('load',()=>setTimeout(()=>{const e=new Event('beforeinstallprompt',{cancelable:true});
 e.prompt=()=>{window.__prompted++;return Promise.resolve()}; e.userChoice=Promise.resolve({outcome:'accepted'}); window.dispatchEvent(e);},100));"""
STANDALONE = "const _mm=window.matchMedia.bind(window); window.matchMedia=q=>/display-mode: standalone/.test(q)?{matches:true,addEventListener(){},addListener(){}}:_mm(q);"
try:
    with sync_playwright() as p:
        try: b = p.chromium.launch(channel="chrome")
        except Exception: b = p.chromium.launch()
        def ctx(ua): return b.new_context(viewport={"width": 390, "height": 844}, user_agent=ua, is_mobile=True, has_touch=True)
        # Android Chrome: real Install button
        c = ctx(AND); pg = c.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(FAKE_PROMPT); pg.goto(U); pg.wait_for_timeout(1500)
        check("android: Get the app offer appears", pg.is_visible("#mInstall"))
        check("android: Install button prompts", pg.locator("#installRight button").inner_text().endswith("Install"))
        pg.click("#installRight button"); pg.wait_for_timeout(300)
        check("android: install prompt called", pg.evaluate("window.__prompted") == 1)
        check("manifest linked + sw registered", pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>!!r)") and pg.evaluate("document.querySelector('link[rel=manifest]').href").endswith("manifest.webmanifest"))
        check("no page errors", not errs)
        c.close()
        # iPhone Safari: steps; Never show again; ?install=1 overrides
        c = ctx(IOS); pg = c.new_page(); pg.goto(U); pg.wait_for_timeout(1200)
        check("iphone: Share → Add to Home Screen steps", pg.is_visible("#mInstall") and "Add to Home Screen" in pg.inner_text("#installHow"))
        pg.check("#installNever"); pg.click("#installLater")
        pg.goto(U); pg.wait_for_timeout(1200)
        check("never show again respected", not pg.is_visible("#mInstall") and pg.is_visible("#btnInstall"))
        pg.goto(U + "?install=1"); pg.wait_for_timeout(1200)
        check("?install=1 (Download button) always shows it", pg.is_visible("#mInstall"))
        c.close()
        # Inside another web app (Ai-Tools app window): Copy link
        c = ctx(AND); pg = c.new_page(); pg.add_init_script(STANDALONE); pg.goto(U + "?from=ai-tools"); pg.wait_for_timeout(1200)
        check("inside another app: explains + Copy link", pg.is_visible("#mInstall") and pg.locator("#installRight button").inner_text() == "Copy link")
        check("back link shown when opened from Ai-Tools", pg.is_visible("#backLink") and pg.inner_text("#backLink") == "‹ Ai-Tools")
        c.close()
        # Installed (own manifest start_url ?app=1): no offer, no back link
        c = ctx(AND); pg = c.new_page(); pg.add_init_script(STANDALONE); pg.goto(U + "?app=1"); pg.wait_for_timeout(1200)
        check("installed app: no offer, no install button", not pg.is_visible("#mInstall") and not pg.is_visible("#btnInstall"))
        c.close()
        # Plain visit (not from Ai-Tools): no back link
        c = ctx(AND); pg = c.new_page(); pg.goto(U); pg.wait_for_timeout(800)
        check("no back link on a direct visit", not pg.is_visible("#backLink"))
        c.close(); b.close()
finally:
    srv.terminate()
print(f"\n{sum(res)}/{len(res)} passed"); sys.exit(0 if all(res) else 1)
