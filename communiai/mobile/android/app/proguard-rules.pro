# CommuniAI R8 rules.
# Several plugins (shared_preferences_android, path_provider_android, android_file_picker) call Java/Kotlin
# classes from Dart via JNI by their *names* (e.g. JClass.forName('kotlin/Unit')). R8 cannot see those
# references, so shrinking/obfuscation removed or renamed them and the release app failed at startup.
# R8 is disabled for release builds (android/gradle.properties: shrink=false). If it is ever
# re-enabled, these rules keep every class that is looked up by name.

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
