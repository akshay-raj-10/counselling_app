# booking/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime, time

class CounselorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='counselor_profile')
    # you can add more fields like department, phone etc
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Slot(models.Model):
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.counselor.username} {self.date} {self.start_time}-{self.end_time}"

    def generate_sessions(self):
        """
        Returns list of (start_time, end_time) 15-min sessions between start_time and end_time.
        """
        sessions = []
        dt = datetime.combine(self.date, self.start_time)
        end_dt = datetime.combine(self.date, self.end_time)
        while dt + timedelta(minutes=60) <= end_dt:
            sessions.append((dt.time(), (dt + timedelta(minutes=60)).time()))
            dt += timedelta(minutes=60)
        return sessions

class Booking(models.Model):
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='bookings')
    session_start = models.TimeField()  # the 15-min session start time
    session_end = models.TimeField()
    student_name = models.CharField(max_length=150)
    student_email = models.EmailField()
    student_department = models.CharField(max_length=150)
    student_year = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    counselor_remark = models.TextField(blank=True, null=True)
    attended = models.BooleanField(default=False)

    def masked_student_name(self):
        parts = self.student_name.split()
        masked = []
        for p in parts:
            if len(p) <= 1:
                masked.append("*")
            else:
                masked.append(p[0] + "*" * (len(p) - 1))
        return " ".join(masked)
    def masked_student_email(self):
        """
        Example:
        john.doe@gmail.com → j***.***@g****.com
        a@x.com → *@*.com
        """
        try:
            local, domain = self.student_email.split('@')
            domain_name, domain_ext = domain.rsplit('.', 1)

            # mask local part
            if len(local) <= 1:
                local_masked = '*'
            else:
                local_masked = local[0] + '*' * (len(local) - 1)

            # mask domain name
            if len(domain_name) <= 1:
                domain_masked = '*'
            else:
                domain_masked = domain_name[0] + '*' * (len(domain_name) - 1)

            return f"{local_masked}@{domain_masked}.{domain_ext}"
        except Exception:
            return "***@***"

    class Meta:
        unique_together = ('slot', 'session_start')  # prevents double-booking same session

    def __str__(self):
        return f"Booking {self.student_name} {self.slot.date} {self.session_start}"
    