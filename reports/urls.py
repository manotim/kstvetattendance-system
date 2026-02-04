from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.reports_dashboard, name='dashboard'),
    
    # Attendance Reports
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('student-attendance/', views.student_attendance_report, name='student_attendance_report'),
    path('class-attendance/', views.class_attendance_report, name='class_attendance_report'),
    
    # Export
    path('export/<str:report_type>/', views.export_report, name='export_report'),
    
    # Saved Reports
    path('save/', views.save_report, name='save_report'),
    path('saved/<int:report_id>/', views.view_saved_report, name='view_saved'),
    
    # Widgets and Quick Reports
    path('widget/<int:widget_id>/data/', views.dashboard_widget_data, name='widget_data'),
    path('quick-report/', views.generate_quick_report, name='quick_report'),
]