import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/analytics/analytics_screens.dart';
import '../features/auth/auth_screens.dart';
import '../features/communication_coach/assessment_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/defense/defense_screens.dart';
import '../features/practice/practice_screen.dart';
import '../features/profile/profile_screens.dart';
import '../features/project_analysis/analysis_screens.dart';
import '../features/projects/projects_screens.dart';
import 'providers.dart';

final _rootKey = GlobalKey<NavigatorState>();

/// Bridges Riverpod auth state to GoRouter's refreshListenable.
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(Ref ref) {
    ref.listen<AuthState>(authProvider, (_, _) => notifyListeners());
  }
}

const _public = {'/', '/onboarding', '/login', '/register', '/password-reset'};

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    navigatorKey: _rootKey,
    initialLocation: '/',
    refreshListenable: _AuthListenable(ref),
    redirect: (context, state) {
      final status = ref.read(authProvider).status;
      final loc = state.matchedLocation;
      if (status == AuthStatus.unknown) return loc == '/' ? null : '/';
      final loggedIn = status == AuthStatus.authenticated;
      if (!loggedIn && !_public.contains(loc)) return '/login';
      if (loggedIn && (loc == '/login' || loc == '/register' || loc == '/onboarding')) return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, _) => const SplashScreen()),
      GoRoute(path: '/onboarding', builder: (_, _) => const OnboardingScreen()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, _) => const RegisterScreen()),
      GoRoute(path: '/password-reset', builder: (_, _) => const PasswordResetScreen()),
      StatefulShellRoute.indexedStack(
        builder: (_, _, shell) => HomeShell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [GoRoute(path: '/home', builder: (_, _) => const DashboardScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/projects', builder: (_, _) => const ProjectsListScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/defense', builder: (_, _) => const DefenseListScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/results', builder: (_, _) => const CompetencyProgressScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen())]),
        ],
      ),
      // Full-screen routes (above the bottom navigation)
      GoRoute(parentNavigatorKey: _rootKey, path: '/projects/new', builder: (_, _) => const ProjectFormScreen()),
      GoRoute(
        parentNavigatorKey: _rootKey,
        path: '/projects/:id',
        builder: (_, s) => ProjectDetailScreen(id: s.pathParameters['id']!),
        routes: [
          GoRoute(path: 'edit', builder: (_, s) => ProjectFormScreen(projectId: s.pathParameters['id'])),
          GoRoute(path: 'upload', builder: (_, s) => UploadDocumentsScreen(projectId: s.pathParameters['id']!)),
          GoRoute(path: 'analysis', builder: (_, s) => AnalysisScreen(projectId: s.pathParameters['id']!)),
          GoRoute(
            path: 'improvement',
            builder: (_, s) => ImprovementReportScreen(
                projectId: s.pathParameters['id']!, sessionId: s.uri.queryParameters['session']),
          ),
        ],
      ),
      GoRoute(
        parentNavigatorKey: _rootKey,
        path: '/defense/new',
        builder: (_, s) => SelectModeScreen(projectId: s.uri.queryParameters['project']),
      ),
      GoRoute(
        parentNavigatorKey: _rootKey,
        path: '/defense/config',
        builder: (_, s) => DefenseConfigScreen(
            projectId: s.uri.queryParameters['project']!, mode: s.uri.queryParameters['mode'] ?? 'hackathon'),
      ),
      GoRoute(
        parentNavigatorKey: _rootKey,
        path: '/defense/:id',
        builder: (_, s) => ExpertChatScreen(sessionId: s.pathParameters['id']!),
        routes: [
          GoRoute(path: 'complete', builder: (_, s) => DefenseCompletionScreen(sessionId: s.pathParameters['id']!)),
          GoRoute(path: 'assessment', builder: (_, s) => AssessmentScreen(sessionId: s.pathParameters['id']!)),
        ],
      ),
      GoRoute(
          parentNavigatorKey: _rootKey,
          path: '/practice/:id',
          builder: (_, s) => PracticeScreen(planId: s.pathParameters['id']!)),
      GoRoute(parentNavigatorKey: _rootKey, path: '/history', builder: (_, _) => const ActivityHistoryScreen()),
      GoRoute(parentNavigatorKey: _rootKey, path: '/settings', builder: (_, _) => const SettingsScreen()),
      GoRoute(parentNavigatorKey: _rootKey, path: '/admin', builder: (_, _) => const AdminScreen()),
    ],
  );
});
