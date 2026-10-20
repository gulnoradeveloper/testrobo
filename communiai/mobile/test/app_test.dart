import 'package:communiai/core/api/api_client.dart';
import 'package:communiai/core/api/models.dart';
import 'package:communiai/core/providers.dart';
import 'package:communiai/core/storage/token_storage.dart';
import 'package:communiai/features/auth/auth_screens.dart';
import 'package:communiai/shared/widgets/common.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<Widget> _app(Widget child) async {
  SharedPreferences.setMockInitialValues({});
  final prefs = await AppPrefs.load();
  return ProviderScope(
    overrides: [prefsProvider.overrideWithValue(prefs)],
    child: MaterialApp(home: child),
  );
}

void main() {
  group('ApiException', () {
    test('parses the unified backend error format', () {
      final req = RequestOptions(path: '/x');
      final e = DioException(
        requestOptions: req,
        response: Response(requestOptions: req, statusCode: 422, data: {
          'error': {
            'code': 'WEAK_PASSWORD',
            'message': 'Parol zaif',
            'details': [
              {'field': 'password', 'message': 'Kamida 10 belgi'}
            ]
          }
        }),
      );
      final ex = ApiException.from(e);
      expect(ex.code, 'WEAK_PASSWORD');
      expect(ex.status, 422);
      expect(ex.detailedMessage, 'Parol zaif: Kamida 10 belgi');
    });

    test('maps connection errors to a network error', () {
      final ex = ApiException.from(
          DioException(requestOptions: RequestOptions(path: '/'), type: DioExceptionType.connectionError));
      expect(ex.isNetwork, isTrue);
    });
  });

  test('AppUser parses role and consent', () {
    final u = AppUser.fromJson({
      'id': '1',
      'first_name': 'Aziza',
      'last_name': 'Karimova',
      'email': 'a@b.uz',
      'university': 'TATU',
      'study_program': 'AT',
      'role': 'admin',
      'ai_consent_at': '2026-01-01T00:00:00Z',
    });
    expect(u.isAdmin, isTrue);
    expect(u.hasAiConsent, isTrue);
    expect(u.initials, 'AK');
  });

  testWidgets('ScoreBar shows "Hali baholanmagan" instead of zero', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(
        body: Column(children: [
          ScoreBar(code: 'K6', label: 'Refleksiya', score: null, max: 10),
          ScoreBar(code: 'K1', label: 'Aniqlik', score: 15, max: 20),
        ]),
      ),
    ));
    expect(find.text('Hali baholanmagan'), findsOneWidget);
    expect(find.text('15 / 20'), findsOneWidget);
  });

  testWidgets('Login validates email and password before calling the API', (tester) async {
    await tester.pumpWidget(await _app(const LoginScreen()));
    await tester.tap(find.text('Tizimga kirish'));
    await tester.pump();
    expect(find.text('Elektron pochtani kiriting'), findsOneWidget);
    expect(find.text("Parol to'ldirilishi shart"), findsOneWidget);
  });

  testWidgets('Register enforces 10+ character password and matching confirmation', (tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    addTearDown(tester.view.resetPhysicalSize);
    await tester.pumpWidget(await _app(const RegisterScreen()));
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'Aziza');
    await tester.enterText(fields.at(1), 'Karimova');
    await tester.enterText(fields.at(2), 'aziza@example.uz');
    await tester.enterText(fields.at(3), 'qisqa');
    await tester.enterText(fields.at(4), 'boshqa');
    await tester.enterText(fields.at(5), 'TATU');
    await tester.ensureVisible(find.byType(FilledButton));
    await tester.tap(find.byType(FilledButton));
    await tester.pump();
    expect(find.text("Parol kamida 10 ta belgidan iborat bo'lishi kerak"), findsOneWidget);
    expect(find.text('Parollar mos kelmadi'), findsOneWidget);
  });

  test('formatScore and formatDate', () {
    expect(formatScore(null), '—');
    expect(formatScore(12), '12');
    expect(formatScore(12.5), '12.5');
    expect(formatDate('2026-03-05T10:07:00', time: false), '05.03.2026');
  });
}
