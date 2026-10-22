import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/app_logo.dart';
import '../../shared/widgets/common.dart';

// =============================================================== Splash
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});
  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  Object? _error;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    setState(() => _error = null);
    await Future<void>.delayed(const Duration(milliseconds: 900));
    try {
      await ref.read(authProvider.notifier).restore();
    } catch (e) {
      if (mounted) setState(() => _error = e);
      return;
    }
    if (!mounted) return;
    final auth = ref.read(authProvider);
    if (auth.status == AuthStatus.authenticated) {
      context.go('/home');
    } else if (!ref.read(prefsProvider).onboardingSeen) {
      context.go('/onboarding');
    } else {
      context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    // First screen: only the logo on a plain background (same as the native launch screen).
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: dark ? AppColors.navy : Colors.white,
      body: SafeArea(
        child: Stack(children: [
          const Center(child: AppLogo(size: 220)),
          if (_error != null)
            Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(32, 0, 32, 40),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error is ApiException ? (_error as ApiException).message : '$_error',
                      textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  Wrap(spacing: 12, alignment: WrapAlignment.center, children: [
                    OutlinedButton(
                      style: OutlinedButton.styleFrom(minimumSize: const Size(140, 44)),
                      onPressed: _check,
                      child: const Text('Qayta urinish'),
                    ),
                    TextButton(
                      onPressed: () async {
                        await showServerDialog(context, ref);
                        _check();
                      },
                      child: const Text('Server manzili'),
                    ),
                  ]),
                ]),
              ),
            ),
        ]),
      ),
    );
  }
}

// =============================================================== Onboarding
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});
  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pc = PageController();
  int _page = 0;

  static const _pages = [
    (Icons.upload_file_rounded, 'Loyihangni yukla', "Dasturiy loyihangni AI ekspertga taqdim et."),
    (Icons.record_voice_over_rounded, 'Ekspert bilan mashq qil', "Real himoyaga o'xshash savol-javoblardan o't."),
    (Icons.trending_up_rounded, 'Kompetensiyangni rivojlantir',
        "Nutqingni, javoblaringni va taqdimot mahoratingni takomillashtir."),
  ];

  Future<void> _finish() async {
    await ref.read(prefsProvider).setOnboardingSeen();
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(children: [
            Align(alignment: Alignment.topRight, child: TextButton(onPressed: _finish, child: const Text("O'tkazib yuborish"))),
            Expanded(
              child: PageView.builder(
                controller: _pc,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (_, i) {
                  final p = _pages[i];
                  return Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Container(
                        width: 220,
                        height: 220,
                        decoration: BoxDecoration(
                          gradient: AppColors.splashGradient,
                          borderRadius: BorderRadius.circular(48),
                        ),
                        child: Icon(p.$1, size: 96, color: Colors.white),
                      ),
                      const SizedBox(height: 40),
                      Text(p.$2,
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 12),
                      Text(p.$3,
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.slate)),
                    ]),
                  );
                },
              ),
            ),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              for (var i = 0; i < _pages.length; i++)
                AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _page ? 24 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: i == _page ? AppColors.primary : AppColors.slate.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
            ]),
            Padding(
              padding: const EdgeInsets.all(24),
              child: FilledButton(
                onPressed: () => _page == _pages.length - 1
                    ? _finish()
                    : _pc.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut),
                child: Text(_page == _pages.length - 1 ? 'Boshlash' : 'Keyingi'),
              ),
            ),
          ]),
        ),
      );
}

// =============================================================== Validators
String? requiredField(String? v, [String label = 'Maydon']) =>
    (v == null || v.trim().isEmpty) ? "$label to'ldirilishi shart" : null;

String? emailValidator(String? v) {
  if (v == null || v.trim().isEmpty) return "Elektron pochtani kiriting";
  final ok = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v.trim());
  return ok ? null : "Elektron pochta formati noto'g'ri";
}

String? passwordValidator(String? v) {
  if (v == null || v.length < 10) return "Parol kamida 10 ta belgidan iborat bo'lishi kerak";
  if (v.toLowerCase().contains('password') || RegExp(r'^(\d)\1+$').hasMatch(v) || v == '1234567890') {
    return 'Bu parol juda oddiy';
  }
  return null;
}

// =============================================================== Login
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _pw = TextEditingController();
  bool _obscure = true;

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    try {
      await ref.read(authProvider.notifier).login(_email.text.trim(), _pw.text);
      if (mounted) context.go('/home');
    } catch (e) {
      if (!mounted) return;
      showError(context, e);
      if (e is ApiException && e.isNetwork) await showServerDialog(context, ref);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _form,
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  const Center(child: AppLogo(size: 110)),
                  const SizedBox(height: 16),
                  Text('Xush kelibsiz!',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  Text('Hisobingizga kiring', textAlign: TextAlign.center, style: TextStyle(color: AppColors.slate)),
                  const SizedBox(height: 28),
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: const InputDecoration(labelText: 'Elektron pochta', prefixIcon: Icon(Icons.mail_outline)),
                    validator: emailValidator,
                  ),
                  const SizedBox(height: 14),
                  TextFormField(
                    controller: _pw,
                    obscureText: _obscure,
                    autofillHints: const [AutofillHints.password],
                    decoration: InputDecoration(
                      labelText: 'Parol',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                    validator: (v) => requiredField(v, 'Parol'),
                    onFieldSubmitted: (_) => _submit(),
                  ),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(onPressed: () => context.push('/password-reset'), child: const Text('Parolni unutdingizmi?')),
                  ),
                  const SizedBox(height: 8),
                  BusyButton(label: 'Tizimga kirish', onPressed: _submit),
                  const SizedBox(height: 16),
                  Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                    const Flexible(child: Text("Hisobingiz yo'qmi?")),
                    TextButton(onPressed: () => context.push('/register'), child: const Text("Ro'yxatdan o'tish")),
                  ]),
                  TextButton.icon(
                    onPressed: () => showServerDialog(context, ref),
                    icon: const Icon(Icons.dns_outlined, size: 18),
                    label: const Text('Server manzili'),
                  ),
                ]),
              ),
            ),
          ),
        ),
      );
}

// =============================================================== Register
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _c = {for (final k in ['first', 'last', 'email', 'pw', 'pw2', 'uni', 'program']) k: TextEditingController()};
  bool _obscure = true;

  @override
  void initState() {
    super.initState();
    _c['program']!.text = '60610100 — Axborot tizimlari va texnologiyalari';
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    try {
      await ref.read(authProvider.notifier).register({
        'first_name': _c['first']!.text.trim(),
        'last_name': _c['last']!.text.trim(),
        'email': _c['email']!.text.trim(),
        'password': _c['pw']!.text,
        'password_confirm': _c['pw2']!.text,
        'university': _c['uni']!.text.trim(),
        'study_program': _c['program']!.text.trim(),
      });
      if (mounted) context.go('/home');
    } catch (e) {
      if (!mounted) return;
      showError(context, e);
      if (e is ApiException && e.isNetwork) await showServerDialog(context, ref);
    }
  }

  Widget _field(String key, String label, IconData icon,
          {String? Function(String?)? validator, bool password = false, TextInputType? type}) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: TextFormField(
          controller: _c[key],
          obscureText: password && _obscure,
          keyboardType: type,
          decoration: InputDecoration(
            labelText: label,
            prefixIcon: Icon(icon),
            suffixIcon: password
                ? IconButton(
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure))
                : null,
          ),
          validator: validator ?? (v) => requiredField(v, label),
        ),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text("Ro'yxatdan o'tish")),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Form(
              key: _form,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                _field('first', 'Ism', Icons.person_outline),
                _field('last', 'Familiya', Icons.person_outline),
                _field('email', 'Elektron pochta', Icons.mail_outline,
                    validator: emailValidator, type: TextInputType.emailAddress),
                _field('pw', 'Parol (kamida 10 belgi)', Icons.lock_outline,
                    password: true, validator: passwordValidator),
                _field('pw2', 'Parolni tasdiqlash', Icons.lock_outline,
                    password: true, validator: (v) => v != _c['pw']!.text ? 'Parollar mos kelmadi' : null),
                _field('uni', 'Universitet', Icons.school_outlined),
                _field('program', "Ta'lim yo'nalishi", Icons.menu_book_outlined),
                const SizedBox(height: 8),
                BusyButton(label: "Ro'yxatdan o'tish", onPressed: _submit),
              ]),
            ),
          ),
        ),
      );
}

// =============================================================== Password reset
class PasswordResetScreen extends ConsumerStatefulWidget {
  const PasswordResetScreen({super.key});
  @override
  ConsumerState<PasswordResetScreen> createState() => _PasswordResetScreenState();
}

class _PasswordResetScreenState extends ConsumerState<PasswordResetScreen> {
  final _email = TextEditingController();
  final _token = TextEditingController();
  final _pw = TextEditingController();
  final _pw2 = TextEditingController();
  final _form1 = GlobalKey<FormState>();
  final _form2 = GlobalKey<FormState>();
  bool _codeSent = false;
  String? _unavailable;

  Future<void> _request() async {
    if (!_form1.currentState!.validate()) return;
    try {
      final r = await ref.read(repositoryProvider).requestPasswordReset(_email.text.trim());
      if (!mounted) return;
      setState(() => _codeSent = true);
      showMessage(context, r['message']?.toString() ?? 'Kod yuborildi');
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.code == 'EMAIL_NOT_CONFIGURED') {
        setState(() => _unavailable = e.message);
      } else {
        showError(context, e);
      }
    }
  }

  Future<void> _confirm() async {
    if (!_form2.currentState!.validate()) return;
    try {
      final r = await ref.read(repositoryProvider).confirmPasswordReset(_token.text.trim(), _pw.text, _pw2.text);
      if (!mounted) return;
      showMessage(context, r['message']?.toString() ?? 'Parol yangilandi');
      context.go('/login');
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Parolni tiklash')),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              if (_unavailable != null) ...[
                DisclaimerBox(_unavailable!, icon: Icons.mark_email_unread_outlined),
                const SizedBox(height: 16),
              ],
              Form(
                key: _form1,
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  const Text("Elektron pochtangizni kiriting. Unga parolni tiklash kodi yuboriladi."),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(labelText: 'Elektron pochta', prefixIcon: Icon(Icons.mail_outline)),
                    validator: emailValidator,
                  ),
                  const SizedBox(height: 16),
                  BusyButton(label: _codeSent ? 'Kodni qayta yuborish' : 'Kod yuborish', onPressed: _request,
                      outlined: _codeSent),
                ]),
              ),
              if (_codeSent) ...[
                const SizedBox(height: 28),
                Form(
                  key: _form2,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    TextFormField(
                      controller: _token,
                      decoration: const InputDecoration(labelText: 'Emaildagi kod', prefixIcon: Icon(Icons.key_outlined)),
                      validator: (v) => requiredField(v, 'Kod'),
                    ),
                    const SizedBox(height: 14),
                    TextFormField(
                      controller: _pw,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Yangi parol', prefixIcon: Icon(Icons.lock_outline)),
                      validator: passwordValidator,
                    ),
                    const SizedBox(height: 14),
                    TextFormField(
                      controller: _pw2,
                      obscureText: true,
                      decoration:
                          const InputDecoration(labelText: 'Yangi parolni tasdiqlash', prefixIcon: Icon(Icons.lock_outline)),
                      validator: (v) => v != _pw.text ? 'Parollar mos kelmadi' : null,
                    ),
                    const SizedBox(height: 16),
                    BusyButton(label: 'Parolni yangilash', onPressed: _confirm),
                  ]),
                ),
              ],
            ]),
          ),
        ),
      );
}

// =============================================================== Server address dialog
String? _normalizeServerUrl(String raw) {
  var v = raw.trim();
  if (v.isEmpty) return null;
  if (!v.startsWith('http://') && !v.startsWith('https://')) v = 'http://$v';
  final uri = Uri.tryParse(v);
  if (uri == null || uri.host.isEmpty) return null;
  if (!uri.hasPort && uri.scheme == 'http') v = '${uri.scheme}://${uri.host}:8000';
  return v.endsWith('/') ? v.substring(0, v.length - 1) : v;
}

/// Connects to the given server and explains the result in plain words.
Future<(bool, String)> testServerConnection(String url) async {
  final dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 8), receiveTimeout: const Duration(seconds: 8)));
  try {
    final res = await dio.get('$url/api/v1/meta');
    final data = res.data;
    if (data is! Map || data['version'] == null) {
      return (false, "Bu manzilda CommuniAI serveri topilmadi. Manzil va portni (:8000) tekshiring.");
    }
    final ai = data['ai_configured'] == true
        ? "AI xizmati ulangan."
        : "AI xizmati serverda sozlanmagan: kompyuterdagi backend/.env fayliga AI_API_KEY yozing.";
    return (true, "Server bilan aloqa bor (versiya ${data['version']}). $ai");
  } on DioException catch (e) {
    final msg = '${e.message ?? ''} ${e.error ?? ''}'.toLowerCase();
    if (msg.contains('cleartext')) {
      return (false,
          "Bu APK faqat HTTPS manzillar bilan ishlaydi. Kompyuterdagi server uchun 'dev-http' APK ni o'rnating.");
    }
    if (e.response?.statusCode == 404) {
      return (false, "Bu manzilda CommuniAI serveri topilmadi (404). Manzilni tekshiring.");
    }
    return (
      false,
      "Serverga ulanib bo'lmadi. Tekshiring:\n"
          "1) kompyuterda server oynasi ochiq va ishlab turibdi;\n"
          "2) telefon va kompyuter bitta Wi-Fi tarmog'ida;\n"
          "3) manzil server oynasida ko'rsatilgani bilan bir xil (masalan http://192.168.1.15:8000);\n"
          "4) Windows Firewall Python'ga ruxsat bergan."
    );
  } catch (e) {
    return (false, "Xatolik: $e");
  } finally {
    dio.close();
  }
}

Future<void> showServerDialog(BuildContext context, WidgetRef ref) async {
  final prefs = ref.read(prefsProvider);
  final c = TextEditingController(text: prefs.baseUrl);
  String? status;
  bool? ok;
  bool testing = false;
  final result = await showDialog<String>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setState) => AlertDialog(
        title: const Text('Server manzili'),
        content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text(
                "Kompyuterdagi server oynasida ko'rsatilgan manzilni kiriting, masalan http://192.168.1.15:8000",
                style: TextStyle(fontSize: 13)),
            const SizedBox(height: 12),
            TextField(
              controller: c,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: const InputDecoration(hintText: 'http://192.168.1.15:8000'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: testing
                  ? null
                  : () async {
                      final url = _normalizeServerUrl(c.text);
                      if (url == null) {
                        setState(() {
                          ok = false;
                          status = "Manzil noto'g'ri";
                        });
                        return;
                      }
                      c.text = url;
                      setState(() {
                        testing = true;
                        status = null;
                      });
                      final r = await testServerConnection(url);
                      setState(() {
                        testing = false;
                        ok = r.$1;
                        status = r.$2;
                      });
                    },
              icon: testing
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.wifi_tethering),
              label: Text(testing ? 'Tekshirilmoqda...' : 'Ulanishni tekshirish'),
            ),
            if (status != null) ...[
              const SizedBox(height: 10),
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Icon(ok == true ? Icons.check_circle : Icons.error_outline,
                    color: ok == true ? AppColors.success : AppColors.error, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text(status!, style: const TextStyle(fontSize: 13))),
              ]),
            ],
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Bekor qilish')),
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(80, 40)),
            onPressed: () => Navigator.pop(ctx, c.text.trim()),
            child: const Text('Saqlash'),
          ),
        ],
      ),
    ),
  );
  if (result == null || result.isEmpty) return;
  final url = _normalizeServerUrl(result);
  if (url == null) {
    if (context.mounted) showMessage(context, "Manzil noto'g'ri", error: true);
    return;
  }
  await prefs.setBaseUrl(url);
  ref.read(apiClientProvider).baseUrl = url;
  ref.invalidate(metaProvider);
  if (context.mounted) showMessage(context, 'Server manzili saqlandi: $url');
}

/// Asks for explicit consent before any project data is sent to the AI service (TZ 19).
Future<bool> ensureAiConsent(BuildContext context, WidgetRef ref) async {
  final user = ref.read(authProvider).user;
  if (user != null && user.hasAiConsent) return true;
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('AI tahliliga rozilik'),
      content: const SingleChildScrollView(
        child: Text(
          "AI ekspertiza va himoya mashqi uchun loyiha ma'lumotlaringiz, yuklangan hujjatlardan ajratilgan matn va "
          "javoblaringiz tahlil uchun AI xizmatiga (tashqi provayderga) yuboriladi.\n\n"
          "• Ma'lumotlaringiz modelni o'qitish uchun ishlatilmaydi.\n"
          "• Rozilikni istalgan vaqtda Profil → Sozlamalar bo'limida bekor qilishingiz mumkin.\n"
          "• AI natijalari dastlabki tavsiya bo'lib, validatsiyadan o'tgan pedagogik o'lchov emas.",
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Rad etish')),
        FilledButton(
          style: FilledButton.styleFrom(minimumSize: const Size(100, 40)),
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Roziman'),
        ),
      ],
    ),
  );
  if (ok != true) return false;
  try {
    final u = await ref.read(repositoryProvider).updateProfile({'ai_consent': true});
    ref.read(authProvider.notifier).setUser(u);
    return true;
  } catch (e) {
    if (context.mounted) showError(context, e);
    return false;
  }
}
