"""
Prototipo de predicción de riesgo de no conformidad — F4-02

Implementa un modelo heurístico determinista que estima el riesgo
de no conformidad de cada proceso combinando variables históricas
del dataset preparado en F4-01.

IMPORTANTE: Este es un prototipo exploratorio, no un sistema predictivo
validado industrialmente. Los resultados deben interpretarse como
señales orientativas, no como predicciones estadísticamente robustas.
La base de datos histórica actual (10 snapshots) es insuficiente para
modelos de machine learning. Este enfoque heurístico es apropiado para
el volumen de datos disponible y evoluciona hacia ML cuando el histórico
sea suficiente.
"""

from .analytics_dataset import get_process_dataset, get_risk_dataset


# ─────────────────────────────────────────────
# Constantes del modelo heurístico
# ─────────────────────────────────────────────

# Pesos de cada factor en el score de riesgo final
WEIGHT_COMPLIANCE = 0.40      # Score de cumplimiento actual
WEIGHT_TREND = 0.20           # Tendencia del cumplimiento
WEIGHT_RISK_LEVEL = 0.25      # Nivel de riesgo del proceso
WEIGHT_FINDINGS_HISTORY = 0.15  # Historial de no conformidades

# Umbrales para categoría de riesgo de no conformidad
RISK_CATEGORY_THRESHOLDS = [
    (0.75, 'HIGH',     'Alto riesgo de no conformidad'),
    (0.50, 'MEDIUM',   'Riesgo moderado de no conformidad'),
    (0.25, 'LOW',      'Bajo riesgo de no conformidad'),
    (0.00, 'MINIMAL',  'Riesgo mínimo de no conformidad'),
]


# ─────────────────────────────────────────────
# Funciones de normalización
# ─────────────────────────────────────────────

def _normalize_compliance_to_risk(score):
    """
    Convierte el score de cumplimiento (0-100) a factor de riesgo (0-1).
    A menor cumplimiento, mayor riesgo.
    """
    return 1.0 - (score / 100.0)


def _normalize_trend_to_risk(trend_value):
    """
    Convierte la tendencia a factor de riesgo (0-1).
    - DECLINING (-1) → riesgo alto (0.8)
    - STABLE (0) → riesgo medio (0.5)
    - IMPROVING (1) → riesgo bajo (0.2)
    - INSUFFICIENT_DATA → riesgo neutro (0.5)
    """
    mapping = {
        1: 0.2,    # IMPROVING
        0: 0.5,    # STABLE / INSUFFICIENT_DATA
        -1: 0.8,   # DECLINING
    }
    return mapping.get(trend_value, 0.5)


def _normalize_risk_score(risk_score, max_risk=3.0):
    """
    Normaliza el score de riesgo agregado del proceso (1-3) a (0-1).
    """
    return min(1.0, max(0.0, (risk_score - 1.0) / (max_risk - 1.0)))


def _normalize_findings_history(nc_mayor, nc_menor, num_audits):
    """
    Normaliza el historial de hallazgos a factor de riesgo (0-1).
    NC_MAYOR pesan más que NC_MENOR. Se relativiza por número de auditorías.
    """
    if num_audits == 0:
        return 0.5
    weighted = (nc_mayor * 2 + nc_menor * 1) / max(1, num_audits)
    return min(1.0, weighted / 2.0)


def _risk_score_to_category(risk_score):
    """
    Convierte el score de riesgo (0-1) a categoría cualitativa.
    """
    for threshold, category, description in RISK_CATEGORY_THRESHOLDS:
        if risk_score >= threshold:
            return category, description
    return 'MINIMAL', 'Riesgo mínimo de no conformidad'


# ─────────────────────────────────────────────
# Motor de predicción
# ─────────────────────────────────────────────

def predict_non_conformity_risk(standard_id=None):
    """
    Calcula el riesgo de no conformidad para cada proceso con
    datos históricos disponibles.

    Parámetros:
    - standard_id: filtrar por norma (opcional)

    Retorna una lista de dicts ordenada por riesgo descendente,
    con el score de riesgo, categoría y desglose de factores.
    """
    process_data = get_process_dataset(standard_id=standard_id)

    if not process_data:
        return {
            'error': 'No hay datos históricos disponibles. '
                     'Calcula primero el cumplimiento de al menos un proceso.'
        }

    predictions = []

    for process in process_data:
        # Factor 1 — Cumplimiento actual (peso 40%)
        f_compliance = _normalize_compliance_to_risk(process['latest_score'])

        # Factor 2 — Tendencia (peso 20%)
        f_trend = _normalize_trend_to_risk(process['trend_value'])

        # Factor 3 — Nivel de riesgo del proceso (peso 25%)
        f_risk = _normalize_risk_score(process['risk_score'])

        # Factor 4 — Historial de no conformidades (peso 15%)
        f_findings = _normalize_findings_history(
            process['nc_mayor_count'],
            process['nc_menor_count'],
            process['num_audits'],
        )

        # Score de riesgo final ponderado
        risk_score = (
            f_compliance * WEIGHT_COMPLIANCE +
            f_trend * WEIGHT_TREND +
            f_risk * WEIGHT_RISK_LEVEL +
            f_findings * WEIGHT_FINDINGS_HISTORY
        )

        risk_category, risk_description = _risk_score_to_category(risk_score)

        predictions.append({
            'process_id': process['process_id'],
            'process_name': process['process_name'],
            'risk_score': round(risk_score * 100, 1),
            'risk_category': risk_category,
            'risk_description': risk_description,
            'factors': {
                'compliance_factor': round(f_compliance * 100, 1),
                'trend_factor': round(f_trend * 100, 1),
                'risk_level_factor': round(f_risk * 100, 1),
                'findings_factor': round(f_findings * 100, 1),
            },
            'source_data': {
                'latest_score': process['latest_score'],
                'latest_category': process['latest_category'],
                'trend': process['trend'],
                'risk_score_raw': process['risk_score'],
                'nc_mayor_count': process['nc_mayor_count'],
                'nc_menor_count': process['nc_menor_count'],
                'num_audits': process['num_audits'],
            },
        })

    # Ordenar por riesgo descendente
    predictions.sort(key=lambda x: x['risk_score'], reverse=True)

    # Resumen agregado
    high_risk = sum(1 for p in predictions if p['risk_category'] == 'HIGH')
    medium_risk = sum(1 for p in predictions if p['risk_category'] == 'MEDIUM')
    low_risk = sum(1 for p in predictions if p['risk_category'] == 'LOW')
    minimal_risk = sum(1 for p in predictions if p['risk_category'] == 'MINIMAL')

    return {
        'success': True,
        'model_info': {
            'type': 'HEURISTIC',
            'version': '1.0',
            'description': (
                'Modelo heurístico determinista basado en ponderación '
                'de factores históricos. Prototipo exploratorio — '
                'no validado estadísticamente.'
            ),
            'weights': {
                'compliance': WEIGHT_COMPLIANCE,
                'trend': WEIGHT_TREND,
                'risk_level': WEIGHT_RISK_LEVEL,
                'findings_history': WEIGHT_FINDINGS_HISTORY,
            },
            'data_points': len(predictions),
        },
        'summary': {
            'total_processes': len(predictions),
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'minimal_risk': minimal_risk,
        },
        'predictions': predictions,
    }