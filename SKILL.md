---
name: clock-app
description: Use when someone wants a clock, alarm clock, world clock, countdown timer or stopwatch app (or all of them in one), a customised/branded version, or wants it packaged for Google Play / the App Store — e.g. "make me a clock app", "alarm clock for my bedside tablet", "timer app in our café colours", "put my clock app on the app stores".
status: DRAFT v0.1. All-in-one template (Clock + nightstand mode, World clock, Alarms with repeat/snooze, Timer, Stopwatch with laps), 4 themes, Capacitor 8 packaging with native alarm notifications. Template tested with 51 automated browser checks; not yet tested on real phones; not yet cleared for commercial release.
---

# Clock App Builder

Builds a polished clock app as **one self-contained HTML file**: no install, no libraries, no tracking. Five tabs: **Clock, World, Alarm, Timer, Stopwatch**. It runs in any modern browser, and the build script packages it as an Android and iPhone/iPad app whose alarms still go off when the app is closed.

Always start from the tested template (`assets/clock-template.html`) and customise it. Don't write a new clock from scratch: the template already handles the parts that are easy to get wrong:
- Timers and the stopwatch are based on timestamps, so they stay accurate in the background and after a reload.
- Alarms never ring twice in the same minute, and an alarm missed while the tab was asleep still rings if it's less than 90 s late.
- Time zones and daylight saving come from the browser's `Intl` time-zone data.
- Phone audio unlocks on the first tap.
- Saved data is checked and cleaned up when it loads.

## When to use
- "Make me a clock / alarm clock / world clock / timer / stopwatch app"
- "A bedside clock for my old tablet" (Nightstand mode + Keep screen on)
- "In our brand colours" / "for our gym, with a 45-second preset"
- "Make it an app for Google Play / the App Store"
- **Not for:** medical or medication reminders where a missed alert could cause harm (say alarms are best-effort and suggest a dedicated, certified reminder app), safety or industrial timing, or copying another company's clock design or branding.

## Step 0: Build first, ask later
For "make a clock app", **build the default immediately**, then offer changes. Only ask when the request hints at something:

| Option | Default | Where |
|---|---|---|
| Title | CLOCK | `CONFIG.title` (use an original name for anything published) |
| Tabs | All five | Hide a tab by removing its `nav` button and `section` (keep the IDs others rely on: test after) |
| Theme | Dark | `DEFAULTS.theme`; add a theme to `THEMES` + a `[data-theme]` CSS block |
| 12/24-hour | 12-hour | `DEFAULTS.h24` (Australia/US usually 12h; much of Europe 24h) |
| Timer presets | 1, 3, 5, 10, 15, 30 min, 1 h | `CONFIG.timerPresets` (seconds) |
| Default cities | London, New York, Tokyo | `CONFIG.defaultCities` (IANA zone names) |
| Snooze | 9 min | `DEFAULTS.snooze` (must be in `SNOOZES`) |
| Week start | Monday | `DEFAULTS.monday` |

Change `CONFIG.storageKey` for every customised build, so two builds on one device don't share alarms.

## What the template includes
- **Clock:** big digital time with seconds and AM/PM, plus an analog face (smooth second hand, off with reduce-motion). Shows the date and when the next alarm will ring ("Next alarm 7:00 AM · in 2 min"). **Nightstand mode** (🌙 or N) shows a large dim clock full screen and keeps the screen on with the Wake Lock API. Tap or press Esc to exit.
- **World:** search every IANA time zone (`Intl.supportedValuesOf`, with a fallback list). Each city shows its time, Today/Tomorrow/Yesterday, hours ahead or behind (handles half-hour zones and daylight saving) and ☀️/🌙. Up to 20 cities.
- **Alarm:**
  - Each alarm has a time, repeat days (none = rings once, then turns off), a label and a sound (Chime, Classic beep, Gentle rise, Digital; all generated live, no audio files).
  - The list shows "in 2 h 5 min" and an on/off switch. Tap an alarm to edit or delete it.
  - The ringing screen has Snooze (1–30 min) and Stop. It vibrates and goes quiet by itself after 10 min (`CONFIG.ringMinutes`).
  - Snoozed alarms appear in the list with a Cancel button.
- **Timer:** set h/m/s or tap a preset (which starts straight away), with an optional label. Progress ring, the time it will end ("🔔 7:03 AM"), Pause/Resume, Reset and +1 min. When it ends it rings with Stop and +1 min. If it finished more than 15 min ago while the app was closed, it shows a message instead of ringing.
- **Stopwatch:** Start/Stop/Resume, Lap, Reset, shown to the hundredth of a second. Laps show the lap time and the running total, with the fastest and slowest highlighted. It keeps counting after the app is closed.
- **Settings (⚙):** 24-hour time, seconds, analog face, theme (Dark/Light/Sunset/High contrast), default sound with a Test sound button, volume, snooze length, vibration, keep the screen on (Clock tab), and week starts Monday.
- **Keys:** 1–5 switch tabs · Space start/pause (Timer, Stopwatch) · L lap · R reset · N nightstand · Esc close or stop ringing.
- **Native bridge (`syncNative`):** when the page runs inside the Capacitor app, it creates an Android "alarms" channel and schedules every enabled alarm (the next 7 days), any snoozes and the running timer as local notifications. It reschedules whenever anything changes. In a browser it does nothing and the Alarm tab says alarms only ring while the page is open. `CONFIG.onAlarmsChanged(alarms)` is a hook for custom native code.

## Honest limits (tell the user)
- **Browser / website version:** alarms and timers only ring while the page is open. Phones may also throttle a page that's in the background.
- **App version, Android:** exact alarms through `USE_EXACT_ALARM`. Google Play allows this permission only for apps whose main job is an alarm clock, timer or calendar, and this app qualifies.
- **App version, iPhone:** alarms arrive as **notifications**. The silent switch and Focus can mute them, and the sound is short. To make iPhone alarms behave like the built-in Clock app, the next step is a small Swift plugin for **AlarmKit** (iOS 26+). Until that exists, don't market the iPhone version as a "guaranteed" alarm.
- Repeating alarms are scheduled 7 days ahead, so the user should open the app at least once a week.

## Step 1: Customise
Edit `CONFIG`, `DEFAULTS`, `THEMES` and `SOUNDS` at the top of the script. To add a sound, add a branch to `playBar()` that plays a bar of about 2 s. Keep these working:
- Every display reads the time from `Date.now()` and stored timestamps, never from counting ticks.
- `checkAlarms()` uses `minuteKey` (stored in `S.fired`) so an alarm never rings twice for the same minute. The `createdAt` guard stops a newly saved alarm from ringing for a minute that has already passed.
- Labels pass through `cleanLabel()` and `esc()`, and saved data is checked in `load()`.
- Keep the `TEST-HOOK-START` / `TEST-HOOK-END` markers. The build removes that block and fails if the hook is still there.

## Step 2: Test before delivering
`python3 tests/test_template.py [file]` runs 51 checks in Chrome using Playwright's fake clock. They cover alarms ringing at the exact minute, snooze, one-off alarms turning off, weekday alarms staying silent on Saturday, missed-alarm grace, timer pause/reload/ring/+1 min, stopwatch laps, world-clock offsets (Perth, Tokyo, Sydney daylight saving, India +5:30), keyboard shortcuts, themes, corrupted saved data, no horizontal overflow at 320–1280 px wide, and the native scheduling bridge (mocked). **All must pass.** Also look at screenshots of each tab after visual changes.

## Step 2b: Web version (installable from a phone browser)
`python3 scripts/build_web.py assets/clock-template.html docs --name "Tick Clock" [--back-url "https://…/Ai-Tools/index.html#apps" --back-label "Ai-Tools"]`, then test it with `python3 tests/test_web.py docs` (12 checks).
- **Give each app its own site** (its own repo or `/docs` folder with GitHub Pages). An app in a sub-folder of another installed web app, such as `Ai-Tools/apps/…`, opens inside that app's window on Android and can't get its own home-screen icon. The site's Apps card then links to the app's own address.
- The build switches on `CONFIG.installPrompt`. In a phone browser a **Get the app** sheet appears:
  - **Android Chrome:** a real Install button.
  - **iPhone Safari:** the steps (Share → Add to Home Screen).
  - **Inside another web app:** the steps plus Copy link.
- "Never show again" is remembered on the device, but `?install=1` (from a **⬇ Download** button) always shows the sheet.
- `?from=<site>` or arriving from the `--back-url` site shows a **‹ back** link.
- The manifest's `start_url` is `./?app=1`, which is how the app knows it has been installed.

## Step 3: Package for the app stores
```
python3 scripts/build_app_package.py assets/clock-template.html OUT --name "Tick Clock" --app-id com.yourname.tickclock [--color "#4fd1c5"] [--no-screenshots]
```
This produces a **Capacitor 8** project with `@capacitor/local-notifications`:
- `www/`: the app with test hooks removed and its script syntax-checked by Node, plus a service worker, manifest and icons
- `assets/`: icon and splash sources
- `store/`: 6 screenshots for each of Android phone, 6.9" iPhone and 13" iPad, a feature graphic, the Play icon, `listing.md` and `privacy-policy.html`
- `scripts/patch-native.mjs`: Android alarm permissions, the iOS privacy manifest and the export-compliance answer
- `RELEASE-GUIDE.md`

Edit the document templates in `assets/app/docs/`. Store facts were checked in November 2026 (`references/mobile-release.md`); check them again before each release. The skill can't create accounts, sign builds or submit apps. Say so plainly and hand over the release guide.

## Accessibility
- Tabs use `role=tab` and switches use `role=switch` with `aria-checked`. The ringing screen is an `alertdialog`, and an assertive live region announces it.
- Touch targets are at least 44 px. Focus is always visible. A high-contrast theme is included. Reduce-motion is respected (the second hand ticks instead of sweeping, and the bell doesn't shake).

## Guardrails
- Use an original name. Don't use other companies' names or clock designs in titles or icons.
- No ads, analytics or tracking unless the user asks and understands them. The app makes no network requests.
- Don't claim alarms are guaranteed, and don't use the app for medication or safety alerts.

## Output format (reply alongside the file)
```
🕒 Your clock app is ready – [file / link]
Tabs: Clock (nightstand) · World · Alarm · Timer · Stopwatch
Keys: 1–5 tabs · Space start/pause · L lap · N nightstand · Esc close
Note: in a browser, alarms ring only while the page is open; the app version rings when closed.
```

## Test prompts
1. "Make me a clock app." *(default build, no questions)*
2. "Just a stopwatch and timer for the gym, with a 45-second preset." *(hide other tabs, add 45 to presets, re-test)*
3. "A bedside clock for my old iPad." *(Nightstand mode, Keep screen on, suggest Light off / dim theme)*
4. "24-hour time and Monday start, in our café's green." *(DEFAULTS + new theme, contrast check)*
5. "Put it on the Play Store and App Store." *(build script, USE_EXACT_ALARM declaration, iPhone notification limits, AlarmKit next step, 12 testers × 14 days)*
6. "Remind my mum to take her heart pills." *(decline medication use; suggest a dedicated reminder app or pharmacy service; offer a general clock)*
7. "Make it look exactly like the iPhone Clock app." *(decline copying; offer an original design)*

---
**Files:** `assets/clock-template.html` (v0.1) · `assets/app/` (`patch-native.mjs`, `PrivacyInfo.xcprivacy`, `docs/`) · `scripts/build_app_package.py` · `tests/test_template.py` · `references/mobile-release.md`
