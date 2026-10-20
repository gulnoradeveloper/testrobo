typedef Json = Map<String, dynamic>;

Json asJson(dynamic v) => v == null ? <String, dynamic>{} : Map<String, dynamic>.from(v as Map);
List<Json> asJsonList(dynamic v) => v == null ? <Json>[] : (v as List).map((e) => asJson(e)).toList();
List<String> asStrList(dynamic v) => v == null ? <String>[] : (v as List).map((e) => e.toString()).toList();

class AppUser {
  AppUser({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.university,
    required this.studyProgram,
    required this.role,
    this.aiConsentAt,
    this.supportAccessUntil,
  });

  final String id;
  final String firstName;
  final String lastName;
  final String email;
  final String university;
  final String studyProgram;
  final String role;
  final DateTime? aiConsentAt;
  final DateTime? supportAccessUntil;

  bool get isAdmin => role == 'admin';
  bool get hasAiConsent => aiConsentAt != null;
  String get fullName => '$firstName $lastName';
  String get initials =>
      '${firstName.isNotEmpty ? firstName[0] : ''}${lastName.isNotEmpty ? lastName[0] : ''}'.toUpperCase();

  factory AppUser.fromJson(Json j) => AppUser(
        id: j['id'],
        firstName: j['first_name'] ?? '',
        lastName: j['last_name'] ?? '',
        email: j['email'] ?? '',
        university: j['university'] ?? '',
        studyProgram: j['study_program'] ?? '',
        role: j['role'] ?? 'student',
        aiConsentAt: j['ai_consent_at'] != null ? DateTime.tryParse(j['ai_consent_at']) : null,
        supportAccessUntil: j['support_access_until'] != null ? DateTime.tryParse(j['support_access_until']) : null,
      );
}

/// Labels used across the UI (consistent Uzbek terminology).
class Labels {
  static const categories = {
    'web': 'Veb-ilova',
    'mobile': 'Mobil ilova',
    'info_system': 'Axborot tizimi',
    'ai': "Sun'iy intellekt loyihasi",
    'cybersecurity': 'Kiberxavfsizlik loyihasi',
    'iot': 'IoT',
    'robotics': 'Robototexnika',
    'other': 'Boshqa IT loyiha',
  };

  static const modes = {
    'hackathon': 'Hakaton va tanlov',
    'client': 'Buyurtmachi bilan suhbat',
    'academic': 'Akademik loyiha himoyasi',
    'investor': 'Investor oldida taqdimot',
  };

  static const modeDescriptions = {
    'hackathon': "Dolzarb muammo, innovatsion yechim, raqobatchilardan farq, MVP darajasi va kengayish imkoniyatlari.",
    'client': "AI buyurtmachi rolida: foyda, muddat, xavfsizlik, yangi talablar va nosozlik holatlari.",
    'academic': "Dolzarblik, maqsad va vazifalar, texnologik tanlov, arxitektura, ma'lumotlar bazasi, testlash.",
    'investor': "Qiymat taklifi, bozor, biznes model, xavflar. Faqat muzokara mashqi — investitsiya tavsiyasi emas.",
  };

  static const sessionStatus = {
    'CREATED': 'Yaratildi',
    'IN_PROGRESS': 'Davom etmoqda',
    'COMPLETED': 'Yakunlandi',
    'EVALUATING': 'Baholanmoqda',
    'EVALUATED': 'Baholandi',
    'FAILED': 'Baholashda xatolik',
    'CANCELLED': 'Bekor qilindi',
  };

  static const extraction = {
    'completed': 'Matn ajratildi',
    'empty': 'Matn topilmadi',
    'failed': 'Xatolik',
    'pending': 'Kutilmoqda',
  };

  static const recCategories = {
    'problem_goal': 'Muammo va maqsad',
    'functionality': 'Funksional imkoniyatlar',
    'ux': 'Foydalanuvchi tajribasi',
    'architecture': 'Texnik arxitektura',
    'security_privacy': 'Xavfsizlik va maxfiylik',
    'innovation': 'Innovatsion jihatlar',
    'effectiveness_evidence': 'Amaliy samaradorlik dalillari',
    'presentation': 'Taqdimot',
  };

  static const competencies = {
    'K1': 'Fikrni aniq va tushunarli ifodalash',
    'K2': 'Savolni tushunish va mazmunli javob',
    'K3': 'Texnik qarorni dalillar bilan asoslash',
    'K4': 'Mantiqiy izchillik va tuzilma',
    'K5': 'Auditoriyaga mos kommunikatsiya',
    'K6': 'Refleksiya va takomillashtirish',
  };
}
