"""
Prototipo de detección de anomalías sobre datos de calidad — F4-03

Implementa un detector de anomalías basado en reglas y umbrales
que identifica patrones atípicos en auditorías, cumplimiento y riesgos.

IMPORTANTE: Este es un prototipo exploratorio basado en reglas
deterministas. Con el volumen de datos actual (10 snapshots) no es
viable aplicar algoritmos estadísticos de detección de anomalías
(Isolation Forest, DBSCAN, z-score). Este enfoque es apropiado
para el estado actual del sistema y evoluciona hacia métodos
estadísticos cuando el histórico sea suficiente.
"""

from .analytics_dataset import (
    get_process_dataset,
    get_snapshot_dataset,
    get_risk_dataset,
)
from .models import ComplianceSnapshot


# ─────────────────────────────────────────────
# Definición de anomalías
# ─────────────────────────────────────────────

ANOMALY_TYPES = {
    'SCORE_DROP': {
        'name': 'Caída brusca de cumplimiento',
        'description': (
            'El score de cumplimiento cayó más de 20 puntos entre '
            'dos auditorías consecutivas.'
        ),
        'severity': 'HIGH',
    },
    'CRITICAL_COMPLIANCE': {
        'name': 'Cumplimiento crítico persistente',
        'description': (
            'El proceso tiene un score de cumplimiento crítico '
            '(inferior al 25%) en su última auditoría.'
        ),
        'severity': 'HIGH',
    },
    'HIGH_RISK_LOW_COVERAGE': {
        'name': 'Alto riesgo con cobertura normativa insuficiente',
        'description': (
            'El proceso tiene un nivel de riesgo alto pero menos '
            'de 3 requisitos normativos asignados.'
        ),
        'severity': 'MEDIUM',
    },
    'REPEATED_FINDINGS': {
        'name': 'No conformidades mayores repetidas',
        'description': (
            'El proceso acumula más de una no conformidad mayor '
            'en su historial de auditorías.'
        ),
        'severity': 'HIGH',
    },
    'STAGNANT_LOW_COMPLIANCE': {
        'name': 'Estancamiento en cumplimiento bajo',
        'description': (
            'El proceso tiene un score inferior al 50% y su '
            'tendencia es estable, sin señales de mejora.'
        ),
        'severity': 'MEDIUM',
    },
    'HIGH_NPN_RISK': {
        'name': 'Riesgo con NPN muy elevado',
        'description': (
            'El proceso tiene al menos un riesgo con NPN superior '
            'a 200, indicando alta prioridad de tratamiento.'
        ),
        'severity': 'HIGH',
    },
    'NO_RECENT_AUDIT': {
        'name': 'Proceso sin auditoría reciente',
        'description': (
            'El proceso solo tiene una auditoría registrada, '
            'insuficiente para evaluar tendencias.'
        ),
        'severity': 'LOW',
    },
}

# Umbrales configurables
THRESHOLD_SCORE_DROP = 20.0       # Puntos de caída para SCORE_DROP
THRESHOLD_CRITICAL_SCORE = 25.0   # Score máximo para CRITICAL_COMPLIANCE
THRESHOLD_HIGH_RISK_SCORE = 2.5   # risk_score mínimo para HIGH_RISK
THRESHOLD_MIN_COVERAGE = 3        # Requisitos mínimos para cobertura adecuada
THRESHOLD_HIGH_NPN = 200          # NPN mínimo para HIGH_NPN_RISK


# ─────────────────────────────────────────────
# Detectores individuales
# ─────────────────────────────────────────────

def _detect_score_drops(snapshot_dataset):
    """
    Detecta caídas bruscas de score entre auditorías consecutivas
    del mismo proceso.
    """
    anomalies = []

    # Agrupar snapshots por proceso
    by_process = {}
    for snap in snapshot_dataset:
        pid = snap['process_id']
        if pid not in by_process:
            by_process[pid] = []
        by_process[pid].append(snap)

    for process_id, snaps in by_process.items():
        if len(snaps) < 2:
            continue

        # Ordenar por fecha
        snaps_sorted = sorted(snaps, key=lambda x: x['calculated_at'])

        for i in range(1, len(snaps_sorted)):
            prev = snaps_sorted[i - 1]
            curr = snaps_sorted[i]
            delta = curr['score'] - prev['score']

            if delta <= -THRESHOLD_SCORE_DROP:
                anomalies.append({
                    'anomaly_type': 'SCORE_DROP',
                    'process_id': process_id,
                    'process_name': curr['process_name'],
                    'severity': ANOMALY_TYPES['SCORE_DROP']['severity'],
                    'description': ANOMALY_TYPES['SCORE_DROP']['description'],
                    'details': {
                        'previous_score': prev['score'],
                        'current_score': curr['score'],
                        'score_delta': round(delta, 1),
                        'previous_snapshot_id': prev['snapshot_id'],
                        'current_snapshot_id': curr['snapshot_id'],
                        'previous_date': prev['calculated_at'],
                        'current_date': curr['calculated_at'],
                    },
                })

    return anomalies


def _detect_critical_compliance(process_dataset):
    """
    Detecta procesos con score crítico en su última auditoría.
    """
    anomalies = []

    for process in process_dataset:
        if process['latest_score'] < THRESHOLD_CRITICAL_SCORE:
            anomalies.append({
                'anomaly_type': 'CRITICAL_COMPLIANCE',
                'process_id': process['process_id'],
                'process_name': process['process_name'],
                'severity': ANOMALY_TYPES['CRITICAL_COMPLIANCE']['severity'],
                'description': ANOMALY_TYPES['CRITICAL_COMPLIANCE']['description'],
                'details': {
                    'latest_score': process['latest_score'],
                    'latest_category': process['latest_category'],
                    'threshold': THRESHOLD_CRITICAL_SCORE,
                },
            })

    return anomalies


def _detect_high_risk_low_coverage(process_dataset):
    """
    Detecta procesos con alto riesgo pero poca cobertura normativa.
    """
    anomalies = []

    for process in process_dataset:
        if (
            process['risk_score'] >= THRESHOLD_HIGH_RISK_SCORE and
            process['normative_coverage'] < THRESHOLD_MIN_COVERAGE
        ):
            anomalies.append({
                'anomaly_type': 'HIGH_RISK_LOW_COVERAGE',
                'process_id': process['process_id'],
                'process_name': process['process_name'],
                'severity': ANOMALY_TYPES['HIGH_RISK_LOW_COVERAGE']['severity'],
                'description': ANOMALY_TYPES['HIGH_RISK_LOW_COVERAGE']['description'],
                'details': {
                    'risk_score': process['risk_score'],
                    'normative_coverage': process['normative_coverage'],
                    'threshold_risk': THRESHOLD_HIGH_RISK_SCORE,
                    'threshold_coverage': THRESHOLD_MIN_COVERAGE,
                },
            })

    return anomalies


def _detect_repeated_findings(process_dataset):
    """
    Detecta procesos con no conformidades mayores repetidas.
    """
    anomalies = []

    for process in process_dataset:
        if process['nc_mayor_count'] > 1:
            anomalies.append({
                'anomaly_type': 'REPEATED_FINDINGS',
                'process_id': process['process_id'],
                'process_name': process['process_name'],
                'severity': ANOMALY_TYPES['REPEATED_FINDINGS']['severity'],
                'description': ANOMALY_TYPES['REPEATED_FINDINGS']['description'],
                'details': {
                    'nc_mayor_count': process['nc_mayor_count'],
                    'nc_menor_count': process['nc_menor_count'],
                    'num_audits': process['num_audits'],
                },
            })

    return anomalies


def _detect_stagnant_low_compliance(process_dataset):
    """
    Detecta procesos con score bajo y sin tendencia de mejora.
    """
    anomalies = []

    for process in process_dataset:
        if (
            process['latest_score'] < 50.0 and
            process['trend_value'] == 0 and
            process['num_audits'] >= 2
        ):
            anomalies.append({
                'anomaly_type': 'STAGNANT_LOW_COMPLIANCE',
                'process_id': process['process_id'],
                'process_name': process['process_name'],
                'severity': ANOMALY_TYPES['STAGNANT_LOW_COMPLIANCE']['severity'],
                'description': ANOMALY_TYPES['STAGNANT_LOW_COMPLIANCE']['description'],
                'details': {
                    'latest_score': process['latest_score'],
                    'trend': process['trend'],
                    'num_audits': process['num_audits'],
                    'avg_score': process['avg_score'],
                },
            })

    return anomalies


def _detect_high_npn_risks(risk_dataset):
    """
    Detecta riesgos con NPN muy elevado que requieren atención inmediata.
    """
    anomalies = []
    seen_processes = set()

    for risk in risk_dataset:
        if (
            risk['npn'] is not None and
            risk['npn'] > THRESHOLD_HIGH_NPN and
            risk['process_id'] not in seen_processes
        ):
            seen_processes.add(risk['process_id'])
            anomalies.append({
                'anomaly_type': 'HIGH_NPN_RISK',
                'process_id': risk['process_id'],
                'process_name': risk['process_name'],
                'severity': ANOMALY_TYPES['HIGH_NPN_RISK']['severity'],
                'description': ANOMALY_TYPES['HIGH_NPN_RISK']['description'],
                'details': {
                    'risk_id': risk['risk_id'],
                    'identified_risk': risk['identified_risk'],
                    'npn': risk['npn'],
                    'severity': risk['severity'],
                    'occurrence': risk['occurrence'],
                    'detection': risk['detection'],
                    'risk_level': risk['risk_level'],
                    'threshold_npn': THRESHOLD_HIGH_NPN,
                },
            })

    return anomalies


def _detect_no_recent_audit(process_dataset):
    """
    Detecta procesos con insuficiente histórico de auditorías.
    """
    anomalies = []

    for process in process_dataset:
        if process['num_audits'] < 2:
            anomalies.append({
                'anomaly_type': 'NO_RECENT_AUDIT',
                'process_id': process['process_id'],
                'process_name': process['process_name'],
                'severity': ANOMALY_TYPES['NO_RECENT_AUDIT']['severity'],
                'description': ANOMALY_TYPES['NO_RECENT_AUDIT']['description'],
                'details': {
                    'num_audits': process['num_audits'],
                    'latest_score': process['latest_score'],
                },
            })

    return anomalies


# ─────────────────────────────────────────────
# Motor principal
# ─────────────────────────────────────────────

def detect_anomalies(standard_id=None):
    """
    Ejecuta todos los detectores de anomalías y devuelve
    un informe consolidado ordenado por severidad.

    Parámetros:
    - standard_id: filtrar por norma (opcional)

    Retorna un dict con el resumen y la lista de anomalías detectadas.
    """
    process_data = get_process_dataset(standard_id=standard_id)
    snapshot_data = get_snapshot_dataset(standard_id=standard_id)
    risk_data = get_risk_dataset()

    if not process_data:
        return {
            'error': 'No hay datos históricos disponibles.'
        }

    # Ejecutar todos los detectores
    all_anomalies = []
    all_anomalies.extend(_detect_score_drops(snapshot_data))
    all_anomalies.extend(_detect_critical_compliance(process_data))
    all_anomalies.extend(_detect_high_risk_low_coverage(process_data))
    all_anomalies.extend(_detect_repeated_findings(process_data))
    all_anomalies.extend(_detect_stagnant_low_compliance(process_data))
    all_anomalies.extend(_detect_high_npn_risks(risk_data))
    all_anomalies.extend(_detect_no_recent_audit(process_data))

    # Ordenar por severidad
    severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    all_anomalies.sort(
        key=lambda x: severity_order.get(x['severity'], 3)
    )

    # Resumen
    high_count = sum(1 for a in all_anomalies if a['severity'] == 'HIGH')
    medium_count = sum(1 for a in all_anomalies if a['severity'] == 'MEDIUM')
    low_count = sum(1 for a in all_anomalies if a['severity'] == 'LOW')

    # Procesos afectados únicos
    affected_processes = len(set(a['process_id'] for a in all_anomalies))

    # Tipos de anomalía detectados
    detected_types = list(set(a['anomaly_type'] for a in all_anomalies))

    return {
        'success': True,
        'model_info': {
            'type': 'RULE_BASED',
            'version': '1.0',
            'description': (
                'Detector de anomalías basado en reglas y umbrales '
                'deterministas. Prototipo exploratorio — no validado '
                'estadísticamente.'
            ),
            'thresholds': {
                'score_drop': THRESHOLD_SCORE_DROP,
                'critical_score': THRESHOLD_CRITICAL_SCORE,
                'high_risk_score': THRESHOLD_HIGH_RISK_SCORE,
                'min_coverage': THRESHOLD_MIN_COVERAGE,
                'high_npn': THRESHOLD_HIGH_NPN,
            },
            'anomaly_types_evaluated': list(ANOMALY_TYPES.keys()),
        },
        'summary': {
            'total_anomalies': len(all_anomalies),
            'high_severity': high_count,
            'medium_severity': medium_count,
            'low_severity': low_count,
            'affected_processes': affected_processes,
            'detected_types': detected_types,
        },
        'anomalies': all_anomalies,
    }