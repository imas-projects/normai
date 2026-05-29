# Implementación de Vistas Ejecutivas de Cumplimiento y Riesgo

**Issue:** F5-02 — Implementación de vistas ejecutivas de cumplimiento y riesgo  
**Fase:** FASE 5 — Dashboard Ejecutivo  
**Dependencias:** F5-01 (Modelo de información del dashboard)  
**Impacto arquitectónico:** Bajo — nuevo módulo de agregación, un endpoint  

---

## Tabla de Contenidos

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Arquitectura de la Solución](#2-arquitectura-de-la-solución)
3. [Bloques Implementados](#3-bloques-implementados)
4. [Endpoint Implementado](#4-endpoint-implementado)
5. [Verificación Funcional](#5-verificación-funcional)
6. [Decisiones de Diseño](#6-decisiones-de-diseño)

---

## 1. Contexto y Objetivo

### 1.1 Problema de Partida

Tras F5-01 el sistema tenía definido el modelo de información del
dashboard ejecutivo. Sin embargo, los datos estaban dispersos en
múltiples endpoints independientes:

- `/audits/get-standard-compliance/<id>/` — cumplimiento por norma
- `/audits/get-risk-predictions/` — predicciones de riesgo
- `/audits/get-anomaly-detection/` — anomalías detectadas
- `/audits/get-analytics-dataset/` — dataset histórico

Para obtener una vista ejecutiva completa había que hacer 4 llamadas
separadas y ensamblar los resultados manualmente.

### 1.2 Objetivo

Implementar un endpoint único `/audits/executive-dashboard/` que
agregue todos los indicadores definidos en F5-01 en una sola
respuesta estructurada, lista para consumir por cualquier capa
de visualización.

---

## 2. Arquitectura de la Solución

### 2.1 Módulo creado

audits/executive_dashboard.py

### 2.2 Función principal

```python
def get_executive_dashboard(standard_id=None):
    """
    Consolida indicadores de cumplimiento, riesgo, auditorías
    y señales predictivas en una única vista ejecutiva.
    """
```

### 2.3 Fuentes de datos consumidas

executive_dashboard.py
├── analytics_dataset.get_process_dataset()     → cumplimiento por proceso
├── analytics_dataset.get_risk_dataset()        → riesgos por proceso
├── risk_predictor.predict_non_conformity_risk() → predicciones
├── anomaly_detector.detect_anomalies()          → anomalías
└── models: AnnualPlan, Findings                → auditorías y hallazgos

---

## 3. Bloques Implementados

### Bloque 1 — Resumen Ejecutivo

Indicadores globales del sistema en una sola línea de lectura:

```json
"executive_summary": {
    "global_compliance_score": 66.2,
    "global_compliance_category": "PARTIAL",
    "compliance_trend": "IMPROVING",
    "total_audits": 10,
    "processes_audited": 5,
    "standard_filter": null
}
```

**Lógica de tendencia global:** Si hay más procesos IMPROVING que
DECLINING → IMPROVING. Si hay más DECLINING → DECLINING. En caso
contrario → STABLE.

### Bloque 2 — Cumplimiento

Distribución de procesos por categoría, ranking de peores y mejores
procesos y listado completo con tendencias:

```json
"compliance_block": {
    "by_category": {
        "EXCELLENT": 0, "GOOD": 2, "PARTIAL": 2, "LOW": 1, "CRITICAL": 0
    },
    "worst_processes": [...],
    "best_processes": [...],
    "all_processes": [...],
    "improving_count": 3,
    "declining_count": 0,
    "stable_count": 0
}
```

### Bloque 3 — Riesgos

Distribución de riesgos por nivel, NPN máximo y medio, procesos
con riesgo alto y top 5 riesgos por NPN:

```json
"risk_block": {
    "total_high_risks": 6,
    "total_moderate_risks": 3,
    "total_low_risks": 11,
    "max_npn": 600,
    "avg_npn": 140.9,
    "processes_with_high_risk_count": 3,
    "top_risks_by_npn": [...]
}
```

### Bloque 4 — Auditorías y Hallazgos

Resumen de planes de auditoría realizados y hallazgos registrados:

```json
"audit_block": {
    "total_audits": 10,
    "total_findings": 2,
    "nc_mayor_total": 2,
    "nc_menor_total": 0,
    "oportunidad_total": 0,
    "processes_without_recent_audit": 0,
    "avg_audits_per_process": 1.0
}
```

### Bloque 5 — Alertas y Predicciones

Anomalías detectadas y predicciones de riesgo de no conformidad:

```json
"alert_block": {
    "total_anomalies": 3,
    "high_severity_anomalies": 3,
    "medium_severity_anomalies": 0,
    "anomaly_types_detected": ["HIGH_NPN_RISK"],
    "top_anomalies": [...],
    "high_risk_predictions_count": 0,
    "medium_risk_predictions_count": 0,
    "top_risk_predictions": [...]
}
```

---

## 4. Endpoint Implementado

### GET /audits/executive-dashboard/

Devuelve el dashboard ejecutivo completo.

**Parámetro opcional:** `?standard_id=N` para filtrar por norma.

**Casos de error:**
- Sin datos de cumplimiento disponibles → error con mensaje explicativo
- Excepción inesperada → error 500

---

## 5. Verificación Funcional

GET http://127.0.0.1:8000/audits/executive-dashboard/
success: true
executive_summary.global_compliance_score: 66.2% ✅
executive_summary.global_compliance_category: PARTIAL ✅
executive_summary.compliance_trend: IMPROVING ✅
compliance_block.by_category: {GOOD:2, PARTIAL:2, LOW:1} ✅
risk_block.total_high_risks: 6 ✅
risk_block.max_npn: 600 ✅
audit_block.total_audits: 10 ✅
alert_block.total_anomalies: 3 ✅


---

## 6. Decisiones de Diseño

### 6.1 Módulo separado executive_dashboard.py

La lógica de agregación se implementó en un módulo separado,
siguiendo el patrón establecido en Fases 3 y 4. Esto permite
invocar el dashboard desde tests, scripts o tareas programadas
sin simular una petición HTTP.

### 6.2 Endpoint único vs. múltiples endpoints

Se optó por un único endpoint que devuelve todos los bloques en
lugar de mantener los endpoints individuales de cada bloque.
Esto simplifica el consumo desde el frontend y reduce el número
de llamadas necesarias para construir la vista ejecutiva.

Los endpoints individuales siguen disponibles para consultas
específicas cuando solo se necesita un bloque concreto.

### 6.3 Filtrado por standard_id

El parámetro `standard_id` se propaga a todas las funciones
internas, garantizando coherencia: si se filtra por ISO 9001,
todos los bloques — cumplimiento, riesgos, anomalías y
predicciones — muestran solo datos de procesos relevantes
para esa norma.