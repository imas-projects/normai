from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Area)
admin.site.register(models.Requirement)
admin.site.register(models.Position)
admin.site.register(models.Rol)
admin.site.register(models.ExternalClient)
admin.site.register(models.ExternalSupplier)
admin.site.register(models.Documentation)
admin.site.register(models.DocumentationType)
