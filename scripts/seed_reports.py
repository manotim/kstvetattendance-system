#!/usr/bin/env python
"""
Script to seed reports data only
Run with: python manage.py shell < scripts/seed_reports.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from accounts.models import User
from reports.models import ReportTemplate, DashboardWidget, GeneratedReport

def seed_reports():
    print("Seeding reports data...")
    
    # Get admin user
    admin_user = User.objects.filter(user_type='admin').first()
    if not admin_user:
        print("❌ No admin user found. Please seed accounts first.")
        return
    
    # Create report templates
    templates = [
        {
            'name': 'Daily Attendance Summary',
            'report_type': 'attendance_summary',
            'description': 'Daily summary report of attendance across all classes',
            'parameters': {'group_by': 'day', 'include_charts': True},
        },
        {
            'name': 'Weekly Student Report',
            'report_type': 'student_attendance',
            'description': 'Weekly attendance report for individual students',
            'parameters': {'period': 'weekly', 'include_details': True},
        },
        {
            'name': 'Monthly Class Report',
            'report_type': 'class_attendance',
            'description': 'Monthly attendance performance by class',
            'parameters': {'period': 'monthly', 'include_comparison': True},
        },
    ]
    
    for template_data in templates:
        template, created = ReportTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={
                'report_type': template_data['report_type'],
                'description': template_data['description'],
                'parameters': template_data['parameters'],
                'created_by': admin_user,
            }
        )
        if created:
            print(f"✅ Created report template: {template.name}")
    
    # Create dashboard widgets
    widgets = [
        {
            'name': 'Today\'s Overview',
            'widget_type': 'attendance_chart',
            'chart_type': 'doughnut',
            'description': 'Today\'s attendance statistics',
            'configuration': {'refresh_interval': 30},
            'width': 6,
            'height': 300,
            'user_types': ['admin', 'instructor'],
        },
        {
            'name': 'Quick Stats',
            'widget_type': 'student_stats',
            'description': 'Student statistics overview',
            'configuration': {'show_counts': True},
            'width': 6,
            'height': 300,
            'user_types': ['admin', 'registrar', 'hod'],
        },
    ]
    
    for i, widget_data in enumerate(widgets):
        widget, created = DashboardWidget.objects.get_or_create(
            name=widget_data['name'],
            defaults={
                'widget_type': widget_data['widget_type'],
                'chart_type': widget_data.get('chart_type'),
                'description': widget_data['description'],
                'configuration': widget_data['configuration'],
                'width': widget_data['width'],
                'height': widget_data['height'],
                'display_order': i,
                'user_types': widget_data['user_types'],
            }
        )
        if created:
            print(f"✅ Created dashboard widget: {widget.name}")
    
    # Create sample generated reports
    for i in range(3):
        report_date = timezone.now().date() - timedelta(days=i*7)
        
        GeneratedReport.objects.create(
            report_name=f'Sample Report {i+1}',
            report_type='attendance_summary',
            description=f'Sample generated report {i+1}',
            parameters={'period': 'weekly'},
            start_date=report_date - timedelta(days=6),
            end_date=report_date,
            data={
                'total_sessions': 25,
                'total_present': 450,
                'total_absent': 25,
                'attendance_rate': 94.7,
            },
            summary={
                'attendance_rate': 94.7,
                'punctuality_rate': 89.2,
            },
            file_format='pdf',
            generated_by=admin_user,
            is_ready=True,
        )
        print(f"✅ Created sample report {i+1}")
    
    print(f"\n📊 Total report templates: {ReportTemplate.objects.count()}")
    print(f"📊 Total dashboard widgets: {DashboardWidget.objects.count()}")
    print(f"📊 Total generated reports: {GeneratedReport.objects.count()}")
    print("Reports seeding completed!")

if __name__ == '__main__':
    seed_reports()