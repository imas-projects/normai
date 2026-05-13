# Migración inicial compactada — risks
#
# HISTORIAL DE MIGRACIONES:
# El módulo risks tenía originalmente 5 migraciones (0001 a 0005) que
# evolucionaban el modelo desde su estado inicial hasta el estado actual.
#
# Al inicio del proyecto se detectó un conflicto en las migraciones
# (documentado en docs/estado-proyecto.md, sección "Problemas detectados",
# punto 1) que impedía ejecutar migrate correctamente.
#
# Como solución documentada, se eliminaron todas las migraciones y se
# regeneró una única migración inicial que representa el estado final
# del modelo. Esta decisión está justificada porque:
#
# 1. El proyecto estaba en fase de desarrollo sin datos productivos.
# 2. El conflicto original era incompatible con una migración incremental.
# 3. Todos los desarrolladores partían de una base de datos limpia.
#
# COMPATIBILIDAD:
# Esta migración es compatible con instalaciones nuevas (base limpia).
# No es compatible con bases de datos que hubieran aplicado el historial
# original de 5 migraciones, ya que ese historial ya no existe.
# Para esos casos, la base de datos debe reinicializarse.
#
# Estado del modelo representado: equivalente al resultado acumulado
# de las migraciones originales 0001 a 0005.

import django.db.models.deletion
import multiselectfield.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('company', '0007_externalsupplier_country_and_more'),
        ('processes', '0010_processperformanceindicators_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContingencyPlanCommunicateTo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'tb_risks_contingency_plan_communicate_to',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ContingencyPlanResponsible',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'tb_risks_contingency_plan_responsible',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RiskIdentification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identified_risk', models.CharField(max_length=255, unique=True)),
                ('consequences', models.TextField()),
                ('source', models.CharField(blank=True, max_length=64, null=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risks', to='company.area')),
                ('process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risks', to='processes.process')),
            ],
            options={
                'db_table': 'tb_risks_identification',
            },
        ),
        migrations.CreateModel(
            name='RiskEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('severity', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])),
                ('current_preventive_controls', models.TextField(blank=True, null=True)),
                ('occurrence', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])),
                ('current_detection_controls', models.TextField(blank=True, null=True)),
                ('detection', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])),
                ('risk_level', models.CharField(choices=[('High', 'Alto'), ('Moderate', 'Moderado'), ('Low', 'Bajo')], max_length=10)),
                ('risk', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='risks.riskidentification')),
            ],
            options={
                'db_table': 'tb_risks_evaluation',
            },
        ),
        migrations.CreateModel(
            name='Reevaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('severity', models.PositiveIntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], default=0)),
                ('occurrence', models.PositiveIntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], default=0)),
                ('detection', models.PositiveIntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], default=0)),
                ('risk_level', models.CharField(choices=[('High', 'Alto'), ('Moderate', 'Moderado'), ('Low', 'Bajo')], max_length=10)),
                ('risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reevaluations', to='risks.riskidentification')),
            ],
            options={
                'db_table': 'tb_risks_reevaluation',
            },
        ),
        migrations.CreateModel(
            name='ContingencyPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contingency_actions', multiselectfield.db.fields.MultiSelectField(choices=[('N/A', 'N/A'), ('ALT_PROCEDURES', 'Establecer procedimientos alternativos'), ('ALT_SUPPLIERS', 'Identificar proveedores sustitutos'), ('BACKUP_STAFF', 'Asignar personal de respaldo'), ('EMERGENCY_STOCK', 'Mantener inventarios de emergencia'), ('TECH_REDUNDANCY', 'Implementar redundancias tecnológicas'), ('CRISIS_COMM', 'Establecer protocolos de comunicación de crisis'), ('DRILLS', 'Realizar simulacros y pruebas periódicas'), ('INSURANCE', 'Contratar seguros o coberturas específicas'), ('OUTSOURCE', 'Externalizar temporalmente operaciones críticas'), ('MANUALS', 'Crear manuales de operación ante fallos')], max_length=124)),
                ('communicate_to', models.ManyToManyField(related_name='communicate_to_contingency', through='risks.ContingencyPlanCommunicateTo', to='company.position')),
                ('responsible', models.ManyToManyField(related_name='responsible_for_contingency', through='risks.ContingencyPlanResponsible', to='company.position')),
                ('risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='risks.riskidentification')),
            ],
            options={
                'db_table': 'tb_risks_contingency_plan',
            },
        ),
        migrations.CreateModel(
            name='RiskTreatment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('treatment_action', models.TextField()),
                ('target_date', models.DateField()),
                ('actual_date', models.DateField()),
                ('responsible', models.ManyToManyField(to='company.position')),
                ('risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='treatments', to='risks.riskidentification')),
            ],
            options={
                'db_table': 'tb_risks_treatment',
            },
        ),
    ]