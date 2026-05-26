"""
Preparación del dataset histórico para analítica predictiva — F4-01

Este módulo extrae, estructura y normaliza los datos históricos disponibles
en NormAI para construir un dataset reutilizable por los módulos de
predicción de riesgo (F4-02) y detección de anomalías (F4-03).

Fuentes de datos:
- ComplianceSnapshot: historial de cumplimiento por proceso y norma
- Findings: hallazgos de auditoría clasificados
- RiskIdentification + RiskEvaluation: riesgos identificados y evaluados
- ProcessRequirement: cobertura normativa por proceso
- Checklist: resultados de evaluación por requisito
"""

from django.db.models import Count, Avg, Min, Max, Q
from audits.models import (
    ComplianceSnapshot, Findings, ProcessRequirement,
    Checklist, AnnualPlan
)
from risks.models import RiskIdentification, RiskEvaluation
from processes.models import Process
from standards.models import Standard


# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────

RISK_LEVEL_SCORE = {
    'High': 3,
    'Moderate': 2,
    'Low': 1,
}

CATEGORY_SCORE = {
    'EXCELLENT': 5,
    'GOOD': 4,
    'PARTIAL': 3,
    'LOW': 2,
    'CRITICAL': 1,
}


# ─────────────────────────────────────────────
# Funciones de extracción
# ─────────────────────────────────────────────

def get_process_dataset(standard_id=None):
    """
    Construye el dataset histórico a nivel de proceso.

    Para cada proceso con snapshots disponibles extrae:
    - Identificador y nombre del proceso
    - Score de cumplimiento más reciente
    - Tendencia de cumplimiento (mejora/declive/estable)
    - Número de hallazgos históricos (NC_MAYOR, NC_MENOR)
    - Nivel de riesgo agregado del proceso
    - Cobertura normativa (número de requisitos asignados)
    - Número de auditorías realizadas

    Parámetros:
    - standard_id: filtrar por norma (opcional)

    Retorna una lista de dicts con una fila por proceso.
    """
    filters = {}
    if standard_id:
        filters['standard_id'] = standard_id

    # Obtener procesos con snapshots
    process_ids = ComplianceSnapshot.objects.filter(
        **filters
    ).values_list('process_id', flat=True).distinct()

    dataset = []

    for process_id in process_ids:
        process = Process.objects.get(id=process_id)

        snapshots = ComplianceSnapshot.objects.filter(
            process_id=process_id, **filters
        ).order_by('calculated_at')

        if not snapshots.exists():
            continue

        snapshots_list = list(snapshots)
        latest = snapshots_list[-1]

        # Tendencia
        if len(snapshots_list) >= 2:
            delta = snapshots_list[-1].score - snapshots_list[0].score
            if delta > 0.05:
                trend = 'IMPROVING'
                trend_value = 1
            elif delta < -0.05:
                trend = 'DECLINING'
                trend_value = -1
            else:
                trend = 'STABLE'
                trend_value = 0
        else:
            trend = 'INSUFFICIENT_DATA'
            trend_value = 0

        # Hallazgos históricos del proceso
        audit_plans = AnnualPlan.objects.filter(
            annual_program__process=process
        )
        nc_mayor_count = Findings.objects.filter(
            audit_plan__in=audit_plans,
            classification='NC_MAYOR'
        ).count()
        nc_menor_count = Findings.objects.filter(
            audit_plan__in=audit_plans,
            classification='NC_MENOR'
        ).count()
        oportunidad_count = Findings.objects.filter(
            audit_plan__in=audit_plans,
            classification='OPORTUNIDAD_MEJORA'
        ).count()

        # Riesgos del proceso
        risks = RiskIdentification.objects.filter(process=process)
        risk_evaluations = RiskEvaluation.objects.filter(
            risk__process=process
        )
        high_risks = risk_evaluations.filter(risk_level='High').count()
        moderate_risks = risk_evaluations.filter(risk_level='Moderate').count()
        low_risks = risk_evaluations.filter(risk_level='Low').count()

        # Score de riesgo agregado (promedio ponderado)
        risk_score = 0.0
        total_risk_evals = risk_evaluations.count()
        if total_risk_evals > 0:
            risk_score = (
                high_risks * 3 + moderate_risks * 2 + low_risks * 1
            ) / total_risk_evals

        # Cobertura normativa
        if standard_id:
            coverage = ProcessRequirement.objects.filter(
                process=process,
                requirement__clause__standard_id=standard_id,
            ).count()
        else:
            coverage = ProcessRequirement.objects.filter(
                process=process
            ).count()

        # Métricas de checklist
        checklist_items = Checklist.objects.filter(
            audit_plan__in=audit_plans
        )
        total_checks = checklist_items.count()
        compliant_checks = checklist_items.filter(compliance=True).count()
        compliance_rate = (
            compliant_checks / total_checks if total_checks > 0 else 0.0
        )

        dataset.append({
            # Identificadores
            'process_id': process.id,
            'process_name': process.name,
            'process_code': process.process_code,

            # Variables de cumplimiento
            'latest_score': round(latest.score * 100, 1),
            'latest_category': latest.category,
            'latest_category_value': CATEGORY_SCORE.get(latest.category, 0),
            'num_audits': len(snapshots_list),
            'trend': trend,
            'trend_value': trend_value,
            'score_delta': round(
                (snapshots_list[-1].score - snapshots_list[0].score) * 100, 1
            ) if len(snapshots_list) >= 2 else 0.0,
            'avg_score': round(
                sum(s.score for s in snapshots_list) / len(snapshots_list) * 100, 1
            ),
            'min_score': round(
                min(s.score for s in snapshots_list) * 100, 1
            ),
            'max_score': round(
                max(s.score for s in snapshots_list) * 100, 1
            ),

            # Variables de hallazgos
            'nc_mayor_count': nc_mayor_count,
            'nc_menor_count': nc_menor_count,
            'oportunidad_count': oportunidad_count,
            'total_findings': nc_mayor_count + nc_menor_count + oportunidad_count,

            # Variables de riesgo
            'total_risks': risks.count(),
            'high_risks': high_risks,
            'moderate_risks': moderate_risks,
            'low_risks': low_risks,
            'risk_score': round(risk_score, 2),

            # Variables de cobertura
            'normative_coverage': coverage,
            'checklist_compliance_rate': round(compliance_rate * 100, 1),
            'total_checks': total_checks,
        })

    return dataset


def get_snapshot_dataset(standard_id=None):
    """
    Construye el dataset histórico a nivel de snapshot individual.

    Cada fila representa una auditoría concreta con su resultado
    y el contexto del proceso en ese momento.

    Útil para análisis de series temporales y detección de anomalías.
    """
    filters = {}
    if standard_id:
        filters['standard_id'] = standard_id

    snapshots = ComplianceSnapshot.objects.filter(
        **filters
    ).select_related(
        'process', 'standard', 'annual_plan__annual_program'
    ).order_by('process_id', 'calculated_at')

    dataset = []

    for snap in snapshots:
        audit_plan = snap.annual_plan

        # Hallazgos de este plan específico
        findings = Findings.objects.filter(audit_plan=audit_plan)
        nc_mayor = findings.filter(classification='NC_MAYOR').count()
        nc_menor = findings.filter(classification='NC_MENOR').count()

        # Checklist de este plan
        checks = Checklist.objects.filter(audit_plan=audit_plan)
        total_checks = checks.count()
        compliant = checks.filter(compliance=True).count()
        non_compliant_with_evidence = checks.filter(
            compliance=False
        ).exclude(evidence='').exclude(evidence__isnull=True).count()
        insufficient = checks.filter(
            compliance=False
        ).filter(
            Q(evidence='') | Q(evidence__isnull=True)
        ).count()

        dataset.append({
            # Identificadores
            'snapshot_id': snap.id,
            'annual_plan_id': audit_plan.id,
            'process_id': snap.process.id,
            'process_name': snap.process.name,
            'standard_name': snap.standard.name,
            'calculated_at': snap.calculated_at.isoformat(),

            # Variables de cumplimiento
            'score': round(snap.score * 100, 1),
            'category': snap.category,
            'category_value': CATEGORY_SCORE.get(snap.category, 0),
            'total_requirements': snap.total_requirements,
            'compliant_count': snap.compliant_count,
            'non_compliant_count': snap.non_compliant_count,
            'insufficient_count': snap.insufficient_count,
            'not_evaluated_count': snap.not_evaluated_count,

            # Variables de checklist
            'total_checks': total_checks,
            'compliant_checks': compliant,
            'non_compliant_with_evidence': non_compliant_with_evidence,
            'insufficient_evidence_checks': insufficient,

            # Variables de hallazgos
            'nc_mayor_count': nc_mayor,
            'nc_menor_count': nc_menor,
            'has_findings': (nc_mayor + nc_menor) > 0,
        })

    return dataset


def get_risk_dataset():
    """
    Construye el dataset de riesgos por proceso.

    Cada fila representa un riesgo identificado con su evaluación
    y el contexto del proceso al que pertenece.
    """
    dataset = []

    for risk in RiskIdentification.objects.select_related(
        'process', 'area'
    ).prefetch_related('evaluations'):

        evaluations = list(risk.evaluations.all())

        if evaluations:
            latest_eval = evaluations[-1]
            npn = (
                latest_eval.severity *
                latest_eval.occurrence *
                latest_eval.detection
            )
            risk_level = latest_eval.risk_level
            risk_level_value = RISK_LEVEL_SCORE.get(risk_level, 0)
        else:
            npn = None
            risk_level = None
            risk_level_value = None

        dataset.append({
            'risk_id': risk.id,
            'process_id': risk.process.id,
            'process_name': risk.process.name,
            'area_name': risk.area.name,
            'identified_risk': risk.identified_risk,
            'source': risk.source,
            'severity': evaluations[-1].severity if evaluations else None,
            'occurrence': evaluations[-1].occurrence if evaluations else None,
            'detection': evaluations[-1].detection if evaluations else None,
            'npn': npn,
            'risk_level': risk_level,
            'risk_level_value': risk_level_value,
            'num_evaluations': len(evaluations),
        })

    return dataset


def get_full_dataset_summary():
    """
    Devuelve un resumen del dataset histórico disponible,
    útil para validar la consistencia y completitud antes
    de aplicar modelos predictivos.
    """
    process_data = get_process_dataset()
    snapshot_data = get_snapshot_dataset()
    risk_data = get_risk_dataset()

    processes_with_audits = len(process_data)
    processes_improving = sum(
        1 for p in process_data if p['trend'] == 'IMPROVING'
    )
    processes_declining = sum(
        1 for p in process_data if p['trend'] == 'DECLINING'
    )
    processes_stable = sum(
        1 for p in process_data if p['trend'] == 'STABLE'
    )

    avg_score = (
        sum(p['latest_score'] for p in process_data) / len(process_data)
        if process_data else 0
    )

    high_risk_processes = sum(
        1 for p in process_data if p['high_risks'] > 0
    )

    return {
        'dataset_summary': {
            'processes_with_audits': processes_with_audits,
            'total_snapshots': len(snapshot_data),
            'total_risks_evaluated': len(
                [r for r in risk_data if r['risk_level'] is not None]
            ),
            'avg_compliance_score': round(avg_score, 1),
            'processes_improving': processes_improving,
            'processes_declining': processes_declining,
            'processes_stable': processes_stable,
            'high_risk_processes': high_risk_processes,
        },
        'process_dataset': process_data,
        'snapshot_dataset': snapshot_data,
        'risk_dataset': risk_data,
    }