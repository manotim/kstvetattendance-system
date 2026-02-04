from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course URLs
    path('', views.course_list, name='list'),
    path('create/', views.course_create, name='create'),
    path('<int:pk>/', views.course_detail, name='detail'),
    path('<int:pk>/update/', views.course_update, name='update'),
    path('<int:pk>/delete/', views.course_delete, name='delete'),
    
    # Class URLs
    path('classes/', views.class_list, name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/<int:pk>/update/', views.class_update, name='class_update'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),
    path('classes/<int:class_id>/enroll/', views.enroll_students, name='enroll_students'),
    
    # User-specific views
    path('instructor/classes/', views.instructor_classes, name='instructor_classes'),
    path('student/classes/', views.student_classes, name='student_classes'),
]