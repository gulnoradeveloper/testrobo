from django import forms
from django.urls import reverse_lazy

from .models import Report
from .validators import IMAGE_VALIDATORS


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Bir nechta rasmni yuklash; har biri turi va hajmi bo'yicha tekshiriladi."""

    def __init__(self, *args, max_files=6, **kwargs):
        self.max_files = max_files
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
        kwargs.setdefault("required", False)
        kwargs.setdefault("validators", IMAGE_VALIDATORS)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            if len(data) > self.max_files:
                raise forms.ValidationError(f"Ko‘pi bilan {self.max_files} ta rasm yuklash mumkin.")
            return [single(d, initial) for d in data if d]
        return [single(data, initial)] if data else []


def wire_region_fields(form, region="region", district="district", mahalla=None):
    """Viloyat tanlanganda tuman/mahalla ro'yxatini JS orqali yangilash uchun atributlar."""
    attrs = {
        "data-region": f"#id_{form.add_prefix(district)}",
        "data-districts-url": reverse_lazy("core:districts_json"),
        "data-mahallas-url": reverse_lazy("core:mahallas_json"),
    }
    if mahalla:
        attrs["data-mahalla"] = f"#id_{form.add_prefix(mahalla)}"
    form.fields[region].widget.attrs.update(attrs)


class RegionSelectMixin:
    """Viloyat -> tuman -> mahalla izchilligini server tomonida tekshirish."""

    def clean(self):
        data = super().clean()
        region, district = data.get("region"), data.get("district")
        mahalla = data.get("mahalla")
        if region and district and district.region_id != region.pk:
            self.add_error("district", "Tanlangan tuman ushbu viloyatga tegishli emas.")
        if district and mahalla and mahalla.district_id != district.pk:
            self.add_error("mahalla", "Tanlangan mahalla ushbu tumanga tegishli emas.")
        return data


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Qisqacha izoh (ixtiyoriy)"})}
