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
    name = models.TextField()
    effective = models.BooleanField(default=False) #Si mide eficacia
    efficient = models.BooleanField(default=False) #Si mide eficiencia

    class Meta:
        db_table = 'tb_performance_indicator'

    def __str__(self):
        return self.name


# Tabla de Proceso 
class Process(models.Model):
    name = models.TextField()
    objective = models.TextField()
    creation_date = models.DateField()
    process_code = models.TextField()
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, related_name="process")
    review = models.TextField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)

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
        return f"{self.id}"

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

    class Meta:
        db_table = 'tb_process_measurement_product'

    def __str__(self):
        return self.measurement_product_parameter