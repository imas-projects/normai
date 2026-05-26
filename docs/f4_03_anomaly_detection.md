# Prototipo de Detección de Anomalías sobre Datos de Calidad

**Issue:** F4-03 — Prototipo de detección de anomalías sobre datos de calidad  
**Fase:** FASE 4 — Analítica Predictiva  
**Dependencias:** F4-01 (Dataset histórico), F4-02 (Predicción de riesgo)  
**Impacto arquitectónico:** Bajo — nuevo módulo de detección, un endpoint  

---

## Tabla de Contenidos

1. [Contexto y Enfoque](#1-contexto-y-enfoque)
2. [Definición de Anomalías](#2-definición-de-anomalías)
3. [Detectores Implementados](#3-detectores-implementados)
4. [Implementación](#4-implementación)
5. [Endpoint Implementado](#5-endpoint-implementado)
6. [Verificación Funcional](#6-verificación-funcional)
7. [Limitaciones y Evolución Futura](#7-limitaciones-y-evolución-futura)

---

## 1. Contexto y Enfoque

### 1.1 Limitación del volumen de datos

Al igual que en F4-02, el volumen de datos históricos disponibles
(10 snapshots) es insuficiente para aplicar algoritmos estadísticos
de detección de anomalías como Isolation Forest, DBSCAN o z-score,
que requieren distribuciones de datos suficientemente grandes para
establecer qué es "normal".

### 1.2 Enfoque adoptado — Detección basada en reglas

Se optó por un detector de anomalías basado en reglas y umbrales
deterministas. Cada regla define explícitamente qué constituye
una anomalía en términos de negocio de calidad, con umbrales
justificados y configurables.

Este enfoque garantiza que las anomalías detectadas sean siempre
explicables en términos de negocio, sin cajas negras estadísticas.

---

## 2. Definición de Anomalías

Se definieron 7 tipos de anomalía relevantes para un sistema de
gestión de calidad aeroespacial:

| Tipo | Severidad | Descripción |
|------|-----------|-------------|
| `SCORE_DROP` | HIGH | Caída > 20 puntos entre auditorías consecutivas |
| `CRITICAL_COMPLIANCE` | HIGH | Score < 25% en la última auditoría |
| `HIGH_RISK_LOW_COVERAGE` | MEDIUM | Risk score ≥ 2.5 con < 3 requisitos asignados |
| `REPEATED_FINDINGS` | HIGH | Más de 1 NC_MAYOR en el historial |
| `STAGNANT_LOW_COMPLIANCE` | MEDIUM | Score < 50% con tendencia STABLE y ≥ 2 auditorías |
| `HIGH_NPN_RISK` | HIGH | Al menos un riesgo con NPN > 200 |
| `NO_RECENT_AUDIT` | LOW | Proceso con menos de 2 auditorías registradas |

### 2.1 Umbrales configurables

Todos los umbrales están definidos como constantes en la parte
superior del módulo, facilitando su ajuste sin modificar la lógica:

```python
THRESHOLD_SCORE_DROP = 20.0
THRESHOLD_CRITICAL_SCORE = 25.0
THRESHOLD_HIGH_RISK_SCORE = 2.5
THRESHOLD_MIN_COVERAGE = 3
THRESHOLD_HIGH_NPN = 200
```

---

## 3. Detectores Implementados

### 3.1 `_detect_score_drops`

Compara snapshots consecutivos del mismo proceso ordenados
cronológicamente. Detecta caídas brutas superiores al umbral.

**Señal:** `score_actual - score_anterior < -20`

### 3.2 `_detect_critical_compliance`

Evalúa el score más reciente de cada proceso contra el umbral crítico.

**Señal:** `latest_score < 25%`

### 3.3 `_detect_high_risk_low_coverage`

Cruza el nivel de riesgo agregado del proceso con su cobertura
normativa. Un proceso con alto riesgo y pocos requisitos asignados
indica una brecha de gestión.

**Señal:** `risk_score ≥ 2.5` AND `normative_coverage < 3`

### 3.4 `_detect_repeated_findings`

Cuenta las NC_MAYOR acumuladas en el historial del proceso.
Más de una NC_MAYOR indica un problema sistémico no resuelto.

**Señal:** `nc_mayor_count > 1`

### 3.5 `_detect_stagnant_low_compliance`

Detecta procesos que llevan varias auditorías con score bajo
sin mostrar mejora. Requiere al menos 2 auditorías para evitar
falsos positivos.

**Señal:** `latest_score < 50%` AND `trend == STABLE` AND `num_audits ≥ 2`

### 3.6 `_detect_high_npn_risks`

Analiza el dataset de riesgos identificando evaluaciones con
NPN (Número de Prioridad de Riesgo) superior al umbral.

**Señal:** `NPN = severidad × ocurrencia × detección > 200`

### 3.7 `_detect_no_recent_audit`

Identifica procesos con histórico insuficiente para evaluar
tendencias, señalando la necesidad de planificar más auditorías.

**Señal:** `num_audits < 2`

---

## 4. Implementación

### 4.1 Módulo creado

audits/anomaly_detector.py

### 4.2 Función principal

```python
def detect_anomalies(standard_id=None):
    """
    Ejecuta todos los detectores y devuelve el informe consolidado
    ordenado por severidad (HIGH → MEDIUM → LOW).
    """
```

### 4.3 Orden de severidad en la salida

Las anomalías se devuelven ordenadas por severidad descendente:
HIGH primero, LOW último. Dentro de cada nivel de severidad se
mantiene el orden de detección.

---

## 5. Endpoint Implementado

### GET /audits/get-anomaly-detection/

Ejecuta todos los detectores y devuelve el informe consolidado.

**Parámetro opcional:** `?standard_id=N` para filtrar por norma.

**Estructura de respuesta:**
```json
{
    "success": true,
    "model_info": {
        "type": "RULE_BASED",
        "version": "1.0",
        "thresholds": {
            "score_drop": 20.0,
            "critical_score": 25.0,
            "high_risk_score": 2.5,
            "min_coverage": 3,
            "high_npn": 200
        },
        "anomaly_types_evaluated": [
            "SCORE_DROP", "CRITICAL_COMPLIANCE",
            "HIGH_RISK_LOW_COVERAGE", "REPEATED_FINDINGS",
            "STAGNANT_LOW_COMPLIANCE", "HIGH_NPN_RISK",
            "NO_RECENT_AUDIT"
        ]
    },
    "summary": {
        "total_anomalies": 4,
        "high_severity": 4,
        "medium_severity": 0,
        "low_severity": 0,
        "affected_processes": 4,
        "detected_types": ["HIGH_NPN_RISK"]
    },
    "anomalies": [
        {
            "anomaly_type": "HIGH_NPN_RISK",
            "process_id": 2,
            "process_name": "Integración de Sistemas Eléctricos",
            "severity": "HIGH",
            "description": "El proceso tiene al menos un riesgo con NPN superior a 200...",
            "details": {
                "risk_id": 6,
                "identified_risk": "Error en la conexión...",
                "npn": 360,
                "severity": 4,
                "occurrence": 9,
                "detection": 10,
                "risk_level": "High",
                "threshold_npn": 200
            }
        },
        ...
    ]
}
```

---

## 6. Verificación Funcional

GET http://127.0.0.1:8000/audits/get-anomaly-detection/
total_anomalies: 4
high_severity: 4
medium_severity: 0
low_severity: 0
affected_processes: 4
detected_types: ["HIGH_NPN_RISK"]

Las 4 anomalías detectadas corresponden a procesos con riesgos
de NPN superior a 200, todos de severidad HIGH. El resultado
es coherente con los datos disponibles:

- Los datos de prueba incluyen riesgos con NPN elevado
- No hay caídas bruscas de score entre auditorías consecutivas
  que superen el umbral de 20 puntos
- No hay procesos con score crítico persistente en la última
  auditoría (score mínimo actual: 25%)
- No hay NC_MAYOR repetidas (solo 2 hallazgos en total)

---

## 7. Limitaciones y Evolución Futura

### 7.1 Limitaciones actuales

**Umbrales no calibrados estadísticamente:**
Los umbrales actuales son juicios expertos sobre lo que constituye
una anomalía en calidad aeroespacial. Con más datos históricos,
podrían calibrarse estadísticamente usando percentiles o
desviaciones típicas.

**Sin detección de anomalías multivariante:**
El detector actual evalúa cada variable de forma independiente.
Un detector más avanzado cruzaría múltiples variables simultáneamente
para detectar combinaciones anómalas que individualmente parecen
normales.

**Sin contexto temporal avanzado:**
No se detectan anomalías de estacionalidad ni patrones cíclicos,
que requieren series temporales más largas.

### 7.2 Evolución hacia métodos estadísticos

Cuando el histórico supere los 50-100 snapshots, el detector
puede evolucionar hacia:

- **Z-score** por proceso para detectar auditorías con scores
  estadísticamente atípicos respecto al histórico del propio proceso
- **Isolation Forest** para detección multivariante de combinaciones
  anómalas de variables
- **Control charts** (cartas de control) para monitorización
  continua del cumplimiento con límites de control estadísticos

El módulo `anomaly_detector.py` está diseñado para que esta
evolución sea un cambio interno sin impacto en la API.