import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';
import '../auth/auth_screens.dart';

/// Individual practice (adaptive step): re-answer for the weakest competencies and compare.
class PracticeScreen extends ConsumerStatefulWidget {
  const PracticeScreen({super.key, required this.planId});
  final String planId;
  @override
  ConsumerState<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends ConsumerState<PracticeScreen> {
  Json? _plan;
  Object? _error;
  Timer? _timer;
  final Map<int, TextEditingController> _inputs = {};
  final Map<int, String> _keys = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in _inputs.values) {
      c.dispose();
    }
    super.dispose();
  }

  bool get _pending => asJsonList(_plan?['attempts']).any((a) => a['status'] == 'pending');

  Future<void> _load() async {
    try {
      final p = await ref.read(repositoryProvider).plan(widget.planId);
      if (mounted) {
        setState(() {
          _plan = p;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted && _plan == null) setState(() => _error = e);
    }
    _timer?.cancel();
    if (mounted && _pending) _timer = Timer(const Duration(seconds: 3), _load);
  }

  Future<void> _submit(int index) async {
    final text = _inputs[index]?.text.trim() ?? '';
    if (text.isEmpty) {
      showMessage(context, 'Qayta javob matnini kiriting', error: true);
      return;
    }
    if (!await ensureAiConsent(context, ref)) return;
    try {
      await ref.read(repositoryProvider).submitAttempt(widget.planId, index, text, _keys[index] ??= ApiClient.newIdempotencyKey());
      _keys.remove(index);
      _inputs[index]?.clear();
      ref.invalidate(competenciesProvider);
      ref.invalidate(progressProvider);
      await _load();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _retry(String attemptId) async {
    try {
      await ref.read(repositoryProvider).retryAttempt(attemptId);
      await _load();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Individual mashq')),
        body: _plan == null
            ? (_error != null ? ErrorView(error: _error!, onRetry: _load) : const LoadingView())
            : RefreshIndicator(onRefresh: _load, child: _body(_plan!)),
      );

  Widget _body(Json plan) {
    final exercises = asJsonList(plan['exercises']);
    final attempts = asJsonList(plan['attempts']);
    if (exercises.isEmpty) {
      return ListView(children: const [
        SizedBox(height: 60),
        EmptyView(icon: Icons.check_circle_outline, title: "Mashq yo'q", message: 'Bu himoya uchun mashq shakllanmadi.'),
      ]);
    }
    return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
      Text(plan['project_title'] ?? '', style: TextStyle(color: AppColors.slate)),
      const SizedBox(height: 8),
      DisclaimerBox(
          "Tizim eng past natija ko'rsatgan ${asStrList(plan['target_competencies']).join(' va ')} kompetensiyalari uchun "
          "mashq tanladi. Qayta javobingiz o'sha rubrika bilan baholanib, avvalgi javob bilan solishtiriladi.",
          icon: Icons.auto_graph_rounded),
      for (final ex in exercises) ...[
        SectionTitle('${ex['competency']} — ${ex['competency_title']}'),
        _exercise(ex, attempts.where((a) => a['exercise_index'] == ex['index']).toList()),
      ],
    ]);
  }

  Widget _exercise(Json ex, List<Json> attempts) {
    final i = ex['index'] as int;
    final c = _inputs.putIfAbsent(i, () => TextEditingController());
    final pending = attempts.any((a) => a['status'] == 'pending');
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(ex['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 8),
          Text(ex['task'] ?? ''),
          const SizedBox(height: 10),
          const Text('Muvaffaqiyat mezonlari', style: TextStyle(fontSize: 12, color: AppColors.slate, fontWeight: FontWeight.w600)),
          BulletList(asStrList(ex['success_criteria']), icon: Icons.check, color: AppColors.success),
          const Divider(height: 24),
          const Text('Savol', style: TextStyle(fontSize: 12, color: AppColors.slate, fontWeight: FontWeight.w600)),
          Text(ex['question_text'] ?? ''),
          const SizedBox(height: 8),
          const Text('Avvalgi javobingiz', style: TextStyle(fontSize: 12, color: AppColors.slate, fontWeight: FontWeight.w600)),
          Text(ex['original_answer'] ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
        ]),
      ),
      const SizedBox(height: 10),
      for (final a in attempts) _AttemptCard(a, onRetry: () => _retry(a['id'])),
      if (pending)
        const AiWorkingCard(title: 'Qayta javobingiz baholanmoqda...', subtitle: 'Natija avvalgi javob bilan solishtiriladi')
      else ...[
        TextField(
          controller: c,
          minLines: 4,
          maxLines: 10,
          maxLength: 6000,
          textCapitalization: TextCapitalization.sentences,
          decoration: const InputDecoration(hintText: 'Yaxshilangan javobingizni yozing...', alignLabelWithHint: true),
        ),
        BusyButton(label: attempts.isEmpty ? 'Qayta javobni yuborish' : 'Yana urinib ko‘rish', onPressed: () => _submit(i)),
      ],
    ]);
  }
}

class _AttemptCard extends StatelessWidget {
  const _AttemptCard(this.a, {required this.onRetry});
  final Json a;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    if (a['status'] == 'pending') return const SizedBox.shrink();
    final ev = asJson(a['evaluation']);
    if (a['status'] == 'failed') {
      return Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(ev['error_message'] ?? 'Baholashda xatolik', style: const TextStyle(color: AppColors.error)),
            const SizedBox(height: 8),
            OutlinedButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Qayta baholash')),
          ]),
        ),
      );
    }
    final rows = asJsonList(ev['score_comparison']);
    final target = a['target_competency'];
    final cmp = asJson(ev['comparison']);
    final refl = asJson(ev['reflection']);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.compare_arrows_rounded, color: AppColors.primary),
            const SizedBox(width: 8),
            Expanded(child: Text('Urinish • ${formatDate(a['created_at'])}', style: const TextStyle(fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 8),
          Text(a['revised_answer'] ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
          const SizedBox(height: 12),
          Table(
            columnWidths: const {0: FlexColumnWidth(2), 1: FlexColumnWidth(1), 2: FlexColumnWidth(1), 3: FlexColumnWidth(1)},
            children: [
              const TableRow(children: [
                Text('Mezon', style: TextStyle(fontSize: 12, color: AppColors.slate)),
                Text('Oldin', style: TextStyle(fontSize: 12, color: AppColors.slate)),
                Text('Keyin', style: TextStyle(fontSize: 12, color: AppColors.slate)),
                Text('Farq', style: TextStyle(fontSize: 12, color: AppColors.slate)),
              ]),
              for (final r in rows)
                TableRow(children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Text(r['code'] == target ? '${r['code']} (maqsad)' : r['code'],
                        style: TextStyle(fontWeight: r['code'] == target ? FontWeight.w800 : FontWeight.w400)),
                  ),
                  Text(r['before'] == null ? '—' : '${formatScore(r['before'])}/${r['max_score']}'),
                  Text(r['after'] == null ? '—' : '${formatScore(r['after'])}/${r['max_score']}'),
                  Text(
                    r['delta'] == null ? '—' : '${(r['delta'] as num) > 0 ? '+' : ''}${formatScore(r['delta'])}',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: r['delta'] == null
                          ? null
                          : (r['delta'] as num) > 0
                              ? AppColors.success
                              : (r['delta'] as num) < 0
                                  ? AppColors.error
                                  : null,
                    ),
                  ),
                ]),
            ],
          ),
          const SizedBox(height: 10),
          ScoreBar(code: 'K6', label: 'Refleksiya va takomillashtirish',
              score: refl['assessed'] == true ? refl['score'] as num? : null, max: (refl['max_score'] ?? 10) as num),
          if ((refl['feedback'] ?? '').toString().isNotEmpty) Text(refl['feedback'], style: const TextStyle(fontSize: 13)),
          const SizedBox(height: 8),
          Text(cmp['summary'] ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
          if (asStrList(cmp['improved_aspects']).isNotEmpty)
            BulletList(asStrList(cmp['improved_aspects']), icon: Icons.arrow_upward_rounded, color: AppColors.success),
          if (asStrList(cmp['remaining_issues']).isNotEmpty)
            BulletList(asStrList(cmp['remaining_issues']), icon: Icons.priority_high_rounded, color: AppColors.warning),
        ]),
      ),
    );
  }
}
