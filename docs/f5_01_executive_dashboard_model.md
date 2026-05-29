# Modelo de Información del Dashboard Ejecutivo

**Issue:** F5-01 — Diseño del modelo de información del dashboard ejecutivo  
**Fase:** FASE 5 — Dashboard Ejecutivo  
**Dependencias:** F3-02 (ComplianceSnapshot), F3-03 (Evolución temporal), F4-01 (Dataset histórico)  
**Impacto:** Documental — define la base conceptual para F5-02 y F5-03  

---

## Tabla de Contenidos

1. [Objetivo del Dashboard](#1-objetivo-del-dashboard)
2. [Preguntas de Negocio](#2-preguntas-de-negocio)
3. [Indicadores Seleccionados](#3-indicadores-seleccionados)
4. [Fuentes de Datos](#4-fuentes-de-datos)
5. [Agregaciones Necesarias](#5-agregaciones-necesarias)
6. [Bloques de Información](#6-bloques-de-información)
7. [Limitaciones](#7-limitaciones)
8. [Criterio de Aceptación](#8-criterio-de-aceptación)
9. [Ejemplos de Salida Esperada](#9-ejemplos-de-salida-esperada)

---

## 1. Objetivo del Dashboard

El dashboard ejecutivo de NormAI tiene como objetivo proporcionar
a la dirección una visión consolidada, clara y accionable del estado
del sistema de gestión de calidad de la organización.

No es un panel de detalle técnico — es una herramienta de seguimiento
estratégico que responde a preguntas de alto nivel sobre el estado
del cumplimiento normativo, la evolución de los riesgos y la eficacia
del sistema de auditorías internas.

### Perfil de usuario objetivo

**Dirección y responsables de calidad** que necesitan:
- Saber en qué estado está el sistema de gestión sin revisar
  cada auditoría individualmente
- Identificar qué procesos o áreas requieren atención inmediata
- Tomar decisiones sobre priorización de recursos y acciones correctivas
- Hacer seguimiento de la evolución del sistema en el tiempo

---

## 2. Preguntas de Negocio

El dashboard debe ser capaz de responder estas preguntas concretas:

### Cumplimiento normativo
1. ¿Cuál es el nivel de cumplimiento global de la organización con
   ISO 9001:2015 y AS9100 Rev D?
2. ¿Qué procesos tienen el peor nivel de cumplimiento?
3. ¿El cumplimiento está mejorando, empeorando o estancado?
4. ¿Cuántos procesos están en estado crítico o bajo?

### Riesgos
5. ¿Cuántos riesgos de nivel alto tiene la organización?
6. ¿Qué procesos concentran más riesgos de nivel alto?
7. ¿Hay procesos con riesgo alto y bajo cumplimiento simultáneamente?

### Auditorías
8. ¿Cuántas auditorías se han realizado este año?
9. ¿Qué procesos no han sido auditados recientemente?
10. ¿Cuántas no conformidades mayores hay abiertas?

### Alertas y señales
11. ¿Hay procesos con caídas bruscas de cumplimiento?
12. ¿Hay riesgos con NPN muy elevado sin tratamiento?
13. ¿Qué procesos acumulan no conformidades repetidas?

---

## 3. Indicadores Seleccionados

### 3.1 Indicadores de cumplimiento

| Indicador | Descripción | Fuente |
|-----------|-------------|--------|
| `global_compliance_score` | Score medio de cumplimiento de todos los procesos auditados | ComplianceSnapshot |
| `global_compliance_category` | Categoría cualitativa global (EXCELLENT/GOOD/PARTIAL/LOW/CRITICAL) | ComplianceSnapshot |
| `processes_by_category` | Número de procesos en cada categoría de cumplimiento | ComplianceSnapshot |
| `compliance_trend` | Tendencia global del cumplimiento (IMPROVING/STABLE/DECLINING) | ComplianceSnapshot |
| `worst_processes` | Los 3 procesos con peor score de cumplimiento | ComplianceSnapshot |
| `best_processes` | Los 3 procesos con mejor score de cumplimiento | ComplianceSnapshot |

### 3.2 Indicadores de riesgo

| Indicador | Descripción | Fuente |
|-----------|-------------|--------|
| `total_high_risks` | Número total de riesgos de nivel alto | RiskEvaluation |
| `total_moderate_risks` | Número total de riesgos de nivel moderado | RiskEvaluation |
| `processes_with_high_risk` | Procesos que tienen al menos un riesgo alto | RiskEvaluation |
| `max_npn` | NPN máximo registrado en la organización | RiskEvaluation |
| `avg_risk_score` | Score de riesgo medio por proceso | RiskEvaluation |

### 3.3 Indicadores de auditorías

| Indicador | Descripción | Fuente |
|-----------|-------------|--------|
| `total_audits` | Total de planes de auditoría realizados | AnnualPlan |
| `total_findings` | Total de hallazgos registrados | Findings |
| `nc_mayor_total` | Total de no conformidades mayores | Findings |
| `nc_menor_total` | Total de no conformidades menores | Findings |
| `processes_without_recent_audit` | Procesos con menos de 2 auditorías | ComplianceSnapshot |

### 3.4 Indicadores predictivos

| Indicador | Descripción | Fuente |
|-----------|-------------|--------|
| `high_risk_predictions` | Procesos con riesgo de no conformidad HIGH | risk_predictor |
| `total_anomalies` | Total de anomalías detectadas | anomaly_detector |
| `high_severity_anomalies` | Anomalías de severidad alta | anomaly_detector |

---

## 4. Fuentes de Datos

Todos los indicadores del dashboard se obtienen de datos ya
disponibles en el sistema, sin necesidad de modelos nuevos:

| Módulo | Datos que aporta |
|--------|-----------------|
| `ComplianceSnapshot` | Score, categoría, tendencia e histórico de cumplimiento |
| `Findings` | No conformidades y hallazgos de auditoría |
| `RiskIdentification` + `RiskEvaluation` | Riesgos identificados y evaluados por proceso |
| `AnnualPlan` | Planes de auditoría realizados |
| `analytics_dataset.py` | Dataset agregado por proceso (F4-01) |
| `compliance_engine.py` | Cálculo y consulta de snapshots (F3-02) |
| `risk_predictor.py` | Predicciones de riesgo de no conformidad (F4-02) |
| `anomaly_detector.py` | Anomalías detectadas (F4-03) |

---

## 5. Agregaciones Necesarias

### 5.1 Score global de cumplimiento

Media ponderada de los scores más recientes de cada proceso,
ponderada por número de requisitos:

score_global = Σ(score_proceso × n_requisitos) / Σ(n_requisitos)

Esta fórmula ya está implementada en `get_compliance_by_standard()`
de `compliance_engine.py`.

### 5.2 Distribución de procesos por categoría

Conteo de procesos en cada categoría de cumplimiento basado
en el snapshot más reciente de cada proceso:

{
EXCELLENT: n,
GOOD: n,
PARTIAL: n,
LOW: n,
CRITICAL: n
}

### 5.3 Tendencia global

Porcentaje de procesos con tendencia IMPROVING, STABLE y DECLINING
sobre el total de procesos con al menos 2 snapshots.

### 5.4 Distribución de riesgos

Conteo de evaluaciones de riesgo por nivel (High/Moderate/Low)
y cálculo del NPN máximo y medio.

### 5.5 Resumen de hallazgos

Suma de NC_MAYOR, NC_MENOR y OPORTUNIDAD_MEJORA de todos los
planes de auditoría registrados.

---

## 6. Bloques de Información

El dashboard se organiza en cuatro bloques principales:

### Bloque 1 — Resumen Ejecutivo
Vista rápida del estado global del sistema.

┌──────────────────────────────────────────────────────┐
│  Score Global    Categoría    Tendencia    Auditorías│
│    66.2%          PARTIAL     IMPROVING       10     │
└──────────────────────────────────────────────────────┘

### Bloque 2 — Cumplimiento por Proceso
Estado de cumplimiento de cada proceso con su categoría y tendencia.

┌──────────────────────────────────────────────────────┐
│ Proceso                  Score   Cat.    Tendencia   │
│ Montaje Fuselaje         62.5%   PARTIAL IMPROVING   │
│ Control Documental       81.2%   GOOD    IMPROVING   │
│ Integración Eléctrica    50.0%   PARTIAL IMPROVING   │
│ Gestión Proveedores      75.0%   GOOD    IMPROVING   │
│ Inspección NDT           25.0%   LOW     —           │
└──────────────────────────────────────────────────────┘

### Bloque 3 — Riesgos
Distribución de riesgos por nivel y procesos más expuestos.

┌─────────────────────────────────────────────────────┐
│  Riesgos Alto    Moderado    Bajo    NPN máximo      │
│      8              12        5         600          │
└─────────────────────────────────────────────────────┘

### Bloque 4 — Alertas y Señales
Anomalías detectadas y predicciones de riesgo alto.

┌─────────────────────────────────────────────────────┐
│  Anomalías HIGH    NC_MAYOR    Predicciones HIGH     │
│       4               2              1               │
└─────────────────────────────────────────────────────┘

---

## 7. Limitaciones

### Volumen de datos
El dashboard actual se alimenta de 10 snapshots y datos de prueba.
En producción, los indicadores ganarán precisión y representatividad
a medida que se realicen más auditorías reales.

### Acciones correctivas
El modelo `CorrectiveAction` existe en el sistema pero no tiene
registros actualmente. El bloque de seguimiento de acciones
correctivas queda pendiente para cuando existan datos reales.

### Datos en tiempo real
El dashboard no es en tiempo real — refleja el estado de los
snapshots calculados. Para actualizar los indicadores hay que
ejecutar `calculate-compliance` para los planes nuevos.

### Sin capa visual
F5-01 define el modelo de información. La capa visual
(HTML/JavaScript) se implementa en F5-02.

---

## 8. Criterio de Aceptación

La issue F5-01 se considera completada cuando:

- ✅ Están definidas las preguntas de negocio que debe responder
  el dashboard
- ✅ Están seleccionados y justificados los indicadores clave
- ✅ Están identificadas las fuentes de datos para cada indicador
- ✅ Están definidas las agregaciones necesarias
- ✅ Está descrita la estructura de bloques del dashboard
- ✅ Están documentadas las limitaciones conocidas
- ✅ Existe una base consistente para implementar F5-02 y F5-03

---

## 9. Ejemplos de Salida Esperada

### Ejemplo de respuesta del endpoint del dashboard (F5-02)

```json
{
    "executive_summary": {
        "global_compliance_score": 66.2,
        "global_compliance_category": "PARTIAL",
        "compliance_trend": "IMPROVING",
        "total_audits": 10,
        "processes_audited": 5
    },
    "compliance_blocks": {
        "by_category": {
            "EXCELLENT": 0,
            "GOOD": 2,
            "PARTIAL": 2,
            "LOW": 1,
            "CRITICAL": 0
        },
        "worst_processes": [
            {"name": "Inspección NDT", "score": 25.0, "category": "LOW"},
            {"name": "Integración Eléctrica", "score": 50.0, "category": "PARTIAL"},
            {"name": "Montaje Fuselaje", "score": 62.5, "category": "PARTIAL"}
        ],
        "improving_processes": 3,
        "declining_processes": 0
    },
    "risk_blocks": {
        "total_high_risks": 8,
        "total_moderate_risks": 12,
        "total_low_risks": 5,
        "max_npn": 600,
        "processes_with_high_risk": 4
    },
    "audit_blocks": {
        "total_findings": 2,
        "nc_mayor_total": 2,
        "nc_menor_total": 0,
        "oportunidad_total": 0
    },
    "alert_blocks": {
        "total_anomalies": 4,
        "high_severity_anomalies": 4,
        "high_risk_predictions": 1
    }
}
```