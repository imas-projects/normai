from django.db import models


class Standard(models.Model):
    """
    Representa una norma de gestión de calidad (ISO 9001, AS9100, etc.)
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Norma",
        help_text="Ej: ISO 9001:2015 Sistemas de Gestión de Calidad"
    )
    version = models.CharField(
        max_length=50,
        verbose_name="Versión",
        help_text="Ej: 2015, Rev D"
    )
    sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Sector Industrial",
        help_text="Ej: General, Aeroespacial, Automotriz"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="¿Esta norma está actualmente en uso?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        db_table = 'tb_standards'
        verbose_name = 'Norma'
        verbose_name_plural = 'Normas'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.version})"


class Clause(models.Model):
    """
    Representa una cláusula dentro de una norma (estructura jerárquica)
    """
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='clauses',
        verbose_name="Norma"
    )
    code = models.CharField(
        max_length=20,
        verbose_name="Código de Cláusula",
        help_text="Ej: 4.1, 7.2.1"
    )
    title = models.CharField(
        max_length=500,
        verbose_name="Título"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subclauses',
        verbose_name="Cláusula Padre"
    )
    ordering = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de visualización dentro de la norma"
    )

    class Meta:
        db_table = 'tb_standard_clauses'
        verbose_name = 'Cláusula'
        verbose_name_plural = 'Cláusulas'
        ordering = ['standard', 'ordering', 'code']
        unique_together = [('standard', 'code')]

    def __str__(self):
        return f"{self.standard.name} - {self.code} {self.title}"

    def get_level(self):
        """Calcula el nivel de profundidad de la cláusula en la jerarquía"""
        level = 1
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level


class StandardRequirement(models.Model):
    """
    Representa un requisito específico dentro de una cláusula
    """
    CRITICALITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]

    clause = models.ForeignKey(
        Clause,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name="Cláusula"
    )
    text = models.TextField(
        verbose_name="Texto del Requisito"
    )
    mandatory = models.BooleanField(
        default=True,
        verbose_name="Obligatorio",
        help_text="¿Este requisito es obligatorio para la certificación?"
    )
    criticality_level = models.CharField(
        max_length=10,
        choices=CRITICALITY_CHOICES,
        default='medium',
        verbose_name="Nivel de Criticidad"
    )
    is_extension = models.BooleanField(
        default=False,
        verbose_name="Es Extensión",
        help_text="¿Este requisito es una extensión específica del sector?"
    )
    ordering = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden dentro de la cláusula"
    )

    class Meta:
        db_table = 'tb_standard_requirements'
        verbose_name = 'Requisito Normativo'
        verbose_name_plural = 'Requisitos Normativos'
        ordering = ['clause', 'ordering']

    def __str__(self):
        return f"{self.clause.code} - {self.text[:100]}..."

    def get_full_reference(self):
        """Retorna la referencia completa: Norma § Cláusula"""
        return f"{self.clause.standard.name} § {self.clause.code}"
