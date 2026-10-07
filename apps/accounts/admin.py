from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from apps.core.services import audit

from .models import (
    CustomerUser, MahallaUser, PortfolioImage, Profile, ProviderUser, PsychologistUser, Skill, User, UserSkill,
    VerificationRequest,
)
from .services import decide_verification


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Parol", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Parolni tasdiqlash", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["phone", "role"]

    def clean_password2(self):
        if self.cleaned_data.get("password1") != self.cleaned_data.get("password2"):
            raise forms.ValidationError("Parollar mos kelmadi.")
        return self.cleaned_data["password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Parol")

    class Meta:
        model = User
        fields = "__all__"


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ["first_name", "last_name", "region", "district", "mahalla", "verification_status", "rating", "reviews_count", "bio"]
    readonly_fields = ["rating", "reviews_count"]
    autocomplete_fields = ["mahalla"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [ProfileInline]
    list_display = ["phone", "display_name", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["phone", "profile__first_name", "profile__last_name"]
    ordering = ["-created_at"]
    fieldsets = [
        (None, {"fields": ["phone", "password", "role"]}),
        ("Holat", {"fields": ["is_active", "is_staff", "is_superuser", "groups"]}),
        ("Sana", {"fields": ["last_login", "created_at"]}),
    ]
    add_fieldsets = [(None, {"classes": ["wide"], "fields": ["phone", "role", "password1", "password2"]})]
    readonly_fields = ["last_login", "created_at"]
    filter_horizontal = ["groups"]
    actions = ["block_users", "unblock_users"]

    @admin.display(description="F.I.Sh.")
    def display_name(self, obj):
        return obj.display_name

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        Profile.objects.get_or_create(user=obj)

    @admin.action(description="Bloklash (kirishni o‘chirish)")
    def block_users(self, request, queryset):
        for u in queryset.exclude(is_superuser=True):
            u.is_active = False
            u.save(update_fields=["is_active"])
            audit(request.user, "user.block", u, request)

    @admin.action(description="Blokdan chiqarish")
    def unblock_users(self, request, queryset):
        queryset.update(is_active=True)


for proxy in (ProviderUser, CustomerUser, MahallaUser, PsychologistUser):
    admin.site.register(proxy, type(f"{proxy.__name__}Admin", (UserAdmin,), {}))


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    list_filter = ["category"]
    search_fields = ["name"]


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ["user", "skill", "level"]
    list_filter = ["skill"]


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = ["user", "caption", "created_at"]


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "mahalla", "status", "created_at", "decided_at", "reviewer"]
    list_filter = ["status", "mahalla__district__region"]
    search_fields = ["user__phone", "user__profile__first_name", "user__profile__last_name"]
    readonly_fields = ["user", "mahalla", "note", "created_at", "decided_at", "reviewer"]
    actions = ["approve", "reject"]

    def _decide(self, request, queryset, decision):
        for vr in queryset.filter(status=VerificationRequest.Status.PENDING):
            decide_verification(request.user, vr, decision, "Administrator qarori", request)

    @admin.action(description="Tasdiqlash")
    def approve(self, request, queryset):
        self._decide(request, queryset, "approve")

    @admin.action(description="Rad etish")
    def reject(self, request, queryset):
        self._decide(request, queryset, "reject")
