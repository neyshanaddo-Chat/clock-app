// Run after `npx cap add android` and/or `npx cap add ios`:  node scripts/patch-native.mjs
// Safe to run more than once.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
let changed = 0;

// ---- Android: permissions so alarms ring on time while the app is closed ----
const manifest = path.join(root, "android/app/src/main/AndroidManifest.xml");
if (fs.existsSync(manifest)) {
  let xml = fs.readFileSync(manifest, "utf8");
  const perms = [
    '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
    // Clock/alarm apps may use USE_EXACT_ALARM (granted at install, Android 13+).
    // Google Play only allows it for apps whose core function is an alarm clock or calendar,
    // and asks you to declare it in Play Console > App content.
    '<uses-permission android:name="android.permission.USE_EXACT_ALARM" />',
    '<uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" android:maxSdkVersion="32" />',
    '<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />',
    '<uses-permission android:name="android.permission.VIBRATE" />',
    '<uses-permission android:name="android.permission.WAKE_LOCK" />'
  ];
  for (const p of perms) {
    const name = p.match(/android:name="([^"]+)"/)[1];
    if (!xml.includes(`"${name}"`)) { xml = xml.replace("</manifest>", `    ${p}\n</manifest>`); changed++; }
  }
  fs.writeFileSync(manifest, xml);
  console.log("Android manifest: permissions checked");
} else console.log("No android/ folder yet (run npx cap add android) - skipped");

// ---- iOS: privacy manifest + background note ----
const iosApp = path.join(root, "ios/App/App");
if (fs.existsSync(iosApp)) {
  const dest = path.join(iosApp, "PrivacyInfo.xcprivacy");
  if (!fs.existsSync(dest)) { fs.copyFileSync(path.join(here, "PrivacyInfo.xcprivacy"), dest); changed++; }
  const pbx = path.join(root, "ios/App/App.xcodeproj/project.pbxproj");
  if (fs.existsSync(pbx) && !fs.readFileSync(pbx, "utf8").includes("PrivacyInfo.xcprivacy"))
    console.log("iOS: PrivacyInfo.xcprivacy copied. In Xcode, drag it into the App group and tick the App target once.");
  // Export compliance: the app uses no non-exempt encryption.
  const plist = path.join(iosApp, "Info.plist");
  if (fs.existsSync(plist)) {
    let s = fs.readFileSync(plist, "utf8");
    if (!s.includes("ITSAppUsesNonExemptEncryption")) {
      s = s.replace(/<\/dict>\s*<\/plist>\s*$/, "\t<key>ITSAppUsesNonExemptEncryption</key>\n\t<false/>\n</dict>\n</plist>\n");
      fs.writeFileSync(plist, s); changed++;
    }
  }
  console.log("iOS: checked");
} else console.log("No ios/ folder yet (run npx cap add ios on a Mac) - skipped");

console.log(changed ? `Done (${changed} change(s)).` : "Done (nothing to change).");
