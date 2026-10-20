import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';
import '../auth/auth_screens.dart';

// =============================================================== AI Project Analysis
class AnalysisScreen extends ConsumerStatefulWidget {
  const AnalysisScreen({super.key, required this.projectId});
  final String projectId;
  @override
  ConsumerState<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends ConsumerState<AnalysisScreen> {
  Json? _analysis;
  Object? _error;
  bool _loading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadLatest();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadLatest() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final p = await ref.read(repositoryProvider).project(widget.projectId);
      _analysis = p['latest_analysis'] == null ? null : asJson(p['latest_analysis']);
      _schedulePoll();
    } catch (e) {
      _error = e;
    }
    if (mounted) setState(() => _loading = false);
  }

  void _schedulePoll() {
    _timer?.cancel();
    if (_analysis?['status'] == 'pending') {
      _timer = Timer(const Duration(seconds: 3), _poll);
    }
  }

  Future<void> _poll() async {
    try {
      final a = await ref.read(repositoryProvider).analysis(_analysis!['id']);
      if (!mounted) return;
      setState(() => _analysis = a);
      if (a['status'] != 'pending') ref.invalidate(projectProvider(widget.projectId));
    } catch (_) {
      // transient network error: keep polling
    }
    if (mounted) _schedulePoll();
  }

  Future<void> _run({bool force = false}) async {
    if (!await ensureAiConsent(context, ref)) return;
    try {
      final a = await ref.read(repositoryProvider).analyze(widget.projectId, force: force, key: ApiClient.newIdempotencyKey());
      if (!mounted) return;
      setState(() => _analysis = a);
      _schedulePoll();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final a = _analysis;
    return Scaffold(
      appBar: AppBar(title: const Text('AI loyiha ekspertizasi')),
      body: _loading
          ? const LoadingView()
          : _error != null
              ? ErrorView(error: _error!, onRetry: _loadLatest)
              : a == null
                  ? EmptyView(
                      icon: Icons.auto_awesome_rounded,
                      title: 'AI ekspertiza',
                      message:
                          "AI loyiha ma'lumotlari va yuklangan hujjatlarni o'rganib, kuchli va zaif tomonlar, tavsiyalar hamda ehtimoliy ekspert savollarini tayyorlaydi.",
                      action: SizedBox(width: 240, child: BusyButton(label: 'Ekspertizani boshlash', onPressed: _run)),
                    )
                  : _body(a),
    );
  }

  Widget _body(Json a) {
    final status = a['status'];
    if (status == 'pending') {
      return ListView(padding: const EdgeInsets.all(16), children: const [
        AiWorkingCard(
            title: 'AI loyihani tahlil qilmoqda...',
            subtitle: "Bu jarayon odatda 30–90 soniya davom etadi. Sahifadan chiqsangiz ham tahlil davom etadi."),
      ]);
    }
    if (status == 'failed') {
      return ListView(padding: const EdgeInsets.all(16), children: [
        ErrorView(error: a['error_message'] ?? 'Ekspertiza bajarilmadi'),
        BusyButton(label: 'Qayta urinish', icon: Icons.refresh, onPressed: () => _run(force: true)),
      ]);
    }
    final r = asJson(a['result']);
    final strengths = asJsonList(r['strengths']);
    final weaknesses = asJsonList(r['weaknesses']);
    final imp = asJson(r['improvements']);
    final questions = asJsonList(r['expected_questions']);
    final dims = asJsonList(r['dimensions']);
    final verification = asJson(r['verification']);
    return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
      Row(children: [
        Expanded(
          child: Text('${formatDate(a['created_at'])} • ${a['ai_model']}',
              style: TextStyle(color: AppColors.slate, fontSize: 12)),
        ),
        if (a['is_outdated'] == true) const StatusChip("Loyiha o'zgargan", color: AppColors.warning),
      ]),
      const SectionTitle('A. Qisqa xulosa'),
      InfoCard(child: Text(r['summary'] ?? '')),
      const SectionTitle('B. Kuchli jihatlar'),
      if (strengths.isEmpty)
        const Text("Materiallarda kuchli jihatlarni tasdiqlovchi yetarli dalil topilmadi.")
      else
        for (final s in strengths)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InfoCard(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 20),
                  const SizedBox(width: 8),
                  Expanded(child: Text(s['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700))),
                ]),
                const SizedBox(height: 6),
                Text(s['explanation'] ?? ''),
                const SizedBox(height: 6),
                Text('Dalil: “${s['evidence_quote']}”',
                    style: TextStyle(color: AppColors.slate, fontSize: 12, fontStyle: FontStyle.italic)),
              ]),
            ),
          ),
      if ((verification['unsupported_strengths_removed'] ?? 0) > 0)
        DisclaimerBox(verification['note'] ?? ''),
      const SectionTitle('C. Aniqlangan kamchiliklar'),
      for (final w in weaknesses)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: InfoCard(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.report_problem_outlined, color: AppColors.warning, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text(w['problem'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700))),
              ]),
              const SizedBox(height: 8),
              KeyValue('Qayerda aniqlandi', w['location'] ?? ''),
              KeyValue('Nima uchun muhim', w['why_important'] ?? ''),
              KeyValue('Qanday tuzatish mumkin', w['how_to_fix'] ?? ''),
            ]),
          ),
        ),
      const SectionTitle('D. Takomillashtirish tavsiyalari'),
      _PriorityGroup('Zudlik bilan', asStrList(imp['immediate']), AppColors.error),
      _PriorityGroup('Muhim', asStrList(imp['important']), AppColors.warning),
      _PriorityGroup('Keyingi bosqich', asStrList(imp['future']), AppColors.primary),
      const SectionTitle('E. Ekspert berishi mumkin bo‘lgan savollar'),
      InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          for (var i = 0; i < questions.length; i++)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${i + 1}. ${questions[i]['question']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(questions[i]['rationale'] ?? '', style: TextStyle(color: AppColors.slate, fontSize: 12)),
              ]),
            ),
        ]),
      ),
      const SectionTitle('F. Himoyaga tayyorgarlik tavsiyalari'),
      InfoCard(child: BulletList(asStrList(r['defense_tips']), icon: Icons.school_outlined)),
      if (asStrList(r['missing_information']).isNotEmpty) ...[
        const SectionTitle("Yetishmayotgan ma'lumotlar"),
        InfoCard(child: BulletList(asStrList(r['missing_information']), icon: Icons.help_outline, color: AppColors.warning)),
      ],
      if (dims.isNotEmpty) ...[
        const SectionTitle("Yo'nalishlar bo'yicha holat"),
        InfoCard(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Column(children: [
            for (final d in dims)
              ListTile(
                dense: true,
                title: Text(d['dimension'] ?? ''),
                subtitle: Text(d['comment'] ?? ''),
                trailing: StatusChip(
                  d['status'] == 'yetarli' ? 'Yetarli' : d['status'] == 'qisman' ? 'Qisman' : 'Aniqlanmadi',
                  color: d['status'] == 'yetarli'
                      ? AppColors.success
                      : d['status'] == 'qisman'
                          ? AppColors.warning
                          : AppColors.slate,
                ),
              ),
          ]),
        ),
      ],
      const SizedBox(height: 16),
      OutlinedButton.icon(
        onPressed: () => context.push('/projects/${widget.projectId}/improvement'),
        icon: const Icon(Icons.tips_and_updates_outlined),
        label: const Text('Loyihani rivojlantirish hisobotini ochish'),
      ),
      const SizedBox(height: 10),
      FilledButton.icon(
        onPressed: () => context.push('/defense/new?project=${widget.projectId}'),
        icon: const Icon(Icons.mic_rounded),
        label: const Text('Himoya mashqini boshlash'),
      ),
      const SizedBox(height: 10),
      BusyButton(label: 'Ekspertizani yangilash', outlined: true, onPressed: () => _run(force: true)),
      const SizedBox(height: 12),
      const DisclaimerBox("AI ekspertiza faqat siz kiritgan ma'lumotlar va hujjatlarga asoslanadi. "
          "Unda ko'rsatilmagan funksiya yoki natijalar mavjud deb hisoblanmaydi."),
    ]);
  }
}

class _PriorityGroup extends StatelessWidget {
  const _PriorityGroup(this.title, this.items, this.color);
  final String title;
  final List<String> items;
  final Color color;
  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          StatusChip(title, color: color),
          const SizedBox(height: 8),
          BulletList(items, color: color),
        ]),
      ),
    );
  }
}

// =============================================================== Project Improvement Report
class ImprovementReportScreen extends ConsumerWidget {
  const ImprovementReportScreen({super.key, required this.projectId, this.sessionId});
  final String projectId;
  final String? sessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final project = ref.watch(projectProvider(projectId));
    final session = sessionId == null ? null : ref.watch(resultsProvider(sessionId!));
    return Scaffold(
      appBar: AppBar(title: const Text('Loyihani rivojlantirish')),
      body: AsyncView<Json>(
        value: project,
        onRetry: () => ref.invalidate(projectProvider(projectId)),
        builder: (p) {
          final analysis = p['latest_analysis'] == null ? null : asJson(p['latest_analysis']);
          final fromAnalysis = analysis != null && analysis['status'] == 'completed'
              ? asJsonList(asJson(analysis['result'])['project_recommendations'])
              : <Json>[];
          final fromDefense = session?.value == null
              ? <Json>[]
              : asJsonList(asJson(asJson(asJson(session!.value)['result'])['summary'])['project_recommendations']);
          if (fromAnalysis.isEmpty && fromDefense.isEmpty) {
            return EmptyView(
              icon: Icons.tips_and_updates_outlined,
              title: "Tavsiyalar hali yo'q",
              message: "Tavsiyalar AI ekspertiza yoki himoya baholangandan so'ng shakllanadi.",
              action: SizedBox(
                width: 220,
                child: FilledButton(
                    onPressed: () => context.push('/projects/$projectId/analysis'), child: const Text('Ekspertiza')),
              ),
            );
          }
          final order = {'Yuqori': 0, "O'rta": 1, 'Past': 2};
          int byPriority(Json a, Json b) => (order[a['priority']] ?? 3).compareTo(order[b['priority']] ?? 3);
          fromAnalysis.sort(byPriority);
          fromDefense.sort(byPriority);
          return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
            Text(p['title'] ?? '', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            if (fromDefense.isNotEmpty) ...[
              const SectionTitle('Himoya javoblari asosida'),
              for (final r in fromDefense) RecommendationCard(r),
            ],
            if (fromAnalysis.isNotEmpty) ...[
              const SectionTitle('Loyiha hujjatlari asosida'),
              for (final r in fromAnalysis) RecommendationCard(r),
            ],
            const SizedBox(height: 8),
            const DisclaimerBox(
                "Tavsiyalar tasdiqlanmagan xulosa emas: ular loyihani yaxshilash uchun yo'nalish beradi va siz kiritgan "
                "ma'lumotlarga asoslanadi."),
          ]);
        },
      ),
    );
  }
}

class RecommendationCard extends StatelessWidget {
  const RecommendationCard(this.r, {super.key});
  final Json r;
  @override
  Widget build(BuildContext context) {
    final color = r['priority'] == 'Yuqori'
        ? AppColors.error
        : r['priority'] == "O'rta"
            ? AppColors.warning
            : AppColors.primary;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Wrap(spacing: 8, runSpacing: 6, children: [
            StatusChip('Ustuvorlik: ${r['priority']}', color: color),
            StatusChip(Labels.recCategories[r['category']] ?? r['category'] ?? '', color: AppColors.slate),
          ]),
          const SizedBox(height: 10),
          Text(r['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 10),
          KeyValue('Aniqlangan muammo', r['problem'] ?? ''),
          KeyValue('Taklif etilayotgan yechim', r['solution'] ?? ''),
          const Text('Amaliy qadamlar', style: TextStyle(color: AppColors.slate, fontSize: 12, fontWeight: FontWeight.w600)),
          BulletList(asStrList(r['steps']), icon: Icons.arrow_right_rounded),
          const SizedBox(height: 8),
          KeyValue('Kutilayotgan natija', r['expected_result'] ?? ''),
          Text('Asos: ${r['based_on'] ?? ''}',
              style: TextStyle(color: AppColors.slate, fontSize: 12, fontStyle: FontStyle.italic)),
        ]),
      ),
    );
  }
}
