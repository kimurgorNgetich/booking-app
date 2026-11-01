import re
from django import forms
from django.utils import timezone
from .models import Service


class BookingForm(forms.Form):
    name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=15, help_text="e.g. 0712345678")
    service = forms.ModelChoiceField(queryset=Service.objects.all())
    start_time = forms.DateTimeField(
        label="Date and time",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full border rounded-lg px-3 py-2"

    def clean_phone(self):
        phone = re.sub(r"\D", "", self.cleaned_data["phone"])
        if re.fullmatch(r"0[17]\d{8}", phone):
            phone = "254" + phone[1:]
        if not re.fullmatch(r"254[17]\d{8}", phone):
            raise forms.ValidationError("Enter a valid Safaricom number, e.g. 0712345678.")
        return phone

    def clean_start_time(self):
        start = self.cleaned_data["start_time"]
        if start <= timezone.now():
            raise forms.ValidationError("Please pick a time in the future.")
        return start