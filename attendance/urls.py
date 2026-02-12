# attendance/urls.py
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard and overview
    path('', views.attendance_dashboard, name='dashboard'),
    
    # Session management
    path('session/create/', views.create_session, name='create_session'),
    path('session/<int:session_id>/', views.mark_attendance, name='mark_attendance'),
    path('session/<int:session_id>/bulk/', views.bulk_mark_attendance, name='bulk_mark'),
    path('session/<int:session_id>/qr/', views.qr_attendance, name='qr_attendance'),
    path('session/<int:session_id>/qr/view/', views.view_qr_code, name='view_qr'),
    
    # Reports
    path('report/', views.attendance_report, name='report'),
    path('report/export/', views.export_attendance_report, name='export_report'),
    
    # Student attendance
    path('student/history/', views.student_attendance_history, name='student_history'),
    path('student/<int:student_id>/history/', views.student_attendance_history, name='student_history_by_id'),
    
    # Excuse management
    path('excuse/apply/', views.apply_excuse, name='apply_excuse'),
    path('excuse/list/', views.excuse_list, name='excuse_list'),
    path('excuse/<int:excuse_id>/review/', views.review_excuse, name='review_excuse'),
    
    # AJAX endpoints
    path('record/<int:record_id>/update/', views.update_attendance_status, name='update_status'),
]