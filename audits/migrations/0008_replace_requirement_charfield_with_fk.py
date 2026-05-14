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
# Esta migración incluye una comprobación activa que impide su ejecución
# si la tabla no está vacía, para evitar pérdida de datos silenciosa.
# Ver docs/processrequirement_refactor.md — sección 4.

import django.db.models.deletion
from django.db import migrations, models


def check_table_is_empty(apps, schema_editor):
    """
    Comprueba que ProcessRequirement está vacía antes de aplicar el cambio.
    Si hay registros, la migración falla con un mensaje claro que explica
    qué hay que hacer antes de poder continuar.
    """
    ProcessRequirement = apps.get_model('audits', 'ProcessRequirement')
    count = ProcessRequirement.objects.count()
    if count > 0:
        raise Exception(
            f"\n\n"
            f"ERROR: No se puede aplicar esta migración.\n"
            f"La tabla ProcessRequirement contiene {count} registro(s).\n\n"
            f"Esta migración cambia el campo 'requirement' de texto plano a\n"
            f"ForeignKey(StandardRequirement). Los registros existentes no pueden\n"
            f"migrarse automáticamente porque no existe equivalencia entre texto\n"
            f"libre y StandardRequirement estructurado.\n\n"
            f"Para continuar, elimina los registros existentes ejecutando:\n\n"
            f"  python manage.py shell\n"
            f"  >>> from audits.models import Findings, AuditedEvaluationQuestion, ProcessRequirement\n"
            f"  >>> Findings.objects.all().update(requirement=None)\n"
            f"  >>> AuditedEvaluationQuestion.objects.all().update(requirement=None)\n"
            f"  >>> ProcessRequirement.objects.all().delete()\n\n"
            f"Después vuelve a ejecutar migrate.\n"
        )


def reverse_check(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0007_remove_auditreport_audit_auditreport_audit_plan'),
        ('standards', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(check_table_is_empty, reverse_check),
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