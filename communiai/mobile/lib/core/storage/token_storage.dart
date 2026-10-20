import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';

/// Session tokens live only in secure storage (Android Keystore backed).
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage]) : _s = storage ?? const FlutterSecureStorage();
  final FlutterSecureStorage _s;

  static const _access = 'access_token';
  static const _refresh = 'refresh_token';

  String? _cachedAccess;
  String? _cachedRefresh;

  Future<String?> get accessToken async => _cachedAccess ??= await _s.read(key: _access);
  Future<String?> get refreshToken async => _cachedRefresh ??= await _s.read(key: _refresh);

  Future<void> save(String access, String refresh) async {
    _cachedAccess = access;
    _cachedRefresh = refresh;
    await _s.write(key: _access, value: access);
    await _s.write(key: _refresh, value: refresh);
  }

  Future<void> clear() async {
    _cachedAccess = null;
    _cachedRefresh = null;
    await _s.delete(key: _access);
    await _s.delete(key: _refresh);
  }
}

/// Non-sensitive preferences.
class AppPrefs {
  AppPrefs(this._p);
  final SharedPreferences _p;

  static Future<AppPrefs> load() async => AppPrefs(await SharedPreferences.getInstance());

  bool get onboardingSeen => _p.getBool('onboarding_seen') ?? false;
  Future<void> setOnboardingSeen() => _p.setBool('onboarding_seen', true);

  String get baseUrl => _p.getString('base_url') ?? AppConfig.defaultBaseUrl;
  Future<void> setBaseUrl(String v) => _p.setString('base_url', v);

  String get themeMode => _p.getString('theme_mode') ?? 'system';
  Future<void> setThemeMode(String v) => _p.setString('theme_mode', v);
}
