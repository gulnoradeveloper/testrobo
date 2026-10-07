from django import forms
from django.utils import timezone

from apps.core.forms import MultipleImageField, RegionSelectMixin, wire_region_fields
from apps.core.models import District, Region

from .models import Category, Order, Review, Service
from .search import SORT_CHOICES


class ServiceForm(RegionSelectMixin, forms.ModelForm):
    images = MultipleImageField(label="Rasmlar (jpg, png, webp; har biri 5 MB gacha)")

    class Meta:
        model = Service
        fields = ["title", "category", "description", "price_type", "price", "service_mode", "region", "district", "duration"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Masalan: Buyurtma asosida parda tikish"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "price": forms.NumberInput(attrs={"min": 0, "step": 1000, "placeholder": "80000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        wire_region_fields(self)
        self.fields["status_choice"] = forms.ChoiceField(
            label="Holat", required=False,
            choices=[(Service.Status.ACTIVE, "Faol"), (Service.Status.PAUSED, "To‘xtatilgan")],
            initial=self.instance.status if self.instance.pk and self.instance.status != Service.Status.BLOCKED else Service.Status.ACTIVE,
        )

    def clean(self):
        data = super().clean()
        if data.get("price_type") != Service.PriceType.NEGOTIABLE and not data.get("price"):
            self.add_error("price", "Narxni kiriting yoki narx turini “Kelishiladi” qiling.")
        return data


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["service_date", "price", "address_or_area", "comment"]
        widgets = {
            "service_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "address_or_area": forms.TextInput(attrs={"placeholder": "Masalan: Buxoro sh., Navbahor mahallasi"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Qo‘shimcha istaklar"}),
        }

    def __init__(self, *args, service=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_date"].initial = timezone.localdate()
        self.fields["price"].help_text = "Ijrochi bilan kelishilgan narx (ixtiyoriy)"
        if service is not None and service.price:
            self.fields["price"].initial = service.price

    def clean_service_date(self):
        d = self.cleaned_data["service_date"]
        if d < timezone.localdate():
            raise forms.ValidationError("Sana o‘tib ketgan bo‘lmasligi kerak.")
        return d


STARS = [(i, "★" * i) for i in range(5, 0, -1)]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "quality_rating", "communication_rating", "punctuality_rating", "comment"]
        widgets = {
            "rating": forms.RadioSelect(choices=STARS),
            "quality_rating": forms.RadioSelect(choices=STARS),
            "communication_rating": forms.RadioSelect(choices=STARS),
            "punctuality_rating": forms.RadioSelect(choices=STARS),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }


class SearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Qanday xizmat izlayapsiz?"}))
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True), required=False, empty_label="Barcha kategoriyalar", to_field_name="slug")
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, empty_label="Barcha hududlar")
    district = forms.ModelChoiceField(queryset=District.objects.all(), required=False, empty_label="Barcha tumanlar")
    price_min = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"placeholder": "dan"}))
    price_max = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"placeholder": "gacha"}))
    min_rating = forms.ChoiceField(required=False, choices=[("", "Har qanday reyting"), ("4.5", "4.5 ★ va yuqori"), ("4", "4 ★ va yuqori"), ("3", "3 ★ va yuqori")])
    verified = forms.BooleanField(required=False, label="Faqat tasdiqlangan profillar")
    mode = forms.ChoiceField(required=False, choices=[("", "Har qanday shakl")] + list(Service.Mode.choices))
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        wire_region_fields(self)
        self.fields["district"].queryset = District.objects.filter(region_id=self.data.get("region") or 0)


class SmartMatchForm(forms.Form):
    text = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Masalan: Ertaga Buxoro shahrida 2 ta xonani tozalaydigan ayol kerak."}),
    )
