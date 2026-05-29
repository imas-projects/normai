"""
Indicadores estratégicos y alertas para el dashboard ejecutivo — F5-03

Define y evalúa un conjunto de alertas estratégicas con criterios
explícitos de activación, orientadas a dirección y responsables
de calidad.

Principio de diseño: pocas alertas, bien definidas y accionables.
Una alerta que no lleva a una acción concreta no aporta valor.
"""

from .analytics_dataset import get_process_dataset, get_risk_dataset
from .models import Findings, AnnualPlan, ComplianceSnapshot


# ─────────────────────────────────────────────
# Definición de alertas estratégicas
# ─────────────────────────────────────────────

ALERT_DEFINITIONS = {
    'CRITICAL_PROCESS': {
        'name': 'Proceso en estado crítico',
        'description': 'Hay procesos con score de cumplimiento inferior al 25%.',
        'action': 'Revisar inmediatamente el proceso y planificar auditoría correctiva.',
        'severity': 'CRITICAL',
        'color': 'red',
    },
    'GLOBAL_SCORE_LOW': {
        'name': 'Score global de cumplimiento bajo',
        'description': 'El score medio de cumplimiento de la organización es inferior al 50%.',
        'action': 'Convocar revisión por la dirección para analizar causas.',
        'severity': 'HIGH',
        'color': 'orange',
    },
    'DECLINING_PROCESSES': {
        'name': 'Procesos con tendencia negativa',
        'description': 'Hay procesos cuyo cumplimiento está empeorando entre auditorías.',
        'action': 'Identificar causas del declive e implementar acciones preventivas.',
        'severity': 'HIGH',
        'color': 'orange',
    },
    'HIGH_NPN_UNADDRESSED': {
        'name': 'Riesgos con NPN crítico sin tratamiento',
        'description': 'Hay riesgos con NPN superior a 300 que requieren atención prioritaria.',
        'action': 'Activar plan de tratamiento de riesgo para los procesos afectados.',
        'severity': 'HIGH',
        'color': 'orange',
    },
    'NC_MAYOR_ACCUMULATED': {
        'name': 'No conformidades mayores acumuladas',
        'description': 'El sistema acumula no conformidades mayores sin resolver.',
        'action': 'Verificar estado de acciones correctivas asociadas.',
        'severity': 'MEDIUM',
        'color': 'yellow',
    },
    'PROCESSES_NOT_AUDITED': {
        'name': 'Procesos sin cobertura de auditoría suficiente',
        'description': 'Hay procesos con menos de 2 auditorías registradas.',
        'action': 'Planificar auditorías para los procesos sin cobertura suficiente.',
        'severity': 'MEDIUM',
        'color': 'yellow',
    },
    'ALL_PROCESSES_COMPLIANT': {
        'name': 'Cumplimiento satisfactorio en todos los procesos',
        'description': 'Todos los procesos auditados tienen score superior al 70%.',
        'action': 'Mantener el nivel actual y planificar mejora continua.',
        'severity': 'INFO',
        'color': 'green',
    },
}

# Umbrales
THRESHOLD_CRITICAL_SCORE = 25.0
THRESHOLD_LOW_GLOBAL_SCORE = 50.0
THRESHOLD_GOOD_SCORE = 70.0
THRESHOLD_HIGH_NPN = 300
THRESHOLD_MIN_AUDITS = 2


# ─────────────────────────────────────────────
# Motor de evaluación de alertas
# ─────────────────────────────────────────────

def evaluate_strategic_alerts(standard_id=None):
    """
    Evalúa las alertas estratégicas sobre el estado actual del sistema.

    Retorna una lista de alertas activas ordenadas por severidad,
    con criterios de activación y acciones recomendadas.
    """
    process_data = get_process_dataset(standard_id=standard_id)

    if not process_data:
        return {
            'success': False,
            'error': 'No hay datos disponibles para evaluar alertas.',
        }

    relevant_process_ids = [p['process_id'] for p in process_data]
    risk_data = get_risk_dataset(process_ids=relevant_process_ids)

    active_alerts = []

    # ── Alerta 1: Proceso en estado crítico ───────────────────────
    critical_processes = [
        p for p in process_data
        if p['latest_score'] < THRESHOLD_CRITICAL_SCORE
    ]
    if critical_processes:
        active_alerts.append({
            **ALERT_DEFINITIONS['CRITICAL_PROCESS'],
            'alert_id': 'CRITICAL_PROCESS',
            'active': True,
            'affected_count': len(critical_processes),
            'affected_items': [
                {
                    'process_id': p['process_id'],
                    'process_name': p['process_name'],
                    'score': p['latest_score'],
                }
                for p in critical_processes
            ],
        })

    # ── Alerta 2: Score global bajo ───────────────────────────────
    avg_score = sum(p['latest_score'] for p in process_data) / len(process_data)
    if avg_score < THRESHOLD_LOW_GLOBAL_SCORE:
        active_alerts.append({
            **ALERT_DEFINITIONS['GLOBAL_SCORE_LOW'],
            'alert_id': 'GLOBAL_SCORE_LOW',
            'active': True,
            'affected_count': 1,
            'affected_items': [
                {'global_score': round(avg_score, 1)}
            ],
        })

    # ── Alerta 3: Procesos con tendencia negativa ─────────────────
    declining_processes = [
        p for p in process_data if p['trend'] == 'DECLINING'
    ]
    if declining_processes:
        active_alerts.append({
            **ALERT_DEFINITIONS['DECLINING_PROCESSES'],
            'alert_id': 'DECLINING_PROCESSES',
            'active': True,
            'affected_count': len(declining_processes),
            'affected_items': [
                {
                    'process_id': p['process_id'],
                    'process_name': p['process_name'],
                    'score_delta': p['score_delta'],
                }
                for p in declining_processes
            ],
        })

    # ── Alerta 4: Riesgos con NPN crítico ────────────────────────
    high_npn_risks = [
        r for r in risk_data
        if r['npn'] is not None and r['npn'] > THRESHOLD_HIGH_NPN
    ]
    if high_npn_risks:
        active_alerts.append({
            **ALERT_DEFINITIONS['HIGH_NPN_UNADDRESSED'],
            'alert_id': 'HIGH_NPN_UNADDRESSED',
            'active': True,
            'affected_count': len(high_npn_risks),
            'affected_items': [
                {
                    'risk_id': r['risk_id'],
                    'identified_risk': r['identified_risk'],
                    'process_name': r['process_name'],
                    'npn': r['npn'],
                }
                for r in sorted(
                    high_npn_risks, key=lambda x: x['npn'], reverse=True
                )[:5]
            ],
        })

    # ── Alerta 5: NC_MAYOR acumuladas ─────────────────────────────
    nc_mayor_total = Findings.objects.filter(
        classification='NC_MAYOR'
    ).count()
    if nc_mayor_total > 0:
        active_alerts.append({
            **ALERT_DEFINITIONS['NC_MAYOR_ACCUMULATED'],
            'alert_id': 'NC_MAYOR_ACCUMULATED',
            'active': True,
            'affected_count': nc_mayor_total,
            'affected_items': [
                {'nc_mayor_total': nc_mayor_total}
            ],
        })

    # ── Alerta 6: Procesos sin cobertura suficiente ───────────────
    not_audited = [
        p for p in process_data
        if p['num_audits'] < THRESHOLD_MIN_AUDITS
    ]
    if not_audited:
        active_alerts.append({
            **ALERT_DEFINITIONS['PROCESSES_NOT_AUDITED'],
            'alert_id': 'PROCESSES_NOT_AUDITED',
            'active': True,
            'affected_count': len(not_audited),
            'affected_items': [
                {
                    'process_id': p['process_id'],
                    'process_name': p['process_name'],
                    'num_audits': p['num_audits'],
                }
                for p in not_audited
            ],
        })

    # ── Alerta positiva: Todo en orden ───────────────────────────
    all_good = all(
        p['latest_score'] >= THRESHOLD_GOOD_SCORE
        for p in process_data
    )
    if all_good:
        active_alerts.append({
            **ALERT_DEFINITIONS['ALL_PROCESSES_COMPLIANT'],
            'alert_id': 'ALL_PROCESSES_COMPLIANT',
            'active': True,
            'affected_count': len(process_data),
            'affected_items': [],
        })

    # Ordenar por severidad
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'INFO': 3}
    active_alerts.sort(key=lambda x: severity_order.get(x['severity'], 4))

    # Resumen
    critical_count = sum(1 for a in active_alerts if a['severity'] == 'CRITICAL')
    high_count = sum(1 for a in active_alerts if a['severity'] == 'HIGH')
    medium_count = sum(1 for a in active_alerts if a['severity'] == 'MEDIUM')
    info_count = sum(1 for a in active_alerts if a['severity'] == 'INFO')

    # Indicadores estratégicos adicionales
    strategic_indicators = _calculate_strategic_indicators(
        process_data, risk_data, avg_score
    )

    return {
        'success': True,
        'summary': {
            'total_active_alerts': len(active_alerts),
            'critical_alerts': critical_count,
            'high_alerts': high_count,
            'medium_alerts': medium_count,
            'info_alerts': info_count,
            'requires_immediate_action': critical_count + high_count > 0,
        },
        'alerts': active_alerts,
        'strategic_indicators': strategic_indicators,
    }


def _calculate_strategic_indicators(process_data, risk_data, avg_score):
    """
    Calcula indicadores estratégicos de alto nivel para dirección.
    """
    total_processes = len(process_data)

    # Índice de madurez del sistema (0-100)
    # Combina score de cumplimiento, cobertura de auditorías y tendencia
    audit_coverage = sum(
        min(1.0, p['num_audits'] / 2.0) for p in process_data
    ) / total_processes if total_processes > 0 else 0

    trend_score = sum(
        1.0 if p['trend'] == 'IMPROVING' else
        0.5 if p['trend'] == 'STABLE' else
        0.0 if p['trend'] == 'DECLINING' else
        0.5
        for p in process_data
    ) / total_processes if total_processes > 0 else 0

    maturity_index = round(
        (avg_score * 0.5 + audit_coverage * 100 * 0.3 + trend_score * 100 * 0.2),
        1
    )

    # Tasa de conformidad efectiva
    total_compliant = sum(p['checklist_compliance_rate'] for p in process_data)
    avg_checklist_rate = round(
        total_compliant / total_processes, 1
    ) if total_processes > 0 else 0

    # Exposición al riesgo
    high_risks = sum(1 for r in risk_data if r['risk_level'] == 'High')
    total_risks = len(risk_data)
    risk_exposure = round(
        (high_risks / total_risks * 100) if total_risks > 0 else 0, 1
    )

    # Procesos bajo control (score >= 70%)
    processes_under_control = sum(
        1 for p in process_data if p['latest_score'] >= 70
    )
    control_rate = round(
        processes_under_control / total_processes * 100, 1
    ) if total_processes > 0 else 0

    return {
        'maturity_index': maturity_index,
        'maturity_label': (
            'Alto' if maturity_index >= 70 else
            'Medio' if maturity_index >= 40 else
            'Bajo'
        ),
        'avg_checklist_compliance_rate': avg_checklist_rate,
        'risk_exposure_rate': risk_exposure,
        'processes_under_control': processes_under_control,
        'control_rate': control_rate,
        'audit_coverage_rate': round(audit_coverage * 100, 1),
    }