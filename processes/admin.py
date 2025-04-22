from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.ProcessInput)
admin.site.register(models.ProcessOutput)
admin.site.register(models.PerformanceIndicator)
admin.site.register(models.Process)
admin.site.register(models.ProcessActivity)
admin.site.register(models.ProcessPosition)
admin.site.register(models.ProcessMeasurement)
admin.site.register(models.ProductMeasurement)




