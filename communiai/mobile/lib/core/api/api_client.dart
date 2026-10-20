import 'dart:async';

import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import '../storage/token_storage.dart';

/// Error in the backend's unified format: {"error": {"code", "message", "details"}}.
class ApiException implements Exception {
  ApiException(this.code, this.message, {this.status, this.details});
  final String code;
  final String message;
  final int? status;
  final dynamic details;

  bool get isNetwork => code == 'NETWORK_ERROR' || code == 'TIMEOUT';

  /// First field-level message, if the server returned validation details.
  String get detailedMessage {
    if (details is List && (details as List).isNotEmpty) {
      final first = (details as List).first;
      if (first is Map && first['message'] != null) {
        return '$message: ${first['message']}';
      }
    }
    return message;
  }

  @override
  String toString() => message;

  static ApiException from(Object e) {
    if (e is ApiException) return e;
    if (e is DioException) {
      final data = e.response?.data;
      if (data is Map && data['error'] is Map) {
        final err = data['error'] as Map;
        return ApiException(err['code']?.toString() ?? 'ERROR', err['message']?.toString() ?? 'Xatolik',
            status: e.response?.statusCode, details: err['details']);
      }
      switch (e.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.receiveTimeout:
        case DioExceptionType.sendTimeout:
          return ApiException('TIMEOUT', "Server javob bermadi. Internet aloqasini tekshiring.");
        case DioExceptionType.connectionError:
          return ApiException('NETWORK_ERROR',
              "Serverga ulanib bo'lmadi. Internet aloqasini va server manzilini (Sozlamalar) tekshiring.");
        default:
          return ApiException('HTTP_${e.response?.statusCode ?? 0}', "So'rovni bajarishda xatolik yuz berdi",
              status: e.response?.statusCode);
      }
    }
    return ApiException('UNKNOWN', 'Kutilmagan xatolik: $e');
  }
}

typedef SessionExpiredCallback = void Function();

/// HTTP client with bearer auth, automatic refresh-token rotation and unified errors.
class ApiClient {
  ApiClient({required String baseUrl, required this.tokens}) {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60),
      sendTimeout: const Duration(seconds: 120),
      headers: {'Accept': 'application/json'},
    ));
    dio.interceptors.add(QueuedInterceptorsWrapper(
      onRequest: (options, handler) async {
        if (options.extra['auth'] != false) {
          final t = await tokens.accessToken;
          if (t != null) options.headers['Authorization'] = 'Bearer $t';
        }
        handler.next(options);
      },
      onError: (err, handler) async {
        final code = (err.response?.data is Map && err.response!.data['error'] is Map)
            ? err.response!.data['error']['code']
            : null;
        final isAuthCall = err.requestOptions.extra['auth'] == false;
        if (err.response?.statusCode == 401 && !isAuthCall && err.requestOptions.extra['retried'] != true &&
            (code == 'TOKEN_EXPIRED' || code == 'UNAUTHORIZED')) {
          final ok = await _refresh();
          if (ok) {
            final opts = err.requestOptions..extra['retried'] = true;
            opts.headers['Authorization'] = 'Bearer ${await tokens.accessToken}';
            try {
              final res = await dio.fetch(opts);
              return handler.resolve(res);
            } on DioException catch (e) {
              return handler.next(e);
            }
          }
          onSessionExpired?.call();
        }
        handler.next(err);
      },
    ));
  }

  late final Dio dio;
  final TokenStorage tokens;
  SessionExpiredCallback? onSessionExpired;
  static const _uuid = Uuid();

  set baseUrl(String v) => dio.options.baseUrl = v;
  String get baseUrl => dio.options.baseUrl;

  Future<bool> _refresh() async {
    final rt = await tokens.refreshToken;
    if (rt == null) return false;
    try {
      final res = await Dio(BaseOptions(baseUrl: dio.options.baseUrl, connectTimeout: const Duration(seconds: 15)))
          .post('/api/v1/auth/refresh', data: {'refresh_token': rt});
      await tokens.save(res.data['access_token'], res.data['refresh_token']);
      return true;
    } catch (_) {
      await tokens.clear();
      return false;
    }
  }

  static String newIdempotencyKey() => _uuid.v4();

  Future<T> _wrap<T>(Future<Response> Function() call) async {
    try {
      final res = await call();
      return res.data as T;
    } catch (e) {
      throw ApiException.from(e);
    }
  }

  Future<T> get<T>(String path, {Map<String, dynamic>? query}) =>
      _wrap<T>(() => dio.get(path, queryParameters: query));

  Future<T> post<T>(String path, {Object? data, bool auth = true, String? idempotencyKey, Map<String, dynamic>? query}) =>
      _wrap<T>(() => dio.post(path,
          data: data,
          queryParameters: query,
          options: Options(
            extra: {'auth': auth},
            headers: {'Idempotency-Key': ?idempotencyKey},
          )));

  Future<T> patch<T>(String path, {Object? data}) => _wrap<T>(() => dio.patch(path, data: data));

  Future<T> put<T>(String path, {Object? data}) => _wrap<T>(() => dio.put(path, data: data));

  Future<void> delete(String path) => _wrap<dynamic>(() => dio.delete(path));

  Future<Map<String, dynamic>> upload(String path, List<int> bytes, String fileName,
      {void Function(int, int)? onProgress, CancelToken? cancel}) async {
    try {
      final form = FormData.fromMap({'file': MultipartFile.fromBytes(bytes, filename: fileName)});
      final res = await dio.post(path, data: form, onSendProgress: onProgress, cancelToken: cancel);
      return Map<String, dynamic>.from(res.data as Map);
    } catch (e) {
      throw ApiException.from(e);
    }
  }
}
