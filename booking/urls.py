# booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # student flows
    path('', views.home, name='home'),
    path('student/login/', views.student_login_view, name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/book/<int:slot_id>/<str:session_start>/', views.book_session, name='book_session'),
    path('student/logout/', views.student_logout, name='student_logout'),

    # counselor flows
    path('login/', views.unified_login_view, name='login'),

    path('counselor/dashboard/', views.counselor_dashboard, name='counselor_dashboard'),
    path('counselor/slots/add/', views.add_slot, name='add_slot'),
    path('counselor/bookings/', views.counselor_bookings, name='counselor_bookings'),
    path('counselor/history/', views.counselor_history, name='counselor_history'),
    path('counselor/booking/<int:booking_id>/remark/', views.add_remark, name='add_remark'),
    path('counselor/logout/', views.counselor_logout, name='counselor_logout'),
    path('login/', views.unified_login_view, name='login'),

path('principal/dashboard/', views.principal_dashboard, name='principal_dashboard'),
path('principal/add-counselor/', views.add_counselor, name='add_counselor'),
path('principal/delete-counselor/<int:user_id>/', views.delete_counselor, name='delete_counselor'),
path('principal/add-counselor/', views.add_counselor, name='add_counselor'),
path(
    'principal/delete-counselor/<int:user_id>/',
    views.delete_counselor,
    name='delete_counselor'
),



]
