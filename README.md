# Clock app (skill)

An all-in-one clock app (Clock, World clock, Alarms, Timer, Stopwatch) built as a single HTML file, plus packaging for Google Play and the App Store.

- **Try it:** open `assets/clock-template.html` in Chrome.
- **How the skill works:** see `SKILL.md`.
- **Test:** `python3 tests/test_template.py` (needs Python Playwright + Chrome).
- **Make the phone apps:** `python3 scripts/build_app_package.py assets/clock-template.html build --name "Your App Name" --app-id com.yourname.clock`, then follow `build/RELEASE-GUIDE.md`.

Status: draft v0.1, not yet tested on real phones.
