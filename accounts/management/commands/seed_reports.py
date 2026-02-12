from django.core.management.base import BaseCommand
from accounts.models import User
from reports.models import ReportTemplate, DashboardWidget

class Command(BaseCommand):
    help = 'Seed reports data'

    def handle(self, *args, **kwargs):
        # Get admin user
        admin_user = User.objects.filter(username='admin').first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('Admin user not found. Run seed_accounts first.'))
            return
        
        # Create report template
        template, created = ReportTemplate.objects.get_or_create(
            name='Daily Attendance Summary',
            defaults={
                'report_type': 'attendance_summary',
                'description': 'Daily summary of attendance across all classes',
                'parameters': {'group_by': 'day', 'include_charts': True},
                'created_by': admin_user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created report template: {template.name}'))
        
        # Create dashboard widget
        widget, created = DashboardWidget.objects.get_or_create(
            name='Today\'s Overview',
            defaults={
                'widget_type': 'attendance_chart',
                'chart_type': 'doughnut',
                'description': 'Today\'s attendance statistics',
                'configuration': {'refresh_interval': 30},
                'width': 6,
                'height': 300,
                'user_types': ['admin', 'instructor'],
                'display_order': 0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created dashboard widget: {widget.name}'))
        
        self.stdout.write(self.style.SUCCESS('Reports seeded successfully!'))