from django.contrib.auth import password_validation
from rest_framework import serializers

from apps.accounts.models import Profile, User, UserSkill, VerificationRequest
from apps.catalog.models import Category, Order, Review, Service, ServiceImage
from apps.core.models import District, Mahalla, Notification, Region, Report
from apps.core.validators import normalize_phone, phone_validator
from apps.psychology.models import Consultation, Psychologist, PsychologistSchedule


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in User.SELF_REGISTER_ROLES])

    def validate_phone(self, value):
        phone = normalize_phone(value)
        phone_validator(phone)
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Bu telefon raqami bilan allaqachon ro‘yxatdan o‘tilgan.")
        return phone

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar mos kelmadi."})
        password_validation.validate_password(data["password"], User(phone=data["phone"]))
        return data

    def create(self, data):
        user = User.objects.create_user(phone=data["phone"], password=data["password"], role=data["role"])
        Profile.objects.create(user=user)
        return user


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name", "region"]


class MahallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mahalla
        fields = ["id", "name", "district"]


class UserSkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = UserSkill
        fields = ["skill", "name", "level"]


class ProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    skills = UserSkillSerializer(source="user.user_skills", many=True, read_only=True)
    completed_orders = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id", "user", "phone", "role", "first_name", "last_name", "avatar", "bio", "experience", "birth_year",
            "age_range", "region", "district", "mahalla", "verification_status", "rating", "reviews_count",
            "skills", "completed_orders",
        ]
        read_only_fields = ["user", "verification_status", "rating", "reviews_count"]

    def get_completed_orders(self, obj):
        return obj.user.orders_received.filter(status=Order.Status.COMPLETED).count()

    def validate(self, data):
        region = data.get("region", getattr(self.instance, "region", None))
        district = data.get("district", getattr(self.instance, "district", None))
        mahalla = data.get("mahalla", getattr(self.instance, "mahalla", None))
        if region and district and district.region_id != region.pk:
            raise serializers.ValidationError({"district": "Tuman ushbu viloyatga tegishli emas."})
        if district and mahalla and mahalla.district_id != district.pk:
            raise serializers.ValidationError({"mahalla": "Mahalla ushbu tumanga tegishli emas."})
        if self.instance and self.instance.verification_status in ("pending", "verified"):
            for f in ("region", "district", "mahalla"):
                if f in data and data[f] != getattr(self.instance, f):
                    raise serializers.ValidationError({f: "Tasdiqlangan profilda hududni o‘zgartirib bo‘lmaydi."})
        return data


class PublicProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="full_name")
    verified = serializers.BooleanField(source="is_verified")

    class Meta:
        model = Profile
        fields = ["user", "name", "avatar", "rating", "reviews_count", "verified"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "order"]


class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ["id", "image"]


class ServiceSerializer(serializers.ModelSerializer):
    provider = PublicProfileSerializer(source="provider.profile", read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    price_label = serializers.CharField(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "provider", "category", "title", "description", "price_type", "price", "price_label", "service_mode",
            "region", "district", "duration", "status", "images", "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_status(self, value):
        if value == Service.Status.BLOCKED or (self.instance and self.instance.status == Service.Status.BLOCKED):
            raise serializers.ValidationError("Bloklangan holatni faqat administrator o‘zgartiradi.")
        return value

    def validate(self, data):
        region = data.get("region", getattr(self.instance, "region", None))
        district = data.get("district", getattr(self.instance, "district", None))
        if region and district and district.region_id != region.pk:
            raise serializers.ValidationError({"district": "Tuman ushbu viloyatga tegishli emas."})
        price_type = data.get("price_type", getattr(self.instance, "price_type", None))
        price = data.get("price", getattr(self.instance, "price", None))
        if price_type != Service.PriceType.NEGOTIABLE and not price:
            raise serializers.ValidationError({"price": "Narxni kiriting."})
        return data


class OrderSerializer(serializers.ModelSerializer):
    service_title = serializers.CharField(source="service.title", read_only=True)
    customer_name = serializers.CharField(source="customer.display_name", read_only=True)
    provider_name = serializers.CharField(source="provider.display_name", read_only=True)
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "service", "service_title", "customer", "customer_name", "provider", "provider_name", "price",
            "service_date", "address_or_area", "comment", "status", "started_at", "completed_at", "created_at", "has_review",
        ]
        read_only_fields = ["customer", "provider", "status", "started_at", "completed_at", "created_at"]

    def get_has_review(self, obj):
        return hasattr(obj, "review")


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "order", "customer", "customer_name", "provider", "rating", "quality_rating",
                  "communication_rating", "punctuality_rating", "comment", "created_at"]
        read_only_fields = ["customer", "provider", "created_at"]


class VerificationRequestSerializer(serializers.ModelSerializer):
    applicant = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = VerificationRequest
        fields = ["id", "user", "applicant", "mahalla", "note", "status", "reviewer_comment", "created_at", "decided_at"]
        read_only_fields = ["user", "mahalla", "status", "reviewer_comment", "created_at", "decided_at"]


class VerificationDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject", "revision"])
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PsychologistSchedule
        fields = ["id", "start_at", "end_at", "is_booked"]


class PsychologistSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.display_name", read_only=True)
    free_slots = serializers.SerializerMethodField()

    class Meta:
        model = Psychologist
        fields = ["id", "name", "specialization", "experience_years", "consultation_format", "about", "free_slots"]

    def get_free_slots(self, obj):
        from django.utils import timezone

        slots = obj.slots.filter(is_booked=False, start_at__gt=timezone.now())[:10]
        return ScheduleSerializer(slots, many=True).data


class ConsultationSerializer(serializers.ModelSerializer):
    """Faqat murojaat egasi va psixologga qaytariladi (view darajasida filtrlanadi)."""

    psychologist_name = serializers.CharField(source="psychologist.user.display_name", read_only=True)

    class Meta:
        model = Consultation
        fields = ["id", "psychologist", "psychologist_name", "slot", "format", "message", "status", "psychologist_note", "created_at"]
        read_only_fields = ["status", "psychologist_note", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "link", "is_read", "created_at"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "target_user", "target_service", "reason", "comment", "status", "admin_note", "created_at"]
        read_only_fields = ["status", "admin_note", "created_at"]

    def validate(self, data):
        if not data.get("target_user") and not data.get("target_service"):
            raise serializers.ValidationError("Shikoyat obyekti (profil yoki xizmat) ko‘rsatilishi kerak.")
        return data
