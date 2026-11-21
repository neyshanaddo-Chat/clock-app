"""Browser tests for the clock template.

Run:  python3 tests/test_template.py [path/to/index.html]
Needs: Python Playwright + Chrome (channel="chrome") or Playwright's Chromium.
Uses Playwright's fake clock so alarms and timers are tested without waiting.
"""
import sys, pathlib, datetime
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "assets/clock-template.html").resolve()
URL = FILE.as_uri()
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))


def launch(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def new_page(browser, start, viewport=(390, 844), tz="Australia/Perth", storage=None):
    ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]}, timezone_id=tz, locale="en-AU")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.clock.install(time=start)
    if storage:
        page.add_init_script(f"localStorage.setItem('clockapp.v1', {storage!r})")
    page.goto(URL)
    page.wait_for_timeout(300)
    return ctx, page, errors


with sync_playwright() as p:
    b = launch(p)
    T0 = datetime.datetime(2026, 11, 23, 6, 58, 0)  # Monday 06:58 local (Perth)

    # 1 Load, clock renders, no errors
    ctx, page, errors = new_page(b, T0)
    page.clock.run_for(1000)
    txt = page.inner_text("#bigTime")
    check("loads without errors", not errors, "; ".join(errors))
    check("clock shows local time 12h", txt.startswith("6:58") and "AM" in txt, txt)
    check("date shown", "Monday" in page.inner_text("#bigDate"), page.inner_text("#bigDate"))

    # 2 24h toggle + persistence
    page.click("#btnSettings"); page.click("#s24"); page.click("#mSettings [data-close]")
    page.clock.run_for(500)
    check("24h format", page.inner_text("#bigTime").startswith("06:58"), page.inner_text("#bigTime"))
    page.reload(); page.wait_for_timeout(300); page.clock.run_for(500)
    check("settings persist on reload", page.inner_text("#bigTime").startswith("06:"), page.inner_text("#bigTime"))
    page.click("#btnSettings"); page.click("#s24"); page.click("#mSettings [data-close]")

    # 3 Alarm: create 07:00 once, rings at 07:00, snooze, rings again, stop
    page.click("nav [data-view=alarm]")
    page.click("#btnAddAlarm")
    page.fill("#aTime", "07:00"); page.fill("#aLabel", "<b>Wake</b>")
    page.click("#aSave")
    check("alarm listed", "7:00" in page.inner_text("#alarmList"))
    check("label escaped", page.locator("#alarmList b").count() == 0 and "<b>Wake</b>" in page.inner_text("#alarmList"))
    check("next alarm on clock tab", "Next alarm 7:00" in page.inner_text("#nextAlarm"), page.inner_text("#nextAlarm"))
    page.clock.run_for(60_000)
    check("not ringing early", not page.is_visible("#ring"))
    page.clock.run_for(61_000)
    check("alarm rings at 07:00", page.is_visible("#ring"))
    check("ring shows label", "<b>Wake</b>" in page.inner_text("#ringLabel"))
    page.click("#ringSnooze")
    check("snooze hides ring", not page.is_visible("#ring"))
    check("snooze listed", "snoozed" in page.inner_text("#alarmList"))
    page.clock.run_for(9 * 60_000 + 2000)
    check("rings again after 9 min snooze", page.is_visible("#ring"))
    page.click("#ringStop")
    st = page.evaluate("__clock.S.alarms[0].on")
    check("one-off alarm turns off after ringing", st is False)

    # 4 Repeat alarm: weekdays, should NOT ring on Saturday
    check("long waits shown in days", page.evaluate("(()=>{const S=__clock.S;S.alarms=[{id:'d',h:6,m:0,days:[6],label:'',on:true,sound:'chime',createdAt:0}];__clock.renderAlarms();return document.querySelector('#alarmList').innerText})()").find(" d ") > 0)
    page.evaluate("""() => { const S=__clock.S; S.alarms=[{id:'r1',h:8,m:0,days:[1,2,3,4,5],label:'Work',on:true,sound:'beep',createdAt:0}]; __clock.save(); __clock.renderAlarms(); }""")
    check("repeat text Weekdays", "Weekdays" in page.inner_text("#alarmList"), page.inner_text("#alarmList"))
    ctx.close()

    sat = datetime.datetime(2026, 11, 28, 7, 59, 30)  # Saturday
    store = '{"alarms":[{"id":"r1","h":8,"m":0,"days":[1,2,3,4,5],"label":"Work","on":true,"sound":"beep","createdAt":0}]}'
    ctx, page, errors = new_page(b, sat, storage=store)
    page.clock.run_for(90_000)
    check("weekday alarm silent on Saturday", not page.is_visible("#ring"))
    nf = page.evaluate("__clock.nextFire(__clock.S.alarms[0]).getDay()")
    check("next weekday alarm is Monday", nf == 1, nf)
    ctx.close()

    # 5 Missed alarm while asleep (within grace) still rings; long-missed doesn't
    store1 = '{"alarms":[{"id":"a","h":7,"m":0,"days":[],"label":"x","on":true,"sound":"chime","createdAt":0}]}'
    ctx, page, errors = new_page(b, datetime.datetime(2026, 11, 23, 7, 1, 0), storage=store1)
    page.clock.run_for(500)
    check("alarm missed by 60s still rings", page.is_visible("#ring"))
    ctx.close()
    ctx, page, errors = new_page(b, datetime.datetime(2026, 11, 23, 7, 30, 0), storage=store1)
    page.clock.run_for(500)
    check("alarm missed by 30 min does not ring late", not page.is_visible("#ring"))
    ctx.close()

    # 6 Timer
    ctx, page, errors = new_page(b, T0)
    page.click("nav [data-view=timer]")
    page.fill("#tH", "0"); page.fill("#tM", "0"); page.fill("#tS", "10"); page.fill("#tLabel", "Tea")
    page.click("#tStart")
    page.clock.run_for(3000)
    check("timer counts down", page.inner_text("#timerText") in ("00:07", "00:08"), page.inner_text("#timerText"))
    page.click("#tStart")  # pause
    page.clock.run_for(5000)
    left = page.inner_text("#timerText")
    check("timer pauses", left in ("00:07", "00:08"), left)
    page.reload(); page.wait_for_timeout(300); page.clock.run_for(300)
    check("paused timer survives reload", page.inner_text("#timerText") == left and page.inner_text("#tStart") == "Resume")
    page.click("#tStart")
    page.clock.run_for(9000)
    check("timer rings at zero", page.is_visible("#ring") and "Tea" in page.inner_text("#ringLabel"))
    page.click("#ringSnooze")  # +1 min
    check("+1 min restarts timer", page.inner_text("#timerText") in ("01:00", "00:59"), page.inner_text("#timerText"))
    page.click("#tReset")
    check("reset returns to setup", page.is_visible("#timerSetup"))
    page.click("#presets [data-preset='60']")
    check("preset starts 1 min", page.inner_text("#timerText") in ("01:00", "00:59"))
    page.click("#tReset")

    # 7 Stopwatch
    page.click("nav [data-view=stopwatch]")
    page.click("#swStart")
    page.clock.run_for(2000); page.click("#swLap")
    page.clock.run_for(5000); page.click("#swLap")
    page.clock.run_for(3000); page.click("#swLap")
    page.click("#swStart")  # stop
    check("stopwatch ~10s", page.inner_text("#swTime").startswith("00:10"), page.inner_text("#swTime"))
    check("3 laps", page.locator("#laps li").count() == 3)
    check("fastest/slowest marked", page.locator("#laps li.best").inner_text().startswith("Lap 1") and page.locator("#laps li.worst").inner_text().startswith("Lap 2"))
    page.clock.run_for(4000)
    check("stopped stopwatch doesn't move", page.inner_text("#swTime").startswith("00:10"))
    page.click("#swLap")  # reset
    check("reset clears", page.inner_text("#swTime").startswith("00:00") and page.locator("#laps li").count() == 0)

    # 8 World clock
    page.click("nav [data-view=world]")
    wl = page.inner_text("#cityList")
    check("default cities shown", "London" in wl and "Tokyo" in wl and "New York" in wl, wl)
    check("Tokyo is 1 h ahead of Perth", "1 h ahead" in wl, wl)
    page.click("#btnAddCity"); page.fill("#citySearch", "sydney")
    page.click("#cityResults [data-add='Australia/Sydney']")
    check("Sydney added, 3 h ahead (Nov DST)", "Sydney" in page.inner_text("#cityList") and "3 h ahead" in page.inner_text("#cityList"))
    page.click("[data-del='Asia/Tokyo']")
    check("city removed", "Tokyo" not in page.inner_text("#cityList"))
    check("India offset 2 h 30 min behind", page.evaluate("__clock.offsetMin('Asia/Kolkata') - __clock.offsetMin('Australia/Perth')") == -150)

    # 9 Keyboard shortcuts + nightstand
    page.keyboard.press("1")
    check("key 1 -> clock", page.is_visible("#view-clock"))
    page.keyboard.press("n")
    check("nightstand on", page.is_visible("#night"))
    page.keyboard.press("Escape")
    check("nightstand off", not page.is_visible("#night"))

    # 10 Themes + corrupted storage
    page.click("#btnSettings"); page.select_option("#sTheme", "light"); page.click("#mSettings [data-close]")
    check("light theme", page.evaluate("document.body.dataset.theme") == "light")
    check("no errors during session", not errors, "; ".join(errors))
    ctx.close()

    bad = '{"settings":{"theme":"<x>","volume":999,"snooze":7},"cities":["Not/AZone","Asia/Tokyo"],"alarms":[{"h":99,"m":-4,"days":[9,1],"label":"\\u0007hi"}],"sw":{"laps":["x",5]}}'
    ctx, page, errors = new_page(b, T0, storage=bad)
    s = page.evaluate("__clock.S")
    check("corrupt storage sanitised", s["settings"]["theme"] == "dark" and s["settings"]["volume"] == 100 and s["settings"]["snooze"] == 9
          and s["cities"] == ["Asia/Tokyo"] and s["alarms"][0]["h"] == 23 and s["alarms"][0]["m"] == 0 and s["alarms"][0]["days"] == [1]
          and s["alarms"][0]["label"] == "hi" and s["sw"]["laps"] == [5], s)
    check("no errors with corrupt storage", not errors, "; ".join(errors))
    ctx.close()

    # 11 Layout: small landscape phone and desktop, no horizontal overflow
    for vp in [(844, 390), (667, 375), (1280, 800), (320, 568)]:
        ctx, page, errors = new_page(b, T0, viewport=vp)
        for v in ["clock", "world", "alarm", "timer", "stopwatch"]:
            page.click(f"nav [data-view={v}]")
            ow = page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
            if ow:
                break
        check(f"no horizontal overflow {vp[0]}x{vp[1]}", not ow, v)
        ctx.close()

    # 12 Native scheduling bridge (mock Capacitor LocalNotifications)
    ctx = b.new_context(timezone_id="Australia/Perth")
    page = ctx.new_page()
    page.clock.install(time=T0)
    page.add_init_script("""
      window.__sched=[];
      window.Capacitor={Plugins:{LocalNotifications:{
        checkPermissions:async()=>({display:'granted'}), requestPermissions:async()=>({display:'granted'}),
        getPending:async()=>({notifications:[]}), cancel:async()=>{},
        schedule:async(o)=>{window.__sched=o.notifications;}}}};
      localStorage.setItem('clockapp.v1', JSON.stringify({alarms:[{id:'w',h:7,m:30,days:[1,2,3,4,5],label:'Work',on:true,sound:'chime',createdAt:0},{id:'o',h:9,m:0,days:[],label:'Once',on:true,sound:'chime',createdAt:0}]}));
    """)
    page.goto(URL); page.wait_for_timeout(300); page.clock.run_for(500)
    n = page.evaluate("window.__sched.length")
    check("native: weekday alarm scheduled 5x + one-off 1x", n == 6, n)
    check("web-only note hidden in app", page.inner_text("#alarmNote") == "")
    ctx.close()
    b.close()

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
