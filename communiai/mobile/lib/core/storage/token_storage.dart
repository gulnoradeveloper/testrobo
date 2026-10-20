import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';

/// Session tokens live in secure storage (Android Keystore backed) on mobile.
/// In the browser version, WebCrypto-based secure storage needs HTTPS, so tokens are kept in the
/// browser's local storage instead (acceptable for the demo/web fallback; the APK is the main client).
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage]) : _s = storage ?? const FlutterSecureStorage();
  final FlutterSecureStorage _s;

  Future<String?> _read(String k) async =>
      kIsWeb ? (await SharedPreferences.getInstance()).getString(k) : _s.read(key: k);
  Future<void> _write(String k, String v) async =>
      kIsWeb ? (await SharedPreferences.getInstance()).setString(k, v) : _s.write(key: k, value: v);
  Future<void> _delete(String k) async =>
      kIsWeb ? (await SharedPreferences.getInstance()).remove(k) : _s.delete(key: k);

  static const _access = 'access_token';
  static const _refresh = 'refresh_token';

  String? _cachedAccess;
  String? _cachedRefresh;

  Future<String?> get accessToken async => _cachedAccess ??= await _read(_access);
  Future<String?> get refreshToken async => _cachedRefresh ??= await _read(_refresh);

  Future<void> save(String access, String refresh) async {
    _cachedAccess = access;
    _cachedRefresh = refresh;
    await _write(_access, access);
    await _write(_refresh, refresh);
  }

  Future<void> clear() async {
    _cachedAccess = null;
    _cachedRefresh = null;
    await _delete(_access);
    await _delete(_refresh);
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
