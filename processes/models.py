from django.db import models
from company.models import Area, Position, Documentation, ExternalSupplier, Rol, ExternalClient
from django.contrib.auth.models import User


# Entradas
class ProcessInput(models.Model):
    name = models.TextField()

    class Meta:
        db_table = 'tb_process_input_aux'

    def __str__(self):
        return self.name

# Salidas
class ProcessOutput(models.Model):
    name = models.TextField()

    class Meta:
        db_table = 'tb_process_output_aux'

    def __str__(self):
        return self.name

# Tabla de desempeño 
class PerformanceIndicator(models.Model):
    process = models.ForeignKey('Process', on_delete=models.CASCADE)
    performanceindicator = models.ForeignKey('PerformanceIndicator', on_delete=models.CASCADE)
    min_acceptable_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    max_acceptable_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    min_max = models.CharField(max_length=10, choices=[('min', 'Min'), ('max', 'Max'), ('range', 'Range')], null=True, blank=True)

    class Meta:
        db_table = 'tb_process_performance_indicators'
        unique_together = ('process', 'performanceindicator')

    def _str_(self):
        return f"{self.process} - {self.performanceindicator}"

# Tabla de Proceso 
class Process(models.Model):
    name = models.TextField()
    objective = models.TextField()
    creation_date = models.DateField()
    process_code = models.TextField()
    responsible = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="process")
    review = models.TextField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)
    summary = models.CharField(max_length=1000, verbose_name="Resumen", blank=True, null=True)

    staff_roles = models.TextField(blank=True, null=True)
    workspaces = models.TextField(blank=True, null=True)
    facilities = models.TextField(blank=True, null=True)
    equipment = models.TextField(blank=True, null=True)
    materials = models.TextField(blank=True, null=True)
    transport_resources = models.TextField(blank=True, null=True)
    communication_technologies = models.TextField(blank=True, null=True)
    operational_environment = models.TextField(blank=True, null=True)

    internal_suppliers = models.ManyToManyField(Area, related_name="process_internal_supplier", blank=True)
    external_suppliers = models.ManyToManyField(ExternalSupplier, related_name="process_external_supplier", blank=True)
    internal_clients = models.ManyToManyField(Area, related_name="process_internal_client", blank=True)
    external_clients = models.ManyToManyField(ExternalClient, related_name="process_external_client", blank=True)
    inputs = models.ManyToManyField(ProcessInput, related_name="process")
    outputs = models.ManyToManyField(ProcessOutput, related_name="process")
    documents = models.ManyToManyField(Documentation, related_name="process")
    performance_indicators = models.ManyToManyField(PerformanceIndicator, related_name="processes")

    class Meta:
        db_table = 'tb_process'

    def __str__(self):
        return self.name

# Tabla personalizadad relacion proceso y sus actividades    
class ProcessActivity(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    activity = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        db_table = 'tb_process_activities'

    def __str__(self):
        return f"{self.activity}"

class ProcessPosition(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    role = models.ForeignKey(Rol, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tb_process_positions'

    def __str__(self):
        return f"{self.id}"
    
# Tabla mediciones procesos
class ProcessMeasurement(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    measurement_process_parameter = models.TextField()
    measurement_process_range = models.TextField(blank=True, null=True)
    measurement_process_equipment = models.TextField(blank=True, null=True)
    equipment = models.CharField(max_length=50, null=True, blank=True) 

    class Meta:
        db_table = 'tb_process_measurement_process'

    def __str__(self):
        return self.measurement_process_parameter

    
# Tabla mediciones productos
class ProductMeasurement(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    measurement_product_parameter = models.TextField()
    measurement_product_range = models.TextField(blank=True, null=True)
    measurement_product_equipment = models.TextField(blank=True, null=True)
    equipment = models.CharField(max_length=50, blank=True, null=True) 

    class Meta:
        db_table = 'tb_process_measurement_product'

    def __str__(self):
        return self.measurement_product_parameter


from django.db import models

class ProcessPerformanceMeasurement(models.Model):
    process = models.ForeignKey(
        'Process',
        on_delete=models.CASCADE,
        verbose_name="Process"
    )
    performance_indicator = models.ForeignKey(
        'PerformanceIndicator',
        on_delete=models.CASCADE,
        verbose_name="Performance Indicator"
    )
    date = models.DateField(verbose_name="Date")
    measured_value = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Measured Value")
    target_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Target Value")
    unit = models.TextField(null=True, blank=True, verbose_name="Unit") 
    comment = models.TextField(null=True, blank=True, verbose_name="Comment")

    class Meta:
        db_table = 'tb_process_performance_measurements'

    def __str__(self):
        return f"{self.process} - {self.performance_indicator} ({self.date}): {self.measured_value}{self.unit or ''}"


class ProcessMeasurementRecord(models.Model):
    process = models.ForeignKey(
        'Process',
        on_delete=models.CASCADE,
        verbose_name="Process"
    )
    measurement_name = models.TextField(verbose_name="Measurement Name")
    date = models.DateField(verbose_name="Date")
    measured_value = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Measured Value")
    target_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Target Value")
    unit = models.TextField(null=True, blank=True, verbose_name="Unit")
    comment = models.TextField(null=True, blank=True, verbose_name="Comment")

    class Meta:
        db_table = 'tb_process_measurement_records'

    def __str__(self):
        return f"{self.measurement_name} - {self.process} ({self.date}): {self.measured_value}{self.unit or ''}"


class ProductMeasurementRecord(models.Model):
    process = models.ForeignKey(
        'Process',
        on_delete=models.CASCADE,
        verbose_name="Process"
    )
    measurement_name = models.TextField(verbose_name="Measurement Name")  
    product_reference = models.TextField(verbose_name="Product Reference")  
    date = models.DateField(verbose_name="Date")
    measured_value = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Measured Value")
    tolerance_min = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Tolerance Min")
    tolerance_max = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Tolerance Max")
    unit = models.TextField(verbose_name="Unit")
    result_ok = models.BooleanField(verbose_name="Result OK")
    comment = models.TextField(null=True, blank=True, verbose_name="Comment")

    class Meta:
        db_table = 'tb_product_measurement_records'

    def __str__(self):
        status = "OK" if self.result_ok else "Not OK"
        return f"{self.measurement_name} ({self.product_reference}) - {self.process} [{status}]"

