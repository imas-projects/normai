from django.db import models
from django.contrib.auth.models import User

# Modelos generales aplicables a varias aplicaciones.

#Tipos de documentos
class DocumentationType(models.Model):
    type = models.TextField()

    class Meta:
        db_table = 'tb_company_documentation_type'

    def __str__(self):
        return self.type

#Documentacion de la companía
class Documentation(models.Model):
    document_type = models.ForeignKey(DocumentationType, on_delete=models.PROTECT, related_name="company_documentation") #Procedimiento, instructivo, metodo
    document_description = models.TextField()
    document_code = models.TextField()

    class Meta:
        db_table = 'tb_company_documentation'

    def __str__(self):
        return self.document_description
    
#Proveedores externos
class ExternalSupplier(models.Model):
    name=models.TextField()

    class Meta:
        db_table = 'tb_company_external_supplier'

    def __str__(self):
        return self.name
    
class ExternalClient(models.Model):
    name=models.TextField()

    class Meta:
        db_table = 'tb_company_external_client'

    def __str__(self):
        return self.name
    
#Areas
class Area(models.Model):
    name = models.CharField(max_length=100, verbose_name="Area Name")
    users = models.ManyToManyField(User, related_name="users")  # Un área puede tener varios usuarios y cada usuario estar en más de un area
    
    class Meta:
        db_table = 'tb_company_area'
    
    def __str__(self):
        return self.name
    
    def as_dict(self):
        return {"id": self.id, "name": self.name}

#Roles
class Rol(models.Model):
    name=models.TextField()

    class Meta:
        db_table = 'tb_company_rol'

    def __str__(self):
        return self.name

#Posiciones
class Position(models.Model):
    name=models.TextField()
    code=models.TextField()
    area=models.ForeignKey(Area, on_delete=models.PROTECT, related_name="areas")
    rol=models.ForeignKey(Rol, on_delete=models.PROTECT, related_name="roles", null=True)

    class Meta:
        db_table = 'tb_company_position'

    def __str__(self):
        return self.name
    
