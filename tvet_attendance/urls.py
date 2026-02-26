# tvet_attendance/urls.py (or whatever your project folder is named)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from accounts.views import dashboard_view
from accounts.views import CustomLoginView  # We'll create this

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Main dashboard
    path('', dashboard_view, name='dashboard'),
    
    # App includes
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('courses/', include('courses.urls')),
    path('attendance/', include('attendance.urls')),
    path('reports/', include('reports.urls')),
    
    # Custom authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Password reset URLs (optional but recommended)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), name='password_reset_complete'),
    
    # Password change URLs
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/password-change/done/'
         ), name='password_change'),
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ), name='password_change_done'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar (optional - install django-debug-toolbar if needed)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers (optional)
handler404 = 'accounts.views.handler404'
handler500 = 'accounts.views.handler500'
handler403 = 'accounts.views.handler403'