import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';

class HomeShell extends StatelessWidget {
  const HomeShell({super.key, required this.shell});
  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) => Scaffold(
        body: shell,
        bottomNavigationBar: NavigationBar(
          selectedIndex: shell.currentIndex,
          onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Asosiy'),
            NavigationDestination(icon: Icon(Icons.folder_outlined), selectedIcon: Icon(Icons.folder_rounded), label: 'Loyihalar'),
            NavigationDestination(icon: Icon(Icons.mic_none_rounded), selectedIcon: Icon(Icons.mic_rounded), label: 'Himoya'),
            NavigationDestination(icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights_rounded), label: 'Natijalar'),
            NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person_rounded), label: 'Profil'),
          ],
        ),
      );
}

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(dashboardProvider);
    final user = ref.watch(authProvider).user;
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.refresh(dashboardProvider.future),
          child: AsyncView<Json>(
            value: data,
            onRetry: () => ref.invalidate(dashboardProvider),
            builder: (d) => ListView(padding: const EdgeInsets.fromLTRB(20, 16, 20, 32), children: [
              Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Salom, ${d['first_name'] ?? user?.firstName ?? ''} 👋',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    Text('Bugun loyihangizni himoyaga tayyorlaymiz', style: TextStyle(color: AppColors.slate)),
                  ]),
                ),
                CircleAvatar(
                  radius: 24,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                  child: Text(user?.initials ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
                ),
              ]),
              const SizedBox(height: 20),
              Row(children: [
                Expanded(child: _Stat(icon: Icons.folder_rounded, label: 'Jami loyihalar', value: '${d['projects_count']}')),
                const SizedBox(width: 12),
                Expanded(
                    child: _Stat(
                        icon: Icons.verified_rounded, label: 'Yakunlangan himoyalar', value: '${d['completed_defenses']}')),
              ]),
              const SizedBox(height: 12),
              _LatestResult(asJson(d['latest_result']).isEmpty ? null : asJson(d['latest_result'])),
              if (d['ongoing_defense'] != null) ...[
                const SectionTitle('Davom ettirilayotgan himoya'),
                _Ongoing(asJson(d['ongoing_defense'])),
              ],
              const SectionTitle('Tezkor amallar'),
              Row(children: [
                Expanded(
                  child: _Action(
                      icon: Icons.add_circle_outline_rounded,
                      label: 'Yangi loyiha',
                      onTap: () => context.push('/projects/new')),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _Action(
                      icon: Icons.play_circle_outline_rounded,
                      label: 'Himoyani boshlash',
                      onTap: () => context.push('/defense/new')),
                ),
              ]),
              if (asStrList(d['recommendations']).isNotEmpty) ...[
                const SectionTitle("So'nggi AI tavsiyalar"),
                InfoCard(child: BulletList(asStrList(d['recommendations']), icon: Icons.lightbulb_outline_rounded)),
              ],
              SectionTitle('Faoliyatlar tarixi',
                  trailing: TextButton(onPressed: () => context.push('/history'), child: const Text('Barchasi'))),
              if (asJsonList(d['recent_activity']).isEmpty)
                Text("Hali faoliyat yo'q", style: TextStyle(color: AppColors.slate))
              else
                InfoCard(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Column(children: [
                    for (final a in asJsonList(d['recent_activity']))
                      ListTile(
                        dense: true,
                        leading: const Icon(Icons.history_rounded, size: 20),
                        title: Text(a['label'] ?? ''),
                        trailing: Text(formatDate(a['created_at']), style: const TextStyle(fontSize: 12)),
                      ),
                  ]),
                ),
            ]),
          ),
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => InfoCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, color: AppColors.primary),
          const SizedBox(height: 10),
          Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
          Text(label, style: TextStyle(color: AppColors.slate, fontSize: 13)),
        ]),
      );
}

class _LatestResult extends StatelessWidget {
  const _LatestResult(this.r);
  final Json? r;
  @override
  Widget build(BuildContext context) {
    if (r == null) {
      return InfoCard(
        child: Row(children: [
          const Icon(Icons.insights_rounded, color: AppColors.slate),
          const SizedBox(width: 12),
          Expanded(
              child: Text("Kompetentlik natijasi himoya baholangandan so'ng paydo bo'ladi",
                  style: TextStyle(color: AppColors.slate))),
        ]),
      );
    }
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(gradient: AppColors.splashGradient, borderRadius: BorderRadius.circular(18)),
      child: InkWell(
        onTap: () => context.push('/defense/${r!['session_id']}/assessment'),
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text("So'nggi kompetentlik natijasi", style: TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 6),
              Text('${formatScore(r!['total_score'])} / ${r!['max_applicable_score']}',
                  style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              Text('${r!['level']} • qamrov ${((r!['coverage'] as num) * 100).round()}%',
                  style: const TextStyle(color: Colors.white)),
            ]),
          ),
          const Icon(Icons.chevron_right_rounded, color: Colors.white),
        ]),
      ),
    );
  }
}

class _Ongoing extends StatelessWidget {
  const _Ongoing(this.s);
  final Json s;
  @override
  Widget build(BuildContext context) => InfoCard(
        onTap: () => context.push('/defense/${s['id']}'),
        child: Row(children: [
          const CircleAvatar(child: Icon(Icons.mic_rounded)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(s['project_title'] ?? '', maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text('${Labels.modes[s['mode']]} • ${s['answered']}/${s['question_limit']} javob',
                  style: TextStyle(color: AppColors.slate, fontSize: 13)),
            ]),
          ),
          StatusChip(Labels.sessionStatus[s['status']] ?? s['status'], color: sessionStatusColor(s['status'])),
        ]),
      );
}

class _Action extends StatelessWidget {
  const _Action({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InfoCard(
        onTap: onTap,
        child: Column(children: [
          Icon(icon, size: 32, color: AppColors.primary),
          const SizedBox(height: 8),
          Text(label, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w600)),
        ]),
      );
}
