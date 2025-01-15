from django.core.management import execute_from_command_line
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import ProductionLog as OldProductionLog
from prod.models import ProductionLog as NewProductionLog

def copy_data():
    for log in OldProductionLog.objects.all():
        NewProductionLog.objects.create(
            log_designation=log.log_designation,
            quantity=log.quantity,
            process=log.process,
            production_date=log.production_date,
            facility=log.facility,
            team=log.team,
            created_at=log.created_at
        )

if __name__ == '__main__':
    copy_data()
