# {{APP_NAME}}: getting it onto Google Play and the App Store

This folder is a ready-made **Capacitor 8** project. Capacitor wraps the clock app (one HTML file in `www/`) in a real Android app and a real iPhone/iPad app. Everything is bundled inside, so it works with no internet.

**Already done for you:**
- Clock, world clock, alarms, timer and stopwatch, tuned for phones (safe areas, big touch targets, light/dark/high-contrast themes)
- Alarms and the running timer are scheduled as **system notifications** (`@capacitor/local-notifications`), so they still go off when the app is closed
- Android exact-alarm permissions and the iOS privacy manifest (`scripts/patch-native.mjs`)
- App icon and splash artwork (`assets/`), store screenshots (Android phone, 6.9" iPhone, 13" iPad), feature graphic and Play icon (`store/`)
- Draft store listing (`store/listing.md`) and a privacy policy template (`store/privacy-policy.html`)

**Only you can:** create the developer accounts, sign the apps, build on your own computers and submit.

---

## 0. Decide these first (hard to change later)

| Item | Now | What to do |
|---|---|---|
| App name | {{APP_NAME}} | Pick a name you can own. Search IP Australia, both stores and the web. Avoid other brands (Apple, Google, Casio, etc.). |
| App ID / bundle ID | `{{APP_ID}}` | Reverse of a domain you control. **Can never be changed** after publishing. Edit `capacitor.config.json` before step 2 if needed. |
| Privacy policy URL | – | Fill in `store/privacy-policy.html` and host it on your website. Apple requires one; Google asks for one. |
| Support URL / email | – | A simple contact page (Apple requires it). |
| Google account type | – | **Organisation** (needs a D-U-N-S number) skips the 12-tester rule. **Personal**: closed test first (step 5). |

## 1. What you need

| | Android | iPhone / iPad |
|---|---|---|
| Computer | Windows, Mac or Linux | **A Mac** |
| Software | Node.js 22+, Android Studio (includes JDK 21) | Node.js 22+, **Xcode 26 or newer** (App Store Connect only accepts Xcode 26 / iOS 26 SDK builds since 28 April 2026) |
| Account | Google Play Console: US$25 once | Apple Developer Program: yearly fee |
| Test device | Any Android phone | A real iPhone (alarms can't be tested properly in the simulator) |

## 2. Set up the project (once)

```bash
npm install                 # Capacitor 8 + local notifications
npx cap add android
npx cap add ios             # Mac only
npm run patch               # Android alarm permissions, iOS privacy manifest + export answer
npm run assets              # every icon + splash size from assets/
npx cap sync
```

**iOS, one manual step:** open `ios/App/App.xcworkspace` in Xcode, drag `ios/App/App/PrivacyInfo.xcprivacy` into the **App** group and tick the **App** target.

## 3. How alarms work in the app (read this)

| | Android | iPhone |
|---|---|---|
| App open | Rings full screen with Snooze / Stop | Same |
| App closed or phone locked | A **high-priority notification** with sound at the exact minute (uses `USE_EXACT_ALARM`) | A **notification** with sound at the exact minute |
| Silent switch / Focus / Do Not Disturb | Follows the phone's alarm/notification settings | **Can be silenced**, and the sound is short (a notification, not a ringing alarm) |
| After a restart | Re-scheduled by the plugin | Kept by iOS |

The app schedules the next 7 days of alarms each time it's opened or an alarm changes. **Open the app at least once a week** so repeating alarms stay scheduled (tell users this in the description if needed).

**Make iPhone alarms behave like the built-in Clock (recommended before marketing it as an alarm clock):** iOS 26 added **AlarmKit**, which lets third-party apps ring through silent mode and Focus with a full-screen alarm. Using it needs a small native Swift plugin (not included yet). Until then, describe the iPhone version honestly: "alarms are delivered as notifications".

## 4. Test on real devices

- Android: `npx cap open android` → plug in the phone → ▶ Run.
- iOS: `npx cap open ios` → choose your Team under *Signing & Capabilities* → pick your iPhone → ▶ Run.

Checklist:
- [ ] First alarm asks for notification permission; allow it
- [ ] Alarm 2 minutes ahead rings with the app **open**
- [ ] Alarm 2 minutes ahead with the app **closed** and the phone **locked** shows a notification with sound
- [ ] Repeat alarm (e.g. weekdays) appears under Settings → Notifications as scheduled (Android: also *Alarms & reminders* allowed)
- [ ] Snooze rings again after the snooze length; Stop silences it
- [ ] Timer finishes with the app closed → notification
- [ ] Stopwatch keeps counting after closing and reopening the app
- [ ] World clock shows correct times; add and remove a city
- [ ] Nightstand mode keeps the screen on; tapping exits
- [ ] Airplane mode: everything still works
- [ ] Restart the phone: Android alarms still fire

## 5. Google Play

1. **Target SDK:** new apps must target Android 16 (API 36) from 31 August 2026. Capacitor 8 sets `targetSdkVersion = 36` in `android/variables.gradle`; check it.
2. **Signed bundle:** Android Studio → *Build → Generate Signed App Bundle* → create an upload key. ⚠️ Back up the keystore and passwords.
3. **Play Console → Create app → App content:** privacy policy URL, Ads = No, Data safety = **No data collected or shared**, content rating questionnaire (answer No throughout), target audience.
4. **Exact alarm permission:** the app declares `USE_EXACT_ALARM`. Google Play only allows this for apps whose core function is an alarm clock, timer or calendar. This app qualifies. If Play Console asks, declare it as an **alarm clock app**.
5. **Store listing:** copy from `store/listing.md`; upload `play-icon-512.png`, `feature-graphic-1024x500.png` and the `android-phone-*` screenshots.
6. **Personal account created after 13 Nov 2023:** closed test with **at least 12 testers for 14 days in a row**, then apply for production.
7. **Production → Create release** → upload the `.aab` → send for review.

## 6. Apple App Store

1. **App Store Connect → Apps → +** with bundle ID `{{APP_ID}}`.
2. Xcode: *Any iOS Device* → *Product → Archive* → *Distribute App → App Store Connect*.
3. **TestFlight** on your own iPhone; run the checklist again.
4. App information, **App Privacy: Data Not Collected**, age rating (all None), screenshots (`iphone-6.9-*`, `ipad-13-*`).
5. Export compliance is answered automatically (`ITSAppUsesNonExemptEncryption = NO`).
6. Review notes from `store/listing.md` → Submit.

**Main Apple risk: Guidelines 4.2 / 4.3.** Clock and alarm apps are a crowded category, and Apple rejects apps that add little over the built-in Clock or feel like a website in a wrapper. This build is fully offline, uses native notifications, and combines five tools with themes and a nightstand mode. Adding AlarmKit (step 3) and a distinctive feature or design will make approval more likely.

## 7. Version numbers (each upload must be higher)

- Android: `android/app/build.gradle` → `versionCode` and `versionName`
- iOS: Xcode → App target → General → **Version** and **Build**

## 8. Updating later

Rebuild `www/` from the latest template (or edit `www/index.html`) → `npx cap sync` → raise version numbers → build and upload.

---
Checked November 2026: Capacitor 8.x, Google Play target API 36, `USE_EXACT_ALARM` for alarm clock apps (Android 13+), Xcode 26 / iOS 26 SDK, AlarmKit on iOS 26, Google's 12 testers for 14 days rule. Store rules change often, so check them again before submitting.
