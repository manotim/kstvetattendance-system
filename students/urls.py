# students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student management (accessible by instructors)
    path('', views.student_list, name='list'),
    path('register/', views.student_register, name='register'),
    path('bulk-import/', views.bulk_import_students, name='bulk_import'),
    
    # Individual student operations
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/update/', views.student_update, name='update'),
    path('<int:pk>/enroll/', views.enroll_student, name='enroll'),
    path('<int:pk>/toggle-status/', views.toggle_student_status, name='toggle_status'),
    
    # Student dashboard (for students themselves)
    path('dashboard/', views.student_dashboard, name='dashboard'),
    
    # Class-based student views (for instructors)
    path('class/<int:class_id>/', views.students_by_class, name='students_by_class'),
    path('class/<int:class_id>/add-existing/', views.add_existing_students_to_class, name='add_existing_to_class'),
    path('class/<int:class_id>/add-student/', views.student_register, name='add_student_to_class'),
]