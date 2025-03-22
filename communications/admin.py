from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.CommunicationType)
admin.site.register(models.Channel)
admin.site.register(models.Periodicity)
admin.site.register(models.Message)
admin.site.register(models.CommunicationTable)


