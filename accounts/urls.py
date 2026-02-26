from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin approval URLs
    path('approvals/', views.pending_approvals_view, name='pending_approvals'),
    path('approvals/<int:user_id>/', views.approve_user_view, name='approve_user'),
    path('approvals/bulk-approve/', views.bulk_approve_users_view, name='bulk_approve'),
    
    # Account creation URLs (admin only)
    path('create/instructor/', views.create_instructor_view, name='create_instructor'),
    path('create/admin/', views.create_admin_view, name='create_admin'),
    path('create/hod/', views.create_hod_view, name='create_hod'),
    path('create/registrar/', views.create_registrar_view, name='create_registrar'),
]