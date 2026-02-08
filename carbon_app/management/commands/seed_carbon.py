from django.core.management.base import BaseCommand
from carbon_app.models import Employee, CompanyConfig, DailyLog
import random
from datetime import timedelta, date

class Command(BaseCommand):
    help = 'Seeds the database with initial carbon data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        # global config
        config, _ = CompanyConfig.objects.get_or_create(id=1)
        config.save()
        
        # Employees
        names = ['Aarav Patel', 'Diya Sharma', 'Rohan Gupta', 'Ananya Singh', 'Vikram Malhotra']
        employees = []
        for name in names:
            emp, created = Employee.objects.get_or_create(name=name)
            if created:
                emp.home_address = f"Locality {random.randint(1,20)}, Bengaluru"
                emp.home_commute_distance_km = round(random.uniform(5.0, 25.0), 1)
                emp.save()
            employees.append(emp)
        
        # Logs for last 7 days
        self.stdout.write(f'Created {len(employees)} employees.')
        
        DailyLog.objects.all().delete()
        
        for i in range(7):
            day = date.today() - timedelta(days=i)
            for emp in employees:
                # Randomize behavior
                is_home = random.choice([True, True, True, False])
                mode = random.choice(['METRO', 'EV', 'CAR', 'AUTO', 'BIKE', 'WFH'])
                
                log = DailyLog(
                    employee=emp,
                    hours_worked=random.choice([8, 8, 9, 7.5, 8.5]),
                    is_home_commute=is_home,
                    start_location="Client Site" if not is_home else None,
                    commute_mode=mode,
                    vcpu_hours=random.randint(0, 10),
                    storage_gb=random.randint(0, 50)
                )
                log.date = day
                log.save()
        
        self.stdout.write('Seeding Complete!')
