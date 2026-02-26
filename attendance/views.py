# attendance/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import AttendanceSession, AttendanceRecord, AttendanceSummary, ExcuseApplication
from .forms import (
    AttendanceSessionForm, ManualAttendanceForm, BulkAttendanceForm, 
    QRAttendanceForm, ExcuseApplicationForm, AttendanceReportFilterForm
)
from students.models import Student
from courses.models import Class

@login_required
def attendance_dashboard(request):
    """Main attendance dashboard"""
    today = timezone.now().date()
    
    # Get user's classes (if instructor)
    if request.user.user_type == 'instructor':
        active_sessions = AttendanceSession.objects.filter(
            class_session__instructor=request.user,
            status='ongoing'
        )
        
        today_sessions = AttendanceSession.objects.filter(
            class_session__instructor=request.user,
            session_date=today
        ).order_by('start_time')
        
        upcoming_sessions = AttendanceSession.objects.filter(
            class_session__instructor=request.user,
            session_date__gt=today,
            status='scheduled'
        ).order_by('session_date', 'start_time')[:5]
        
    elif request.user.user_type == 'student':
        # Student view - show their attendance
        try:
            student = request.user.student
            active_sessions = AttendanceSession.objects.filter(
                class_session=student.current_class,
                status='ongoing'
            )
            
            today_sessions = AttendanceSession.objects.filter(
                class_session=student.current_class,
                session_date=today
            ).order_by('start_time')
            
            # Get student's recent attendance
            recent_attendance = AttendanceRecord.objects.filter(
                student=student
            ).select_related('session', 'session__class_session').order_by('-session__session_date')[:10]
            
            # Calculate attendance stats
            total_sessions = AttendanceSession.objects.filter(
                class_session=student.current_class,
                session_date__gte=student.created_at.date()
            ).count()
            
            present_count = AttendanceRecord.objects.filter(
                student=student,
                status='present'
            ).count()
            
            attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0
            
            context = {
                'active_sessions': active_sessions,
                'today_sessions': today_sessions,
                'recent_attendance': recent_attendance,
                'attendance_rate': round(attendance_rate, 2),
                'present_count': present_count,
                'total_sessions': total_sessions,
                'student': student,
            }
            return render(request, 'attendance/student_dashboard.html', context)
            
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
    
    else:
        # Admin/Registrar view
        active_sessions = AttendanceSession.objects.filter(status='ongoing')
        today_sessions = AttendanceSession.objects.filter(session_date=today)
        upcoming_sessions = AttendanceSession.objects.filter(
            session_date__gte=today,
            status='scheduled'
        ).order_by('session_date', 'start_time')[:5]
    
    # Statistics for admin/instructor
    total_sessions_today = today_sessions.count()
    active_sessions_count = active_sessions.count()
    
    # Get attendance statistics for today
    today_attendance = AttendanceRecord.objects.filter(
        session__session_date=today
    ).aggregate(
        total_present=Count('id', filter=Q(status='present')),
        total_absent=Count('id', filter=Q(status='absent')),
        total_late=Count('id', filter=Q(status='late'))
    )
    
    context = {
        'active_sessions': active_sessions,
        'today_sessions': today_sessions,
        'upcoming_sessions': upcoming_sessions,
        'total_sessions_today': total_sessions_today,
        'active_sessions_count': active_sessions_count,
        'today_stats': today_attendance,
    }
    
    return render(request, 'attendance/dashboard.html', context)


@login_required
@permission_required('attendance.add_attendancesession', raise_exception=True)
def create_session(request):
    """Create a new attendance session"""
    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.instructor = request.user
            session.save()
            
            # Pre-populate attendance records for all enrolled students
            enrolled_students = session.class_session.enrollments.filter(
                is_active=True
            ).select_related('student')
            
            for enrollment in enrolled_students:
                AttendanceRecord.objects.create(
                    session=session,
                    student=enrollment.student,
                    status='absent',  # Default status
                    marked_by=request.user
                )
            
            messages.success(request, f'Attendance session created successfully!')
            
            if session.attendance_method == 'qr_code':
                return redirect('attendance:view_qr', session_id=session.id)
            else:
                return redirect('attendance:mark_attendance', session_id=session.id)
    else:
        form = AttendanceSessionForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'attendance/create_session.html', context)


@login_required
def mark_attendance(request, session_id):
    """Mark attendance for a session"""
    session = get_object_or_404(
        AttendanceSession.objects.select_related('class_session'),
        id=session_id
    )
    
    # Check permissions
    if request.user.user_type not in ['instructor', 'admin']:
        if request.user != session.instructor:
            messages.error(request, "You don't have permission to mark attendance for this session.")
            return redirect('attendance:dashboard')
    
    # Get enrolled students
    enrolled_students = session.class_session.enrollments.filter(
        is_active=True
    ).select_related('student', 'student__user')
    
    # Get existing attendance records
    attendance_records = {
        record.student_id: record
        for record in session.attendance_records.select_related('student', 'marked_by')
    }
    
    if request.method == 'POST':
        # Process attendance marking
        student_id = request.POST.get('student_id')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        is_excused = request.POST.get('is_excused') == 'on'
        
        if student_id:
            student = get_object_or_404(Student, id=student_id)
            
            # Update or create attendance record
            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                student=student,
                defaults={
                    'status': status,
                    'marked_by': request.user,
                    'remarks': remarks,
                    'is_excused': is_excused,
                    'check_in_time': timezone.now() if status in ['present', 'late'] else None
                }
            )
            
            if not created:
                record.status = status
                record.marked_by = request.user
                record.remarks = remarks
                record.is_excused = is_excused
                if status in ['present', 'late'] and not record.check_in_time:
                    record.check_in_time = timezone.now()
                record.save()
            
            messages.success(request, f'Attendance marked for {student.user.get_full_name()}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'student_name': student.user.get_full_name(),
                    'attendance_status': status,
                    'record_id': record.id
                })
    
    # Prepare student data for template
    students_data = []
    for enrollment in enrolled_students:
        student = enrollment.student
        record = attendance_records.get(student.id)
        
        students_data.append({
            'id': student.id,
            'admission_number': student.admission_number,
            'full_name': student.user.get_full_name(),
            'attendance_record': record,
            'profile_picture_url': student.profile_picture.url if student.profile_picture else None,
        })
    
    context = {
        'session': session,
        'students_data': students_data,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
        'total_students': len(students_data),
        'present_count': session.total_present,
        'absent_count': session.total_absent,
        'late_count': session.total_late,
    }
    
    return render(request, 'attendance/mark_attendance.html', context)

@login_required
def bulk_mark_attendance(request, session_id):
    """Bulk mark attendance for a session"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    if request.user != session.instructor and request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to mark attendance for this session.")
        return redirect('attendance:dashboard')
    
    if request.method == 'POST':
        attendance_data = json.loads(request.POST.get('attendance_data', '{}'))
        
        for student_id, status in attendance_data.items():
            try:
                student = Student.objects.get(id=student_id)
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'check_in_time': timezone.now() if status in ['present', 'late'] else None
                    }
                )
                
                if not created:
                    record.status = status
                    record.marked_by = request.user
                    if status in ['present', 'late'] and not record.check_in_time:
                        record.check_in_time = timezone.now()
                    record.save()
                    
            except Student.DoesNotExist:
                continue
        
        # Recalculate session statistics
        session.calculate_stats()
        
        messages.success(request, 'Attendance marked in bulk successfully!')
        return redirect('attendance:mark_attendance', session_id=session_id)
    
    return redirect('attendance:mark_attendance', session_id=session_id)

@login_required
def qr_attendance(request, session_id):
    """Handle QR code based attendance"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    if request.method == 'POST':
        form = QRAttendanceForm(request.POST)
        if form.is_valid():
            qr_code = form.cleaned_data['qr_code']
            student_id = form.cleaned_data.get('student_id')
            
            # Verify QR code
            if qr_code != session.qr_code_data:
                messages.error(request, 'Invalid QR code.')
                return redirect('attendance:qr_attendance', session_id=session_id)
            
            # Check QR code expiry
            if session.qr_code_expiry and timezone.now() > session.qr_code_expiry:
                messages.error(request, 'QR code has expired.')
                return redirect('attendance:qr_attendance', session_id=session_id)
            
            # If student_id is provided (manual entry), mark attendance
            if student_id:
                try:
                    student = Student.objects.get(id=student_id)
                    
                    # Check if student is enrolled in this class
                    if not session.class_session.enrollments.filter(student=student, is_active=True).exists():
                        messages.error(request, 'Student is not enrolled in this class.')
                        return redirect('attendance:qr_attendance', session_id=session_id)
                    
                    # Mark attendance
                    record, created = AttendanceRecord.objects.get_or_create(
                        session=session,
                        student=student,
                        defaults={
                            'status': 'present',
                            'marked_by': request.user,
                            'check_in_time': timezone.now()
                        }
                    )
                    
                    if not created:
                        record.status = 'present'
                        record.marked_by = request.user
                        record.check_in_time = timezone.now()
                        record.save()
                    
                    messages.success(request, f'Attendance marked for {student.user.get_full_name()}')
                    
                except Student.DoesNotExist:
                    messages.error(request, 'Student not found.')
            
            else:
                # Show student selection form
                enrolled_students = session.class_session.enrollments.filter(
                    is_active=True
                ).select_related('student', 'student__user')
                
                context = {
                    'session': session,
                    'qr_code': qr_code,
                    'enrolled_students': enrolled_students,
                    'form': QRAttendanceForm(initial={'qr_code': qr_code})
                }
                return render(request, 'attendance/qr_student_selection.html', context)
    
    else:
        form = QRAttendanceForm()
    
    context = {
        'session': session,
        'form': form,
        'qr_code_url': f'/attendance/qr/view/{session_id}/' if session.qr_code_data else None,
    }
    return render(request, 'attendance/qr_attendance.html', context)

@login_required
def view_qr_code(request, session_id):
    """Display QR code for attendance session"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    if request.user != session.instructor and request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to view this QR code.")
        return redirect('attendance:dashboard')
    
    context = {
        'session': session,
        'qr_code_data': session.qr_code_data,
        'expiry_time': session.qr_code_expiry,
    }
    return render(request, 'attendance/view_qr.html', context)

@login_required
def attendance_report(request):
    """Generate attendance reports"""
    form = AttendanceReportFilterForm(request.GET or None)
    attendance_data = []
    
    if form.is_valid():
        date_range = form.cleaned_data['date_range']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        class_session = form.cleaned_data['class_session']
        student = form.cleaned_data['student']
        status = form.cleaned_data['status']
        
        # Set date range based on selection
        today = timezone.now().date()
        
        if date_range == 'today':
            start_date = today
            end_date = today
        elif date_range == 'yesterday':
            start_date = today - timedelta(days=1)
            end_date = start_date
        elif date_range == 'this_week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_range == 'last_week':
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif date_range == 'this_month':
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif date_range == 'last_month':
            if today.month == 1:
                start_date = today.replace(year=today.year - 1, month=12, day=1)
            else:
                start_date = today.replace(month=today.month - 1, day=1)
            end_date = today.replace(day=1) - timedelta(days=1)
        
        # Filter attendance records
        filters = Q(session__session_date__range=[start_date, end_date])
        
        if class_session:
            filters &= Q(session__class_session=class_session)
        
        if student:
            filters &= Q(student=student)
        
        if status:
            filters &= Q(status=status)
        
        attendance_data = AttendanceRecord.objects.filter(
            filters
        ).select_related(
            'session', 'session__class_session', 'student', 'student__user'
        ).order_by('-session__session_date', '-check_in_time')
        
        # Calculate statistics
        total_records = attendance_data.count()
        present_count = attendance_data.filter(status='present').count()
        absent_count = attendance_data.filter(status='absent').count()
        late_count = attendance_data.filter(status='late').count()
        excused_count = attendance_data.filter(is_excused=True).count()
        
        attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
        
        context = {
            'form': form,
            'attendance_data': attendance_data,
            'start_date': start_date,
            'end_date': end_date,
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'attendance_rate': round(attendance_rate, 2),
        }
    else:
        # Default: show today's attendance
        today = timezone.now().date()
        attendance_data = AttendanceRecord.objects.filter(
            session__session_date=today
        ).select_related(
            'session', 'session__class_session', 'student', 'student__user'
        ).order_by('-session__session_date', '-check_in_time')
        
        context = {
            'form': form,
            'attendance_data': attendance_data,
            'start_date': today,
            'end_date': today,
            'total_records': attendance_data.count(),
        }
    
    return render(request, 'attendance/report.html', context)


@login_required
def student_attendance_history(request, student_id=None):
    """View attendance history for a student"""
    if student_id:
        student = get_object_or_404(Student, id=student_id)
    elif request.user.user_type == 'student':
        try:
            student = request.user.student
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
    else:
        messages.error(request, "Student not specified.")
        return redirect('students:list')
    
    # Get attendance records
    attendance_records = AttendanceRecord.objects.filter(
        student=student
    ).select_related(
        'session', 'session__class_session', 'session__instructor'
    ).order_by('-session__session_date', '-check_in_time')
    
    # Calculate statistics
    total_sessions = AttendanceSession.objects.filter(
        class_session=student.current_class
    ).count() if student.current_class else 0
    
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    late_count = attendance_records.filter(status='late').count()
    
    attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Pagination
    paginator = Paginator(attendance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'student': student,
        'page_obj': page_obj,
        'total_sessions': total_sessions,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_rate': round(attendance_rate, 2),
    }
    
    return render(request, 'attendance/student_history.html', context)


@login_required
def apply_excuse(request):
    """Apply for an excuse"""
    if request.user.user_type != 'student':
        messages.error(request, "Only students can apply for excuses.")
        return redirect('dashboard')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExcuseApplicationForm(request.POST, request.FILES, student=student)
        if form.is_valid():
            excuse = form.save(commit=False)
            excuse.student = student
            excuse.save()
            messages.success(request, 'Excuse application submitted successfully!')
            return redirect('attendance:excuse_list')
    else:
        form = ExcuseApplicationForm(student=student)
    
    context = {'form': form}
    return render(request, 'attendance/apply_excuse.html', context)

@login_required
def excuse_list(request):
    """List excuse applications"""
    if request.user.user_type == 'student':
        try:
            student = request.user.student
            excuses = ExcuseApplication.objects.filter(student=student).order_by('-applied_at')
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
    else:
        # Instructor/Admin view
        excuses = ExcuseApplication.objects.all().order_by('-applied_at')
    
    context = {'excuses': excuses}
    return render(request, 'attendance/excuse_list.html', context)

@login_required
def review_excuse(request, excuse_id):
    """Review an excuse application"""
    excuse = get_object_or_404(ExcuseApplication, id=excuse_id)
    
    # Check if user is instructor of this class or admin
    if request.user.user_type == 'instructor':
        # Check if this instructor teaches the class
        if excuse.class_session.instructor != request.user:
            messages.error(request, "You can only review excuses for your own classes.")
            return redirect('attendance:excuse_list')
    elif request.user.user_type == 'admin' or request.user.is_superuser:
        # Admin can review any excuse
        pass
    else:
        messages.error(request, "You don't have permission to review excuses.")
        return redirect('attendance:excuse_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        
        if action == 'approve':
            # Call the approve method
            excuse.status = 'approved'
            excuse.reviewed_by = request.user
            excuse.reviewed_at = timezone.now()
            excuse.review_notes = review_notes
            excuse.save()
            messages.success(request, 'Excuse application approved.')
            
        elif action == 'reject':
            # Call the reject method
            excuse.status = 'rejected'
            excuse.reviewed_by = request.user
            excuse.reviewed_at = timezone.now()
            excuse.review_notes = review_notes
            excuse.save()
            messages.success(request, 'Excuse application rejected.')
        
        return redirect('attendance:excuse_list')
    
    context = {'excuse': excuse}
    return render(request, 'attendance/review_excuse.html', context)


@require_POST
@login_required
def update_attendance_status(request, record_id):
    """Update attendance status via AJAX"""
    record = get_object_or_404(AttendanceRecord, id=record_id)
    
    # Check permissions
    if request.user != record.session.instructor and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    status = request.POST.get('status')
    remarks = request.POST.get('remarks', '')
    
    if status in dict(AttendanceRecord.STATUS_CHOICES).keys():
        record.status = status
        record.remarks = remarks
        record.marked_by = request.user
        
        if status in ['present', 'late'] and not record.check_in_time:
            record.check_in_time = timezone.now()
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'status': status,
            'status_display': record.get_status_display(),
            'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({'error': 'Invalid status'}, status=400)

@login_required
def export_attendance_report(request):
    """Export attendance report as CSV"""
    import csv
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    class_session_id = request.GET.get('class_session')
    
    # Filter records
    filters = Q()
    if start_date and end_date:
        filters &= Q(session__session_date__range=[start_date, end_date])
    if class_session_id:
        filters &= Q(session__class_session_id=class_session_id)
    
    attendance_records = AttendanceRecord.objects.filter(
        filters
    ).select_related(
        'session', 'session__class_session', 'student', 'student__user'
    ).order_by('session__session_date', 'student__admission_number')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Class', 'Admission No', 'Student Name', 'Status', 
                     'Check-in Time', 'Marked By', 'Remarks'])
    
    for record in attendance_records:
        writer.writerow([
            record.session.session_date,
            record.session.class_session.class_code,
            record.student.admission_number,
            record.student.user.get_full_name(),
            record.get_status_display(),
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else 'N/A',
            record.marked_by.get_full_name() if record.marked_by else 'System',
            record.remarks[:50]  # Limit remarks length
        ])
    
    return response