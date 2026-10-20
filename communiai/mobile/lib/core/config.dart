/// Build-time configuration. Override with:
///   flutter build apk --dart-define=API_BASE_URL=https://api.example.uz
/// The server address can also be changed at runtime in Sozlamalar (Settings).
class AppConfig {
  /// 10.0.2.2 is the host machine as seen from the Android emulator.
  static const defaultBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  static const appName = 'CommuniAI';
  static const slogan = "Loyihangni ishonch bilan himoya qil!";
  static const version = '1.0.0';
}
