import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers.dart';
import 'core/router.dart';
import 'core/storage/token_storage.dart';
import 'core/theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final AppPrefs prefs;
  try {
    prefs = await AppPrefs.load().timeout(const Duration(seconds: 10));
  } catch (e) {
    // Never leave the user on a blank/frozen screen: show what went wrong.
    runApp(StartupErrorApp(error: e));
    return;
  }
  runApp(ProviderScope(
    // Errors are shown with an explicit "Qayta urinish" button instead of silent automatic retries.
    retry: (_, _) => null,
    overrides: [prefsProvider.overrideWithValue(prefs)],
    child: const CommuniApp(),
  ));
}

class CommuniApp extends ConsumerWidget {
  const CommuniApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'CommuniAI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ref.watch(themeModeProvider),
      routerConfig: ref.watch(routerProvider),
      locale: const Locale('uz'),
      supportedLocales: const [Locale('uz'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) {
        // Respect user font scaling but cap it so layouts do not break on small screens.
        final mq = MediaQuery.of(context);
        return MediaQuery(
          data: mq.copyWith(textScaler: mq.textScaler.clamp(minScaleFactor: 0.85, maxScaleFactor: 1.3)),
          child: child!,
        );
      },
    );
  }
}

/// Shown only if the device storage cannot be initialised at startup.
class StartupErrorApp extends StatelessWidget {
  const StartupErrorApp({super.key, required this.error});
  final Object error;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: Scaffold(
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Icon(Icons.error_outline_rounded, size: 64, color: AppColors.error),
                const SizedBox(height: 16),
                const Text("Ilovani ishga tushirib bo'lmadi",
                    textAlign: TextAlign.center, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                const SizedBox(height: 12),
                const Text("Qurilma xotirasiga kirishda xatolik. Ilovani qayta o'rnatib ko'ring.",
                    textAlign: TextAlign.center),
                const SizedBox(height: 12),
                SelectableText('$error', textAlign: TextAlign.center, style: const TextStyle(fontSize: 12)),
              ]),
            ),
          ),
        ),
      );
}
