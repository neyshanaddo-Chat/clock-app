# Mobile release notes: clock app (checked November 2026)

The step-by-step guide that ships with each build is `assets/app/docs/RELEASE-GUIDE.md`. This file records the facts behind it and where they came from. Re-check before each release.

## Alarm delivery
| Platform | Mechanism in v0.1 | Behaviour | Source |
|---|---|---|---|
| Browser / PWA | `setInterval` + timestamps | Rings only while the page is open; background tabs may be throttled | – |
| Android 13+ | `@capacitor/local-notifications` + `USE_EXACT_ALARM` | Exact time while closed/locked. `USE_EXACT_ALARM` is granted at install and is meant for alarm clock and calendar apps; Google Play restricts it to apps whose core function needs it and may ask for a declaration. `SCHEDULE_EXACT_ALARM` (Android 12, maxSdk 32) is denied by default for new installs on 14+. | developer.android.com/about/versions/14/changes/schedule-exact-alarms; capacitorjs.com/docs/apis/local-notifications |
| Android 8+ | Notification channel `alarms` (importance 5) | A channel's sound can't be changed after creation without reinstalling | capacitorjs.com/docs/apis/local-notifications |
| iOS | `@capacitor/local-notifications` | Notification at the exact time; silenced by silent switch/Focus; short sound | – |
| iOS 26+ (future) | **AlarmKit** (needs native Swift plugin) | System-level alarms and timers: Lock Screen, Dynamic Island, rings through silent mode. Authorisation requested on first alarm. | developer.apple.com/documentation/alarmkit; WWDC25 session 230 |

## Store requirements (shared with the Pong skill's checks)
- Capacitor 8.x (Capacitor 9 expected around end of November 2026; staying on 8 is fine).
- Google Play: new apps target API 36 from 31 Aug 2026; personal accounts created after 13 Nov 2023 need 12 testers for 14 consecutive days before production; one-off US$25 fee.
- Apple: builds must use Xcode 26 / iOS 26 SDK since 28 April 2026; privacy manifest; `ITSAppUsesNonExemptEncryption = NO`.
- Apple Guidelines 4.2 (minimum functionality) and 4.3 (spam/duplicate apps) are the main review risk for a clock app; native alarms (AlarmKit) and a distinctive design reduce it.

## Roadmap for v0.2
1. AlarmKit plugin for iOS 26+ (fallback to notifications on older iOS).
2. Notification actions (Snooze / Stop from the lock screen).
3. Custom alarm sounds bundled as audio files (needed for notification sound on iOS/Android channels).
4. Translations (follow the Pong skill's `i18n.json` + inject pattern).
