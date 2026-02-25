# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from attendance.models import AttendanceSession

def dashboard_view(request):
    # Get active sessions based on user type
    if request.user.is_authenticated:
        if request.user.user_type == 'instructor':
            # Show sessions for this instructor
            sessions = AttendanceSession.objects.filter(
                instructor=request.user,
                status='ongoing'  # Only active sessions
            ).order_by('-session_date', '-start_time')[:5]  # Last 5 sessions
            
        elif request.user.user_type == 'student':
            # Show sessions for student's class
            try:
                student = request.user.student
                sessions = AttendanceSession.objects.filter(
                    class_session=student.current_class,
                    status='ongoing'
                ).order_by('-session_date', '-start_time')[:5]
            except:
                sessions = []
        else:
            # Admin/staff - show all active sessions
            sessions = AttendanceSession.objects.filter(
                status='ongoing'
            ).order_by('-session_date', '-start_time')[:5]
    else:
        sessions = []
    
    context = {
        'sessions': sessions
    }
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