from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Process)
admin.site.register(models.Activity)
admin.site.register(models.JobPosition)
admin.site.register(models.PositionRole)
admin.site.register(models.Supplier)
admin.site.register(models.ExternalSupplier)
admin.site.register(models.Client)
admin.site.register(models.ExternalClient)
admin.site.register(models.ProcessInput)
admin.site.register(models.ProcessOutput)
admin.site.register(models.Resource)
admin.site.register(models.Documentation)
admin.site.register(models.ProcessMeasurement)
admin.site.register(models.PerformanceIndicator)



