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
    name = models.CharField(max_length=200, verbose_name="Area Name or Position Title")
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sub_areas",
        verbose_name="Parent Area"
    )
    users = models.ManyToManyField(User, related_name="areas", blank=True)

    def __str__(self):
        return f"{self.name}" if not self.parent else f"{self.name} (under {self.parent.name})"

    class Meta:
        db_table = 'tb_company_area'

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.as_dict() if self.parent else None,
            "users": [{
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email
            } for u in self.users.all()],
        }

class Requirement(models.Model):
    name = models.CharField(max_length=200, verbose_name="Requirement Name")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="sub_requirements"
    )

    def __str__(self):
        return f"{self.name}" if not self.parent else f"{self.name} (under {self.parent.name})"

    class Meta:
        db_table = 'tb_company_requirement'

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.as_dict() if self.parent else None,
        }

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
    
