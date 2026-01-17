# booking/forms.py  (replace SlotCreateForm with this)
from django import forms
from .models import Slot, Booking
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from datetime import datetime, timedelta

class CounselorLoginForm(AuthenticationForm):
    pass

class SlotCreateForm(forms.ModelForm):
    class Meta:
        model = Slot
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'step': '900', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'step': '900', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get('date')
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')

        if not (date and start and end):
            return cleaned

        if start >= end:
            raise forms.ValidationError("End time must be after start time.")

        slot_start_dt = datetime.combine(date, start)
        now = timezone.localtime(timezone.now()).replace(tzinfo=None)

        if slot_start_dt < now:
            raise forms.ValidationError("Slot start is in the past. Choose a future date/time.")

        def minutes_ok(t):
            return (t.minute % 60) == 0 and t.second == 0 and t.microsecond == 0

        if not minutes_ok(start) or not minutes_ok(end):
            raise forms.ValidationError("Start and end times must be aligned to 15-minute increments (e.g. 10:00, 10:15, 10:30).")

        if (datetime.combine(date, end) - datetime.combine(date, start)) < timedelta(minutes=15):
            raise forms.ValidationError("Slot window must be at least 15 minutes.")

        return cleaned

# (leave StudentLoginForm and BookingForm as before)


class StudentLoginForm(forms.Form):
    student_name = forms.CharField(max_length=150, label='Your name')
    student_email = forms.EmailField(label='Your email')

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['student_name', 'student_email', 'student_department', 'student_year']
