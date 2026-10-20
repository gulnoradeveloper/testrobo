# CommuniAI R8 rules.
# Several plugins (shared_preferences_android, path_provider_android, android_file_picker) call Java/Kotlin
# classes from Dart via JNI by their *names* (e.g. JClass.forName('kotlin/Unit')). R8 cannot see those
# references, so shrinking/obfuscation removed or renamed them and the release app failed at startup.
# The app is small, so we keep all code as-is: no shrinking, no obfuscation, no optimization.
-dontshrink
-dontobfuscate
-dontoptimize

-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class kotlin.** { *; }
-keep class kotlinx.** { *; }
-keep class androidx.datastore.** { *; }
-keep class com.it_nomads.** { *; }
-keep class com.github.dart_lang.** { *; }
-dontwarn com.google.errorprone.annotations.**
-dontwarn javax.annotation.**
-dontwarn com.google.android.play.core.**
