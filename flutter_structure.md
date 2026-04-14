# Flutter Project Structure — Release 1.0
## AI English Learning App

---

## Architecture Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| State Management | Riverpod | Compile-safe, testable, no BuildContext dependency |
| Folder Style | Feature-first | Each flow is self-contained, easy to find files |
| Navigation | GoRouter | Declarative, deep link ready, redirect guards |
| API Layer | Repository pattern | Swap real/mock easily, single responsibility |
| File Size Rule | Max 200–250 lines | Every file. Extract widgets, split logic, no exceptions |

---

## Light Skeleton — What You Create on Day 1

Only create folders when you start working on that feature.
The tree below shows the **full Release 1.0 target**. Folders marked with `★` are your Day 1 skeleton.

```
lib/
├── main.dart                          ★
├── app.dart                           ★  (MaterialApp + GoRouter + ProviderScope)
│
├── core/                              ★  (shared across all features)
│   ├── constants/
│   │   ├── app_colors.dart            ★
│   │   ├── app_text_styles.dart       ★
│   │   └── api_endpoints.dart         ★
│   ├── models/
│   │   ├── user_model.dart            ★
│   │   ├── mission_model.dart
│   │   └── mission_result_model.dart
│   ├── services/
│   │   ├── api_client.dart            ★  (HTTP wrapper: dio or http)
│   │   ├── secure_storage_service.dart ★  (flutter_secure_storage wrapper)
│   │   ├── gemini_service.dart           (Gemini text chat + audio turns)
│   │   └── tts_service.dart              (local TTS server + device fallback)
│   ├── providers/
│   │   ├── user_provider.dart         ★
│   │   └── session_provider.dart      ★  (free session count state)
│   ├── router/
│   │   └── app_router.dart            ★  (all routes + auth redirect)
│   ├── utils/
│   │   ├── validators.dart            ★  (email, phone, password)
│   │   └── phone_formatter.dart       ★  (+81 normalization)
│   └── widgets/
│       ├── app_button.dart            ★
│       ├── app_text_field.dart        ★
│       ├── loading_indicator.dart     ★
│       └── error_message.dart         ★
│
├── features/
│   ├── auth/                          ★  (Flow A — first feature you build)
│   │   ├── models/
│   │   │   └── registration_form.dart ★
│   │   ├── providers/
│   │   │   └── auth_provider.dart     ★
│   │   ├── repositories/
│   │   │   └── auth_repository.dart   ★
│   │   ├── screens/
│   │   │   ├── splash_screen.dart     ★  (A1)
│   │   │   ├── welcome_screen.dart    ★  (A2)
│   │   │   ├── registration_screen.dart ★ (A3)
│   │   │   ├── profile_setup_screen.dart ★ (A4)
│   │   │   └── login_screen.dart      ★  (A5)
│   │   └── widgets/
│   │       ├── welcome_card.dart      ★
│   │       └── age_group_selector.dart ★
│   │
│   ├── onboarding/                       (Flow B — build after auth works)
│   │   ├── models/
│   │   │   └── onboarding_state.dart
│   │   ├── providers/
│   │   │   └── onboarding_provider.dart
│   │   ├── repositories/
│   │   │   └── onboarding_repository.dart
│   │   ├── screens/
│   │   │   ├── interview_intro_screen.dart    (B1)
│   │   │   ├── interview_chat_screen.dart     (B2)
│   │   │   └── mission_selection_screen.dart   (B3)
│   │   └── widgets/
│   │       ├── chat_bubble.dart
│   │       └── quick_reply_chips.dart
│   │
│   ├── mission/                          (Flow C — build after onboarding works)
│   │   ├── models/
│   │   │   ├── conversation_turn.dart
│   │   │   └── review_result.dart
│   │   ├── providers/
│   │   │   ├── mission_provider.dart
│   │   │   └── practice_provider.dart
│   │   ├── repositories/
│   │   │   └── mission_repository.dart
│   │   ├── screens/
│   │   │   ├── mission_briefing_screen.dart   (C1)
│   │   │   ├── prepare_screen.dart            (C2)
│   │   │   ├── practice_screen.dart           (C3)
│   │   │   └── review_screen.dart             (C4)
│   │   └── widgets/
│   │       ├── key_phrase_card.dart
│   │       ├── mic_button.dart
│   │       ├── objective_checklist.dart
│   │       ├── score_display.dart
│   │       └── feedback_section.dart
│   │
│   ├── home/                             (Flow D — build alongside mission)
│   │   ├── providers/
│   │   │   └── home_provider.dart
│   │   ├── screens/
│   │   │   ├── home_screen.dart               (D1)
│   │   │   ├── progress_screen.dart           (D2)
│   │   │   └── settings_screen.dart           (D3)
│   │   └── widgets/
│   │       ├── session_counter_bar.dart
│   │       ├── mission_list_card.dart
│   │       └── skill_breakdown_chart.dart
│   │
│   └── api_key/                          (Flow E — build last)
│       ├── providers/
│       │   └── api_key_provider.dart
│       ├── screens/
│       │   ├── sessions_used_up_screen.dart   (E1)
│       │   ├── api_key_guide_screen.dart       (E2)
│       │   └── api_key_troubleshoot_screen.dart (E3)
│       └── widgets/
│           └── step_instruction_card.dart
│
└── l10n/                              ★  (Japanese strings from day 1)
    └── ja.dart                        ★
```

---

## Build Order — Which Folder When

| Phase | What to build | Folders to create |
|-------|--------------|-------------------|
| **Week 1** | Splash → Welcome → Registration → Login | `core/` + `features/auth/` + `l10n/` |
| **Week 2** | Onboarding interview + mission generation | `features/onboarding/` |
| **Week 3** | Mission loop (Prepare → Practice → Review) | `features/mission/` + voice services in `core/services/` |
| **Week 4** | Home + Progress + Settings | `features/home/` |
| **Week 5** | API key flow + polish | `features/api_key/` |

Don't create `features/mission/` on Week 1. It doesn't exist yet. Add it when you get there.

---

## Screen → File Mapping (Complete)

Every screen from the User Flow document mapped to exactly one file.

| Screen ID | Screen Name | File Path |
|-----------|-------------|-----------|
| A1 | Splash | `features/auth/screens/splash_screen.dart` |
| A2 | Welcome | `features/auth/screens/welcome_screen.dart` |
| A3 | Registration | `features/auth/screens/registration_screen.dart` |
| A4 | Profile Setup | `features/auth/screens/profile_setup_screen.dart` |
| A5 | Login | `features/auth/screens/login_screen.dart` |
| B1 | Interview Intro | `features/onboarding/screens/interview_intro_screen.dart` |
| B2 | Interview Chat | `features/onboarding/screens/interview_chat_screen.dart` |
| B3 | Mission Selection | `features/onboarding/screens/mission_selection_screen.dart` |
| C1 | Mission Briefing | `features/mission/screens/mission_briefing_screen.dart` |
| C2 | Prepare | `features/mission/screens/prepare_screen.dart` |
| C3 | Practice (Voice) | `features/mission/screens/practice_screen.dart` |
| C4 | Review | `features/mission/screens/review_screen.dart` |
| C5 | Counter Update | Toast/overlay inside `review_screen.dart` — not a separate file |
| D1 | Home | `features/home/screens/home_screen.dart` |
| D2 | Progress | `features/home/screens/progress_screen.dart` |
| D3 | Settings | `features/home/screens/settings_screen.dart` |
| E1 | Sessions Used Up | `features/api_key/screens/sessions_used_up_screen.dart` |
| E2 | API Key Guide | `features/api_key/screens/api_key_guide_screen.dart` |
| E3 | Troubleshooting | `features/api_key/screens/api_key_troubleshoot_screen.dart` |

**19 screens → 18 files** (C5 is a toast, not a screen)

---

## How to Keep Files Under 250 Lines

### Rule 1: Screen files = layout only

A screen file builds the scaffold and arranges widgets. No business logic, no API calls.

```dart
// ✅ registration_screen.dart — ~120 lines
class RegistrationScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(title: Text('アカウント登録')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            AppTextField(label: 'メール', ...),
            AppTextField(label: '電話番号', ...),
            AppTextField(label: 'パスワード', obscure: true, ...),
            AppButton(label: '次へ', onTap: () => ref.read(authProvider.notifier).register()),
          ],
        ),
      ),
    );
  }
}
```

### Rule 2: Extract repeated UI into `widgets/`

If a chunk of UI appears more than once OR exceeds ~60 lines, extract it.

```
features/auth/widgets/
├── welcome_card.dart         ← one swipeable card (A2)
└── age_group_selector.dart   ← tap-to-select age buttons (A4)
```

### Rule 3: All logic lives in providers

Providers hold state + call repositories. Screens just watch and call methods.

```
features/auth/providers/auth_provider.dart     ← register(), login(), state
features/auth/repositories/auth_repository.dart ← HTTP calls to ConoHa VPS
```

### Rule 4: If a screen is still >250 lines after extracting widgets, split into sections

```dart
// practice_screen.dart — orchestrator (~150 lines)
// practice_chat_section.dart — chat bubbles list (~100 lines)  
// practice_input_section.dart — mic button + text toggle (~80 lines)
```

Put section files in `widgets/` within the same feature.

---

## Core Models (Mapped to Backend Tables)

### user_model.dart (~80 lines)

```dart
enum AgeGroup { under16, highSchool, college, age26to35, age36to50, age51plus }
enum EnglishLevel { beginner, elementary, intermediate, upperIntermediate }

class UserModel {
  final String userId;
  final String email;
  final String phone;
  final String? displayName;
  final AgeGroup ageGroup;
  final int maxFreeSessions;
  final int usedFreeSessions;
  final bool apiKeyRegistered;
  final EnglishLevel? englishLevel;
  final String? primaryGoal;
  final bool onboardingCompleted;

  int get remainingSessions => maxFreeSessions - usedFreeSessions;
  bool get hasFreeSessions => remainingSessions > 0;
  bool get canPractice => hasFreeSessions || apiKeyRegistered;

  // fromJson, toJson, copyWith ...
}
```

### mission_model.dart (~60 lines)

```dart
enum MissionStatus { available, inProgress, completed }

class MissionModel {
  final String missionId;
  final String userId;
  final String titleEn;
  final String titleJa;
  final String description;
  final int difficultyLevel;
  final Map<String, dynamic> generatedContent; // key phrases, vocab, dialogue
  final MissionStatus status;

  // fromJson, toJson ...
}
```

### mission_result_model.dart (~50 lines)

```dart
class MissionResultModel {
  final String resultId;
  final String missionId;
  final int overallScore;
  final int pronunciationScore;
  final int grammarScore;
  final int phrasingScore;
  final Map<String, dynamic> feedbackJson;
  final List<Map<String, dynamic>> conversationLog;

  String get encouragement {
    if (overallScore >= 90) return '素晴らしい！';
    if (overallScore >= 75) return 'よくできました！';
    if (overallScore >= 60) return 'いい調子です！';
    return '続ければ必ず上達します！';
  }

  // fromJson, toJson ...
}
```

---

## Core Services (How Each External System Connects)

| Service File | Talks To | Used By |
|-------------|----------|---------|
| `api_client.dart` | ConoHa VPS backend | All repositories |
| `openai_service.dart` | OpenAI GPT-4o-mini | Onboarding, Mission, Review |
| `stt_service.dart` | ConoHa VPS (Whisper) | Practice screen |
| `tts_service.dart` | ConoHa VPS (TTS) | Prepare + Practice screens |
| `secure_storage_service.dart` | Device keychain | Auth token + API key |

### api_client.dart (~100 lines)

```dart
class ApiClient {
  final Dio _dio;

  ApiClient() : _dio = Dio(BaseOptions(baseUrl: ApiEndpoints.baseUrl));

  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  Future<Response> get(String path) => _dio.get(path);
  Future<Response> post(String path, {Map<String, dynamic>? data}) =>
      _dio.post(path, data: data);
}
```

### gemini_service.dart (~120 lines)

```dart
class GeminiService {
  final SecureStorageService _storage;

  // Sends text messages to Gemini (onboarding, mission generation).
  // First uses developer key via backend proxy (free sessions).
  // After free sessions, uses user's own Gemini key directly.
  Future<String> chat(List<Map<String, String>> messages) async {
    final useProxy = await _shouldUseProxy();
    if (useProxy) {
      // POST to backend /api/v1/ai/chat → backend forwards with dev key
    } else {
      final apiKey = await _storage.read('gemini_api_key');
      // POST directly to generativelanguage.googleapis.com
    }
  }

  // Sends audio file for practice turns.
  // Backend handles Gemini audio API call (keeps key server-side for free sessions).
  Future<String> practiceTurn(File audioFile, List conversationHistory) async {
    // POST multipart audio + history to backend /api/v1/practice/turn
    // Backend calls Gemini with audio → returns response text
  }

  Future<bool> _shouldUseProxy() async {
    // check if user has own Gemini key registered
    final key = await _storage.read('gemini_api_key');
    return key == null || key.isEmpty;
  }
}
```

### tts_service.dart (~80 lines)

```dart
class TtsService {
  /// Send text to local TTS server (dev: Mac port 8001, prod: VPS port 8001).
  /// Returns audio bytes for playback.
  Future<Uint8List?> synthesize(String text) async {
    // POST to ttsBaseUrl/api/tts
    // Returns: audio/wav bytes
  }

  /// Fallback: use device TTS when TTS server is unreachable or offline.
  Future<void> speakLocal(String text) async {
    // flutter_tts package
  }
}
```

---

## Router Setup (GoRouter)

### app_router.dart (~120 lines)

```dart
final routerProvider = Provider<GoRouter>((ref) {
  final user = ref.watch(userProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isLoggedIn = user != null;
      final isOnAuthPage = state.matchedLocation.startsWith('/auth');
      final isOnboarded = user?.onboardingCompleted ?? false;

      if (!isLoggedIn && !isOnAuthPage) return '/auth/splash';
      if (isLoggedIn && !isOnboarded) return '/onboarding';
      if (isLoggedIn && isOnAuthPage) return '/home';
      return null;
    },
    routes: [
      // --- Flow A: Auth ---
      GoRoute(path: '/auth/splash', builder: (_, __) => SplashScreen()),
      GoRoute(path: '/auth/welcome', builder: (_, __) => WelcomeScreen()),
      GoRoute(path: '/auth/register', builder: (_, __) => RegistrationScreen()),
      GoRoute(path: '/auth/profile', builder: (_, __) => ProfileSetupScreen()),
      GoRoute(path: '/auth/login', builder: (_, __) => LoginScreen()),

      // --- Flow B: Onboarding ---
      GoRoute(path: '/onboarding', builder: (_, __) => InterviewIntroScreen()),
      GoRoute(path: '/onboarding/chat', builder: (_, __) => InterviewChatScreen()),
      GoRoute(path: '/onboarding/missions', builder: (_, __) => MissionSelectionScreen()),

      // --- Flow C: Mission ---
      GoRoute(path: '/mission/:id/briefing', builder: ...),
      GoRoute(path: '/mission/:id/prepare', builder: ...),
      GoRoute(path: '/mission/:id/practice', builder: ...),
      GoRoute(path: '/mission/:id/review', builder: ...),

      // --- Flow D: Home (ShellRoute for bottom nav) ---
      ShellRoute(
        builder: (_, __, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, __) => HomeScreen()),
          GoRoute(path: '/progress', builder: (_, __) => ProgressScreen()),
          GoRoute(path: '/settings', builder: (_, __) => SettingsScreen()),
        ],
      ),

      // --- Flow E: API Key ---
      GoRoute(path: '/api-key/limit', builder: (_, __) => SessionsUsedUpScreen()),
      GoRoute(path: '/api-key/guide', builder: (_, __) => ApiKeyGuideScreen()),
      GoRoute(path: '/api-key/help', builder: (_, __) => ApiKeyTroubleshootScreen()),
    ],
  );
});
```

---

## Repository Pattern (Example: auth)

### auth_repository.dart (~100 lines)

```dart
class AuthRepository {
  final ApiClient _api;

  AuthRepository(this._api);

  Future<UserModel> register({
    required String email,
    required String phone,
    required String password,
    required AgeGroup ageGroup,
    String? displayName,
  }) async {
    final response = await _api.post('/auth/register', data: {
      'email': email,
      'phone': phone,
      'password': password,
      'age_group': ageGroup.name,
      'display_name': displayName,
      'device_fingerprint': await _getDeviceId(),
    });
    return UserModel.fromJson(response.data);
  }

  Future<UserModel> login({required String identifier, required String password}) async {
    // ...
  }

  Future<void> logout() async { /* ... */ }
}
```

### auth_provider.dart (~100 lines)

```dart
@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AsyncValue<void> build() => const AsyncValue.data(null);

  Future<void> register(RegistrationForm form) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(authRepositoryProvider);
      final user = await repo.register(...);
      ref.read(userProvider.notifier).set(user);
    });
  }

  Future<void> login(String identifier, String password) async {
    // similar pattern
  }
}
```

---

## Adding a New Feature Later (e.g., Release 1.1 Streaks)

Follow the same pattern. No restructuring needed.

```
features/
└── streaks/                     ← new folder
    ├── models/
    │   └── streak_model.dart
    ├── providers/
    │   └── streak_provider.dart
    ├── screens/
    │   └── streak_display.dart   ← or add widget to home
    └── widgets/
        └── flame_counter.dart
```

Then add routes to `app_router.dart` if needed. That's it.

---

## Key Packages (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0

  # Navigation
  go_router: ^14.0.0

  # Network
  dio: ^5.4.0

  # Secure Storage (API key + auth token)
  flutter_secure_storage: ^9.2.0

  # Audio (mic input + playback)
  record: ^5.1.0           # mic recording
  audioplayers: ^6.0.0     # play TTS audio

  # TTS fallback (offline / VPS down)
  flutter_tts: ^4.0.0

  # Device info (fingerprint)
  device_info_plus: ^10.1.0

  # UI
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0          # loading skeletons

dev_dependencies:
  riverpod_generator: ^2.4.0
  build_runner: ^2.4.0
  riverpod_lint: ^2.3.0
```

---

## Summary of Rules

1. **One screen = one file**, max 250 lines. Extract widgets if over.
2. **Screens never call APIs directly.** Screen → Provider → Repository → Service.
3. **Create folders only when you start that feature.** Don't pre-create empty folders.
4. **Every new feature** gets: `models/`, `providers/`, `repositories/`, `screens/`, `widgets/`.
5. **Shared code** goes in `core/`. If only one feature uses it, keep it in that feature.
6. **Japanese strings** go in `l10n/ja.dart` from day 1. Never hardcode strings in widgets.
7. **Router is the single source of truth** for navigation. No `Navigator.push` calls in screens.
