from django.db import models

# Create your models here.

class Project(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    estimation_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project_number = models.CharField(max_length=20, unique=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    project_manager = models.CharField(max_length=100, null=True, blank=True)
    client_name = models.CharField(max_length=200)
    contract_date = models.DateField(null=True, blank=True)
    down_payment_date = models.DateField(null=True, blank=True)
    structure_type = models.CharField(max_length=50)
    erection_subcontractor = models.CharField(max_length=100)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2)
    down_payment_ack = models.BooleanField(default=False)
    payment_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_2_ack = models.BooleanField(default=False)
    payment_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_3_ack = models.BooleanField(default=False)
    payment_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_4_ack = models.BooleanField(default=False)
    payment_5 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_5_ack = models.BooleanField(default=False)
    preliminary_retention = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ho_retention = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    incoterm = models.CharField(max_length=20)
    scope_of_work = models.TextField()
    project_nature = models.CharField(max_length=20)
    contractual_tonnage = models.DecimalField(max_digits=10, decimal_places=2)
    engineering_tonnage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    galvanized = models.BooleanField(default=False)
    galvanization_microns = models.IntegerField(null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    m2_per_ton = models.DecimalField(max_digits=10, decimal_places=2)
    paint_coat_1 = models.CharField(max_length=100, null=True, blank=True)
    coat_1_microns = models.IntegerField(null=True, blank=True)
    coat_1_liters_needed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paint_coat_2 = models.CharField(max_length=100, null=True, blank=True)
    coat_2_microns = models.IntegerField(null=True, blank=True)
    coat_2_liters_needed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paint_coat_3 = models.CharField(max_length=100, null=True, blank=True)
    coat_3_microns = models.IntegerField(null=True, blank=True)
    coat_3_liters_needed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paint_coat_4 = models.CharField(max_length=100, null=True, blank=True)
    coat_4_microns = models.IntegerField(null=True, blank=True)
    coat_4_liters_needed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    top_coat_ral_number = models.CharField(max_length=20, null=True, blank=True)
    welding_process = models.CharField(max_length=20)
    welding_wire_aws_class = models.CharField(max_length=50)
    pqr_no = models.CharField(max_length=50)
    wps_no = models.CharField(max_length=50)
    standard_code = models.CharField(max_length=50)
    erectable = models.BooleanField(null=True, blank=True)
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    down_payment_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    number_of_structures = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'hexa_projects'

    def __str__(self):
        return f"{self.project_number} - {self.project_name or 'Unnamed Project'}"


class Building(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='buildings')
    building_name = models.CharField(max_length=255)
    designer_name = models.CharField(max_length=100)
    subcontractor_name = models.CharField(max_length=100)
    
    # Design dates
    design_start_date = models.DateField(null=True, blank=True)
    design_end_date = models.DateField(null=True, blank=True)
    
    # Shop drawing dates
    shop_drawing_start_date = models.DateField(null=True, blank=True)
    shop_drawing_end_date = models.DateField(null=True, blank=True)
    
    # Production dates
    production_start_date = models.DateField(null=True, blank=True)
    production_end_date = models.DateField(null=True, blank=True)
    
    # Erection dates and status
    erection_applicable = models.BooleanField(default=True)
    erection_start_date = models.DateField(null=True, blank=True)
    erection_end_date = models.DateField(null=True, blank=True)
    
    # Planning dates
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    
    # Actual dates
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # QC date
    qc_inspection_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hexa_buildings'
        ordering = ['building_name']

    def __str__(self):
        return f"{self.building_name} - {self.project.project_number}"


class RawData(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='raw_data')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='raw_data')
    log_designation = models.CharField(max_length=100, default='PENDING', help_text="Unique identifier for production, QC, logistics, and erection activities")
    part_designation = models.CharField(max_length=100, null=True, blank=True)
    assembly_mark = models.CharField(max_length=100, null=True, blank=True)
    sub_assembly_mark = models.CharField(max_length=100, null=True, blank=True)
    part_mark = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    profile = models.CharField(max_length=100, null=True, blank=True)
    grade = models.CharField(max_length=255, null=True, blank=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_area_single = models.CharField(max_length=255, null=True, blank=True)
    net_area_all = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    single_part_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_weight_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    revision = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'HEXA_rawdata'
        indexes = [
            models.Index(fields=['log_designation']),
            models.Index(fields=['project', 'building', 'log_designation']),
        ]

    def __str__(self):
        return f"{self.log_designation} - {self.project.project_number} - {self.building.building_name}"


class ProductionLog(models.Model):
    log_designation = models.CharField(max_length=100)
    quantity = models.IntegerField()
    process = models.CharField(max_length=50, choices=[('fit-up', 'Fit-up'), ('welding', 'Welding'), ('visualization', 'Visualization')])
    production_date = models.DateField()
    facility = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.log_designation} - {self.process}'


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.CharField(max_length=100, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hexa_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
