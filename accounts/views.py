from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import (
    UserApprovalForm, UserSearchForm, CustomUserCreationForm,
    InstructorRegistrationForm, AdminRegistrationForm,  # Add these imports
    HodRegistrationForm, RegistrarRegistrationForm, ProfileUpdateForm
)
from django.db.models import Count, Q
from django.utils import timezone
from attendance.models import AttendanceSession, AttendanceRecord
from students.models import Student
from courses.models import Course, Class
from django.contrib.auth.views import LoginView
from accounts.models import User

def dashboard_view(request):
    # Get today's date
    today = timezone.now().date()
    
    # Initialize context with default values
    context = {
        'total_students': 0,
        'male_students': 0,
        'female_students': 0,
        'total_courses': 0,
        'total_classes': 0,
        'today_attendance': 0,
        'today_present': 0,
        'today_absent': 0,
        'today_late': 0,
        'total_instructors': 0,
        'total_attendance_records': 0,
        'total_present': 0,
        'attendance_rate': 0,
        'active_sessions': [],
        'recent_sessions': [],
        'active_sessions_count': 0,
        'active_session': None,
        'top_departments': [],
        'user_type': request.user.user_type if request.user.is_authenticated else None,
    }
    
    # Fetch real data from all apps
    if request.user.is_authenticated:
        # Student statistics
        context['total_students'] = Student.objects.filter(status='active').count()
        context['male_students'] = Student.objects.filter(gender='male', status='active').count()
        context['female_students'] = Student.objects.filter(gender='female', status='active').count()
        
        # Course statistics
        context['total_courses'] = Course.objects.filter(is_active=True).count()
        context['total_classes'] = Class.objects.filter(is_active=True).count()
        
        # Instructor statistics
        context['total_instructors'] = User.objects.filter(
            user_type='instructor', 
            is_active=True
        ).count()
        
        # Today's attendance statistics
        today_attendance_records = AttendanceRecord.objects.filter(
            session__session_date=today
        )
        context['today_attendance'] = today_attendance_records.count()
        context['today_present'] = today_attendance_records.filter(status='present').count()
        context['today_absent'] = today_attendance_records.filter(status='absent').count()
        context['today_late'] = today_attendance_records.filter(status='late').count()
        
        # Overall attendance statistics
        context['total_attendance_records'] = AttendanceRecord.objects.count()
        context['total_present'] = AttendanceRecord.objects.filter(status='present').count()
        
        # Calculate attendance rate for today
        if context['today_attendance'] > 0:
            context['attendance_rate'] = round(
                (context['today_present'] / context['today_attendance']) * 100, 1
            )
        
        # Initialize sessions as empty lists/querysets
        active_sessions = AttendanceSession.objects.none()
        recent_sessions = AttendanceSession.objects.none()
        
        # Get active sessions based on user type
        if request.user.user_type == 'instructor':
            # Show sessions for this instructor
            active_sessions = AttendanceSession.objects.filter(
                instructor=request.user,
                status='ongoing'
            ).select_related('class_session', 'class_session__course')
            
            recent_sessions = AttendanceSession.objects.filter(
                instructor=request.user
            ).exclude(status='ongoing').order_by('-session_date', '-start_time')[:5]
            
        elif request.user.user_type == 'student':
            # Show sessions for student's class
            try:
                student = request.user.student
                if student.current_class:
                    active_sessions = AttendanceSession.objects.filter(
                        class_session=student.current_class,
                        status='ongoing'
                    ).select_related('class_session', 'class_session__course', 'instructor')
                    
                    recent_sessions = AttendanceSession.objects.filter(
                        class_session=student.current_class
                    ).exclude(status='ongoing').order_by('-session_date', '-start_time')[:5]
                    
                    # Get student's personal attendance stats
                    student_records = AttendanceRecord.objects.filter(student=student)
                    context['my_attendance'] = student_records.count()
                    context['my_present'] = student_records.filter(status='present').count()
                    
                    # Calculate student's attendance rate
                    if context['my_attendance'] > 0:
                        context['my_attendance_rate'] = round(
                            (context['my_present'] / context['my_attendance']) * 100, 1
                        )
                    else:
                        context['my_attendance_rate'] = 0
                else:
                    # Student has no current class
                    active_sessions = AttendanceSession.objects.none()
                    recent_sessions = AttendanceSession.objects.none()
                    context['my_attendance'] = 0
                    context['my_present'] = 0
                    context['my_attendance_rate'] = 0
            except Student.DoesNotExist:
                # Student profile doesn't exist
                active_sessions = AttendanceSession.objects.none()
                recent_sessions = AttendanceSession.objects.none()
                context['my_attendance'] = 0
                context['my_present'] = 0
                context['my_attendance_rate'] = 0
        else:
            # Admin/staff - show all active sessions
            active_sessions = AttendanceSession.objects.filter(
                status='ongoing'
            ).select_related('class_session', 'class_session__course', 'instructor')
            
            recent_sessions = AttendanceSession.objects.exclude(
                status='ongoing'
            ).order_by('-session_date', '-start_time')[:10]
        
        # Process sessions data - FIX: Check if it's a queryset before calling count()
        if hasattr(active_sessions, 'count'):
            # It's a queryset
            context['active_sessions_count'] = active_sessions.count()
            context['active_session'] = active_sessions.first() if active_sessions.exists() else None
            
            # Get other recent sessions (excluding the first one if it's the active session)
            if context['active_session']:
                # Convert to list and slice
                active_list = list(active_sessions)
                context['recent_sessions'] = active_list[1:5] if len(active_list) > 1 else []
            else:
                context['recent_sessions'] = recent_sessions
        else:
            # It's a list
            context['active_sessions_count'] = len(active_sessions)
            context['active_session'] = active_sessions[0] if active_sessions else None
            context['recent_sessions'] = active_sessions[1:5] if len(active_sessions) > 1 else recent_sessions
        
        # Add department distribution (if you have departments)
        departments = Course.objects.values('department').annotate(
            count=Count('id')
        ).filter(department__isnull=False).exclude(department='').order_by('-count')[:5]
        context['top_departments'] = departments
    
    return render(request, 'accounts/dashboard.html', context)





def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

class CustomLoginView(LoginView):
    """
    Custom login view that redirects users based on their user type
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        
        # Redirect based on user type using existing URLs
        if user.user_type == 'admin' or user.is_superuser:
            return reverse('admin:index')  # Django admin
        elif user.user_type == 'hod':
            # Redirect HOD to main dashboard for now
            return reverse('dashboard')
        elif user.user_type == 'instructor':
            # Redirect instructors to main dashboard for now
            return reverse('dashboard')
        elif user.user_type == 'registrar':
            # Redirect registrars to main dashboard for now
            return reverse('dashboard')
        elif user.user_type == 'student':
            # Students go to student_dashboard (this exists)
            return reverse('student_dashboard')
        else:
            # Default fallback
            return reverse('dashboard')
        

def is_admin(user):
    return user.is_authenticated and (user.user_type == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def pending_approvals_view(request):
    """
    View for admins to see and approve/reject pending user accounts
    """
    # Get all pending users (instructors, HODs, registrars who need approval)
    pending_users = User.objects.filter(
        account_status='pending'
    ).order_by('-date_joined')
    
    # Handle approval/rejection
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        pending_user = get_object_or_404(User, id=user_id, account_status='pending')
        
        if action == 'approve':
            pending_user.account_status = 'approved'
            pending_user.is_active = True
            pending_user.save()
            messages.success(request, f'User {pending_user.username} has been approved.')
            
        elif action == 'reject':
            form = UserApprovalForm(request.POST, instance=pending_user)
            if form.is_valid():
                form.save()
                messages.warning(request, f'User {pending_user.username} has been rejected.')
            else:
                messages.error(request, 'Please provide a reason for rejection.')
                return redirect('pending_approvals')
        
        return redirect('pending_approvals')
    
    # Search functionality
    search_form = UserSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        user_type = search_form.cleaned_data.get('user_type')
        
        if query:
            pending_users = pending_users.filter(
                models.Q(username__icontains=query) |
                models.Q(email__icontains=query) |
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query)
            )
        if user_type:
            pending_users = pending_users.filter(user_type=user_type)
    
    # Pagination
    paginator = Paginator(pending_users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pending_users': page_obj,
        'search_form': search_form,
        'total_pending': pending_users.count(),
    }
    return render(request, 'accounts/pending_approvals.html', context)


@login_required
@user_passes_test(is_admin)
def approve_user_view(request, user_id):
    """
    View to approve a specific pending user
    """
    pending_user = get_object_or_404(User, id=user_id, account_status='pending')
    
    if request.method == 'POST':
        form = UserApprovalForm(request.POST, instance=pending_user)
        if form.is_valid():
            form.save()
            if form.cleaned_data['account_status'] == 'approved':
                messages.success(request, f'User {pending_user.username} has been approved.')
            else:
                messages.warning(request, f'User {pending_user.username} has been rejected.')
            return redirect('pending_approvals')
    else:
        form = UserApprovalForm(instance=pending_user)
    
    context = {
        'form': form,
        'pending_user': pending_user,
    }
    return render(request, 'accounts/approve_user.html', context)


@login_required
@user_passes_test(is_admin)
def bulk_approve_users_view(request):
    """
    View to approve multiple users at once
    """
    if request.method == 'POST':
        user_ids = request.POST.getlist('selected_users')
        action = request.POST.get('bulk_action')
        
        if not user_ids:
            messages.warning(request, 'No users selected.')
            return redirect('pending_approvals')
        
        users = User.objects.filter(id__in=user_ids, account_status='pending')
        
        if action == 'approve':
            count = users.update(account_status='approved', is_active=True)
            messages.success(request, f'{count} user(s) have been approved.')
        elif action == 'reject':
            # For bulk reject, we need a reason
            reason = request.POST.get('bulk_rejection_reason')
            if not reason:
                messages.error(request, 'Rejection reason is required for bulk rejection.')
                return redirect('pending_approvals')
            
            count = users.update(
                account_status='rejected', 
                is_active=False,
                rejection_reason=reason
            )
            messages.warning(request, f'{count} user(s) have been rejected.')
        
    return redirect('pending_approvals')


# ============= NEW VIEWS ADDED BELOW =============

@login_required
@user_passes_test(is_admin)
def create_instructor_view(request):
    """
    Admin view to create instructor accounts
    """
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Instructor account {user.username} created successfully!')
            return redirect('pending_approvals')
    else:
        form = InstructorRegistrationForm()
    
    return render(request, 'accounts/create_instructor.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def create_admin_view(request):
    """
    Admin view to create admin accounts
    Note: Only superusers can create admin accounts
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can create admin accounts.')
        return redirect('pending_approvals')
    
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Admin account {user.username} created successfully!')
            return redirect('pending_approvals')
    else:
        form = AdminRegistrationForm()
    
    return render(request, 'accounts/create_admin.html', {'form': form})


# Optional: Add HOD creation view if needed
@login_required
@user_passes_test(is_admin)
def create_hod_view(request):
    """
    Admin view to create HOD accounts
    """
    if request.method == 'POST':
        form = HodRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'HOD account {user.username} created successfully!')
            return redirect('pending_approvals')
    else:
        form = HodRegistrationForm()
    
    return render(request, 'accounts/create_hod.html', {'form': form})


# Optional: Add Registrar creation view if needed
@login_required
@user_passes_test(is_admin)
def create_registrar_view(request):
    """
    Admin view to create Registrar accounts
    """
    if request.method == 'POST':
        form = RegistrarRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Registrar account {user.username} created successfully!')
            return redirect('pending_approvals')
    else:
        form = RegistrarRegistrationForm()
    
    return render(request, 'accounts/create_registrar.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

def handler403(request, exception=None):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

def handler404(request, exception=None):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)