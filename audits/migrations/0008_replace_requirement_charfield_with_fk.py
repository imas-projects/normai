# Migración F1-04 — Refactorización de ProcessRequirement
#
# ESTRATEGIA DE MIGRACIÓN:
# Antes de aplicar esta migración, la tabla tb_audit_process_requirements
# contenía únicamente datos de prueba sin valor productivo, generados
# durante el desarrollo inicial del proyecto.
#
# Estos datos fueron eliminados manualmente antes de ejecutar esta migración
# mediante las siguientes operaciones desde el shell de Django:
#
#   from audits.models import Findings, AuditedEvaluationQuestion, ProcessRequirement
#   Findings.objects.all().update(requirement=None)
#   AuditedEvaluationQuestion.objects.all().update(requirement=None)
#   ProcessRequirement.objects.all().delete()
#
# Esta decisión está justificada y documentada en:
#   docs/processrequirement_refactor.md — sección 4 (Estrategia de Migración)
#
# IMPORTANTE: Esta migración solo es segura en una base de datos donde
# tb_audit_process_requirements esté vacía antes de aplicarla.
# Si existen datos productivos, hay que mapearlos manualmente a
# StandardRequirement antes de ejecutar esta migración.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0007_remove_auditreport_audit_auditreport_audit_plan'),
        ('standards', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='processrequirement',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='processrequirement',
            name='requirement',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='standards.standardrequirement',
                verbose_name='Standard Requirement'
            ),
        ),
    ]