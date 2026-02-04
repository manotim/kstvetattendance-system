# reports/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg, Sum, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from io import BytesIO

from .models import GeneratedReport, DashboardWidget
from .forms import (
    AttendanceReportForm, StudentAttendanceReportForm, 
    ClassAttendanceReportForm, ExportReportForm
)
from accounts.models import User
from students.models import Student, Enrollment
from courses.models import Course, Class
from attendance.models import AttendanceSession, AttendanceRecord

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    # Get user-specific widgets - FIXED for SQLite compatibility
    user_type = request.user.user_type
    
    # Get all active widgets and filter in Python (SQLite doesn't support JSON __contains)
    all_widgets = DashboardWidget.objects.filter(
        is_active=True
    ).order_by('display_order')
    
    # Filter widgets based on user_type
    widgets = []
    for widget in all_widgets:
        if isinstance(widget.user_types, list) and user_type in widget.user_types:
            widgets.append(widget)
        elif isinstance(widget.user_types, str):
            # Try to parse as JSON, or handle as comma-separated
            try:
                types_list = json.loads(widget.user_types)
                if isinstance(types_list, list) and user_type in types_list:
                    widgets.append(widget)
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, try comma-separated
                if user_type in [t.strip() for t in widget.user_types.split(',')]:
                    widgets.append(widget)
    
    # Get recent reports
    recent_reports = GeneratedReport.objects.filter(
        generated_by=request.user
    ).order_by('-generated_at')[:5]
    
    # Get quick stats
    today = timezone.now().date()
    
    # Calculate attendance stats for today
    today_attendance = AttendanceRecord.objects.filter(
        session__session_date=today
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late'))
    )
    
    # Student statistics
    student_stats = {
        'total': Student.objects.count(),
        'active': Student.objects.filter(status='active').count(),
        'male': Student.objects.filter(gender='M').count(),
        'female': Student.objects.filter(gender='F').count(),
    }
    
    # Class statistics
    class_stats = {
        'total': Class.objects.count(),
        'active': Class.objects.filter(is_active=True).count(),
        'instructors': User.objects.filter(user_type='instructor').count(),
    }
    
    context = {
        'widgets': widgets,
        'recent_reports': recent_reports,
        'today_attendance': today_attendance,
        'student_stats': student_stats,
        'class_stats': class_stats,
        'today': today,
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def attendance_report(request):
    """Generate attendance reports"""
    if request.method == 'GET':
        form = AttendanceReportForm(request.GET or None)
        
        if form.is_valid():
            date_range = form.cleaned_data['date_range']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            report_type = form.cleaned_data['report_type']
            group_by = form.cleaned_data['group_by']
            
            # Set date range
            start_date, end_date = _get_date_range(date_range, start_date, end_date)
            
            # Get attendance data
            attendance_data = AttendanceRecord.objects.filter(
                session__session_date__range=[start_date, end_date]
            ).select_related(
                'session', 'session__class_session', 'student', 'student__user'
            )
            
            # Group data based on selection
            if group_by == 'day':
                grouped_data = _group_by_day(attendance_data, start_date, end_date)
            elif group_by == 'week':
                grouped_data = _group_by_week(attendance_data, start_date, end_date)
            elif group_by == 'month':
                grouped_data = _group_by_month(attendance_data, start_date, end_date)
            elif group_by == 'class':
                grouped_data = _group_by_class(attendance_data)
            elif group_by == 'instructor':
                grouped_data = _group_by_instructor(attendance_data)
            elif group_by == 'student':
                grouped_data = _group_by_student(attendance_data)
            else:
                grouped_data = []
            
            # Calculate summary statistics
            summary = _calculate_attendance_summary(attendance_data)
            
            # Prepare chart data
            chart_data = _prepare_chart_data(grouped_data, group_by)
            
            context = {
                'form': form,
                'start_date': start_date,
                'end_date': end_date,
                'grouped_data': grouped_data,
                'summary': summary,
                'chart_data': json.dumps(chart_data) if chart_data else None,
                'report_type': report_type,
                'group_by': group_by,
            }
            
            return render(request, 'reports/attendance_report.html', context)
    
    else:
        form = AttendanceReportForm()
    
    context = {'form': form}
    return render(request, 'reports/attendance_report.html', context)

@login_required
def student_attendance_report(request):
    """Generate student-specific attendance reports"""
    if request.method == 'GET':
        form = StudentAttendanceReportForm(request.GET or None)
        
        if form.is_valid():
            date_range = form.cleaned_data['date_range']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            student = form.cleaned_data['student']
            class_session = form.cleaned_data['class_session']
            
            # Set date range
            start_date, end_date = _get_date_range(date_range, start_date, end_date)
            
            # Build query filters
            filters = Q(session__session_date__range=[start_date, end_date])
            
            if student:
                filters &= Q(student=student)
            
            if class_session:
                filters &= Q(session__class_session=class_session)
            
            # Get attendance data
            attendance_records = AttendanceRecord.objects.filter(
                filters
            ).select_related(
                'session', 'session__class_session', 'student', 'student__user'
            ).order_by('session__session_date')
            
            # Calculate statistics
            total_sessions = AttendanceSession.objects.filter(
                session_date__range=[start_date, end_date],
                class_session=class_session if class_session else None
            ).count()
            
            present_count = attendance_records.filter(status='present').count()
            absent_count = attendance_records.filter(status='absent').count()
            late_count = attendance_records.filter(status='late').count()
            
            attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0
            
            # Group by student if no specific student selected
            if not student:
                student_data = []
                students = Student.objects.filter(
                    enrollments__class_enrolled=class_session
                ) if class_session else Student.objects.all()
                
                for std in students:
                    student_attendance = attendance_records.filter(student=std)
                    student_present = student_attendance.filter(status='present').count()
                    student_rate = (student_present / total_sessions * 100) if total_sessions > 0 else 0
                    
                    student_data.append({
                        'student': std,
                        'present_count': student_present,
                        'absent_count': student_attendance.filter(status='absent').count(),
                        'late_count': student_attendance.filter(status='late').count(),
                        'attendance_rate': round(student_rate, 2),
                        'records': student_attendance,
                    })
                
                grouped_data = student_data
            else:
                grouped_data = [{
                    'student': student,
                    'records': attendance_records,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'attendance_rate': round(attendance_rate, 2),
                }]
            
            # Prepare chart data
            chart_data = _prepare_student_chart_data(attendance_records, start_date, end_date)
            
            context = {
                'form': form,
                'start_date': start_date,
                'end_date': end_date,
                'grouped_data': grouped_data,
                'chart_data': json.dumps(chart_data) if chart_data else None,
                'total_sessions': total_sessions,
                'summary': {
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'attendance_rate': round(attendance_rate, 2),
                },
            }
            
            return render(request, 'reports/student_attendance_report.html', context)
    
    else:
        form = StudentAttendanceReportForm()
    
    context = {'form': form}
    return render(request, 'reports/student_attendance_report.html', context)

@login_required
def class_attendance_report(request):
    """Generate class-specific attendance reports"""
    if request.method == 'GET':
        form = ClassAttendanceReportForm(request.GET or None)
        
        if form.is_valid():
            date_range = form.cleaned_data['date_range']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            class_session = form.cleaned_data['class_session']
            instructor = form.cleaned_data['instructor']
            
            # Set date range
            start_date, end_date = _get_date_range(date_range, start_date, end_date)
            
            # Build query filters for classes
            class_filters = Q()
            if class_session:
                class_filters &= Q(id=class_session.id)
            if instructor:
                class_filters &= Q(instructor=instructor)
            
            classes = Class.objects.filter(class_filters, is_active=True)
            
            class_data = []
            all_sessions = []
            
            for cls in classes:
                # Get attendance sessions for this class
                sessions = AttendanceSession.objects.filter(
                    class_session=cls,
                    session_date__range=[start_date, end_date]
                )
                
                # Get attendance records
                attendance_records = AttendanceRecord.objects.filter(
                    session__in=sessions
                )
                
                # Calculate statistics
                total_sessions = sessions.count()
                total_records = attendance_records.count()
                present_count = attendance_records.filter(status='present').count()
                absent_count = attendance_records.filter(status='absent').count()
                late_count = attendance_records.filter(status='late').count()
                
                attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
                
                # Get student list
                students = cls.enrollments.filter(is_active=True).select_related('student', 'student__user')
                
                class_data.append({
                    'class': cls,
                    'total_sessions': total_sessions,
                    'total_records': total_records,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'attendance_rate': round(attendance_rate, 2),
                    'students': students,
                    'sessions': sessions,
                })
                
                all_sessions.extend(list(sessions))
            
            # Prepare chart data
            chart_data = _prepare_class_chart_data(class_data)
            
            # Overall summary
            overall_summary = {
                'total_classes': len(class_data),
                'total_sessions': sum(cd['total_sessions'] for cd in class_data),
                'total_records': sum(cd['total_records'] for cd in class_data),
                'total_present': sum(cd['present_count'] for cd in class_data),
                'total_absent': sum(cd['absent_count'] for cd in class_data),
                'total_late': sum(cd['late_count'] for cd in class_data),
            }
            
            if overall_summary['total_records'] > 0:
                overall_summary['attendance_rate'] = round(
                    (overall_summary['total_present'] / overall_summary['total_records'] * 100), 2
                )
            else:
                overall_summary['attendance_rate'] = 0
            
            context = {
                'form': form,
                'start_date': start_date,
                'end_date': end_date,
                'class_data': class_data,
                'chart_data': json.dumps(chart_data) if chart_data else None,
                'overall_summary': overall_summary,
            }
            
            return render(request, 'reports/class_attendance_report.html', context)
    
    else:
        form = ClassAttendanceReportForm()
    
    context = {'form': form}
    return render(request, 'reports/class_attendance_report.html', context)

@login_required
def export_report(request, report_type):
    """Export report in various formats"""
    if report_type == 'attendance':
        form_class = AttendanceReportForm
        template = 'reports/export_attendance.html'
    elif report_type == 'student':
        form_class = StudentAttendanceReportForm
        template = 'reports/export_student.html'
    elif report_type == 'class':
        form_class = ClassAttendanceReportForm
        template = 'reports/export_class.html'
    else:
        messages.error(request, "Invalid report type.")
        return redirect('reports:dashboard')
    
    if request.method == 'POST':
        filter_form = form_class(request.POST)
        export_form = ExportReportForm(request.POST)
        
        if filter_form.is_valid() and export_form.is_valid():
            # Get parameters
            export_format = export_form.cleaned_data['export_format']
            include_charts = export_form.cleaned_data['include_charts']
            include_summary = export_form.cleaned_data['include_summary']
            
            # Generate report based on format
            if export_format == 'csv':
                return _export_csv(filter_form, report_type)
            elif export_format == 'excel':
                return _export_excel(filter_form, report_type)
            elif export_format == 'pdf':
                return _export_pdf(filter_form, report_type, request)
            else:
                # HTML export - just display
                messages.info(request, "HTML report displayed on screen.")
                return redirect(request.META.get('HTTP_REFERER', 'reports:dashboard'))
    
    else:
        filter_form = form_class(request.GET)
        export_form = ExportReportForm()
    
    context = {
        'filter_form': filter_form,
        'export_form': export_form,
        'report_type': report_type,
    }
    return render(request, template, context)

@login_required
def dashboard_widget_data(request, widget_id):
    """Get data for dashboard widgets (AJAX endpoint)"""
    widget = get_object_or_404(DashboardWidget, id=widget_id)
    
    # Check user type permission - FIXED for SQLite compatibility
    user_type = request.user.user_type
    has_permission = False
    
    if isinstance(widget.user_types, list) and user_type in widget.user_types:
        has_permission = True
    elif isinstance(widget.user_types, str):
        try:
            types_list = json.loads(widget.user_types)
            if isinstance(types_list, list) and user_type in types_list:
                has_permission = True
        except (json.JSONDecodeError, TypeError):
            if user_type in [t.strip() for t in widget.user_types.split(',')]:
                has_permission = True
    
    if not has_permission:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    data = {}
    
    if widget.widget_type == 'attendance_chart':
        data = _get_attendance_chart_data(widget)
    elif widget.widget_type == 'student_stats':
        data = _get_student_stats_data(widget)
    elif widget.widget_type == 'class_stats':
        data = _get_class_stats_data(widget)
    elif widget.widget_type == 'instructor_stats':
        data = _get_instructor_stats_data(widget)
    elif widget.widget_type == 'recent_activity':
        data = _get_recent_activity_data(widget)
    
    return JsonResponse(data)

@login_required
def generate_quick_report(request):
    """Generate quick reports on the fly"""
    report_type = request.GET.get('type', 'today')
    
    today = timezone.now().date()
    data = {}
    
    if report_type == 'today':
        # Today's attendance summary
        attendance = AttendanceRecord.objects.filter(
            session__session_date=today
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late'))
        )
        
        data = {
            'report_type': "Today's Attendance Summary",
            'date': today.strftime('%d/%m/%Y'),
            'total': attendance['total'],
            'present': attendance['present'],
            'absent': attendance['absent'],
            'late': attendance['late'],
            'attendance_rate': round((attendance['present'] / attendance['total'] * 100), 2) if attendance['total'] > 0 else 0,
        }
    
    elif report_type == 'student_count':
        # Student count by course
        courses = Course.objects.filter(is_active=True)
        course_data = []
        
        for course in courses:
            count = Student.objects.filter(course=course, status='active').count()
            course_data.append({
                'course': course.code,
                'count': count
            })
        
        data = {
            'report_type': "Student Count by Course",
            'date': today.strftime('%d/%m/%Y'),
            'total_students': Student.objects.filter(status='active').count(),
            'course_data': course_data,
        }
    
    elif report_type == 'class_attendance':
        # Class attendance for current week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        classes = Class.objects.filter(is_active=True)
        class_data = []
        
        for cls in classes:
            sessions = AttendanceSession.objects.filter(
                class_session=cls,
                session_date__range=[week_start, week_end]
            )
            records = AttendanceRecord.objects.filter(session__in=sessions)
            
            present = records.filter(status='present').count()
            total = records.count()
            
            class_data.append({
                'class': cls.class_code,
                'total_sessions': sessions.count(),
                'present': present,
                'total': total,
                'rate': round((present / total * 100), 2) if total > 0 else 0,
            })
        
        data = {
            'report_type': "Weekly Class Attendance",
            'period': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
            'class_data': class_data,
        }
    
    return JsonResponse(data)

@login_required
def save_report(request):
    """Save generated report for future reference"""
    if request.method == 'POST':
        report_name = request.POST.get('report_name')
        report_type = request.POST.get('report_type')
        parameters = json.loads(request.POST.get('parameters', '{}'))
        data = json.loads(request.POST.get('data', '{}'))
        
        report = GeneratedReport.objects.create(
            report_name=report_name,
            report_type=report_type,
            parameters=parameters,
            data=data,
            generated_by=request.user,
            is_ready=True,
        )
        
        messages.success(request, f"Report '{report_name}' saved successfully.")
        return JsonResponse({'success': True, 'report_id': report.id})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def view_saved_report(request, report_id):
    """View a saved report"""
    report = get_object_or_404(GeneratedReport, id=report_id)
    
    # Check permissions
    if report.generated_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this report.")
        return redirect('reports:dashboard')
    
    context = {
        'report': report,
        'data': json.dumps(report.data),
        'summary': json.dumps(report.summary),
    }
    return render(request, 'reports/view_saved.html', context)

# Helper functions
def _get_date_range(date_range, start_date, end_date):
    """Calculate date range based on selection"""
    today = timezone.now().date()
    
    if date_range == 'today':
        return today, today
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif date_range == 'this_week':
        week_start = today - timedelta(days=today.weekday())
        return week_start, today
    elif date_range == 'last_week':
        last_week = today - timedelta(days=today.weekday() + 7)
        last_week_end = last_week + timedelta(days=6)
        return last_week, last_week_end
    elif date_range == 'this_month':
        month_start = today.replace(day=1)
        return month_start, today
    elif date_range == 'last_month':
        if today.month == 1:
            last_month = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month - 1, day=1)
        if last_month.month == 12:
            last_month_end = last_month.replace(year=last_month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_month_end = last_month.replace(month=last_month.month + 1, day=1) - timedelta(days=1)
        return last_month, last_month_end
    elif date_range == 'custom' and start_date and end_date:
        return start_date, end_date
    else:
        # Default: last 30 days
        return today - timedelta(days=30), today

def _group_by_day(attendance_data, start_date, end_date):
    """Group attendance data by day"""
    grouped = {}
    current_date = start_date
    
    while current_date <= end_date:
        grouped[current_date] = {
            'date': current_date,
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'total': 0,
        }
        current_date += timedelta(days=1)
    
    for record in attendance_data:
        date = record.session.session_date
        if date in grouped:
            grouped[date]['total'] += 1
            if record.status == 'present':
                grouped[date]['present'] += 1
            elif record.status == 'absent':
                grouped[date]['absent'] += 1
            elif record.status == 'late':
                grouped[date]['late'] += 1
            elif record.status == 'excused':
                grouped[date]['excused'] += 1
    
    return list(grouped.values())

def _group_by_week(attendance_data, start_date, end_date):
    """Group attendance data by week"""
    from django.utils.dateformat import DateFormat
    
    grouped = {}
    current_date = start_date
    
    # Initialize weeks
    while current_date <= end_date:
        week_num = current_date.isocalendar()[1]
        year = current_date.year
        week_key = f"{year}-W{week_num:02d}"
        
        if week_key not in grouped:
            # Get week start and end dates
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            grouped[week_key] = {
                'week_key': week_key,
                'week_start': week_start,
                'week_end': week_end,
                'week_label': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
                'total': 0,
            }
        current_date += timedelta(days=7)
    
    for record in attendance_data:
        date = record.session.session_date
        week_num = date.isocalendar()[1]
        year = date.year
        week_key = f"{year}-W{week_num:02d}"
        
        if week_key in grouped:
            grouped[week_key]['total'] += 1
            if record.status == 'present':
                grouped[week_key]['present'] += 1
            elif record.status == 'absent':
                grouped[week_key]['absent'] += 1
            elif record.status == 'late':
                grouped[week_key]['late'] += 1
            elif record.status == 'excused':
                grouped[week_key]['excused'] += 1
    
    return list(grouped.values())

def _group_by_month(attendance_data, start_date, end_date):
    """Group attendance data by month"""
    grouped = {}
    current_date = start_date.replace(day=1)
    
    # Initialize months
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        grouped[month_key] = {
            'month_key': month_key,
            'month': current_date.strftime('%B %Y'),
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'total': 0,
        }
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    for record in attendance_data:
        date = record.session.session_date
        month_key = date.strftime('%Y-%m')
        
        if month_key in grouped:
            grouped[month_key]['total'] += 1
            if record.status == 'present':
                grouped[month_key]['present'] += 1
            elif record.status == 'absent':
                grouped[month_key]['absent'] += 1
            elif record.status == 'late':
                grouped[month_key]['late'] += 1
            elif record.status == 'excused':
                grouped[month_key]['excused'] += 1
    
    return list(grouped.values())

def _group_by_class(attendance_data):
    """Group attendance data by class"""
    classes = {}
    
    for record in attendance_data:
        class_session = record.session.class_session
        if class_session:
            class_id = class_session.id
            class_name = class_session.class_code
            
            if class_id not in classes:
                classes[class_id] = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'instructor': class_session.instructor.get_full_name() if class_session.instructor else 'N/A',
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0,
                    'total': 0,
                }
            
            classes[class_id]['total'] += 1
            if record.status == 'present':
                classes[class_id]['present'] += 1
            elif record.status == 'absent':
                classes[class_id]['absent'] += 1
            elif record.status == 'late':
                classes[class_id]['late'] += 1
            elif record.status == 'excused':
                classes[class_id]['excused'] += 1
    
    return list(classes.values())

def _group_by_instructor(attendance_data):
    """Group attendance data by instructor"""
    instructors = {}
    
    for record in attendance_data:
        class_session = record.session.class_session
        if class_session and class_session.instructor:
            instructor_id = class_session.instructor.id
            instructor_name = class_session.instructor.get_full_name()
            
            if instructor_id not in instructors:
                instructors[instructor_id] = {
                    'instructor_id': instructor_id,
                    'instructor_name': instructor_name,
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0,
                    'total': 0,
                }
            
            instructors[instructor_id]['total'] += 1
            if record.status == 'present':
                instructors[instructor_id]['present'] += 1
            elif record.status == 'absent':
                instructors[instructor_id]['absent'] += 1
            elif record.status == 'late':
                instructors[instructor_id]['late'] += 1
            elif record.status == 'excused':
                instructors[instructor_id]['excused'] += 1
    
    return list(instructors.values())

def _group_by_student(attendance_data):
    """Group attendance data by student"""
    students = {}
    
    for record in attendance_data:
        student = record.student
        if student:
            student_id = student.id
            student_name = student.user.get_full_name()
            
            if student_id not in students:
                students[student_id] = {
                    'student_id': student_id,
                    'student_name': student_name,
                    'student_number': student.student_number,
                    'course': student.course.code if student.course else 'N/A',
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0,
                    'total': 0,
                }
            
            students[student_id]['total'] += 1
            if record.status == 'present':
                students[student_id]['present'] += 1
            elif record.status == 'absent':
                students[student_id]['absent'] += 1
            elif record.status == 'late':
                students[student_id]['late'] += 1
            elif record.status == 'excused':
                students[student_id]['excused'] += 1
    
    return list(students.values())

def _calculate_attendance_summary(attendance_data):
    """Calculate summary statistics for attendance data"""
    total = attendance_data.count()
    present = attendance_data.filter(status='present').count()
    absent = attendance_data.filter(status='absent').count()
    late = attendance_data.filter(status='late').count()
    excused = attendance_data.filter(status='excused').count()
    
    attendance_rate = (present / total * 100) if total > 0 else 0
    punctuality_rate = ((present - late) / present * 100) if present > 0 else 0
    
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'attendance_rate': round(attendance_rate, 2),
        'punctuality_rate': round(punctuality_rate, 2),
    }

def _prepare_chart_data(grouped_data, group_by):
    """Prepare chart data for visualization"""
    if not grouped_data:
        return None
    
    if group_by in ['day', 'week', 'month']:
        # Time-based chart
        if group_by == 'day':
            labels = [item['date'].strftime('%d/%m') for item in grouped_data]
        elif group_by == 'week':
            labels = [item['week_label'] for item in grouped_data]
        elif group_by == 'month':
            labels = [item['month'] for item in grouped_data]
        
        present_data = [item['present'] for item in grouped_data]
        absent_data = [item['absent'] for item in grouped_data]
        
        return {
            'type': 'line',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Present',
                    'data': present_data,
                    'borderColor': '#28a745',
                    'backgroundColor': 'rgba(40, 167, 69, 0.1)',
                },
                {
                    'label': 'Absent',
                    'data': absent_data,
                    'borderColor': '#dc3545',
                    'backgroundColor': 'rgba(220, 53, 69, 0.1)',
                }
            ]
        }
    
    elif group_by in ['class', 'instructor', 'student']:
        # Bar chart for categories
        if group_by == 'class':
            labels = [item['class_name'] for item in grouped_data]
        elif group_by == 'instructor':
            labels = [item['instructor_name'] for item in grouped_data]
        elif group_by == 'student':
            labels = [item['student_name'] for item in grouped_data]
        
        attendance_rates = []
        
        for item in grouped_data:
            total = item.get('total', 0)
            present = item.get('present', 0)
            rate = (present / total * 100) if total > 0 else 0
            attendance_rates.append(round(rate, 2))
        
        return {
            'type': 'bar',
            'labels': labels,
            'datasets': [{
                'label': 'Attendance Rate %',
                'data': attendance_rates,
                'backgroundColor': '#007bff',
                'borderColor': '#0056b3',
            }]
        }
    
    return None

def _prepare_student_chart_data(attendance_records, start_date, end_date):
    """Prepare chart data for student attendance"""
    if not attendance_records:
        return None
    
    # Group by date
    daily_data = {}
    current_date = start_date
    
    while current_date <= end_date:
        daily_data[current_date] = {
            'present': 0,
            'absent': 0,
            'late': 0,
        }
        current_date += timedelta(days=1)
    
    for record in attendance_records:
        date = record.session.session_date
        if date in daily_data:
            if record.status == 'present':
                daily_data[date]['present'] += 1
            elif record.status == 'absent':
                daily_data[date]['absent'] += 1
            elif record.status == 'late':
                daily_data[date]['late'] += 1
    
    # Convert to lists
    labels = [date.strftime('%d/%m') for date in sorted(daily_data.keys())]
    present_data = [daily_data[date]['present'] for date in sorted(daily_data.keys())]
    absent_data = [daily_data[date]['absent'] for date in sorted(daily_data.keys())]
    
    return {
        'type': 'line',
        'labels': labels,
        'datasets': [
            {
                'label': 'Present',
                'data': present_data,
                'borderColor': '#28a745',
                'backgroundColor': 'rgba(40, 167, 69, 0.1)',
            },
            {
                'label': 'Absent',
                'data': absent_data,
                'borderColor': '#dc3545',
                'backgroundColor': 'rgba(220, 53, 69, 0.1)',
            }
        ]
    }

def _prepare_class_chart_data(class_data):
    """Prepare chart data for class attendance"""
    if not class_data:
        return None
    
    labels = [item['class'].class_code for item in class_data]
    attendance_rates = [item['attendance_rate'] for item in class_data]
    
    return {
        'type': 'bar',
        'labels': labels,
        'datasets': [{
            'label': 'Attendance Rate %',
            'data': attendance_rates,
            'backgroundColor': '#17a2b8',
            'borderColor': '#138496',
        }]
    }

# Widget data functions
def _get_attendance_chart_data(widget):
    """Get data for attendance chart widget"""
    today = timezone.now().date()
    days = widget.config.get('days', 7)
    
    start_date = today - timedelta(days=days-1)
    
    attendance_data = AttendanceRecord.objects.filter(
        session__session_date__range=[start_date, today]
    )
    
    # Group by day
    daily_stats = {}
    current_date = start_date
    
    while current_date <= today:
        daily_stats[current_date] = {
            'present': 0,
            'total': 0,
        }
        current_date += timedelta(days=1)
    
    for record in attendance_data:
        date = record.session.session_date
        if date in daily_stats:
            daily_stats[date]['total'] += 1
            if record.status == 'present':
                daily_stats[date]['present'] += 1
    
    # Prepare chart data
    labels = [date.strftime('%d/%m') for date in sorted(daily_stats.keys())]
    rates = []
    
    for date in sorted(daily_stats.keys()):
        total = daily_stats[date]['total']
        present = daily_stats[date]['present']
        rate = (present / total * 100) if total > 0 else 0
        rates.append(round(rate, 1))
    
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Attendance Rate %',
            'data': rates,
            'borderColor': '#28a745',
            'backgroundColor': 'rgba(40, 167, 69, 0.1)',
        }]
    }

def _get_student_stats_data(widget):
    """Get data for student stats widget"""
    total = Student.objects.count()
    active = Student.objects.filter(status='active').count()
    male = Student.objects.filter(gender='M').count()
    female = Student.objects.filter(gender='F').count()
    
    return {
        'total': total,
        'active': active,
        'male': male,
        'female': female,
        'inactive': total - active,
    }

def _get_class_stats_data(widget):
    """Get data for class stats widget"""
    total = Class.objects.count()
    active = Class.objects.filter(is_active=True).count()
    
    # Get attendance for today
    today = timezone.now().date()
    today_attendance = AttendanceRecord.objects.filter(
        session__session_date=today
    ).aggregate(
        present=Count('id', filter=Q(status='present')),
        total=Count('id')
    )
    
    attendance_rate = (today_attendance['present'] / today_attendance['total'] * 100) if today_attendance['total'] > 0 else 0
    
    return {
        'total': total,
        'active': active,
        'inactive': total - active,
        'today_attendance': round(attendance_rate, 1),
    }

def _get_instructor_stats_data(widget):
    """Get data for instructor stats widget"""
    total = User.objects.filter(user_type='instructor').count()
    active = User.objects.filter(user_type='instructor', is_active=True).count()
    
    # Get classes per instructor
    instructors = User.objects.filter(user_type='instructor')[:10]
    instructor_data = []
    
    for instructor in instructors:
        class_count = Class.objects.filter(instructor=instructor, is_active=True).count()
        instructor_data.append({
            'name': instructor.get_full_name(),
            'classes': class_count,
        })
    
    return {
        'total': total,
        'active': active,
        'inactive': total - active,
        'top_instructors': instructor_data[:5],
    }

def _get_recent_activity_data(widget):
    """Get data for recent activity widget"""
    # Get recent attendance sessions
    recent_sessions = AttendanceSession.objects.filter(
        session_date__gte=timezone.now().date() - timedelta(days=7)
    ).order_by('-session_date', '-start_time')[:10]
    
    activities = []
    for session in recent_sessions:
        present_count = AttendanceRecord.objects.filter(
            session=session, status='present'
        ).count()
        total_count = AttendanceRecord.objects.filter(session=session).count()
        
        activities.append({
            'class': session.class_session.class_code if session.class_session else 'N/A',
            'date': session.session_date.strftime('%d/%m'),
            'time': session.start_time.strftime('%H:%M') if session.start_time else '',
            'attendance': f"{present_count}/{total_count}",
            'rate': round((present_count / total_count * 100), 1) if total_count > 0 else 0,
        })
    
    return {
        'activities': activities,
        'count': len(activities),
    }

# Export functions
def _export_csv(filter_form, report_type):
    """Export report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    
    # Write header based on report type
    if report_type == 'attendance':
        writer.writerow(['Date', 'Class', 'Student', 'Status', 'Check-in Time', 'Remarks'])
        
        # Get filtered data (simplified for example)
        date_range = filter_form.cleaned_data['date_range']
        start_date, end_date = _get_date_range(
            date_range,
            filter_form.cleaned_data['start_date'],
            filter_form.cleaned_data['end_date']
        )
        
        records = AttendanceRecord.objects.filter(
            session__session_date__range=[start_date, end_date]
        ).select_related('session', 'session__class_session', 'student', 'student__user')
        
        for record in records:
            writer.writerow([
                record.session.session_date,
                record.session.class_session.class_code if record.session.class_session else 'N/A',
                record.student.user.get_full_name() if record.student and record.student.user else 'N/A',
                record.get_status_display(),
                record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else 'N/A',
                record.remarks[:50] if record.remarks else ''
            ])
    
    elif report_type == 'student':
        # Add CSV export for student reports
        date_range = filter_form.cleaned_data['date_range']
        start_date, end_date = _get_date_range(
            date_range,
            filter_form.cleaned_data['start_date'],
            filter_form.cleaned_data['end_date']
        )
        
        writer.writerow(['Student ID', 'Name', 'Course', 'Present', 'Absent', 'Late', 'Attendance Rate %'])
        
        # Simplified student data
        student = filter_form.cleaned_data.get('student')
        if student:
            records = AttendanceRecord.objects.filter(
                session__session_date__range=[start_date, end_date],
                student=student
            )
            present = records.filter(status='present').count()
            absent = records.filter(status='absent').count()
            late = records.filter(status='late').count()
            total = present + absent + late
            rate = (present / total * 100) if total > 0 else 0
            
            writer.writerow([
                student.student_number,
                student.user.get_full_name(),
                student.course.code if student.course else 'N/A',
                present,
                absent,
                late,
                round(rate, 2)
            ])
    
    elif report_type == 'class':
        # Add CSV export for class reports
        date_range = filter_form.cleaned_data['date_range']
        start_date, end_date = _get_date_range(
            date_range,
            filter_form.cleaned_data['start_date'],
            filter_form.cleaned_data['end_date']
        )
        
        writer.writerow(['Class Code', 'Instructor', 'Sessions', 'Present', 'Absent', 'Late', 'Attendance Rate %'])
        
        class_session = filter_form.cleaned_data.get('class_session')
        if class_session:
            sessions = AttendanceSession.objects.filter(
                class_session=class_session,
                session_date__range=[start_date, end_date]
            )
            records = AttendanceRecord.objects.filter(session__in=sessions)
            present = records.filter(status='present').count()
            absent = records.filter(status='absent').count()
            late = records.filter(status='late').count()
            total = present + absent + late
            rate = (present / total * 100) if total > 0 else 0
            
            writer.writerow([
                class_session.class_code,
                class_session.instructor.get_full_name() if class_session.instructor else 'N/A',
                sessions.count(),
                present,
                absent,
                late,
                round(rate, 2)
            ])
    
    return response

def _export_excel(filter_form, report_type):
    """Export report as Excel (simplified - returns CSV for now)"""
    # For now, return CSV since we don't have Excel library installed
    # In production, you would use openpyxl or xlsxwriter
    return _export_csv(filter_form, report_type)

def _export_pdf(filter_form, report_type, request):
    """Export report as PDF"""
    # This would require reportlab or similar library
    # For now, return a message
    messages.info(request, "PDF export feature will be implemented with reportlab library.")
    return redirect(request.META.get('HTTP_REFERER', 'reports:dashboard'))