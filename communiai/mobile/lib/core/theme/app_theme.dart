import 'package:flutter/material.dart';

/// CommuniAI palette (TZ 17.2).
class AppColors {
  static const primary = Color(0xFF2563EB);
  static const navy = Color(0xFF0F172A);
  static const background = Color(0xFFF8FAFC);
  static const success = Color(0xFF16A34A);
  static const warning = Color(0xFFF59E0B);
  static const error = Color(0xFFDC2626);
  static const cyan = Color(0xFF22D3EE);
  static const slate = Color(0xFF64748B);

  static const splashGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF2563EB), Color(0xFF1E3A8A), Color(0xFF0F172A)],
  );
}

class AppTheme {
  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness b) {
    final dark = b == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: b,
      primary: AppColors.primary,
      error: AppColors.error,
      surface: dark ? const Color(0xFF111827) : Colors.white,
    );
    final base = ThemeData(useMaterial3: true, colorScheme: scheme, brightness: b);
    final radius = BorderRadius.circular(16);
    return base.copyWith(
      scaffoldBackgroundColor: dark ? AppColors.navy : AppColors.background,
      appBarTheme: AppBarTheme(
        backgroundColor: dark ? AppColors.navy : AppColors.background,
        foregroundColor: dark ? Colors.white : AppColors.navy,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: base.textTheme.titleLarge?.copyWith(
          fontWeight: FontWeight.w700,
          color: dark ? Colors.white : AppColors.navy,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: dark ? const Color(0xFF1E293B) : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: radius,
          side: BorderSide(color: dark ? const Color(0xFF334155) : const Color(0xFFE2E8F0)),
        ),
        margin: EdgeInsets.zero,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xFF1E293B) : Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: dark ? const Color(0xFF334155) : const Color(0xFFE2E8F0)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          backgroundColor: dark ? AppColors.primary : AppColors.navy,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(shape: const StadiumBorder()),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: dark ? const Color(0xFF111827) : Colors.white,
        indicatorColor: AppColors.primary.withValues(alpha: 0.12),
        labelTextStyle: WidgetStatePropertyAll(base.textTheme.labelSmall),
      ),
    );
  }
}
