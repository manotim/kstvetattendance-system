# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .forms import CustomUserCreationForm
from attendance.models import AttendanceSession, AttendanceRecord
from students.models import Student
from courses.models import Course, Class
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

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')