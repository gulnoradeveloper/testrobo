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

const _modeIcons = {
  'hackathon': Icons.emoji_events_outlined,
  'client': Icons.handshake_outlined,
  'academic': Icons.school_outlined,
  'investor': Icons.trending_up_rounded,
};

// =============================================================== Defense tab (list)
class DefenseListScreen extends ConsumerWidget {
  const DefenseListScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(defensesProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Himoya')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/defense/new'),
        icon: const Icon(Icons.play_arrow_rounded),
        label: const Text('Yangi himoya'),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(defensesProvider.future),
        child: AsyncView<Json>(
          value: data,
          onRetry: () => ref.invalidate(defensesProvider),
          builder: (d) {
            final items = asJsonList(d['items']);
            if (items.isEmpty) {
              return ListView(children: [
                const SizedBox(height: 80),
                EmptyView(
                  icon: Icons.mic_none_rounded,
                  title: "Himoya mashqi hali o'tkazilmagan",
                  message: "AI ekspert bilan loyihangizni himoya qilishni mashq qiling.",
                  action: FilledButton(
                    style: FilledButton.styleFrom(minimumSize: const Size(200, 48)),
                    onPressed: () => context.push('/defense/new'),
                    child: const Text('Himoyani boshlash'),
                  ),
                ),
              ]);
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (_, i) {
                final s = items[i];
                final r = s['result'] == null ? null : asJson(s['result']);
                final p = asJson(s['progress']);
                return InfoCard(
                  onTap: () async {
                    await context.push(s['status'] == 'EVALUATED' ? '/defense/${s['id']}/assessment' : '/defense/${s['id']}');
                    ref.invalidate(defensesProvider);
                  },
                  child: Row(children: [
                    CircleAvatar(child: Icon(_modeIcons[s['mode']])),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(s['project_title'] ?? '',
                            maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 2),
                        Text('${s['mode_label']} • ${p['answered']}/${s['question_limit']}',
                            style: TextStyle(color: AppColors.slate, fontSize: 13)),
                        Text(formatDate(s['created_at']), style: TextStyle(color: AppColors.slate, fontSize: 12)),
                      ]),
                    ),
                    const SizedBox(width: 8),
                    r != null
                        ? Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                            Text('${formatScore(r['total_score'])}/${r['max_applicable_score']}',
                                style: const TextStyle(fontWeight: FontWeight.w800)),
                            StatusChip(r['level'] ?? '', color: levelColor(r['level'])),
                          ])
                        : StatusChip(Labels.sessionStatus[s['status']] ?? '', color: sessionStatusColor(s['status'])),
                  ]),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

// =============================================================== Select Defense Mode
class SelectModeScreen extends ConsumerStatefulWidget {
  const SelectModeScreen({super.key, this.projectId});
  final String? projectId;
  @override
  ConsumerState<SelectModeScreen> createState() => _SelectModeScreenState();
}

class _SelectModeScreenState extends ConsumerState<SelectModeScreen> {
  String? _project;
  String? _mode;

  @override
  void initState() {
    super.initState();
    _project = widget.projectId;
  }

  @override
  Widget build(BuildContext context) {
    final projects = ref.watch(projectsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Himoya rejimini tanlash')),
      body: AsyncView<Json>(
        value: projects,
        onRetry: () => ref.invalidate(projectsProvider),
        builder: (d) {
          final items = asJsonList(d['items']);
          if (items.isEmpty) {
            return EmptyView(
              icon: Icons.folder_open_rounded,
              title: 'Avval loyiha yarating',
              message: "Himoya loyiha ma'lumotlari asosida o'tkaziladi.",
              action: FilledButton(
                style: FilledButton.styleFrom(minimumSize: const Size(200, 48)),
                onPressed: () => context.pushReplacement('/projects/new'),
                child: const Text('Loyiha yaratish'),
              ),
            );
          }
          if (_project != null && !items.any((p) => p['id'] == _project)) _project = null;
          return ListView(padding: const EdgeInsets.all(16), children: [
            const Text('1. Loyihani tanlang', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _project,
              isExpanded: true,
              hint: const Text('Loyiha'),
              items: [
                for (final p in items)
                  DropdownMenuItem(value: p['id'] as String, child: Text(p['title'], overflow: TextOverflow.ellipsis)),
              ],
              onChanged: (v) => setState(() => _project = v),
            ),
            const SizedBox(height: 20),
            const Text('2. Himoya rejimini tanlang', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            for (final m in Labels.modes.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: InfoCard(
                  color: _mode == m.key ? AppColors.primary.withValues(alpha: 0.08) : null,
                  onTap: () => setState(() => _mode = m.key),
                  child: Row(children: [
                    Icon(_modeIcons[m.key], color: AppColors.primary, size: 30),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(m.value, style: const TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 4),
                        Text(Labels.modeDescriptions[m.key]!, style: TextStyle(color: AppColors.slate, fontSize: 13)),
                      ]),
                    ),
                    Icon(_mode == m.key ? Icons.radio_button_checked : Icons.radio_button_off,
                        color: AppColors.primary),
                  ]),
                ),
              ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _project == null || _mode == null
                  ? null
                  : () => context.push('/defense/config?project=$_project&mode=$_mode'),
              child: const Text('Davom etish'),
            ),
          ]);
        },
      ),
    );
  }
}

// =============================================================== Defense Configuration
class DefenseConfigScreen extends ConsumerStatefulWidget {
  const DefenseConfigScreen({super.key, required this.projectId, required this.mode});
  final String projectId;
  final String mode;
  @override
  ConsumerState<DefenseConfigScreen> createState() => _DefenseConfigScreenState();
}

class _DefenseConfigScreenState extends ConsumerState<DefenseConfigScreen> {
  int _limit = 10;
  final _key = ApiClient.newIdempotencyKey(); // one key per screen: double taps never create two sessions

  Future<void> _start() async {
    if (!await ensureAiConsent(context, ref)) return;
    try {
      final repo = ref.read(repositoryProvider);
      final s = await repo.createDefense(widget.projectId, widget.mode, _limit, _key);
      await repo.startDefense(s['id']);
      ref.invalidate(defensesProvider);
      ref.invalidate(dashboardProvider);
      if (mounted) context.pushReplacement('/defense/${s['id']}');
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final project = ref.watch(projectProvider(widget.projectId));
    const options = [(5, 'Tezkor himoya', '5 savol'), (10, 'Standart himoya', '10 savol'), (15, 'Chuqurlashtirilgan', '15 savol')];
    return Scaffold(
      appBar: AppBar(title: const Text('Himoya sozlamalari')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        InfoCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Icon(_modeIcons[widget.mode], color: AppColors.primary),
              const SizedBox(width: 10),
              Expanded(child: Text(Labels.modes[widget.mode] ?? '', style: const TextStyle(fontWeight: FontWeight.w800))),
            ]),
            const SizedBox(height: 8),
            Text(project.value?['title'] ?? '', style: TextStyle(color: AppColors.slate)),
          ]),
        ),
        const SectionTitle('Savollar soni'),
        for (final o in options)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InfoCard(
              color: _limit == o.$1 ? AppColors.primary.withValues(alpha: 0.08) : null,
              onTap: () => setState(() => _limit = o.$1),
              child: Row(children: [
                Icon(_limit == o.$1 ? Icons.radio_button_checked : Icons.radio_button_off, color: AppColors.primary),
                const SizedBox(width: 12),
                Expanded(child: Text(o.$2, style: const TextStyle(fontWeight: FontWeight.w600))),
                Text(o.$3, style: TextStyle(color: AppColors.slate)),
              ]),
            ),
          ),
        const SectionTitle('Qanday o‘tadi?'),
        const InfoCard(
          child: BulletList([
            "AI loyihangiz va hujjatlaringiz asosida birma-bir savol beradi.",
            "Har bir javobdan so'ng qisqa feedback va namunaviy javob ko'rsatiladi.",
            "Keyingi savol oldingi javobingizga moslab shakllanadi (aniqlashtiruvchi savollar).",
            "Yakunda kasbiy kommunikativ kompetentlik rubrikasi (K1–K6) bo'yicha baholanasiz.",
            "Internet uzilsa yoki AI vaqtincha ishlamasa, sessiya saqlanadi va keyin davom ettirasiz.",
          ]),
        ),
        if (widget.mode == 'investor') ...[
          const SizedBox(height: 12),
          const DisclaimerBox("Investor rejimi biznes g'oyani tushuntirish va muzokara mashqi uchun. "
              "Bu haqiqiy moliyaviy ekspertiza yoki investitsiya tavsiyasi emas."),
        ],
        const SizedBox(height: 20),
        BusyButton(label: 'Himoyani boshlash', icon: Icons.play_arrow_rounded, onPressed: _start),
      ]),
    );
  }
}

// =============================================================== AI Expert Chat
class ExpertChatScreen extends ConsumerStatefulWidget {
  const ExpertChatScreen({super.key, required this.sessionId});
  final String sessionId;
  @override
  ConsumerState<ExpertChatScreen> createState() => _ExpertChatScreenState();
}

class _ExpertChatScreenState extends ConsumerState<ExpertChatScreen> {
  Json? _s;
  Object? _error;
  Timer? _timer;
  final _input = TextEditingController();
  final _scroll = ScrollController();
  bool _sending = false;
  String? _answerKey; // stable idempotency key for the current question's answer

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  bool get _busy => _s?['active_job'] != null;

  Future<void> _load() async {
    try {
      final s = await ref.read(repositoryProvider).defense(widget.sessionId);
      if (!mounted) return;
      final prevCurrent = _s?['current_question']?['id'];
      setState(() {
        _s = s;
        _error = null;
      });
      if (s['current_question']?['id'] != prevCurrent) {
        _answerKey = ApiClient.newIdempotencyKey();
        _scrollToEnd();
      }
      if (s['status'] == 'EVALUATING' || s['status'] == 'EVALUATED') {
        _timer?.cancel();
        context.pushReplacement('/defense/${widget.sessionId}/complete');
        return;
      }
    } catch (e) {
      if (mounted && _s == null) setState(() => _error = e);
    }
    _timer?.cancel();
    if (mounted && _busy) _timer = Timer(const Duration(seconds: 2), _load);
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent + 200,
            duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _send() async {
    final q = _s?['current_question'];
    final text = _input.text.trim();
    if (q == null || text.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      await ref.read(repositoryProvider).submitAnswer(widget.sessionId, q['id'], text, _answerKey!);
      _input.clear();
      await _load();
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _resume() async {
    try {
      final s = await ref.read(repositoryProvider).resumeDefense(widget.sessionId);
      if (mounted) setState(() => _s = s);
      _load();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _cancel() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Himoyani bekor qilish'),
        content: const Text("Sessiya bekor qilinadi va baholanmaydi. Javoblaringiz tarixda saqlanadi."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Yo'q")),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Bekor qilish')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(repositoryProvider).cancelDefense(widget.sessionId);
      ref.invalidate(defensesProvider);
      ref.invalidate(dashboardProvider);
      if (mounted) context.pop();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = _s;
    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('AI ekspert'),
          if (s != null)
            Text('${s['mode_label']} • ${asJson(s['progress'])['answered']}/${s['question_limit']}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400)),
        ]),
        actions: [
          if (s != null && (s['status'] == 'IN_PROGRESS' || s['status'] == 'CREATED'))
            PopupMenuButton<String>(
              onSelected: (v) => v == 'cancel' ? _cancel() : null,
              itemBuilder: (_) => const [PopupMenuItem(value: 'cancel', child: Text('Himoyani bekor qilish'))],
            ),
        ],
      ),
      body: s == null
          ? (_error != null ? ErrorView(error: _error!, onRetry: _load) : const LoadingView())
          : _body(s),
    );
  }

  Widget _body(Json s) {
    final progress = asJson(s['progress']);
    final questions = asJsonList(s['questions']);
    final status = s['status'];
    final failed = s['last_failed_job'] == null ? null : asJson(s['last_failed_job']);
    final current = s['current_question'] == null ? null : asJson(s['current_question']);
    final allAnswered = progress['all_answered'] == true;
    final ready = progress['ready_to_complete'] == true;

    return Column(children: [
      LinearProgressIndicator(
        value: (progress['answered'] as num) / (s['question_limit'] as num),
        minHeight: 4,
        backgroundColor: AppColors.slate.withValues(alpha: 0.15),
      ),
      Expanded(
        child: ListView(controller: _scroll, padding: const EdgeInsets.fromLTRB(12, 12, 12, 16), children: [
          for (final q in questions) ...[
            _ExpertBubble(q),
            if (q['answer'] != null) ...[
              _StudentBubble(asJson(q['answer'])['answer_text']),
              if (asJson(q['answer'])['evaluation'] != null)
                FeedbackCard(asJson(asJson(asJson(q['answer'])['evaluation'])['feedback']))
              else if (_busy)
                const Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: AiWorkingCard(title: 'AI javobingizni tahlil qilmoqda...', subtitle: 'Feedback va keyingi savol tayyorlanmoqda'),
                ),
            ],
          ],
          if (questions.isEmpty && _busy)
            const AiWorkingCard(title: 'AI birinchi savolni tayyorlamoqda...', subtitle: "Loyihangiz o'rganilmoqda"),
          if (status == 'CANCELLED')
            const DisclaimerBox('Bu himoya bekor qilingan.', icon: Icons.block)
          else if (failed != null && !_busy && s['pending_work'] != null) ...[
            const SizedBox(height: 8),
            DisclaimerBox("${failed['error_message'] ?? 'AI xizmatida xatolik'}\nJavoblaringiz saqlangan — qayta urinib ko'ring.",
                icon: Icons.cloud_off_rounded),
            const SizedBox(height: 8),
            BusyButton(label: 'Qayta urinish', icon: Icons.refresh, outlined: true, onPressed: _resume),
          ] else if (status == 'CREATED' || (status == 'IN_PROGRESS' && !_busy && s['pending_work'] != null)) ...[
            BusyButton(label: 'Davom ettirish', icon: Icons.play_arrow_rounded, onPressed: _resume),
          ],
          if (allAnswered && status == 'IN_PROGRESS') ...[
            const SizedBox(height: 12),
            InfoCard(
              color: AppColors.success.withValues(alpha: 0.08),
              child: Column(children: [
                const Icon(Icons.flag_rounded, color: AppColors.success, size: 32),
                const SizedBox(height: 8),
                const Text("Barcha savollarga javob berildi!", style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: ready && !_busy ? () => context.pushReplacement('/defense/${widget.sessionId}/complete') : null,
                  child: Text(ready && !_busy ? 'Yakuniy baholashni boshlash' : 'Oxirgi javob tahlil qilinmoqda...'),
                ),
              ]),
            ),
          ],
          if (status == 'FAILED' || status == 'COMPLETED')
            FilledButton(
              onPressed: () => context.pushReplacement('/defense/${widget.sessionId}/complete'),
              child: const Text('Yakuniy baholashga o‘tish'),
            ),
        ]),
      ),
      // The input bar stays mounted for the whole defense (no layout jumps, focus is kept);
      // sending is enabled only while there is a current, unanswered question.
      if (status == 'IN_PROGRESS' && !allAnswered)
        SafeArea(
          top: false,
          child: Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
            decoration: BoxDecoration(
              color: Theme.of(context).cardTheme.color,
              border: Border(top: BorderSide(color: AppColors.slate.withValues(alpha: 0.2))),
            ),
            child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Expanded(
                child: TextField(
                  controller: _input,
                  minLines: 1,
                  maxLines: 6,
                  maxLength: 6000,
                  textCapitalization: TextCapitalization.sentences,
                  readOnly: _sending,
                  decoration: InputDecoration(
                    hintText: current == null ? 'AI keyingi savolni tayyorlamoqda...' : 'Javobingizni yozing...',
                    counterText: '',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                tooltip: 'Yuborish',
                onPressed: _sending || current == null ? null : _send,
                icon: _sending
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.send_rounded),
              ),
            ]),
          ),
        ),
    ]);
  }
}

class _ExpertBubble extends StatelessWidget {
  const _ExpertBubble(this.q);
  final Json q;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10, right: 32),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const CircleAvatar(radius: 16, backgroundColor: AppColors.navy, child: Icon(Icons.smart_toy_outlined, size: 18, color: Colors.white)),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Theme.of(context).cardTheme.color,
                borderRadius: const BorderRadius.only(
                    topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
                border: Border.all(color: AppColors.slate.withValues(alpha: 0.2)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Wrap(spacing: 6, runSpacing: 4, children: [
                  StatusChip('${q['sequence_number']}-savol'),
                  if (q['question_type'] == 'follow_up') const StatusChip('Aniqlashtiruvchi', color: AppColors.warning),
                  if ((q['focus_area'] ?? '').toString().isNotEmpty) StatusChip(q['focus_area'], color: AppColors.slate),
                ]),
                const SizedBox(height: 8),
                Text(q['question_text'] ?? '', style: const TextStyle(fontSize: 15, height: 1.4)),
              ]),
            ),
          ),
        ]),
      );
}

class _StudentBubble extends StatelessWidget {
  const _StudentBubble(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10, left: 48),
        child: Align(
          alignment: Alignment.centerRight,
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: const BoxDecoration(
              color: AppColors.primary,
              borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
            ),
            child: Text(text, style: const TextStyle(color: Colors.white, height: 1.4)),
          ),
        ),
      );
}

/// Short per-answer coaching feedback (TZ 9.1). The model answer is shown separately and is never
/// stored or scored as the student's answer.
class FeedbackCard extends StatefulWidget {
  const FeedbackCard(this.f, {super.key, this.initiallyExpanded = false});
  final Json f;
  final bool initiallyExpanded;
  @override
  State<FeedbackCard> createState() => _FeedbackCardState();
}

class _FeedbackCardState extends State<FeedbackCard> {
  late bool _open = widget.initiallyExpanded;
  @override
  Widget build(BuildContext context) {
    final f = widget.f;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14, left: 40),
      child: InfoCard(
        color: AppColors.success.withValues(alpha: 0.06),
        padding: const EdgeInsets.all(12),
        onTap: () => setState(() => _open = !_open),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.psychology_alt_outlined, color: AppColors.success, size: 20),
            const SizedBox(width: 6),
            const Expanded(child: Text('Murabbiy feedbacki', style: TextStyle(fontWeight: FontWeight.w700))),
            Icon(_open ? Icons.expand_less : Icons.expand_more),
          ]),
          const SizedBox(height: 6),
          _row('1. Kuchli jihat', f['strength']),
          _row('2. Asosiy kamchilik', f['main_weakness']),
          if (_open) ...[
            _row('3. Nima uchun bu muhim?', f['why_important']),
            _row('4. Qanday yaxshilash mumkin?', f['how_to_improve']),
            const SizedBox(height: 4),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('5. Professional javob namunasi (AI namunasi — sizning javobingiz emas)',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.primary)),
                const SizedBox(height: 4),
                Text(f['model_answer'] ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
              ]),
            ),
            const SizedBox(height: 8),
            _row('6. Qayta mashq', f['retry_task']),
          ] else
            const Text("Batafsil ko'rish uchun bosing", style: TextStyle(fontSize: 12, color: AppColors.slate)),
        ]),
      ),
    );
  }

  Widget _row(String title, dynamic v) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: RichText(
          text: TextSpan(style: DefaultTextStyle.of(context).style, children: [
            TextSpan(text: '$title: ', style: const TextStyle(fontWeight: FontWeight.w700)),
            TextSpan(text: v?.toString() ?? ''),
          ]),
        ),
      );
}

// =============================================================== Defense Completion
class DefenseCompletionScreen extends ConsumerStatefulWidget {
  const DefenseCompletionScreen({super.key, required this.sessionId});
  final String sessionId;
  @override
  ConsumerState<DefenseCompletionScreen> createState() => _DefenseCompletionScreenState();
}

class _DefenseCompletionScreenState extends ConsumerState<DefenseCompletionScreen> {
  Json? _s;
  Object? _error;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _start() async {
    setState(() => _error = null);
    try {
      final repo = ref.read(repositoryProvider);
      var s = await repo.defense(widget.sessionId);
      if (s['status'] == 'IN_PROGRESS' || s['status'] == 'COMPLETED' || s['status'] == 'FAILED') {
        s = await repo.completeDefense(widget.sessionId);
      }
      if (mounted) setState(() => _s = s);
      _poll();
    } catch (e) {
      if (mounted) setState(() => _error = e);
    }
  }

  Future<void> _poll() async {
    _timer?.cancel();
    if (_s?['status'] != 'EVALUATING') {
      if (_s?['status'] == 'EVALUATED') {
        ref.invalidate(defensesProvider);
        ref.invalidate(dashboardProvider);
      }
      return;
    }
    _timer = Timer(const Duration(seconds: 3), () async {
      try {
        final s = await ref.read(repositoryProvider).defense(widget.sessionId);
        if (mounted) setState(() => _s = s);
      } catch (_) {}
      if (mounted) _poll();
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = _s;
    Widget body;
    if (_error != null) {
      body = ErrorView(error: _error!, onRetry: _start);
    } else if (s == null || s['status'] == 'EVALUATING') {
      body = const Padding(
        padding: EdgeInsets.all(24),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          AiWorkingCard(
            title: 'Yakuniy baholash bajarilmoqda...',
            subtitle: "AI barcha javoblaringizni rubrika asosida tahlil qilib, individual mashqlar tayyorlamoqda. "
                "Bu 1–2 daqiqa davom etishi mumkin.",
          ),
        ]),
      );
    } else if (s['status'] == 'EVALUATED') {
      body = Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const Icon(Icons.verified_rounded, color: AppColors.success, size: 80),
          const SizedBox(height: 16),
          Text('Himoya yakunlandi!',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text('${s['question_limit']} ta savolga javob berdingiz. Natijalar va tavsiyalar tayyor.',
              textAlign: TextAlign.center, style: TextStyle(color: AppColors.slate)),
          const SizedBox(height: 28),
          FilledButton(
            onPressed: () => context.pushReplacement('/defense/${widget.sessionId}/assessment'),
            child: const Text("Natijalarni ko'rish"),
          ),
        ]),
      );
    } else if (s['status'] == 'FAILED') {
      body = ListView(padding: const EdgeInsets.all(24), children: [
        const Icon(Icons.cloud_off_rounded, size: 64, color: AppColors.error),
        const SizedBox(height: 12),
        const Text('Baholash bajarilmadi', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        const SizedBox(height: 8),
        Text(s['failure_reason'] ?? '', textAlign: TextAlign.center),
        const SizedBox(height: 8),
        const Text("Javoblaringiz saqlangan. Qayta urinib ko'ring.", textAlign: TextAlign.center),
        const SizedBox(height: 20),
        BusyButton(label: 'Qayta baholash', icon: Icons.refresh, onPressed: _start),
      ]);
    } else {
      body = ErrorView(error: 'Sessiya holati: ${Labels.sessionStatus[s['status']] ?? s['status']}', onRetry: _start);
    }
    return Scaffold(appBar: AppBar(title: const Text('Himoyani yakunlash')), body: body);
  }
}
