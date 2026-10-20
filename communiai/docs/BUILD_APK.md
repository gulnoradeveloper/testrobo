# Android APK yig'ish

## Tayyor APK (GitHub Actions)

Har bir push'da `.github/workflows/communiai.yml` ikki APK yig'adi va ularni `communiai-apk` branch'iga
hamda Actions artifact'iga joylaydi:

| Fayl | Kimga |
|---|---|
| `CommuniAI-1.0.0-release.apk` | Production: faqat **HTTPS** server (va emulator/localhost) |
| `CommuniAI-1.0.0-dev-http.apk` | Sinov: lokal tarmoqdagi **HTTP** server (masalan `http://192.168.1.10:8000`) |

O'rnatish: APK ni telefonga ko'chiring → oching → "Noma'lum manbalardan o'rnatish"ga ruxsat bering.
Birinchi ochilishda **Kirish → Server manzili** ga backend manzilini kiriting.

## Qo'lda yig'ish

Talablar: Flutter 3.47+, JDK 17/21, Android SDK (platform 36, build-tools).

```bash
cd communiai/mobile
flutter pub get
flutter test
flutter build apk --release                                                  # HTTPS-only
flutter build apk --release --android-project-arg=allowCleartext=true        # lokal HTTP uchun
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.uz  # standart server manzili
# natija: build/app/outputs/flutter-apk/app-release.apk
```

Hajmni kamaytirish: `flutter build apk --release --split-per-abi`.

> **R8 o'chirilgan** (`android/gradle.properties`: `shrink=false`). Ba'zi plaginlar (masalan
> `shared_preferences_android`) Java/Kotlin sinflarini Dart'dan JNI orqali nomi bo'yicha chaqiradi; R8 ularni
> o'chirib/qayta nomlab, ilovani ochilmaydigan qilib qo'ygan edi. Uni qayta yoqmang yoki yoqsangiz
> `app/proguard-rules.pro` dagi keep qoidalarini saqlang va APK'ni qurilmada sinab ko'ring.

## Imzolash (release)

```bash
keytool -genkey -v -keystore ~/communiai-release.jks -keyalg RSA -keysize 4096 -validity 10000 -alias communiai
```

`mobile/android/key.properties` (repoga **qo'shilmaydi**, `.gitignore` da):

```
storePassword=...
keyPassword=...
keyAlias=communiai
storeFile=/home/USER/communiai-release.jks
```

`key.properties` bo'lmasa release APK debug kaliti bilan imzolanadi (sinov uchun o'rnatiladi, lekin
Play Market uchun yaroqsiz). CI dagi APK'lar ham debug kaliti bilan imzolangan.

## iOS

Kod iOS ga tayyor (Flutter, `ios/` papkasi mavjud), lekin MVP da yig'ilmagan va sinalmagan:
`flutter build ios` macOS + Xcode talab qiladi.
