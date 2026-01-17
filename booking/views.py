# ----------------- Counselor flows -----------------
from django.contrib.auth.models import Group
from django.contrib.auth.models import User, Group
from django.db.models import Count
from django.contrib.auth.decorators import user_passes_test
# booking/views.py
import datetime
from datetime import time as dtime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CounselorLoginForm, SlotCreateForm, StudentLoginForm, BookingForm
from .models import Slot, Booking
from django.contrib import messages

def is_principal(user):
    return user.is_authenticated and user.groups.filter(name="Principal").exists()
def principal_required(view_func):
    return login_required(user_passes_test(is_principal)(view_func))

def home(request):
    return render(request, 'booking/home.html')

# ----------------- Student flows -----------------
def student_login_view(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            # store student info in session
            request.session['student'] = {
                'name': form.cleaned_data['student_name'],
                'email': form.cleaned_data['student_email'],
            }
            return redirect('booking:student_dashboard')
    else:
        form = StudentLoginForm()
    return render(request, 'booking/student_login.html', {'form': form})

def student_logout(request):
    request.session.pop('student', None)
    return redirect('booking:home')

def student_dashboard(request):
    student = request.session.get('student')
    if not student:
        return redirect('booking:student_login')
    # show all future slots and their 15-min sessions that are free
    slots = Slot.objects.filter(date__gte=datetime.date.today()).order_by('date', 'start_time')
    # build a structure for available sessions
    available = []
    for slot in slots:
        for sstart, send in slot.generate_sessions():
            # check if that session is booked
            booked = Booking.objects.filter(slot=slot, session_start=sstart).exists()
            if not booked:
                available.append({
                    'slot': slot,
                    'session_start': sstart.strftime('%H:%M:%S'),
                    'session_end': send.strftime('%H:%M:%S'),
                })
    return render(request, 'booking/student_dashboard.html', {'student': student, 'available': available})

def book_session(request, slot_id, session_start):
    """
    Book a specific 15-min session. `session_start` is a string like '12:00:00'.
    """
    student_in_session = request.session.get('student')
    slot = get_object_or_404(Slot, id=slot_id)

    # parse session_start string to time using the module-level datetime
    sstart = datetime.datetime.strptime(session_start, '%H:%M:%S').time()

    # if already booked -> inform
    if Booking.objects.filter(slot=slot, session_start=sstart).exists():
        messages.error(request, "Sorry, this session was just booked.")
        return redirect('booking:student_dashboard')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.slot = slot
            b.session_start = sstart
            # compute session_end (15 minutes later)
            dt = datetime.datetime.combine(slot.date, sstart) + datetime.timedelta(minutes=60)
            b.session_end = dt.time()
            b.save()
            # update session student fields in case they booked with different name/email
            request.session['student'] = {
                'name': b.student_name,
                'email': b.student_email
            }
            messages.success(request, "Booking successful!")
            return redirect('booking:student_dashboard')
    else:
        # prefill form if we have session student data
        initial = {}
        if student_in_session:
            initial['student_name'] = student_in_session.get('name')
            initial['student_email'] = student_in_session.get('email')
        form = BookingForm(initial=initial)
    return render(request, 'booking/book_session.html', {'form': form, 'slot': slot, 'session_start': sstart})


def unified_login_view(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Principal").exists():
            return redirect('booking:principal_dashboard')
        if request.user.groups.filter(name="Counselor").exists():
            return redirect('booking:counselor_dashboard')
        logout(request)

    if request.method == 'POST':
        form = CounselorLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if user.groups.filter(name="Principal").exists():
                login(request, user)
                return redirect('booking:principal_dashboard')

            if user.groups.filter(name="Counselor").exists():
                login(request, user)
                return redirect('booking:counselor_dashboard')

            messages.error(request, "You are not authorized to access this system.")
    else:
        form = CounselorLoginForm()

    return render(request, 'booking/login.html', {'form': form})


@login_required
def counselor_logout(request):
    logout(request)
    return redirect('booking:login')

@login_required
def counselor_dashboard(request):
    # basic summary: upcoming slots & bookings
    slots = Slot.objects.filter(counselor=request.user, date__gte=datetime.date.today()).order_by('date')
    return render(request, 'booking/counselor_dashboard.html', {'slots': slots})

@login_required
def add_slot(request):
    if request.method == 'POST':
        form = SlotCreateForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.counselor = request.user
            slot.save()
            messages.success(request, "Slot added. 15-min sessions generated automatically for booking.")
            return redirect('booking:counselor_dashboard')
    else:
        form = SlotCreateForm()
    return render(request, 'booking/add_slot.html', {'form': form})

@login_required
def counselor_bookings(request):
    # show bookings for upcoming slots
    bookings = Booking.objects.filter(slot__counselor=request.user, slot__date__gte=datetime.date.today()).order_by('slot__date', 'session_start')
    return render(request, 'booking/counselor_bookings.html', {'bookings': bookings})

@login_required
def counselor_history(request):
    bookings = Booking.objects.filter(slot__counselor=request.user).order_by('-slot__date', '-session_start')
    return render(request, 'booking/counselor_history.html', {'bookings': bookings})

@login_required
def add_remark(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, slot__counselor=request.user)
    if request.method == 'POST':
        remark = request.POST.get('remark', '').strip()
        booking.counselor_remark = remark
        booking.attended = True if request.POST.get('attended') == 'on' else booking.attended
        booking.save()
        messages.success(request, "Remark saved.")
        return redirect('booking:counselor_history')
    return render(request, 'booking/add_remark.html', {'booking': booking})


def principal_login_view(request):
    if request.user.is_authenticated and is_principal(request.user):
        return redirect('booking:principal_dashboard')

    if request.method == 'POST':
        form = CounselorLoginForm(data=request.POST)  # reuse form
        if form.is_valid():
            user = form.get_user()

            if not is_principal(user):
                messages.error(request, "Not a principal account.")
                return redirect('booking:principal_login')

            login(request, user)
            return redirect('booking:principal_dashboard')
    else:
        form = CounselorLoginForm()

    return render(request, 'booking/principal_login.html', {'form': form})


@principal_required
def principal_dashboard(request):
    total_bookings = Booking.objects.count()
    attended = Booking.objects.filter(attended=True).count()
    not_attended = total_bookings - attended

    per_counselor = (
        Booking.objects
        .values('slot__counselor__username')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    counselors = User.objects.filter(groups__name="Counselor")

    return render(request, 'booking/principal_dashboard.html', {
        'total_bookings': total_bookings,
        'attended': attended,
        'not_attended': not_attended,
        'per_counselor': per_counselor,
        'counselors': counselors,
    })

@principal_required

def add_counselor(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "All fields are required.")
            return redirect('booking:add_counselor')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('booking:add_counselor')

        user = User.objects.create_user(
            username=username,
            password=password,
            is_active=True
        )

        Group.objects.get(name="Counselor").user_set.add(user)

        messages.success(request, "Counselor added successfully.")
        return redirect('booking:principal_dashboard')

    return render(request, 'booking/add_counselor.html')


@principal_required
def delete_counselor(request, user_id):
    counselor = get_object_or_404(User, id=user_id)

    # Safety: ensure user is actually a counselor
    if not counselor.groups.filter(name="Counselor").exists():
        messages.error(request, "This user is not a counselor.")
        return redirect('booking:principal_dashboard')

    # Optional safety: prevent deletion if bookings exist
    has_bookings = Booking.objects.filter(
        slot__counselor=counselor
    ).exists()

    if has_bookings:
        messages.error(
            request,
            "Cannot delete counselor with existing bookings."
        )
        return redirect('booking:principal_dashboard')

    counselor.delete()
    messages.success(request, "Counselor deleted successfully.")
    return redirect('booking:principal_dashboard')

