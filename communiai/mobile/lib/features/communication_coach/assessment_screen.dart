import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';
import '../defense/defense_screens.dart';

class AssessmentScreen extends ConsumerWidget {
  const AssessmentScreen({super.key, required this.sessionId});
  final String sessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(resultsProvider(sessionId));
    return Scaffold(
      appBar: AppBar(title: const Text('Kommunikativ baholash')),
      body: AsyncView<Json>(
        value: data,
        onRetry: () => ref.invalidate(resultsProvider(sessionId)),
        builder: (s) {
          if (s['result'] == null) {
            return EmptyView(
              icon: Icons.hourglass_empty_rounded,
              title: 'Natija hali tayyor emas',
              message: 'Holat: ${Labels.sessionStatus[s['status']] ?? s['status']}',
              action: FilledButton(
                style: FilledButton.styleFrom(minimumSize: const Size(200, 48)),
                onPressed: () => context.push('/defense/$sessionId'),
                child: const Text('Himoyaga qaytish'),
              ),
            );
          }
          final r = asJson(s['result']);
          final summary = asJson(r['summary']);
          final criteria = asJsonList(r['criteria']);
          final readiness = asJson(r['readiness']);
          final questions = asJsonList(s['questions']);
          final level = r['level'] as String?;
          return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
            Text('${s['project_title'] ?? ''} • ${s['mode_label']}', style: TextStyle(color: AppColors.slate)),
            const SizedBox(height: 12),
            // ---- A. communicative competence (main indicator)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(gradient: AppColors.splashGradient, borderRadius: BorderRadius.circular(20)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Kasbiy kommunikativ kompetentlik', style: TextStyle(color: Colors.white70)),
                const SizedBox(height: 8),
                Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                  Text(formatScore(r['total_score']),
                      style: const TextStyle(color: Colors.white, fontSize: 44, fontWeight: FontWeight.w800, height: 1)),
                  Padding(
                    padding: const EdgeInsets.only(left: 6, bottom: 6),
                    child: Text('/ ${r['max_applicable_score']}',
                        style: const TextStyle(color: Colors.white70, fontSize: 18)),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                    child: Text(level ?? '', style: TextStyle(color: levelColor(level), fontWeight: FontWeight.w800)),
                  ),
                ]),
                const SizedBox(height: 10),
                Text('${formatScore(r['percent'])}% • baholash qamrovi ${((r['coverage'] as num) * 100).round()}% '
                    '• rubrika v${r['rubric_version']}',
                    style: const TextStyle(color: Colors.white)),
              ]),
            ),
            const SizedBox(height: 12),
            InfoCard(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                for (final c in criteria)
                  ScoreBar(code: c['code'], label: c['title'] ?? Labels.competencies[c['code']] ?? '',
                      score: c['score'] as num?, max: c['max_score'] as num),
                const SizedBox(height: 6),
                const Text(
                    "K6 (refleksiya) faqat individual qayta mashqda baholanadi; u baholanmaguncha umumiy balldan chiqarib tashlanadi (0 deb hisoblanmaydi).",
                    style: TextStyle(fontSize: 12, color: AppColors.slate)),
              ]),
            ),
            // ---- B. readiness (separate diagnostic)
            const SectionTitle("Loyihani taqdim etishga tayyorgarlik (qo'shimcha ko'rsatkich)"),
            InfoCard(
              child: readiness['assessed'] == true
                  ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      ScoreBar(label: 'Texnik va mazmuniy tayyorgarlik', score: readiness['percent'] as num?, max: 100),
                      const SizedBox(height: 4),
                      const Text("Bu kommunikativ balldan alohida diagnostik ko'rsatkich.",
                          style: TextStyle(fontSize: 12, color: AppColors.slate)),
                    ])
                  : const Text('Baholanmagan'),
            ),
            const SectionTitle('Umumiy xulosa'),
            InfoCard(child: Text(summary['overall_summary'] ?? '')),
            if (asStrList(summary['strengths']).isNotEmpty) ...[
              const SectionTitle('Kuchli tomonlar'),
              InfoCard(child: BulletList(asStrList(summary['strengths']), icon: Icons.check_circle_outline, color: AppColors.success)),
            ],
            if (asStrList(summary['weaknesses']).isNotEmpty) ...[
              const SectionTitle('Rivojlantirish kerak bo‘lgan jihatlar'),
              InfoCard(child: BulletList(asStrList(summary['weaknesses']), icon: Icons.trending_up, color: AppColors.warning)),
            ],
            const SectionTitle('Batafsil tahlil'),
            InfoCard(
              child: MarkdownBody(
                data: (summary['detailed_analysis'] ?? '').toString(),
                selectable: true,
                // Untrusted text: links and images are not rendered as active content.
                onTapLink: (_, _, _) {},
                imageBuilder: (_, _, _) => const SizedBox.shrink(),
              ),
            ),
            const SectionTitle('Savol-javoblar va feedback'),
            for (final q in questions)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: InfoCard(
                  padding: EdgeInsets.zero,
                  child: ExpansionTile(
                    shape: const Border(),
                    title: Text('${q['sequence_number']}. ${q['question_text']}',
                        maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 14)),
                    childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                    children: [
                      if (q['answer'] != null) ...[
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text('Javobingiz:', style: TextStyle(color: AppColors.slate, fontSize: 12)),
                        ),
                        Align(alignment: Alignment.centerLeft, child: Text(asJson(q['answer'])['answer_text'] ?? '')),
                        const SizedBox(height: 10),
                        if (asJson(q['answer'])['evaluation'] != null) ...[
                          for (final c in asJsonList(asJson(asJson(q['answer'])['evaluation'])['criteria']))
                            _CriterionDetail(c),
                          FeedbackCard(asJson(asJson(asJson(q['answer'])['evaluation'])['feedback'])),
                        ],
                      ],
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 8),
            if (s['plan_id'] != null)
              FilledButton.icon(
                onPressed: () => context.push('/practice/${s['plan_id']}'),
                icon: const Icon(Icons.fitness_center_rounded),
                label: const Text('Individual mashqlarni bajarish'),
              ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () => context.push('/projects/${s['project_id']}/improvement?session=$sessionId'),
              icon: const Icon(Icons.tips_and_updates_outlined),
              label: const Text('Loyihani rivojlantirish tavsiyalari'),
            ),
            const SizedBox(height: 16),
            DisclaimerBox(r['disclaimer'] ?? ''),
            const SizedBox(height: 8),
            for (final l in asStrList(summary['limitations']))
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text('• $l', style: const TextStyle(fontSize: 12, color: AppColors.slate)),
              ),
          ]);
        },
      ),
    );
  }
}

class _CriterionDetail extends StatelessWidget {
  const _CriterionDetail(this.c);
  final Json c;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          ScoreBar(
              code: c['code'],
              label: Labels.competencies[c['code']] ?? '',
              score: c['assessed'] == true ? c['score'] as num? : null,
              max: c['max_score'] as num),
          if (c['assessed'] == true && (c['evidence'] ?? '').toString().isNotEmpty)
            Text('Dalil: “${c['evidence']}”',
                style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: AppColors.slate)),
          if ((c['feedback'] ?? '').toString().isNotEmpty) Text(c['feedback'], style: const TextStyle(fontSize: 13)),
          if ((c['recommendation'] ?? '').toString().isNotEmpty)
            Text('Tavsiya: ${c['recommendation']}', style: const TextStyle(fontSize: 13)),
          if (c['assessed'] != true && (c['confidence_limit'] ?? '').toString().isNotEmpty)
            Text(c['confidence_limit'], style: const TextStyle(fontSize: 12, color: AppColors.warning)),
        ]),
      );
}
