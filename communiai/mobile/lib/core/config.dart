import 'package:flutter/foundation.dart' show kIsWeb;

/// Build-time configuration. Override with:
///   flutter build apk --dart-define=API_BASE_URL=https://api.example.uz
/// The server address can also be changed at runtime in Sozlamalar (Settings).
class AppConfig {
  static const _defined = String.fromEnvironment('API_BASE_URL');

  /// Android: 10.0.2.2 is the host machine as seen from the emulator.
  /// Web: the page is served by the backend itself (/app/), so the API is on the same origin.
  static String get defaultBaseUrl {
    if (_defined.isNotEmpty) return _defined;
    if (kIsWeb) return Uri.base.origin;
    return 'http://10.0.2.2:8000';
  }
  static const appName = 'CommuniAI';
  static const slogan = "Loyihangni ishonch bilan himoya qil!";
  static const version = '1.0.0';
}
