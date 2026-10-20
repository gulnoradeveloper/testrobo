import 'api_client.dart';
import 'models.dart';

/// Thin typed access to every backend endpoint used by the app.
class Repository {
  Repository(this.api);
  final ApiClient api;

  // ---------------------------------------------------------------- auth
  Future<Json> register(Json body) async => asJson(await api.post('/api/v1/auth/register', data: body, auth: false));
  Future<Json> login(String email, String password) async =>
      asJson(await api.post('/api/v1/auth/login', data: {'email': email, 'password': password}, auth: false));
  Future<void> logout(String refresh) => api.post('/api/v1/auth/logout', data: {'refresh_token': refresh});
  Future<AppUser> me() async => AppUser.fromJson(asJson(await api.get('/api/v1/auth/me')));
  Future<Json> requestPasswordReset(String email) async =>
      asJson(await api.post('/api/v1/auth/password-reset/request', data: {'email': email}, auth: false));
  Future<Json> confirmPasswordReset(String token, String pw, String pw2) async => asJson(await api.post(
      '/api/v1/auth/password-reset/confirm',
      data: {'token': token, 'new_password': pw, 'new_password_confirm': pw2},
      auth: false));
  Future<Json> meta() async => asJson(await api.get('/api/v1/meta'));

  // ---------------------------------------------------------------- profile
  Future<AppUser> updateProfile(Json body) async => AppUser.fromJson(asJson(await api.patch('/api/v1/me', data: body)));
  Future<void> changePassword(String current, String next) =>
      api.post('/api/v1/me/password', data: {'current_password': current, 'new_password': next});
  Future<Json> exportData() async => asJson(await api.get('/api/v1/me/export'));
  Future<void> deleteAccount() => api.delete('/api/v1/me');
  Future<Json> dashboard() async => asJson(await api.get('/api/v1/me/dashboard'));
  Future<Json> competencies() async => asJson(await api.get('/api/v1/me/competencies'));
  Future<Json> progress() async => asJson(await api.get('/api/v1/me/progress'));
  Future<Json> history({int page = 1}) async =>
      asJson(await api.get('/api/v1/me/history', query: {'page': page, 'page_size': 30}));

  // ---------------------------------------------------------------- projects
  Future<Json> projects({int page = 1, String? q}) async => asJson(await api.get('/api/v1/projects',
      query: {'page': page, 'page_size': 50, if (q != null && q.isNotEmpty) 'q': q}));
  Future<Json> project(String id) async => asJson(await api.get('/api/v1/projects/$id'));
  Future<Json> createProject(Json body) async => asJson(await api.post('/api/v1/projects', data: body));
  Future<Json> updateProject(String id, Json body) async => asJson(await api.patch('/api/v1/projects/$id', data: body));
  Future<void> deleteProject(String id) => api.delete('/api/v1/projects/$id');
  Future<Json> uploadFile(String projectId, List<int> bytes, String name, {void Function(int, int)? onProgress}) =>
      api.upload('/api/v1/projects/$projectId/files', bytes, name, onProgress: onProgress);
  Future<void> deleteFile(String projectId, String fileId) => api.delete('/api/v1/projects/$projectId/files/$fileId');

  // ---------------------------------------------------------------- analysis
  Future<Json> analyze(String projectId, {bool force = false, String? key}) async => asJson(await api.post(
      '/api/v1/projects/$projectId/analyze',
      query: force ? {'force': 'true'} : null,
      idempotencyKey: key));
  Future<Json> analysis(String id) async => asJson(await api.get('/api/v1/analyses/$id'));
  Future<Json> analyses(String projectId) async => asJson(await api.get('/api/v1/projects/$projectId/analyses'));

  // ---------------------------------------------------------------- defense
  Future<Json> createDefense(String projectId, String mode, int limit, String key) async => asJson(await api.post(
      '/api/v1/defenses',
      data: {'project_id': projectId, 'mode': mode, 'question_limit': limit},
      idempotencyKey: key));
  Future<Json> defenses({String? status}) async =>
      asJson(await api.get('/api/v1/defenses', query: {'page_size': 50, 'status': ?status}));
  Future<Json> defense(String id) async => asJson(await api.get('/api/v1/defenses/$id'));
  Future<Json> startDefense(String id) async => asJson(await api.post('/api/v1/defenses/$id/start'));
  Future<Json> resumeDefense(String id) async => asJson(await api.post('/api/v1/defenses/$id/resume'));
  Future<Json> currentQuestion(String id) async => asJson(await api.get('/api/v1/defenses/$id/current-question'));
  Future<Json> submitAnswer(String id, String questionId, String text, String key) async => asJson(await api.post(
      '/api/v1/defenses/$id/answers',
      data: {'question_id': questionId, 'answer_text': text},
      idempotencyKey: key));
  Future<Json> completeDefense(String id) async => asJson(await api.post('/api/v1/defenses/$id/complete'));
  Future<Json> cancelDefense(String id) async => asJson(await api.post('/api/v1/defenses/$id/cancel'));
  Future<Json> results(String id) async => asJson(await api.get('/api/v1/defenses/$id/results'));
  Future<Json> job(String id) async => asJson(await api.get('/api/v1/jobs/$id'));

  // ---------------------------------------------------------------- practice
  Future<Json> planForSession(String sessionId) async =>
      asJson(await api.post('/api/v1/practice-plans', data: {'session_id': sessionId}));
  Future<Json> plans() async => asJson(await api.get('/api/v1/practice-plans'));
  Future<Json> plan(String id) async => asJson(await api.get('/api/v1/practice-plans/$id'));
  Future<Json> submitAttempt(String planId, int index, String text, String key) async => asJson(await api.post(
      '/api/v1/practice-plans/$planId/attempts',
      data: {'exercise_index': index, 'revised_answer': text},
      idempotencyKey: key));
  Future<Json> retryAttempt(String attemptId) async =>
      asJson(await api.post('/api/v1/practice-attempts/$attemptId/retry'));
  Future<Json> planProgress(String id) async => asJson(await api.get('/api/v1/practice-plans/$id/progress'));

  // ---------------------------------------------------------------- admin
  Future<Json> adminSystem() async => asJson(await api.get('/api/v1/admin/system'));
  Future<Json> adminUsers() async => asJson(await api.get('/api/v1/admin/users', query: {'page_size': 100}));
  Future<Json> adminAiRequests() async => asJson(await api.get('/api/v1/admin/ai-requests', query: {'page_size': 50}));
  Future<Json> adminErrors() async => asJson(await api.get('/api/v1/admin/errors', query: {'page_size': 50}));
  Future<Json> adminSetSetting(String key, Object value) async =>
      asJson(await api.put('/api/v1/admin/settings', data: {'key': key, 'value': value}));
  Future<Json> adminSetUserActive(String id, bool active) async =>
      asJson(await api.patch('/api/v1/admin/users/$id?is_active=$active'));
}
