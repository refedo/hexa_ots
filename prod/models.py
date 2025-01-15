from django.db import models

class ProductionLog(models.Model):
    log_designation = models.CharField(max_length=100)
    quantity = models.IntegerField()
    process = models.CharField(
        max_length=50,
        choices=[
            ('fit-up', 'Fit-up'),
            ('welding', 'Welding'),
            ('visualization', 'Visualization')
        ]
    )
    production_date = models.DateField()
    facility = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.log_designation} - {self.process} - {self.production_date}"

    class Meta:
        db_table = 'prod_productionlog'
