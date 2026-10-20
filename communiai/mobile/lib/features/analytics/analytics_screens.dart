import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';

// =============================================================== Competency Progress (Natijalar tab)
class CompetencyProgressScreen extends ConsumerWidget {
  const CompetencyProgressScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final comp = ref.watch(competenciesProvider);
    final prog = ref.watch(progressProvider);
    final plans = ref.watch(plansProvider);
    Future<void> refresh() async {
      ref.invalidate(competenciesProvider);
      ref.invalidate(progressProvider);
      ref.invalidate(plansProvider);
      await ref.read(progressProvider.future);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Natijalar'), actions: [
        IconButton(tooltip: 'Faoliyatlar tarixi', onPressed: () => context.push('/history'), icon: const Icon(Icons.history)),
      ]),
      body: RefreshIndicator(
        onRefresh: refresh,
        child: AsyncView<Json>(
          value: comp,
          onRetry: refresh,
          builder: (c) {
            if (c['latest'] == null) {
              return ListView(children: [
                const SizedBox(height: 80),
                EmptyView(
                  icon: Icons.insights_rounded,
                  title: "Natijalar hali yo'q",
                  message: "Birinchi himoyangiz baholangandan so'ng kompetentlik natijalari va rivojlanish grafiklari shu yerda ko'rinadi.",
                  action: FilledButton(
                    style: FilledButton.styleFrom(minimumSize: const Size(200, 48)),
                    onPressed: () => context.push('/defense/new'),
                    child: const Text('Himoyani boshlash'),
                  ),
                ),
              ]);
            }
            final latest = asJson(c['latest']);
            final criteria = asJsonList(latest['criteria']);
            final byCrit = asJson(c['by_criterion']);
            return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
              InfoCard(
                onTap: () => context.push('/defense/${latest['session_id']}/assessment'),
                child: Row(children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text("So'nggi natija", style: TextStyle(color: AppColors.slate)),
                      Text('${formatScore(latest['total_score'])} / ${latest['max_applicable_score']}',
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                      Text('Qamrov ${((latest['coverage'] as num) * 100).round()}% • rubrika v${latest['rubric_version']}',
                          style: const TextStyle(fontSize: 12, color: AppColors.slate)),
                    ]),
                  ),
                  StatusChip(latest['level'] ?? '', color: levelColor(latest['level'])),
                ]),
              ),
              const SectionTitle("Kompetensiyalar bo'yicha (%)"),
              InfoCard(child: SizedBox(height: 220, child: _CriteriaBarChart(criteria, byCrit))),
              const SectionTitle('Rivojlanish dinamikasi'),
              prog.when(
                data: (p) => _ProgressSection(p),
                error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(progressProvider)),
                loading: () => const LoadingView(),
              ),
              const SectionTitle('Individual mashq rejalari'),
              plans.when(
                data: (d) {
                  final items = asJsonList(d['items']);
                  if (items.isEmpty) return const Text("Mashq rejalari yo'q", style: TextStyle(color: AppColors.slate));
                  return Column(children: [
                    for (final pl in items)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: InfoCard(
                          onTap: () => context.push('/practice/${pl['id']}'),
                          child: Row(children: [
                            const Icon(Icons.fitness_center_rounded, color: AppColors.primary),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text(pl['project_title'] ?? '', maxLines: 1, overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontWeight: FontWeight.w700)),
                                Text('Maqsad: ${asStrList(pl['target_competencies']).join(', ')} • '
                                    '${asJsonList(pl['attempts']).length} urinish',
                                    style: const TextStyle(fontSize: 13, color: AppColors.slate)),
                              ]),
                            ),
                            StatusChip(pl['status'] == 'completed' ? 'Bajarildi' : 'Faol',
                                color: pl['status'] == 'completed' ? AppColors.success : AppColors.primary),
                          ]),
                        ),
                      ),
                  ]);
                },
                error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(plansProvider)),
                loading: () => const LoadingView(),
              ),
              const SizedBox(height: 12),
              const DisclaimerBox("Ballar va darajalar AI asosidagi dastlabki diagnostika bo'lib, validatsiyadan o'tgan "
                  "pedagogik o'lchov hisoblanmaydi. Daraja chegaralari: 86–100 Yetuk, 71–85 Mas'uliyatli, "
                  "56–70 Shakllanayotgan, 0–55 Intiluvchan."),
            ]);
          },
        ),
      ),
    );
  }
}

class _CriteriaBarChart extends StatelessWidget {
  const _CriteriaBarChart(this.criteria, this.byCrit);
  final List<Json> criteria;
  final Json byCrit;

  @override
  Widget build(BuildContext context) {
    final groups = <BarChartGroupData>[];
    for (var i = 0; i < criteria.length; i++) {
      final c = criteria[i];
      num? pct = c['percent'] as num?;
      if (c['code'] == 'K6') {
        final k6 = asJsonList(byCrit['K6']);
        pct = k6.isEmpty ? null : k6.last['percent'] as num?;
      }
      groups.add(BarChartGroupData(x: i, barRods: [
        BarChartRodData(
          toY: (pct ?? 0).toDouble(),
          width: 22,
          color: pct == null ? AppColors.slate.withValues(alpha: 0.25) : AppColors.primary,
          borderRadius: BorderRadius.circular(6),
          backDrawRodData: BackgroundBarChartRodData(show: true, toY: 100, color: AppColors.slate.withValues(alpha: 0.08)),
        ),
      ]));
    }
    return BarChart(BarChartData(
      maxY: 100,
      minY: 0,
      barGroups: groups,
      gridData: const FlGridData(show: false),
      borderData: FlBorderData(show: false),
      titlesData: FlTitlesData(
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 32, interval: 25)),
        bottomTitles: AxisTitles(
          sideTitles: SideTitles(
            showTitles: true,
            getTitlesWidget: (v, meta) => SideTitleWidget(
              meta: meta,
              child: Text(criteria[v.toInt()]['code'], style: const TextStyle(fontWeight: FontWeight.w700)),
            ),
          ),
        ),
      ),
    ));
  }
}

class _ProgressSection extends StatelessWidget {
  const _ProgressSection(this.p);
  final Json p;
  @override
  Widget build(BuildContext context) {
    final sessions = asJsonList(p['sessions']);
    final practice = asJsonList(p['practice']);
    final spots = <FlSpot>[
      for (var i = 0; i < sessions.length; i++) FlSpot(i.toDouble(), ((sessions[i]['percent'] ?? 0) as num).toDouble()),
    ];
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      InfoCard(
        child: sessions.length < 2
            ? const Text("Dinamika grafigi kamida 2 ta baholangan himoyadan so'ng ko'rinadi.",
                style: TextStyle(color: AppColors.slate))
            : SizedBox(
                height: 200,
                child: LineChart(LineChartData(
                  minY: 0,
                  maxY: 100,
                  gridData: const FlGridData(show: true, drawVerticalLine: false),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 32, interval: 25)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: 1,
                        getTitlesWidget: (v, meta) => SideTitleWidget(meta: meta, child: Text('${v.toInt() + 1}')),
                      ),
                    ),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: AppColors.primary,
                      barWidth: 3,
                      dotData: const FlDotData(show: true),
                      belowBarData: BarAreaData(show: true, color: AppColors.primary.withValues(alpha: 0.1)),
                    ),
                  ],
                )),
              ),
      ),
      if (practice.isNotEmpty) ...[
        const SizedBox(height: 10),
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text("Qayta mashq natijalari (oldin → keyin)", style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            for (final r in practice.reversed.take(8))
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(children: [
                  SizedBox(width: 36, child: Text(r['competency'], style: const TextStyle(fontWeight: FontWeight.w700))),
                  Expanded(child: Text('${formatScore(r['before'])} → ${formatScore(r['after'])}')),
                  Text(
                    r['delta'] == null ? '—' : '${(r['delta'] as num) > 0 ? '+' : ''}${formatScore(r['delta'])}',
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: r['delta'] != null && (r['delta'] as num) > 0 ? AppColors.success : AppColors.slate),
                  ),
                  const SizedBox(width: 8),
                  Text(formatDate(r['date'], time: false), style: const TextStyle(fontSize: 12, color: AppColors.slate)),
                ]),
              ),
          ]),
        ),
      ],
      const SizedBox(height: 10),
      for (final s in sessions.reversed)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: InfoCard(
            onTap: () => context.push('/defense/${s['session_id']}/assessment'),
            child: Row(children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(Labels.modes[s['mode']] ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
                  Text(formatDate(s['date']), style: const TextStyle(fontSize: 12, color: AppColors.slate)),
                ]),
              ),
              Text('${formatScore(s['total_score'])}/${s['max_applicable_score']}',
                  style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(width: 8),
              StatusChip(s['level'] ?? '', color: levelColor(s['level'])),
            ]),
          ),
        ),
    ]);
  }
}

// =============================================================== Activity History
class ActivityHistoryScreen extends ConsumerStatefulWidget {
  const ActivityHistoryScreen({super.key});
  @override
  ConsumerState<ActivityHistoryScreen> createState() => _ActivityHistoryScreenState();
}

class _ActivityHistoryScreenState extends ConsumerState<ActivityHistoryScreen> {
  final List<Json> _items = [];
  int _page = 0;
  int _total = 0;
  bool _loading = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _more();
  }

  Future<void> _more({bool reset = false}) async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _error = null;
      if (reset) {
        _items.clear();
        _page = 0;
      }
    });
    try {
      final d = await ref.read(repositoryProvider).history(page: _page + 1);
      _page++;
      _total = d['total'] as int;
      _items.addAll(asJsonList(d['items']));
    } catch (e) {
      _error = e;
    }
    if (mounted) setState(() => _loading = false);
  }

  IconData _icon(String action) => switch (action.split('.').first) {
        'project' => Icons.folder_outlined,
        'file' => Icons.attach_file,
        'analysis' => Icons.auto_awesome_outlined,
        'defense' => Icons.mic_none_rounded,
        'practice' => Icons.fitness_center_outlined,
        _ => Icons.person_outline,
      };

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Faoliyatlar tarixi')),
        body: _items.isEmpty && _loading
            ? const LoadingView()
            : _items.isEmpty && _error != null
                ? ErrorView(error: _error!, onRetry: () => _more(reset: true))
                : _items.isEmpty
                    ? const EmptyView(icon: Icons.history, title: "Faoliyat yo'q")
                    : RefreshIndicator(
                        onRefresh: () => _more(reset: true),
                        child: ListView.builder(
                          itemCount: _items.length + 1,
                          itemBuilder: (_, i) {
                            if (i == _items.length) {
                              if (_items.length >= _total) return const SizedBox(height: 24);
                              return Padding(
                                padding: const EdgeInsets.all(16),
                                child: OutlinedButton(
                                    onPressed: _loading ? null : _more,
                                    child: Text(_loading ? 'Yuklanmoqda...' : "Ko'proq ko'rsatish")),
                              );
                            }
                            final a = _items[i];
                            return ListTile(
                              leading: CircleAvatar(child: Icon(_icon(a['action']), size: 20)),
                              title: Text(a['label'] ?? ''),
                              subtitle: Text(formatDate(a['created_at'])),
                            );
                          },
                        ),
                      ),
      );
}
