"""
Vistas ejecutivas de cumplimiento y riesgo — F5-02

Implementa la lógica de agregación para el dashboard ejecutivo
de NormAI, consolidando indicadores de cumplimiento, riesgos,
auditorías y señales predictivas en una única vista ejecutiva.

Fuentes de datos:
- compliance_engine.py: scores y snapshots de cumplimiento
- analytics_dataset.py: dataset histórico agregado
- risk_predictor.py: predicciones de riesgo de no conformidad
- anomaly_detector.py: anomalías detectadas
"""

from .compliance_engine import get_compliance_by_standard
from .analytics_dataset import get_process_dataset, get_risk_dataset
from .risk_predictor import predict_non_conformity_risk
from .anomaly_detector import detect_anomalies
from .models import (
    AnnualPlan, Findings, ComplianceSnapshot
)
from standards.models import Standard
from .strategic_alerts import evaluate_strategic_alerts


def get_executive_dashboard(standard_id=None):
    """
    Construye el dashboard ejecutivo completo agregando indicadores
    de cumplimiento, riesgo, auditorías y señales predictivas.

    Parámetros:
    - standard_id: filtrar por norma (opcional)

    Retorna un dict con cuatro bloques:
    - executive_summary: resumen global
    - compliance_block: indicadores de cumplimiento
    - risk_block: indicadores de riesgo
    - audit_block: indicadores de auditorías y hallazgos
    - alert_block: anomalías y predicciones
    """

    # ── Obtener normas disponibles ────────────────────────────────
    standards = list(Standard.objects.filter(is_active=True).values(
        'id', 'name', 'sector'
    ))

    # ── Dataset de procesos ───────────────────────────────────────
    process_data = get_process_dataset(standard_id=standard_id)

    if not process_data:
        return {
            'success': False,
            'error': 'No hay datos de cumplimiento disponibles. '
                     'Calcula primero el cumplimiento de al menos un proceso.',
            'standards_available': standards,
        }

    # ── Bloque 1: Resumen ejecutivo ───────────────────────────────
    total_processes = len(process_data)
    avg_score = sum(p['latest_score'] for p in process_data) / total_processes

    # Categoría global
    if avg_score >= 85:
        global_category = 'EXCELLENT'
    elif avg_score >= 70:
        global_category = 'GOOD'
    elif avg_score >= 50:
        global_category = 'PARTIAL'
    elif avg_score >= 25:
        global_category = 'LOW'
    else:
        global_category = 'CRITICAL'

    # Tendencia global
    improving = sum(1 for p in process_data if p['trend'] == 'IMPROVING')
    declining = sum(1 for p in process_data if p['trend'] == 'DECLINING')
    stable = sum(1 for p in process_data if p['trend'] == 'STABLE')

    if improving > declining:
        global_trend = 'IMPROVING'
    elif declining > improving:
        global_trend = 'DECLINING'
    else:
        global_trend = 'STABLE'

    total_audits = AnnualPlan.objects.count()

    executive_summary = {
        'global_compliance_score': round(avg_score, 1),
        'global_compliance_category': global_category,
        'compliance_trend': global_trend,
        'total_audits': total_audits,
        'processes_audited': total_processes,
        'standard_filter': standard_id,
    }

    # ── Bloque 2: Cumplimiento ────────────────────────────────────
    by_category = {
        'EXCELLENT': 0, 'GOOD': 0, 'PARTIAL': 0, 'LOW': 0, 'CRITICAL': 0
    }
    for p in process_data:
        cat = p['latest_category']
        if cat in by_category:
            by_category[cat] += 1

    sorted_by_score = sorted(process_data, key=lambda x: x['latest_score'])
    worst_processes = [
        {
            'process_id': p['process_id'],
            'process_name': p['process_name'],
            'score': p['latest_score'],
            'category': p['latest_category'],
            'trend': p['trend'],
        }
        for p in sorted_by_score[:3]
    ]
    best_processes = [
        {
            'process_id': p['process_id'],
            'process_name': p['process_name'],
            'score': p['latest_score'],
            'category': p['latest_category'],
            'trend': p['trend'],
        }
        for p in sorted_by_score[-3:][::-1]
    ]

    all_processes = [
        {
            'process_id': p['process_id'],
            'process_name': p['process_name'],
            'score': p['latest_score'],
            'category': p['latest_category'],
            'trend': p['trend'],
            'trend_value': p['trend_value'],
            'num_audits': p['num_audits'],
            'avg_score': p['avg_score'],
            'score_delta': p['score_delta'],
        }
        for p in sorted_by_score
    ]

    compliance_block = {
        'by_category': by_category,
        'worst_processes': worst_processes,
        'best_processes': best_processes,
        'all_processes': all_processes,
        'improving_count': improving,
        'declining_count': declining,
        'stable_count': stable,
        'insufficient_data_count': sum(
            1 for p in process_data if p['trend'] == 'INSUFFICIENT_DATA'
        ),
    }

    # ── Bloque 3: Riesgos ─────────────────────────────────────────
    relevant_process_ids = [p['process_id'] for p in process_data]
    risk_data = get_risk_dataset(process_ids=relevant_process_ids)

    total_high = sum(1 for r in risk_data if r['risk_level'] == 'High')
    total_moderate = sum(1 for r in risk_data if r['risk_level'] == 'Moderate')
    total_low = sum(1 for r in risk_data if r['risk_level'] == 'Low')

    npn_values = [r['npn'] for r in risk_data if r['npn'] is not None]
    max_npn = max(npn_values) if npn_values else 0
    avg_npn = round(sum(npn_values) / len(npn_values), 1) if npn_values else 0

    # Procesos con riesgo alto
    processes_with_high_risk = list(set(
        r['process_name'] for r in risk_data if r['risk_level'] == 'High'
    ))

    # Top riesgos por NPN
    top_risks = sorted(
        [r for r in risk_data if r['npn'] is not None],
        key=lambda x: x['npn'],
        reverse=True
    )[:5]

    risk_block = {
        'total_high_risks': total_high,
        'total_moderate_risks': total_moderate,
        'total_low_risks': total_low,
        'total_risks': len(risk_data),
        'max_npn': max_npn,
        'avg_npn': avg_npn,
        'processes_with_high_risk': processes_with_high_risk,
        'processes_with_high_risk_count': len(processes_with_high_risk),
        'top_risks_by_npn': [
            {
                'risk_id': r['risk_id'],
                'identified_risk': r['identified_risk'],
                'process_name': r['process_name'],
                'npn': r['npn'],
                'risk_level': r['risk_level'],
            }
            for r in top_risks
        ],
    }

    # ── Bloque 4: Auditorías y hallazgos ──────────────────────────
    total_findings = Findings.objects.count()
    nc_mayor_total = Findings.objects.filter(
        classification='NC_MAYOR'
    ).count()
    nc_menor_total = Findings.objects.filter(
        classification='NC_MENOR'
    ).count()
    oportunidad_total = Findings.objects.filter(
        classification='OPORTUNIDAD_MEJORA'
    ).count()

    processes_without_recent_audit = sum(
        1 for p in process_data if p['num_audits'] < 2
    )

    audit_block = {
        'total_audits': total_audits,
        'total_findings': total_findings,
        'nc_mayor_total': nc_mayor_total,
        'nc_menor_total': nc_menor_total,
        'oportunidad_total': oportunidad_total,
        'processes_without_recent_audit': processes_without_recent_audit,
        'avg_audits_per_process': round(
            total_audits / total_processes, 1
        ) if total_processes > 0 else 0,
    }

    # ── Bloque 5: Alertas y predicciones ─────────────────────────
    anomaly_result = detect_anomalies(standard_id=standard_id)
    anomalies = anomaly_result.get('anomalies', [])
    anomaly_summary = anomaly_result.get('summary', {})

    prediction_result = predict_non_conformity_risk(standard_id=standard_id)
    predictions = prediction_result.get('predictions', [])
    high_risk_predictions = [
        p for p in predictions if p['risk_category'] == 'HIGH'
    ]
    medium_risk_predictions = [
        p for p in predictions if p['risk_category'] == 'MEDIUM'
    ]

    alert_block = {
        'total_anomalies': anomaly_summary.get('total_anomalies', 0),
        'high_severity_anomalies': anomaly_summary.get('high_severity', 0),
        'medium_severity_anomalies': anomaly_summary.get('medium_severity', 0),
        'anomaly_types_detected': anomaly_summary.get('detected_types', []),
        'top_anomalies': anomalies[:5],
        'high_risk_predictions_count': len(high_risk_predictions),
        'medium_risk_predictions_count': len(medium_risk_predictions),
        'top_risk_predictions': predictions[:3],
    }

    # ── Bloque 6: Indicadores estratégicos y alertas ─────────────
    strategic_result = evaluate_strategic_alerts(standard_id=standard_id)
    strategic_block = {
        'alerts': strategic_result.get('alerts', []),
        'alerts_summary': strategic_result.get('summary', {}),
        'strategic_indicators': strategic_result.get('strategic_indicators', {}),
    }

    return {
        'success': True,
        'standards_available': standards,
        'executive_summary': executive_summary,
        'compliance_block': compliance_block,
        'risk_block': risk_block,
        'audit_block': audit_block,
        'alert_block': alert_block,
        'strategic_block': strategic_block,
    }