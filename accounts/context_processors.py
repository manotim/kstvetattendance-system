# accounts/context_processors.py
from attendance.models import AttendanceSession

def active_session(request):
    """Make active session available to all templates"""
    context = {
        'active_session': None,
        'active_sessions_count': 0,
        'recent_sessions': []
    }
    
    if request.user.is_authenticated:
        # INSTRUCTOR: Get their ongoing sessions
        if request.user.user_type == 'instructor':
            active_sessions = AttendanceSession.objects.filter(
                instructor=request.user,
                status='ongoing'
            ).order_by('-session_date', '-start_time')
            
            context['active_sessions_count'] = active_sessions.count()
            context['active_session'] = active_sessions.first()
            context['recent_sessions'] = active_sessions[:3]
        
        # STUDENT: Get their class's ongoing sessions
        elif request.user.user_type == 'student':
            try:
                student = request.user.student
                if student.current_class:
                    active_sessions = AttendanceSession.objects.filter(
                        class_session=student.current_class,
                        status='ongoing'
                    ).order_by('-session_date', '-start_time')
                    
                    context['active_sessions_count'] = active_sessions.count()
                    context['active_session'] = active_sessions.first()
                    context['recent_sessions'] = active_sessions[:3]
            except:
                pass
        
        # ADMIN/STAFF: Get all ongoing sessions
        elif request.user.is_staff or request.user.user_type == 'admin':
            active_sessions = AttendanceSession.objects.filter(
                status='ongoing'
            ).order_by('-session_date', '-start_time')
            
            context['active_sessions_count'] = active_sessions.count()
            context['active_session'] = active_sessions.first()
            context['recent_sessions'] = active_sessions[:3]
    
    return context