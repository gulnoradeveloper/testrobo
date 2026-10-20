#!/usr/bin/env bash
# Installs each APK on the emulator, launches it and records evidence:
# process alive?, screenshot, UI text (accessibility dump), crash lines from logcat.
set -u
OUT=dist/diagnostics
mkdir -p "$OUT"
PKG=uz.communiai.app
RESULT=PASS
adb wait-for-device
adb shell getprop ro.build.version.release > "$OUT/android_version.txt"
for APK in dist/CommuniAI-1.0.0-dev-http.apk dist/CommuniAI-1.0.0-release.apk; do
  NAME=$(basename "$APK" .apk)
  echo "=== $NAME"
  adb uninstall "$PKG" >/dev/null 2>&1 || true
  if ! adb install -r "$APK" > "$OUT/$NAME-install.txt" 2>&1; then
    echo "INSTALL FAILED"; cat "$OUT/$NAME-install.txt"; RESULT=FAIL; continue
  fi
  adb logcat -c
  adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
  sleep 30
  adb exec-out screencap -p > "$OUT/$NAME-screen.png"
  adb shell uiautomator dump /sdcard/ui.xml > /dev/null 2>&1 && adb pull /sdcard/ui.xml "$OUT/$NAME-ui.xml" > /dev/null 2>&1
  adb logcat -d > "$OUT/$NAME-logcat.txt"
  PID=$(adb shell pidof "$PKG" | tr -d '\r')
  grep -E "FATAL EXCEPTION|AndroidRuntime|E/flutter|F/libc|Unhandled Exception|DartError" "$OUT/$NAME-logcat.txt" > "$OUT/$NAME-errors.txt" || true
  UI_OK=no
  grep -q -E "tkazib yuborish|Keyingi|Xush kelibsiz" "$OUT/$NAME-ui.xml" 2>/dev/null && UI_OK=yes
  echo "process: ${PID:-NOT RUNNING} | onboarding visible: $UI_OK | error lines: $(wc -l < "$OUT/$NAME-errors.txt")" | tee "$OUT/$NAME-summary.txt"
  if [ -z "$PID" ] || [ "$UI_OK" != yes ]; then RESULT=FAIL; fi
  # Second step: tap "O'tkazib yuborish" (skip onboarding) and check the login screen appears.
  if [ "$UI_OK" = yes ]; then
    B=$(grep -o -E 'content-desc="[^"]*tkazib yuborish"[^>]*bounds="\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]"|text="[^"]*tkazib yuborish"[^>]*bounds="\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]"' "$OUT/$NAME-ui.xml" | grep -o -E '\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]' | head -1)
    if [ -n "$B" ]; then
      COORDS=$(echo "$B" | sed -E 's/\[([0-9]+),([0-9]+)\]\[([0-9]+),([0-9]+)\]/\1 \2 \3 \4/')
      set -- $COORDS
      adb shell input tap $(( ($1 + $3) / 2 )) $(( ($2 + $4) / 2 ))
      sleep 5
      adb exec-out screencap -p > "$OUT/$NAME-screen2.png"
      adb shell uiautomator dump /sdcard/ui2.xml > /dev/null 2>&1 && adb pull /sdcard/ui2.xml "$OUT/$NAME-ui2.xml" > /dev/null 2>&1
      if grep -q -E "Tizimga kirish|Xush kelibsiz" "$OUT/$NAME-ui2.xml" 2>/dev/null; then
        echo "login screen: yes" | tee -a "$OUT/$NAME-summary.txt"
      else
        echo "login screen: NO" | tee -a "$OUT/$NAME-summary.txt"; RESULT=FAIL
      fi
    fi
  fi
done
echo "$RESULT" > "$OUT/RESULT.txt"
echo "SMOKE RESULT: $RESULT"
