import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/models.dart';
import '../../core/config.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';
import '../auth/auth_screens.dart';

// =============================================================== Profile
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _edit(BuildContext context, WidgetRef ref, AppUser u) async {
    final c = {
      'first_name': TextEditingController(text: u.firstName),
      'last_name': TextEditingController(text: u.lastName),
      'university': TextEditingController(text: u.university),
      'study_program': TextEditingController(text: u.studyProgram),
    };
    const labels = {'first_name': 'Ism', 'last_name': 'Familiya', 'university': 'Universitet', 'study_program': "Ta'lim yo'nalishi"};
    final form = GlobalKey<FormState>();
    final ok = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
        child: Form(
          key: form,
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Profilni tahrirlash', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
            const SizedBox(height: 16),
            for (final e in c.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextFormField(
                  controller: e.value,
                  decoration: InputDecoration(labelText: labels[e.key]),
                  validator: (v) => requiredField(v, labels[e.key]!),
                ),
              ),
            FilledButton(
                onPressed: () {
                  if (form.currentState!.validate()) Navigator.pop(ctx, true);
                },
                child: const Text('Saqlash')),
          ]),
        ),
      ),
    );
    if (ok != true) return;
    try {
      final updated = await ref.read(repositoryProvider).updateProfile({for (final e in c.entries) e.key: e.value.text.trim()});
      ref.read(authProvider.notifier).setUser(updated);
      if (context.mounted) showMessage(context, 'Profil yangilandi');
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final u = ref.watch(authProvider).user;
    if (u == null) return const Scaffold(body: LoadingView());
    return Scaffold(
      appBar: AppBar(title: const Text('Profil')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        InfoCard(
          child: Row(children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: AppColors.primary,
              child: Text(u.initials, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(u.fullName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                Text(u.email, style: const TextStyle(color: AppColors.slate)),
                const SizedBox(height: 6),
                StatusChip(u.isAdmin ? 'Administrator' : 'Talaba'),
              ]),
            ),
          ]),
        ),
        const SizedBox(height: 12),
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            KeyValue('Universitet', u.university),
            KeyValue("Ta'lim yo'nalishi", u.studyProgram),
            KeyValue('AI tahliliga rozilik', u.hasAiConsent ? 'Berilgan (${formatDate(u.aiConsentAt?.toIso8601String())})' : 'Berilmagan'),
          ]),
        ),
        const SizedBox(height: 12),
        _tile(Icons.edit_outlined, 'Profilni tahrirlash', () => _edit(context, ref, u)),
        _tile(Icons.history, 'Faoliyatlar tarixi', () => context.push('/history')),
        _tile(Icons.settings_outlined, 'Sozlamalar', () => context.push('/settings')),
        if (u.isAdmin) _tile(Icons.admin_panel_settings_outlined, 'Administrator paneli', () => context.push('/admin')),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(foregroundColor: AppColors.error),
          onPressed: () async {
            await ref.read(authProvider.notifier).logout();
            if (context.mounted) context.go('/login');
          },
          icon: const Icon(Icons.logout),
          label: const Text('Chiqish'),
        ),
      ]),
    );
  }

  Widget _tile(IconData icon, String title, VoidCallback onTap) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: InfoCard(
          padding: EdgeInsets.zero,
          child: ListTile(leading: Icon(icon), title: Text(title), trailing: const Icon(Icons.chevron_right), onTap: onTap),
        ),
      );
}

// =============================================================== Settings
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  Future<void> _changePassword(BuildContext context, WidgetRef ref) async {
    final cur = TextEditingController();
    final next = TextEditingController();
    final form = GlobalKey<FormState>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Parolni o'zgartirish"),
        content: Form(
          key: form,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextFormField(controller: cur, obscureText: true, decoration: const InputDecoration(labelText: 'Joriy parol'),
                validator: (v) => requiredField(v, 'Parol')),
            const SizedBox(height: 12),
            TextFormField(controller: next, obscureText: true, decoration: const InputDecoration(labelText: 'Yangi parol'),
                validator: passwordValidator),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Bekor qilish')),
          TextButton(
              onPressed: () {
                if (form.currentState!.validate()) Navigator.pop(ctx, true);
              },
              child: const Text('Saqlash')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(repositoryProvider).changePassword(cur.text, next.text);
      if (context.mounted) showMessage(context, "Parol o'zgartirildi");
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _export(BuildContext context, WidgetRef ref) async {
    try {
      final data = await ref.read(repositoryProvider).exportData();
      final bytes = utf8.encode(const JsonEncoder.withIndent('  ').convert(data));
      final uri = await FilePicker.saveFile(
        dialogTitle: "Ma'lumotlarni saqlash",
        fileName: 'communiai-export.json',
        bytes: Uint8List.fromList(bytes),
        mimeType: 'application/json',
      );
      if (context.mounted) {
        showMessage(context, uri == null ? 'Saqlash bekor qilindi' : "Ma'lumotlar eksport qilindi");
      }
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _deleteAccount(BuildContext context, WidgetRef ref) async {
    final confirm = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Hisobni o'chirish"),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text("Hisobingiz, loyihalar, fayllar va barcha natijalar butunlay o'chiriladi. Bu amalni qaytarib bo'lmaydi.\n\n"
              "Tasdiqlash uchun O'CHIRISH deb yozing."),
          const SizedBox(height: 12),
          TextField(controller: confirm),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Bekor qilish')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () => Navigator.pop(ctx, confirm.text.trim().toUpperCase() == "O'CHIRISH"),
            child: const Text("O'chirish"),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(repositoryProvider).deleteAccount();
      await ref.read(authProvider.notifier).forgetSession();
      if (context.mounted) context.go('/login');
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _toggleConsent(BuildContext context, WidgetRef ref, bool value) async {
    try {
      final u = await ref.read(repositoryProvider).updateProfile({'ai_consent': value});
      ref.read(authProvider.notifier).setUser(u);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _supportAccess(BuildContext context, WidgetRef ref, bool value) async {
    try {
      final u = await ref.read(repositoryProvider).updateProfile({'support_access_days': value ? 3 : 0});
      ref.read(authProvider.notifier).setUser(u);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(themeModeProvider);
    final u = ref.watch(authProvider).user;
    final supportActive = u?.supportAccessUntil != null && u!.supportAccessUntil!.isAfter(DateTime.now());
    final meta = ref.watch(metaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Sozlamalar')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const SectionTitle('Ko‘rinish'),
        InfoCard(
          child: SegmentedButton<ThemeMode>(
            segments: const [
              ButtonSegment(value: ThemeMode.light, label: Text('Yorug‘'), icon: Icon(Icons.light_mode_outlined)),
              ButtonSegment(value: ThemeMode.dark, label: Text('Tungi'), icon: Icon(Icons.dark_mode_outlined)),
              ButtonSegment(value: ThemeMode.system, label: Text('Tizim'), icon: Icon(Icons.phone_android)),
            ],
            selected: {mode},
            onSelectionChanged: (s) => ref.read(themeModeProvider.notifier).set(s.first),
          ),
        ),
        const SectionTitle('Maxfiylik'),
        InfoCard(
          padding: EdgeInsets.zero,
          child: Column(children: [
            SwitchListTile(
              title: const Text('AI tahliliga rozilik'),
              subtitle: const Text("Loyiha ma'lumotlari va javoblar tahlil uchun AI xizmatiga yuboriladi. Modelni o'qitishda ishlatilmaydi."),
              value: u?.hasAiConsent ?? false,
              onChanged: (v) => _toggleConsent(context, ref, v),
            ),
            const Divider(height: 1),
            SwitchListTile(
              title: const Text('Texnik yordamga ruxsat (3 kun)'),
              subtitle: Text(supportActive
                  ? 'Faol: ${formatDate(u.supportAccessUntil!.toIso8601String())} gacha. Har bir kirish auditda qayd etiladi.'
                  : "Administrator loyiha mazmunini faqat siz ruxsat bergandagina ko'ra oladi."),
              value: supportActive,
              onChanged: (v) => _supportAccess(context, ref, v),
            ),
          ]),
        ),
        const SectionTitle('Hisob'),
        InfoCard(
          padding: EdgeInsets.zero,
          child: Column(children: [
            ListTile(leading: const Icon(Icons.lock_outline), title: const Text("Parolni o'zgartirish"),
                onTap: () => _changePassword(context, ref)),
            const Divider(height: 1),
            ListTile(leading: const Icon(Icons.download_outlined), title: const Text("Ma'lumotlarimni eksport qilish (JSON)"),
                onTap: () => _export(context, ref)),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.delete_forever_outlined, color: AppColors.error),
              title: const Text("Hisobni o'chirish", style: TextStyle(color: AppColors.error)),
              onTap: () => _deleteAccount(context, ref),
            ),
          ]),
        ),
        const SectionTitle('Server'),
        InfoCard(
          padding: EdgeInsets.zero,
          child: Column(children: [
            ListTile(
              leading: const Icon(Icons.dns_outlined),
              title: const Text('Server manzili'),
              subtitle: Text(ref.read(prefsProvider).baseUrl),
              onTap: () => showServerDialog(context, ref),
            ),
            const Divider(height: 1),
            meta.when(
              data: (m) => ListTile(
                leading: Icon(m['ai_configured'] == true ? Icons.cloud_done_outlined : Icons.cloud_off_outlined,
                    color: m['ai_configured'] == true ? AppColors.success : AppColors.warning),
                title: Text(m['ai_configured'] == true ? 'AI xizmati ulangan' : 'AI xizmati serverda sozlanmagan'),
                subtitle: Text('API v${m['version']} • rubrika v${m['rubric_version']}'),
              ),
              error: (e, _) => ListTile(
                leading: const Icon(Icons.error_outline, color: AppColors.error),
                title: const Text('Server holatini olib bo‘lmadi'),
                trailing: IconButton(icon: const Icon(Icons.refresh), onPressed: () => ref.invalidate(metaProvider)),
              ),
              loading: () => const ListTile(title: Text('Tekshirilmoqda...')),
            ),
          ]),
        ),
        const SectionTitle('Ilova haqida'),
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('${AppConfig.appName} ${AppConfig.version} (MVP)', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            const Text(AppConfig.slogan),
            const SizedBox(height: 8),
            const Text("60610100 — Axborot tizimlari va texnologiyalari yo'nalishi talabalari uchun kasbiy kommunikativ "
                "kompetentlikni rivojlantirish platformasi.",
                style: TextStyle(fontSize: 13, color: AppColors.slate)),
            TextButton(
              onPressed: () => Clipboard.setData(ClipboardData(text: ref.read(prefsProvider).baseUrl)),
              child: const Text('Server manzilini nusxalash'),
            ),
          ]),
        ),
      ]),
    );
  }
}

// =============================================================== Admin panel
class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});
  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

final _adminSystem = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).adminSystem());
final _adminUsers = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).adminUsers());
final _adminAi = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).adminAiRequests());
final _adminErrors = FutureProvider.autoDispose<Json>((ref) => ref.watch(repositoryProvider).adminErrors());

class _AdminScreenState extends ConsumerState<AdminScreen> {
  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 4,
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Administrator'),
            bottom: const TabBar(isScrollable: true, tabs: [
              Tab(text: 'Tizim'),
              Tab(text: 'Foydalanuvchilar'),
              Tab(text: "AI so'rovlari"),
              Tab(text: 'Xatoliklar'),
            ]),
          ),
          body: TabBarView(children: [_system(), _users(), _ai(), _errors()]),
        ),
      );

  Widget _system() => AsyncView<Json>(
        value: ref.watch(_adminSystem),
        onRetry: () => ref.invalidate(_adminSystem),
        builder: (s) {
          final ai = asJson(s['ai']);
          final last = asJson(s['last_24h']);
          final settings = asJson(s['settings']);
          return RefreshIndicator(
            onRefresh: () => ref.refresh(_adminSystem.future),
            child: ListView(padding: const EdgeInsets.all(16), children: [
              InfoCard(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  KeyValue("Ma'lumotlar bazasi", s['database'] ?? ''),
                  KeyValue('AI provayder', '${ai['provider']} • ${ai['model']} • ${ai['configured'] == true ? 'sozlangan' : 'sozlanmagan'}'),
                  KeyValue('Email xizmati', s['email_configured'] == true ? 'sozlangan' : 'sozlanmagan'),
                  KeyValue('Fayl saqlash', s['storage_backend'] ?? ''),
                  KeyValue('Rubrika versiyasi', s['rubric_version'] ?? ''),
                  KeyValue('Foydalanuvchilar', '${s['users_total']}'),
                  KeyValue("So'nggi 24 soat", "AI so'rovlari: ${last['ai_requests']}, xatolar: ${last['ai_errors']}, "
                      "o'rtacha kechikish: ${last['ai_avg_latency_ms']} ms\nVazifalar: ${last['jobs']}"),
                ]),
              ),
              const SizedBox(height: 12),
              InfoCard(
                padding: EdgeInsets.zero,
                child: Column(children: [
                  SwitchListTile(
                    title: const Text('AI operatsiyalari yoqilgan'),
                    subtitle: const Text("O'chirilsa, AI so'rovlari bajarilmaydi (texnik xizmat rejimi)"),
                    value: settings['ai_enabled'] != false,
                    onChanged: (v) => _set('ai_enabled', v),
                  ),
                  SwitchListTile(
                    title: const Text("Ro'yxatdan o'tish ochiq"),
                    value: settings['registration_open'] != false,
                    onChanged: (v) => _set('registration_open', v),
                  ),
                ]),
              ),
              const SizedBox(height: 12),
              const DisclaimerBox("Administrator talabalarning loyiha matnlarini avtomatik ko'ra olmaydi. Kirish faqat "
                  "talaba ruxsati bilan va audit jurnalida qayd etilgan holda mumkin."),
            ]),
          );
        },
      );

  Future<void> _set(String key, Object value) async {
    try {
      await ref.read(repositoryProvider).adminSetSetting(key, value);
      ref.invalidate(_adminSystem);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Widget _users() => AsyncView<Json>(
        value: ref.watch(_adminUsers),
        onRetry: () => ref.invalidate(_adminUsers),
        builder: (d) {
          final items = asJsonList(d['items']);
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final u = items[i];
              return InfoCard(
                padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
                child: Row(children: [
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('${u['first_name']} ${u['last_name']}', style: const TextStyle(fontWeight: FontWeight.w700)),
                      Text(u['email'], style: const TextStyle(fontSize: 13, color: AppColors.slate)),
                      Text('${u['role']} • ${u['projects_count']} loyiha • ${u['defenses_count']} himoya',
                          style: const TextStyle(fontSize: 12, color: AppColors.slate)),
                    ]),
                  ),
                  Switch(
                    value: u['is_active'] == true,
                    onChanged: (v) async {
                      try {
                        await ref.read(repositoryProvider).adminSetUserActive(u['id'], v);
                        ref.invalidate(_adminUsers);
                      } catch (e) {
                        if (mounted) showError(context, e);
                      }
                    },
                  ),
                ]),
              );
            },
          );
        },
      );

  Widget _ai() => AsyncView<Json>(
        value: ref.watch(_adminAi),
        onRetry: () => ref.invalidate(_adminAi),
        builder: (d) {
          final items = asJsonList(d['items']);
          if (items.isEmpty) return const EmptyView(icon: Icons.memory, title: "AI so'rovlari yo'q");
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) {
              final r = items[i];
              return ListTile(
                dense: true,
                leading: Icon(r['status'] == 'ok' ? Icons.check_circle_outline : Icons.error_outline,
                    color: r['status'] == 'ok' ? AppColors.success : AppColors.error),
                title: Text('${r['operation']} • ${r['latency_ms']} ms'),
                subtitle: Text('${r['model']} • in ${r['input_tokens'] ?? '-'} / out ${r['output_tokens'] ?? '-'}'
                    '${r['error_type'] != null ? ' • ${r['error_type']}' : ''}\n${formatDate(r['created_at'])}'),
              );
            },
          );
        },
      );

  Widget _errors() => AsyncView<Json>(
        value: ref.watch(_adminErrors),
        onRetry: () => ref.invalidate(_adminErrors),
        builder: (d) {
          final items = asJsonList(d['items']);
          if (items.isEmpty) return const EmptyView(icon: Icons.verified_outlined, title: "Xatoliklar yo'q");
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) {
              final j = items[i];
              return ListTile(
                leading: const Icon(Icons.error_outline, color: AppColors.error),
                title: Text('${j['kind']} • ${j['error_code']}'),
                subtitle: Text('${j['error_message'] ?? ''}\n${formatDate(j['created_at'])}'),
              );
            },
          );
        },
      );
}
