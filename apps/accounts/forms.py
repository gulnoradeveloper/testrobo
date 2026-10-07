from django import forms
from django.contrib.auth import password_validation

from apps.catalog.models import Category
from apps.core.forms import MultipleImageField, RegionSelectMixin, wire_region_fields
from apps.core.validators import normalize_phone, phone_validator

from .models import Profile, Skill, User, VerificationRequest

PHONE_ATTRS = {"placeholder": "+998 90 123 45 67", "inputmode": "tel", "autocomplete": "tel"}


class PhoneField(forms.CharField):
    def to_python(self, value):
        return normalize_phone(super().to_python(value))


class RegisterForm(forms.Form):
    phone = PhoneField(label="Telefon raqami", validators=[phone_validator], widget=forms.TextInput(attrs=PHONE_ATTRS))
    password1 = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Parolni tasdiqlash", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    role = forms.ChoiceField(
        label="Kim sifatida ro‘yxatdan o‘tasiz?",
        choices=[(r.value, r.label) for r in User.SELF_REGISTER_ROLES],
        widget=forms.RadioSelect,
        initial=User.Role.PROVIDER,
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqami bilan allaqachon ro‘yxatdan o‘tilgan.")
        return phone

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Parollar mos kelmadi.")
        if p1 and not self.errors.get("password1"):
            try:
                password_validation.validate_password(p1, User(phone=data.get("phone") or ""))
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return data

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(phone=d["phone"], password=d["password1"], role=d["role"])
        Profile.objects.create(user=user)
        return user


class LoginForm(forms.Form):
    phone = PhoneField(label="Telefon raqami", widget=forms.TextInput(attrs=PHONE_ATTRS))
    password = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class ProfileForm(RegionSelectMixin, forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        label="Ko‘nikmalarim", queryset=Skill.objects.select_related("category"), required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    new_skill = forms.CharField(label="Yangi ko‘nikma qo‘shish", required=False, max_length=80,
                                widget=forms.TextInput(attrs={"placeholder": "Masalan: kashtachilik"}))
    new_skill_category = forms.ModelChoiceField(label="Yangi ko‘nikma kategoriyasi", queryset=Category.objects.filter(is_active=True), required=False)
    portfolio = MultipleImageField(label="Portfolio rasmlari (jpg, png, webp; 5 MB gacha)")

    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "birth_year", "age_range", "region", "district", "mahalla",
                  "avatar", "bio", "experience"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "experience": forms.Textarea(attrs={"rows": 3, "placeholder": "Masalan: 10 yildan beri parda tikaman"}),
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for name in ("first_name", "last_name", "region", "district", "mahalla"):
            self.fields[name].required = True
        wire_region_fields(self, mahalla="mahalla")
        if user is not None and not user.is_provider:
            for name in ("skills", "new_skill", "new_skill_category", "portfolio", "experience"):
                self.fields.pop(name)
        elif user is not None:
            self.fields["skills"].initial = list(user.user_skills.values_list("skill_id", flat=True))
        if self.instance.verification_status in (Profile.Verification.PENDING, Profile.Verification.VERIFIED):
            # Tasdiqlangan/tekshirilayotgan profilda mahallani o'zgartirib bo'lmaydi
            for name in ("region", "district", "mahalla"):
                self.fields[name].disabled = True

    def clean_birth_year(self):
        y = self.cleaned_data.get("birth_year")
        if y and not (1930 <= y <= 2010):
            raise forms.ValidationError("Tug‘ilgan yil noto‘g‘ri.")
        return y


class VerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ["note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 3, "placeholder": "Mahalla vakili uchun qisqacha izoh (ixtiyoriy)"})}


class VerificationDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[("approve", "Tasdiqlash"), ("reject", "Rad etish"), ("revision", "Qayta ko‘rib chiqishga yuborish")])
    comment = forms.CharField(required=False, max_length=1000, widget=forms.Textarea(attrs={"rows": 2}))
