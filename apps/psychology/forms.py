from django import forms
from django.utils import timezone

from .models import Consultation, Psychologist, PsychologistSchedule


class PsychologistProfileForm(forms.ModelForm):
    class Meta:
        model = Psychologist
        fields = ["specialization", "experience_years", "consultation_format", "office_address", "about"]
        widgets = {"about": forms.Textarea(attrs={"rows": 4})}


class SlotForm(forms.ModelForm):
    class Meta:
        model = PsychologistSchedule
        fields = ["start_at", "end_at"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def clean(self):
        data = super().clean()
        start, end = data.get("start_at"), data.get("end_at")
        if start and end:
            if end <= start:
                self.add_error("end_at", "Tugash vaqti boshlanishdan keyin bo‘lishi kerak.")
            if start < timezone.now():
                self.add_error("start_at", "O‘tgan vaqtni belgilab bo‘lmaydi.")
        return data


class BookingForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ["slot", "format", "message"]
        labels = {"slot": "Bo‘sh vaqt", "message": "Murojaat (ixtiyoriy, faqat psixologga ko‘rinadi)"}
        widgets = {"slot": forms.RadioSelect, "format": forms.RadioSelect, "message": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, psychologist=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.psychologist = psychologist
        self.fields["slot"].queryset = PsychologistSchedule.objects.filter(
            psychologist=psychologist, is_booked=False, start_at__gt=timezone.now()
        )
        self.fields["slot"].empty_label = None
        self.fields["slot"].label_from_instance = lambda s: timezone.localtime(s.start_at).strftime("%d.%m.%Y, %H:%M") + " – " + timezone.localtime(s.end_at).strftime("%H:%M")
        choices = [c for c in Consultation._meta.get_field("format").choices if psychologist.supports(c[0])]
        self.fields["format"].choices = choices
        if len(choices) == 1:
            self.fields["format"].initial = choices[0][0]
