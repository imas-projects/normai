"""
Motor de evaluación determinista del cumplimiento — F3-02

Implementa las reglas definidas en docs/f3_01_compliance_scoring_rules.md.
Calcula el cumplimiento por proceso y norma a partir de los datos de
auditoría estructurados y persiste los resultados en ComplianceSnapshot.
"""

from django.utils import timezone
from .models import (
    AnnualPlan, ProcessRequirement, Checklist,
    AuditedEvaluationQuestion, Findings, ComplianceSnapshot
)


# ─────────────────────────────────────────────
# Constantes — Reglas de F3-01
# ─────────────────────────────────────────────

# Puntuación base por estado de checklist
SCORE_BY_STATUS = {
    'COMPLIANT': 1.0,
    'NON_COMPLIANT': 0.0,
    'INSUFFICIENT_EVIDENCE': 0.25,
    'NOT_EVALUATED': 0.0,
}

# Penalización por clasificación de hallazgo
FINDING_PENALTY = {
    'NC_MAYOR': 0.3,
    'NC_MENOR': 0.15,
    'OPORTUNIDAD_MEJORA': 0.0,
}

# Peso por criticidad y obligatoriedad
WEIGHT_TABLE = {
    ('high', True): 3,
    ('high', False): 2,
    ('medium', True): 2,
    ('medium', False): 1,
    ('low', True): 1,
    ('low', False): 0.5,
}

# Umbrales para categoría cualitativa
CATEGORY_THRESHOLDS = [
    (0.85, 'EXCELLENT'),
    (0.70, 'GOOD'),
    (0.50, 'PARTIAL'),
    (0.25, 'LOW'),
    (0.00, 'CRITICAL'),
]


# ─────────────────────────────────────────────
# Funciones auxiliares
# ─────────────────────────────────────────────

def _get_checklist_status(checklist_item):
    """
    Determina el estado de un ítem de checklist según las reglas de F2-03.
    """
    if checklist_item is None:
        return 'NOT_EVALUATED'
    if checklist_item.compliance:
        return 'COMPLIANT'
    if checklist_item.evidence and checklist_item.evidence.strip():
        return 'NON_COMPLIANT'
    return 'INSUFFICIENT_EVIDENCE'


def _get_finding_penalty(process_requirement, annual_plan):
    """
    Calcula la penalización total por hallazgos asociados a un
    ProcessRequirement en un AnnualPlan específico.
    """
    findings = Findings.objects.filter(
        audit_plan=annual_plan,
        requirement=process_requirement,
    )
    total_penalty = 0.0
    for finding in findings:
        total_penalty += FINDING_PENALTY.get(finding.classification, 0.0)
    return total_penalty


def _get_weight(standard_requirement):
    """
    Devuelve el peso de un StandardRequirement según criticidad y obligatoriedad.
    """
    key = (standard_requirement.criticality_level, standard_requirement.mandatory)
    return WEIGHT_TABLE.get(key, 1)


def _score_to_category(score):
    """
    Convierte un score numérico (0.0-1.0) a su categoría cualitativa.
    """
    for threshold, category in CATEGORY_THRESHOLDS:
        if score >= threshold:
            return category
    return 'CRITICAL'


# ─────────────────────────────────────────────
# Motor principal
# ─────────────────────────────────────────────

def calculate_compliance_for_plan(annual_plan_id, overwrite=False):
    """
    Calcula el cumplimiento de un AnnualPlan y persiste el resultado
    en ComplianceSnapshot.

    Parámetros:
    - annual_plan_id: ID del AnnualPlan a calcular
    - overwrite: si True, elimina el snapshot existente y recalcula

    Retorna un dict con el resultado o un dict con 'error'.
    """
    try:
        annual_plan = AnnualPlan.objects.select_related(
            'annual_program__process',
            'annual_program__standard',
        ).get(id=annual_plan_id)
    except AnnualPlan.DoesNotExist:
        return {'error': 'Plan de auditoría no encontrado.'}

    process = annual_plan.annual_program.process
    standard = annual_plan.annual_program.standard

    if not standard:
        return {
            'error': 'El programa de auditoría no tiene norma seleccionada.'
        }

    # Verificar si ya existe snapshot
    existing = ComplianceSnapshot.objects.filter(
        annual_plan=annual_plan,
        process=process,
        standard=standard,
    ).first()

    if existing and not overwrite:
        return {
            'error': 'Ya existe un snapshot para este plan. '
                     'Usa overwrite=True para recalcular.',
            'existing_snapshot_id': existing.id,
        }

    if existing and overwrite:
        existing.delete()

    # Obtener ProcessRequirements del proceso para la norma
    process_requirements = ProcessRequirement.objects.filter(
        process=process,
        requirement__clause__standard=standard,
    ).select_related(
        'requirement__clause__standard',
    )

    if not process_requirements.exists():
        return {
            'error': f'El proceso "{process.name}" no tiene requisitos '
                     f'asignados para la norma "{standard.name}".'
        }

    # Construir índice checklist por ProcessRequirement
    checklist_items = Checklist.objects.filter(
        audit_plan=annual_plan,
    ).select_related('question__requirement')

    checklist_index = {}
    for item in checklist_items:
        if item.question and item.question.requirement:
            checklist_index[item.question.requirement.id] = item

    # Calcular puntuación por requisito
    detail = []
    total_weighted_score = 0.0
    total_weight = 0.0

    counts = {
        'compliant': 0,
        'non_compliant': 0,
        'insufficient': 0,
        'not_evaluated': 0,
    }

    for pr in process_requirements.order_by(
        'requirement__clause__ordering',
        'requirement__ordering',
    ):
        req = pr.requirement
        checklist_item = checklist_index.get(pr.id)

        # Estado base
        status = _get_checklist_status(checklist_item)

        # Puntuación base
        base_score = SCORE_BY_STATUS[status]

        # Penalización por hallazgos
        penalty = _get_finding_penalty(pr, annual_plan)
        final_score = max(0.0, base_score - penalty)

        # Peso
        weight = _get_weight(req)

        # Acumular
        total_weighted_score += final_score * weight
        total_weight += weight

        # Contadores
        if status == 'COMPLIANT':
            counts['compliant'] += 1
        elif status == 'NON_COMPLIANT':
            counts['non_compliant'] += 1
        elif status == 'INSUFFICIENT_EVIDENCE':
            counts['insufficient'] += 1
        else:
            counts['not_evaluated'] += 1

        detail.append({
            'process_requirement_id': pr.id,
            'clause_code': req.clause.code,
            'clause_title': req.clause.title,
            'requirement_text': req.text[:120],
            'mandatory': req.mandatory,
            'criticality_level': req.criticality_level,
            'is_extension': req.is_extension,
            'status': status,
            'base_score': base_score,
            'penalty': round(penalty, 3),
            'final_score': round(final_score, 3),
            'weight': weight,
        })

    # Score global
    global_score = (
        total_weighted_score / total_weight if total_weight > 0 else 0.0
    )
    category = _score_to_category(global_score)

    # Persistir snapshot
    snapshot = ComplianceSnapshot.objects.create(
        annual_plan=annual_plan,
        process=process,
        standard=standard,
        score=global_score,
        category=category,
        total_requirements=process_requirements.count(),
        compliant_count=counts['compliant'],
        non_compliant_count=counts['non_compliant'],
        insufficient_count=counts['insufficient'],
        not_evaluated_count=counts['not_evaluated'],
        detail=detail,
    )

    return {
        'success': True,
        'snapshot': snapshot.as_dict(),
    }


def get_compliance_by_standard(standard_id):
    """
    Calcula el cumplimiento agregado de una norma a partir de los
    snapshots más recientes de cada proceso.

    Retorna un dict con el score global de la norma y el desglose
    por proceso.
    """
    from standards.models import Standard

    try:
        standard = Standard.objects.get(id=standard_id)
    except Standard.DoesNotExist:
        return {'error': 'Norma no encontrada.'}

    # Obtener el snapshot más reciente por proceso para esta norma
    from django.db.models import Max

    latest_snapshots_ids = (
        ComplianceSnapshot.objects
        .filter(standard=standard)
        .values('process')
        .annotate(latest=Max('calculated_at'))
        .values_list('process', 'latest')
    )

    if not latest_snapshots_ids:
        return {
            'error': f'No hay snapshots calculados para la norma '
                     f'"{standard.name}". Calcula primero el cumplimiento '
                     f'de al menos un proceso.'
        }

    snapshots = []
    for process_id, latest_date in latest_snapshots_ids:
        snapshot = ComplianceSnapshot.objects.filter(
            standard=standard,
            process_id=process_id,
            calculated_at=latest_date,
        ).first()
        if snapshot:
            snapshots.append(snapshot)

    # Calcular score global ponderado por número de requisitos
    total_weighted = sum(s.score * s.total_requirements for s in snapshots)
    total_reqs = sum(s.total_requirements for s in snapshots)
    global_score = total_weighted / total_reqs if total_reqs > 0 else 0.0
    global_category = _score_to_category(global_score)

    return {
        'success': True,
        'standard': {
            'id': standard.id,
            'name': standard.name,
        },
        'global_score': round(global_score * 100, 1),
        'global_category': global_category,
        'total_processes': len(snapshots),
        'processes': [s.as_dict() for s in snapshots],
    }