import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/api_client.dart';
import 'api/models.dart';
import 'api/repository.dart';
import 'storage/token_storage.dart';

/// Overridden in main() with the loaded instance.
final prefsProvider = Provider<AppPrefs>((ref) => throw UnimplementedError());
final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final apiClientProvider = Provider<ApiClient>((ref) {
  final prefs = ref.watch(prefsProvider);
  return ApiClient(baseUrl: prefs.baseUrl, tokens: ref.watch(tokenStorageProvider));
});

final repositoryProvider = Provider<Repository>((ref) => Repository(ref.watch(apiClientProvider)));

// ---------------------------------------------------------------- theme
class ThemeModeController extends Notifier<ThemeMode> {
  @override
  ThemeMode build() => _parse(ref.read(prefsProvider).themeMode);

  static ThemeMode _parse(String v) => switch (v) {
        'light' => ThemeMode.light,
        'dark' => ThemeMode.dark,
        _ => ThemeMode.system,
      };

  Future<void> set(ThemeMode m) async {
    state = m;
    await ref.read(prefsProvider).setThemeMode(m.name);
  }
}

final themeModeProvider = NotifierProvider<ThemeModeController, ThemeMode>(ThemeModeController.new);

// ---------------------------------------------------------------- auth
enum AuthStatus { unknown, unauthenticated, authenticated }

class AuthState {
  const AuthState(this.status, [this.user]);
  final AuthStatus status;
  final AppUser? user;
}

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    ref.read(apiClientProvider).onSessionExpired = () {
      if (state.status == AuthStatus.authenticated) state = const AuthState(AuthStatus.unauthenticated);
    };
    return const AuthState(AuthStatus.unknown);
  }

  Repository get _repo => ref.read(repositoryProvider);
  TokenStorage get _tokens => ref.read(tokenStorageProvider);

  /// Called by the splash screen: restore a saved session if the token is still valid.
  Future<void> restore() async {
    final token = await _tokens.accessToken;
    if (token == null) {
      state = const AuthState(AuthStatus.unauthenticated);
      return;
    }
    try {
      state = AuthState(AuthStatus.authenticated, await _repo.me());
    } on ApiException catch (e) {
      if (e.isNetwork) {
        // Keep tokens; the user can retry when online.
        rethrow;
      }
      await _tokens.clear();
      state = const AuthState(AuthStatus.unauthenticated);
    }
  }

  Future<void> _applyTokens(Json res) async {
    await _tokens.save(res['access_token'], res['refresh_token']);
    state = AuthState(AuthStatus.authenticated, AppUser.fromJson(asJson(res['user'])));
  }

  Future<void> login(String email, String password) async => _applyTokens(await _repo.login(email, password));

  Future<void> register(Json body) async => _applyTokens(await _repo.register(body));

  Future<void> refreshUser() async {
    state = AuthState(AuthStatus.authenticated, await _repo.me());
  }

  void setUser(AppUser u) => state = AuthState(AuthStatus.authenticated, u);

  Future<void> logout() async {
    final rt = await _tokens.refreshToken;
    if (rt != null) {
      try {
        await _repo.logout(rt);
      } catch (_) {
        // Logging out locally must still work offline.
      }
    }
    await _tokens.clear();
    state = const AuthState(AuthStatus.unauthenticated);
  }

  Future<void> forgetSession() async {
    await _tokens.clear();
    state = const AuthState(AuthStatus.unauthenticated);
  }
}

final authProvider = NotifierProvider<AuthController, AuthState>(AuthController.new);

// ---------------------------------------------------------------- shared data providers
final dashboardProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).dashboard());
final projectsProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).projects());
final projectProvider =
    FutureProvider.autoDispose.family<Json, String>((ref, id) => ref.watch(repositoryProvider).project(id));
final defensesProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).defenses());
final resultsProvider =
    FutureProvider.autoDispose.family<Json, String>((ref, id) => ref.watch(repositoryProvider).results(id));
final competenciesProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).competencies());
final progressProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).progress());
final plansProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).plans());
final metaProvider = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).meta());
