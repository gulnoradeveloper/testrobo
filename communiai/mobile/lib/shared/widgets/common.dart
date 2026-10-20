import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';

void showMessage(BuildContext context, String text, {bool error = false}) {
  final m = ScaffoldMessenger.maybeOf(context);
  m?.hideCurrentSnackBar();
  m?.showSnackBar(SnackBar(
    content: Text(text),
    backgroundColor: error ? AppColors.error : null,
    behavior: SnackBarBehavior.floating,
  ));
}

void showError(BuildContext context, Object e) =>
    showMessage(context, e is ApiException ? e.detailedMessage : e.toString(), error: true);

class LoadingView extends StatelessWidget {
  const LoadingView({super.key, this.message});
  final String? message;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const CircularProgressIndicator(),
            if (message != null) ...[
              const SizedBox(height: 16),
              Text(message!, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ]),
        ),
      );
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.error, this.onRetry});
  final Object error;
  final VoidCallback? onRetry;
  @override
  Widget build(BuildContext context) {
    final msg = error is ApiException ? (error as ApiException).detailedMessage : error.toString();
    final network = error is ApiException && (error as ApiException).isNetwork;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(network ? Icons.wifi_off_rounded : Icons.error_outline_rounded, size: 56, color: AppColors.error),
          const SizedBox(height: 12),
          Text(network ? "Aloqa yo'q" : 'Xatolik yuz berdi',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Text(msg, textAlign: TextAlign.center),
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            OutlinedButton.icon(
                onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Qayta urinish')),
          ],
        ]),
      ),
    );
  }
}

class EmptyView extends StatelessWidget {
  const EmptyView({super.key, required this.icon, required this.title, this.message, this.action});
  final IconData icon;
  final String title;
  final String? message;
  final Widget? action;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: AppColors.primary.withValues(alpha: 0.08), shape: BoxShape.circle),
              child: Icon(icon, size: 40, color: AppColors.primary),
            ),
            const SizedBox(height: 16),
            Text(title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            if (message != null) ...[
              const SizedBox(height: 8),
              Text(message!, textAlign: TextAlign.center, style: TextStyle(color: AppColors.slate)),
            ],
            if (action != null) ...[const SizedBox(height: 20), action!],
          ]),
        ),
      );
}

/// Renders an AsyncValue with consistent Loading / Error+Retry / Data states.
class AsyncView<T> extends StatelessWidget {
  const AsyncView({super.key, required this.value, required this.builder, this.onRetry, this.loadingMessage});
  final AsyncValue<T> value;
  final Widget Function(T data) builder;
  final VoidCallback? onRetry;
  final String? loadingMessage;

  @override
  Widget build(BuildContext context) => value.when(
        data: builder,
        error: (e, _) => ErrorView(error: e, onRetry: onRetry),
        loading: () => LoadingView(message: loadingMessage),
        skipLoadingOnRefresh: true,
      );
}

/// A button that runs an async action, shows progress and ignores taps while busy.
class BusyButton extends StatefulWidget {
  const BusyButton({super.key, required this.label, required this.onPressed, this.icon, this.outlined = false});
  final String label;
  final Future<void> Function()? onPressed;
  final IconData? icon;
  final bool outlined;
  @override
  State<BusyButton> createState() => _BusyButtonState();
}

class _BusyButtonState extends State<BusyButton> {
  bool _busy = false;

  Future<void> _run() async {
    if (_busy || widget.onPressed == null) return;
    setState(() => _busy = true);
    try {
      await widget.onPressed!();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final child = _busy
        ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
        : Row(mainAxisSize: MainAxisSize.min, children: [
            if (widget.icon != null) ...[Icon(widget.icon, size: 20), const SizedBox(width: 8)],
            Flexible(child: Text(widget.label, overflow: TextOverflow.ellipsis)),
          ]);
    final onPressed = widget.onPressed == null || _busy ? null : _run;
    if (widget.outlined) {
      return OutlinedButton(
          onPressed: onPressed,
          child: _busy ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5)) : child);
    }
    return FilledButton(onPressed: onPressed, child: child);
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 10),
        child: Row(children: [
          Expanded(
            child: Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          ),
          ?trailing,
        ]),
      );
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.child, this.padding = const EdgeInsets.all(16), this.onTap, this.color});
  final Widget child;
  final EdgeInsets padding;
  final VoidCallback? onTap;
  final Color? color;
  @override
  Widget build(BuildContext context) => Card(
        color: color,
        clipBehavior: Clip.antiAlias,
        child: InkWell(onTap: onTap, child: Padding(padding: padding, child: child)),
      );
}

class StatusChip extends StatelessWidget {
  const StatusChip(this.label, {super.key, this.color = AppColors.primary, this.icon});
  final String label;
  final Color color;
  final IconData? icon;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (icon != null) ...[Icon(icon, size: 14, color: color), const SizedBox(width: 4)],
          Flexible(
            child: Text(label,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ]),
      );
}

Color sessionStatusColor(String s) => switch (s) {
      'EVALUATED' => AppColors.success,
      'FAILED' => AppColors.error,
      'CANCELLED' => AppColors.slate,
      'EVALUATING' || 'COMPLETED' => AppColors.warning,
      _ => AppColors.primary,
    };

Color levelColor(String? level) => switch (level) {
      'Yetuk' => AppColors.success,
      "Mas'uliyatli" => AppColors.primary,
      'Shakllanayotgan' => AppColors.warning,
      'Intiluvchan' => AppColors.error,
      _ => AppColors.slate,
    };

/// Horizontal score bar; a null score is shown as "Hali baholanmagan" (never as 0).
class ScoreBar extends StatelessWidget {
  const ScoreBar({super.key, required this.label, required this.score, required this.max, this.code});
  final String label;
  final num? score;
  final num max;
  final String? code;

  @override
  Widget build(BuildContext context) {
    final ratio = score == null ? 0.0 : (score! / max).clamp(0, 1).toDouble();
    final color = ratio >= 0.86
        ? AppColors.success
        : ratio >= 0.71
            ? AppColors.primary
            : ratio >= 0.56
                ? AppColors.warning
                : AppColors.error;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (code != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Text(code!, style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.primary)),
            ),
          Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium)),
          const SizedBox(width: 8),
          Text(score == null ? 'Hali baholanmagan' : '${_fmt(score!)} / ${_fmt(max)}',
              style: TextStyle(
                  fontWeight: FontWeight.w700, color: score == null ? AppColors.slate : null, fontSize: 13)),
        ]),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: ratio,
            minHeight: 8,
            backgroundColor: AppColors.slate.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation(score == null ? Colors.transparent : color),
          ),
        ),
      ]),
    );
  }

  static String _fmt(num v) => v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);
}

/// Shown while the backend AI job is running.
class AiWorkingCard extends StatelessWidget {
  const AiWorkingCard({super.key, required this.title, this.subtitle});
  final String title;
  final String? subtitle;
  @override
  Widget build(BuildContext context) => InfoCard(
        color: AppColors.primary.withValues(alpha: 0.06),
        child: Row(children: [
          const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 3)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
              if (subtitle != null) ...[
                const SizedBox(height: 4),
                Text(subtitle!, style: TextStyle(color: AppColors.slate, fontSize: 13)),
              ],
            ]),
          ),
        ]),
      );
}

class DisclaimerBox extends StatelessWidget {
  const DisclaimerBox(this.text, {super.key, this.icon = Icons.info_outline});
  final String text;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.warning.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.warning.withValues(alpha: 0.4)),
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, size: 18, color: AppColors.warning),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13))),
        ]),
      );
}

class BulletList extends StatelessWidget {
  const BulletList(this.items, {super.key, this.icon = Icons.circle, this.color});
  final List<String> items;
  final IconData icon;
  final Color? color;
  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final t in items)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Padding(
                  padding: EdgeInsets.only(top: icon == Icons.circle ? 7 : 1, right: 10),
                  child: Icon(icon, size: icon == Icons.circle ? 6 : 18, color: color ?? AppColors.primary),
                ),
                Expanded(child: Text(t)),
              ]),
            ),
        ],
      );
}

class KeyValue extends StatelessWidget {
  const KeyValue(this.k, this.v, {super.key});
  final String k;
  final String v;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(k, style: TextStyle(color: AppColors.slate, fontSize: 12, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          Text(v.trim().isEmpty ? 'Kiritilmagan' : v),
        ]),
      );
}

String formatDate(String? iso, {bool time = true}) {
  if (iso == null) return '';
  final d = DateTime.tryParse(iso)?.toLocal();
  if (d == null) return '';
  String two(int v) => v.toString().padLeft(2, '0');
  final date = '${two(d.day)}.${two(d.month)}.${d.year}';
  return time ? '$date ${two(d.hour)}:${two(d.minute)}' : date;
}

String formatScore(num? v) => v == null ? '—' : (v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1));
