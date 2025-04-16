from django.db import models
from audits.models import Area
from django.contrib.auth.models import User

# Tabla de puestos
class JobPosition(models.Model):
    name = models.TextField()
    position_code = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='job_positions')

    class Meta:
        db_table = 'tb_job_position'

    def __str__(self):
        return self.name

# Tabla de proveedores externos
class ExternalSupplier(models.Model):
    name=models.TextField()

    class Meta:
        db_table = 'tb_external_supplier'

    def __str__(self):
        return self.name
    
# Tabla de clientes externos
class ExternalClient(models.Model):
    name=models.TextField()

    class Meta:
        db_table = 'tb_external_client'

    def __str__(self):
        return self.name

# Tabla de proveedores
class Supplier(models.Model):
    SUPPLIER_TYPE_CHOICES = [
    ('internal', 'Internal'),
    ('external', 'External'),
    ]

    name = models.TextField()
    type = models.TextField(choices=SUPPLIER_TYPE_CHOICES)
    external_supplier = models.ForeignKey(ExternalSupplier, on_delete=models.PROTECT, null=True, blank=True, related_name='suppliers')
    internal_supplier = models.ForeignKey(Area, on_delete=models.PROTECT, null=True, blank=True, related_name='suppliers')

    class Meta:
        db_table = 'tb_supplier'

    def __str__(self):
        return self.name

# Tabla de clientes
class Client(models.Model):
    CLIENT_TYPE_CHOICES = [
    ('internal', 'Internal'),
    ('external', 'External'),
    ]

    name = models.TextField()
    type = models.TextField(choices=CLIENT_TYPE_CHOICES)
    external_client = models.ForeignKey(ExternalClient, on_delete=models.PROTECT, null=True, blank=True, related_name='clients')
    internal_client = models.ForeignKey(Area, on_delete=models.PROTECT, null=True, blank=True, related_name='clients')

    class Meta:
        db_table = 'tb_client'

    def __str__(self):
        return self.name

# Entradas
class ProcessInput(models.Model):
    description = models.TextField()

    class Meta:
        db_table = 'tb_process_input'

    def __str__(self):
        return self.description

# Salidas
class ProcessOutput(models.Model):
    description = models.TextField()

    class Meta:
        db_table = 'tb_process_output'

    def __str__(self):
        return self.description

# Tabla de actividades
class Activity(models.Model):
    description = models.TextField()
    order = models.IntegerField()

    class Meta:
        db_table = 'tb_activity'

    def __str__(self):
        return f"{self.order}. {self.description}"

# Tabla de recursos
class Resource(models.Model):
    type = models.TextField()
    description = models.TextField()

    class Meta:
        db_table = 'tb_resource'

    def __str__(self):
        return self.description

# Tabla de documentacion
class Documentation(models.Model):
    DOCUMENTATION_TYPE_CHOICES = [
    ('procedure', 'Procedure'),
    ('instructions', 'Instructions'),
    ('method', 'Method'),
    ]

    type = models.TextField(choices=DOCUMENTATION_TYPE_CHOICES) #Procedimiento, instructivo, metodo
    description = models.TextField()
    documentation_code = models.TextField()

    class Meta:
        db_table = 'tb_documentation'

    def __str__(self):
        return self.description

# Tabla mediciones
class ProcessMeasurement(models.Model):
    MEASUREMENT_TYPE_CHOICES = [
    ('process', 'Process'),
    ('product', 'Product'),
    ]

    measurement_type = models.TextField() #Proceso o producto
    description = models.TextField()
    range = models.TextField(null=True, blank=True)
    equipment = models.TextField()

    class Meta:
        db_table = 'tb_measurement'

    def __str__(self):
        return self.description

# Tabla de desempeño 
class PerformanceIndicator(models.Model):
    name = models.TextField()
    effective = models.BooleanField(default=False) #Si mide eficacia
    efficient = models.BooleanField(default=False) #Si mide eficiencia

    class Meta:
        db_table = 'tb_performance_indicator'

    def __str__(self):
        return self.name

# Tabla intermedia relación puesto-proceso
class PositionRole(models.Model):
    position = models.ForeignKey(JobPosition, on_delete=models.CASCADE)
    role = models.TextField()

    class Meta:
        db_table = 'tb_position_role'

# Tabla de Proceso 
class Process(models.Model):
    name = models.TextField()
    objective = models.TextField()
    creation_date = models.DateField()
    process_code = models.TextField()
    review = models.TextField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)
    sheet = models.TextField()
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, related_name="processes")

    positions = models.ManyToManyField(PositionRole, related_name="processes")
    suppliers = models.ManyToManyField(Supplier, related_name="processes")
    inputs = models.ManyToManyField(ProcessInput, related_name="processes")
    outputs = models.ManyToManyField(ProcessOutput, related_name="processes")
    clients = models.ManyToManyField(Client, related_name="processes")
    activities = models.ManyToManyField(Activity, related_name="processes")
    resources = models.ManyToManyField(Resource, related_name="processes")
    documents = models.ManyToManyField(Documentation, related_name="processes")
    measurements = models.ManyToManyField(ProcessMeasurement, related_name="processes")
    indicators = models.ManyToManyField(PerformanceIndicator, related_name="processes")

    class Meta:
        db_table = 'tb_process'

    def __str__(self):
        return self.name
    

