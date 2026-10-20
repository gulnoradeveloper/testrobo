import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/common.dart';

// =============================================================== My Projects
class ProjectsListScreen extends ConsumerWidget {
  const ProjectsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(projectsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Loyihalarim')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/projects/new'),
        icon: const Icon(Icons.add),
        label: const Text('Yangi loyiha'),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(projectsProvider.future),
        child: AsyncView<Json>(
          value: data,
          onRetry: () => ref.invalidate(projectsProvider),
          builder: (d) {
            final items = asJsonList(d['items']);
            if (items.isEmpty) {
              return ListView(children: [
                const SizedBox(height: 80),
                EmptyView(
                  icon: Icons.folder_open_rounded,
                  title: "Hali loyiha yo'q",
                  message: "Birinchi loyihangizni yarating va AI ekspertiza oling.",
                  action: FilledButton.icon(
                    style: FilledButton.styleFrom(minimumSize: const Size(200, 48)),
                    onPressed: () => context.push('/projects/new'),
                    icon: const Icon(Icons.add),
                    label: const Text('Loyiha yaratish'),
                  ),
                ),
              ]);
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (_, i) => ProjectCard(items[i]),
            );
          },
        ),
      ),
    );
  }
}

class ProjectCard extends StatelessWidget {
  const ProjectCard(this.p, {super.key});
  final Json p;
  @override
  Widget build(BuildContext context) => InfoCard(
        onTap: () => context.push('/projects/${p['id']}'),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
              child: const Icon(Icons.apps_rounded, color: AppColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(p['title'] ?? '',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                const SizedBox(height: 2),
                Text(Labels.categories[p['category']] ?? '', style: TextStyle(color: AppColors.slate, fontSize: 13)),
              ]),
            ),
          ]),
          const SizedBox(height: 10),
          Text(p['description'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 10),
          Wrap(spacing: 8, runSpacing: 6, children: [
            StatusChip('${p['files_count']} fayl', icon: Icons.attach_file, color: AppColors.slate),
            StatusChip('${p['defenses_count']} himoya', icon: Icons.mic_none, color: AppColors.slate),
            StatusChip(formatDate(p['updated_at'], time: false), icon: Icons.schedule, color: AppColors.slate),
          ]),
        ]),
      );
}

// =============================================================== Create / Edit
class ProjectFormScreen extends ConsumerStatefulWidget {
  const ProjectFormScreen({super.key, this.projectId});
  final String? projectId;
  @override
  ConsumerState<ProjectFormScreen> createState() => _ProjectFormScreenState();
}

class _ProjectFormScreenState extends ConsumerState<ProjectFormScreen> {
  final _form = GlobalKey<FormState>();
  static const _fields = [
    ('title', 'Loyiha nomi *', 1),
    ('description', 'Loyiha tavsifi *', 4),
    ('problem', 'Hal qilinayotgan muammo *', 3),
    ('objective', 'Maqsad', 2),
    ('target_users', 'Maqsadli foydalanuvchilar', 2),
    ('features', 'Asosiy funksiyalar', 3),
    ('technologies', 'Ishlatilgan texnologiyalar', 2),
    ('innovation', 'Innovatsion jihatlar', 2),
    ('expected_results', 'Kutilayotgan natijalar', 2),
    ('future_plans', 'Rivojlantirish rejalari', 2),
  ];
  final _c = {for (final f in _fields) f.$1: TextEditingController()};
  String _category = 'info_system';
  bool _loading = false;
  Object? _loadError;

  bool get _edit => widget.projectId != null;

  @override
  void initState() {
    super.initState();
    if (_edit) _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final p = await ref.read(repositoryProvider).project(widget.projectId!);
      for (final f in _fields) {
        _c[f.$1]!.text = (p[f.$1] ?? '').toString();
      }
      _category = p['category'];
    } catch (e) {
      _loadError = e;
    }
    if (mounted) setState(() => _loading = false);
  }

  String? _validate(String key, String? v) {
    final t = (v ?? '').trim();
    switch (key) {
      case 'title':
        return t.length < 3 ? "Nom kamida 3 ta belgidan iborat bo'lsin" : null;
      case 'description':
        return t.length < 20 ? "Tavsif kamida 20 ta belgidan iborat bo'lsin" : null;
      case 'problem':
        return t.length < 10 ? "Muammoni kamida 10 ta belgida bayon qiling" : null;
    }
    return t.length > 5000 ? 'Matn juda uzun' : null;
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    final body = <String, dynamic>{'category': _category, for (final f in _fields) f.$1: _c[f.$1]!.text.trim()};
    try {
      final repo = ref.read(repositoryProvider);
      final p = _edit ? await repo.updateProject(widget.projectId!, body) : await repo.createProject(body);
      ref.invalidate(projectsProvider);
      ref.invalidate(dashboardProvider);
      if (_edit) ref.invalidate(projectProvider(widget.projectId!));
      if (!mounted) return;
      showMessage(context, _edit ? 'Loyiha yangilandi' : 'Loyiha yaratildi');
      if (_edit) {
        context.pop();
      } else {
        context.pushReplacement('/projects/${p['id']}');
      }
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(_edit ? 'Loyihani tahrirlash' : 'Yangi loyiha')),
        body: _loading
            ? const LoadingView()
            : _loadError != null
                ? ErrorView(error: _loadError!, onRetry: _load)
                : SafeArea(
                    child: Form(
                      key: _form,
                      child: ListView(padding: const EdgeInsets.all(16), children: [
                        DropdownButtonFormField<String>(
                          initialValue: _category,
                          isExpanded: true,
                          decoration: const InputDecoration(labelText: 'Loyiha turi *'),
                          items: [
                            for (final e in Labels.categories.entries)
                              DropdownMenuItem(value: e.key, child: Text(e.value)),
                          ],
                          onChanged: (v) => setState(() => _category = v ?? _category),
                        ),
                        const SizedBox(height: 14),
                        for (final f in _fields)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 14),
                            child: TextFormField(
                              controller: _c[f.$1],
                              minLines: f.$3,
                              maxLines: f.$3 == 1 ? 1 : 8,
                              textCapitalization: TextCapitalization.sentences,
                              decoration: InputDecoration(labelText: f.$2, alignLabelWithHint: true),
                              validator: (v) => _validate(f.$1, v),
                            ),
                          ),
                        const Text('* — majburiy maydonlar', style: TextStyle(fontSize: 12, color: AppColors.slate)),
                        const SizedBox(height: 16),
                        BusyButton(label: _edit ? 'Saqlash' : 'Loyihani yaratish', onPressed: _save),
                      ]),
                    ),
                  ),
      );
}

// =============================================================== Project details
class ProjectDetailScreen extends ConsumerWidget {
  const ProjectDetailScreen({super.key, required this.id});
  final String id;

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Loyihani o'chirish"),
        content: const Text("Loyiha va unga yuklangan fayllar o'chiriladi. Davom etasizmi?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Bekor qilish')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text("O'chirish"),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(repositoryProvider).deleteProject(id);
      ref.invalidate(projectsProvider);
      ref.invalidate(dashboardProvider);
      if (context.mounted) {
        showMessage(context, "Loyiha o'chirildi");
        context.pop();
      }
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(projectProvider(id));
    return Scaffold(
      appBar: AppBar(title: const Text('Loyiha'), actions: [
        IconButton(
          tooltip: 'Tahrirlash',
          icon: const Icon(Icons.edit_outlined),
          onPressed: () async {
            await context.push('/projects/$id/edit');
            ref.invalidate(projectProvider(id));
          },
        ),
        IconButton(tooltip: "O'chirish", icon: const Icon(Icons.delete_outline), onPressed: () => _delete(context, ref)),
      ]),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(projectProvider(id).future),
        child: AsyncView<Json>(
          value: data,
          onRetry: () => ref.invalidate(projectProvider(id)),
          builder: (p) {
            final files = asJsonList(p['files']);
            final analysis = p['latest_analysis'] == null ? null : asJson(p['latest_analysis']);
            final defenses = asJsonList(p['defenses']);
            return ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
              Text(p['title'] ?? '', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              StatusChip(Labels.categories[p['category']] ?? ''),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () => context.push('/defense/new?project=$id'),
                    icon: const Icon(Icons.mic_rounded),
                    label: const Text('Himoyani boshlash'),
                  ),
                ),
              ]),
              const SizedBox(height: 10),
              Row(children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => context.push('/projects/$id/analysis'),
                    icon: const Icon(Icons.auto_awesome_outlined),
                    label: Text(analysis == null ? 'AI ekspertiza' : 'Yangi ekspertiza'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () async {
                      await context.push('/projects/$id/upload');
                      ref.invalidate(projectProvider(id));
                    },
                    icon: const Icon(Icons.upload_file_outlined),
                    label: const Text('Hujjat yuklash'),
                  ),
                ),
              ]),
              const SectionTitle("Loyiha ma'lumotlari"),
              InfoCard(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  KeyValue('Tavsif', p['description'] ?? ''),
                  KeyValue('Muammo', p['problem'] ?? ''),
                  KeyValue('Maqsad', p['objective'] ?? ''),
                  KeyValue('Maqsadli foydalanuvchilar', p['target_users'] ?? ''),
                  KeyValue('Asosiy funksiyalar', p['features'] ?? ''),
                  KeyValue('Texnologiyalar', p['technologies'] ?? ''),
                  KeyValue('Innovatsion jihatlar', p['innovation'] ?? ''),
                  KeyValue('Kutilayotgan natijalar', p['expected_results'] ?? ''),
                  KeyValue('Rivojlantirish rejalari', p['future_plans'] ?? ''),
                ]),
              ),
              SectionTitle('Yuklangan fayllar (${files.length})'),
              if (files.isEmpty)
                Text('Fayl yuklanmagan. Taqdimot yoki texnik hujjat yuklash ekspertiza sifatini oshiradi.',
                    style: TextStyle(color: AppColors.slate))
              else
                for (final f in files) Padding(padding: const EdgeInsets.only(bottom: 8), child: FileTile(f)),
              const SectionTitle("Oxirgi ekspertiza"),
              if (analysis == null)
                Text("Ekspertiza hali o'tkazilmagan", style: TextStyle(color: AppColors.slate))
              else
                InfoCard(
                  onTap: () => context.push('/projects/$id/analysis'),
                  child: Row(children: [
                    Icon(
                      analysis['status'] == 'completed'
                          ? Icons.task_alt_rounded
                          : analysis['status'] == 'failed'
                              ? Icons.error_outline
                              : Icons.hourglass_top_rounded,
                      color: analysis['status'] == 'completed'
                          ? AppColors.success
                          : analysis['status'] == 'failed'
                              ? AppColors.error
                              : AppColors.warning,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(
                          analysis['status'] == 'completed'
                              ? 'Ekspertiza tayyor'
                              : analysis['status'] == 'failed'
                                  ? 'Ekspertiza bajarilmadi'
                                  : 'Ekspertiza bajarilmoqda',
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        Text(formatDate(analysis['created_at']), style: TextStyle(color: AppColors.slate, fontSize: 13)),
                        if (analysis['is_outdated'] == true)
                          const Padding(
                            padding: EdgeInsets.only(top: 4),
                            child: StatusChip("Loyiha o'zgargan — yangilash tavsiya etiladi", color: AppColors.warning),
                          ),
                      ]),
                    ),
                    const Icon(Icons.chevron_right),
                  ]),
                ),
              if (analysis != null && analysis['status'] == 'completed') ...[
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  onPressed: () => context.push('/projects/$id/improvement'),
                  icon: const Icon(Icons.tips_and_updates_outlined),
                  label: const Text('AI tavsiyalari (takomillashtirish)'),
                ),
              ],
              SectionTitle('Himoyalar tarixi (${defenses.length})'),
              if (defenses.isEmpty)
                Text("Himoya mashqi hali o'tkazilmagan", style: TextStyle(color: AppColors.slate))
              else
                for (final s in defenses)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: InfoCard(
                      onTap: () => context.push(
                          s['status'] == 'EVALUATED' ? '/defense/${s['id']}/assessment' : '/defense/${s['id']}'),
                      child: Row(children: [
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(Labels.modes[s['mode']] ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
                            Text('${s['question_limit']} savol • ${formatDate(s['created_at'])}',
                                style: TextStyle(color: AppColors.slate, fontSize: 13)),
                          ]),
                        ),
                        if (s['total_score'] != null)
                          Text('${formatScore(s['total_score'])}/${s['max_applicable_score']}',
                              style: const TextStyle(fontWeight: FontWeight.w800))
                        else
                          StatusChip(Labels.sessionStatus[s['status']] ?? '', color: sessionStatusColor(s['status'])),
                      ]),
                    ),
                  ),
            ]);
          },
        ),
      ),
    );
  }
}

class FileTile extends StatelessWidget {
  const FileTile(this.f, {super.key, this.onDelete});
  final Json f;
  final VoidCallback? onDelete;
  @override
  Widget build(BuildContext context) {
    final status = f['extraction_status'];
    final color = status == 'completed' ? AppColors.success : status == 'empty' ? AppColors.warning : AppColors.error;
    final ext = (f['original_filename'] as String).split('.').last.toUpperCase();
    return InfoCard(
      padding: const EdgeInsets.all(12),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 44,
          height: 44,
          alignment: Alignment.center,
          decoration: BoxDecoration(color: AppColors.primary.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
          child: Text(ext, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 11, color: AppColors.primary)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(f['original_filename'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Wrap(spacing: 8, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
              Text('${((f['file_size'] as num) / 1024).toStringAsFixed(0)} KB',
                  style: TextStyle(color: AppColors.slate, fontSize: 12)),
              StatusChip(Labels.extraction[status] ?? status, color: color),
              if (status == 'completed')
                Text('${f['extracted_chars']} belgi', style: TextStyle(color: AppColors.slate, fontSize: 12)),
            ]),
            if (f['extraction_error'] != null) ...[
              const SizedBox(height: 4),
              Text(f['extraction_error'], style: const TextStyle(color: AppColors.error, fontSize: 12)),
            ],
          ]),
        ),
        if (onDelete != null) IconButton(icon: const Icon(Icons.delete_outline), onPressed: onDelete),
      ]),
    );
  }
}

// =============================================================== Upload documents
class UploadDocumentsScreen extends ConsumerStatefulWidget {
  const UploadDocumentsScreen({super.key, required this.projectId});
  final String projectId;
  @override
  ConsumerState<UploadDocumentsScreen> createState() => _UploadDocumentsScreenState();
}

class _UploadDocumentsScreenState extends ConsumerState<UploadDocumentsScreen> {
  bool _uploading = false;
  double _progress = 0;
  String? _currentName;

  Future<void> _pick() async {
    if (_uploading) return; // repeated taps never start a second upload
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'docx', 'pptx', 'txt'],
    );
    if (files.isEmpty) return;
    final file = files.single;
    final maxMb = (ref.read(metaProvider).value?['max_upload_mb'] as num?) ?? 20;
    final size = await file.xFile.length();
    if (size > maxMb * 1024 * 1024) {
      if (mounted) showMessage(context, 'Fayl hajmi $maxMb MB dan oshmasligi kerak', error: true);
      return;
    }
    setState(() {
      _uploading = true;
      _progress = 0;
      _currentName = file.name;
    });
    try {
      final bytes = await file.xFile.readAsBytes();
      final r = await ref.read(repositoryProvider).uploadFile(widget.projectId, bytes, file.name,
          onProgress: (s, t) => setState(() => _progress = t > 0 ? s / t : 0));
      ref.invalidate(projectProvider(widget.projectId));
      if (!mounted) return;
      final status = r['extraction_status'];
      showMessage(
        context,
        status == 'completed'
            ? 'Fayl yuklandi, matn ajratildi'
            : 'Fayl yuklandi, lekin matn ajratilmadi: ${r['extraction_error'] ?? ''}',
        error: status != 'completed',
      );
    } on ApiException catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _delete(Json f) async {
    try {
      await ref.read(repositoryProvider).deleteFile(widget.projectId, f['id']);
      ref.invalidate(projectProvider(widget.projectId));
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(projectProvider(widget.projectId));
    final maxMb = ref.watch(metaProvider).value?['max_upload_mb'] ?? 20;
    return Scaffold(
      appBar: AppBar(title: const Text('Hujjatlarni yuklash')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: _uploading ? null : _pick,
          child: Container(
            padding: const EdgeInsets.all(28),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.primary.withValues(alpha: 0.5), width: 1.5),
              color: AppColors.primary.withValues(alpha: 0.05),
            ),
            child: Column(children: [
              Icon(_uploading ? Icons.cloud_upload_rounded : Icons.upload_file_rounded,
                  size: 48, color: AppColors.primary),
              const SizedBox(height: 12),
              Text(_uploading ? 'Yuklanmoqda: ${_currentName ?? ''}' : 'Fayl tanlash',
                  textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
              const SizedBox(height: 6),
              Text('PDF, DOCX, PPTX yoki TXT • $maxMb MB gacha',
                  textAlign: TextAlign.center, style: TextStyle(color: AppColors.slate)),
              if (_uploading) ...[
                const SizedBox(height: 16),
                LinearProgressIndicator(value: _progress == 0 || _progress >= 1 ? null : _progress),
                const SizedBox(height: 6),
                Text(_progress >= 1 ? 'Matn ajratilmoqda...' : '${(_progress * 100).round()}%',
                    style: const TextStyle(fontSize: 12)),
              ],
            ]),
          ),
        ),
        const SizedBox(height: 12),
        const DisclaimerBox(
            "Skanerlangan PDF yoki rasmdagi matn (OCR) MVP versiyada qo'llab-quvvatlanmaydi. Fayllar xususiy saqlanadi."),
        const SectionTitle('Yuklangan fayllar'),
        data.when(
          data: (p) {
            final files = asJsonList(p['files']);
            if (files.isEmpty) return Text('Hali fayl yuklanmagan', style: TextStyle(color: AppColors.slate));
            return Column(children: [
              for (final f in files)
                Padding(padding: const EdgeInsets.only(bottom: 8), child: FileTile(f, onDelete: () => _delete(f))),
            ]);
          },
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(projectProvider(widget.projectId))),
          loading: () => const LoadingView(),
        ),
      ]),
    );
  }
}
