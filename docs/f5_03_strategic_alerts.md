# Integración de Indicadores Estratégicos y Alertas

**Issue:** F5-03 — Integración de indicadores estratégicos y alertas  
**Fase:** FASE 5 — Dashboard Ejecutivo  
**Dependencias:** F5-01 (Modelo de información), F5-02 (Vistas ejecutivas)  
**Impacto arquitectónico:** Bajo — nuevo módulo de alertas, actualización del dashboard  

---

## Tabla de Contenidos

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Diseño del Sistema de Alertas](#2-diseño-del-sistema-de-alertas)
3. [Indicadores Estratégicos](#3-indicadores-estratégicos)
4. [Implementación](#4-implementación)
5. [Endpoints Implementados](#5-endpoints-implementados)
6. [Verificación Funcional](#6-verificación-funcional)
7. [Propuesta de Evolución Futura](#7-propuesta-de-evolución-futura)

---

## 1. Contexto y Objetivo

### 1.1 Estado tras F5-02

Tras F5-02 el dashboard ejecutivo consolidaba indicadores de
cumplimiento, riesgo, auditorías y señales predictivas. Sin embargo,
la capa de alertas era básica — mostraba anomalías detectadas por
F4-03 sin criterios explícitos de activación ni acciones recomendadas.

### 1.2 Objetivo de F5-03

Añadir un sistema de alertas estratégicas con criterios explícitos
de activación y acciones recomendadas, orientado a dirección, y
complementarlo con indicadores estratégicos de alto nivel que
resuman el estado de madurez del sistema de calidad.

### 1.3 Principio de diseño

> *"Conviene evitar alertas excesivas o poco interpretables que
> resten utilidad al panel."*

Se definieron 7 tipos de alerta máximos, cada una con:
- Criterio de activación explícito y medible
- Descripción en lenguaje de negocio
- Acción recomendada concreta

---

## 2. Diseño del Sistema de Alertas

### 2.1 Alertas definidas

| Alert ID | Severidad | Criterio de Activación |
|----------|-----------|----------------------|
| `CRITICAL_PROCESS` | CRITICAL | Algún proceso con score < 25% |
| `GLOBAL_SCORE_LOW` | HIGH | Score medio global < 50% |
| `DECLINING_PROCESSES` | HIGH | Hay procesos con tendencia DECLINING |
| `HIGH_NPN_UNADDRESSED` | HIGH | Algún riesgo con NPN > 300 |
| `NC_MAYOR_ACCUMULATED` | MEDIUM | Hay NC_MAYOR registradas sin resolver |
| `PROCESSES_NOT_AUDITED` | MEDIUM | Procesos con menos de 2 auditorías |
| `ALL_PROCESSES_COMPLIANT` | INFO | Todos los procesos con score ≥ 70% |

### 2.2 Estructura de una alerta activa

```json
{
    "alert_id": "HIGH_NPN_UNADDRESSED",
    "name": "Riesgos con NPN crítico sin tratamiento",
    "description": "Hay riesgos con NPN superior a 300...",
    "action": "Activar plan de tratamiento de riesgo...",
    "severity": "HIGH",
    "color": "orange",
    "active": true,
    "affected_count": 3,
    "affected_items": [...]
}
```

Cada alerta incluye:
- `action` — qué debe hacer el responsable
- `affected_items` — qué procesos o riesgos la originan
- `color` — para facilitar la visualización (red/orange/yellow/green)

### 2.3 Umbrales configurables

```python
THRESHOLD_CRITICAL_SCORE = 25.0
THRESHOLD_LOW_GLOBAL_SCORE = 50.0
THRESHOLD_GOOD_SCORE = 70.0
THRESHOLD_HIGH_NPN = 300
THRESHOLD_MIN_AUDITS = 2
```

---

## 3. Indicadores Estratégicos

Se implementaron 6 indicadores estratégicos de alto nivel:

| Indicador | Descripción | Fórmula |
|-----------|-------------|---------|
| `maturity_index` | Índice de madurez del sistema (0-100) | score×0.5 + cobertura×0.3 + tendencia×0.2 |
| `maturity_label` | Etiqueta del índice (Alto/Medio/Bajo) | ≥70→Alto, ≥40→Medio, <40→Bajo |
| `avg_checklist_compliance_rate` | Tasa media de conformidad en checklists | Media de checklist_compliance_rate |
| `risk_exposure_rate` | Porcentaje de riesgos de nivel alto | high_risks/total_risks × 100 |
| `processes_under_control` | Procesos con score ≥ 70% | Conteo directo |
| `control_rate` | Porcentaje de procesos bajo control | processes_under_control/total × 100 |
| `audit_coverage_rate` | Cobertura de auditorías (procesos con ≥2) | Media de min(audits/2, 1.0) × 100 |

### 3.1 Índice de madurez

El índice de madurez es el indicador estratégico principal. Combina
tres dimensiones en una sola métrica:

- **Cumplimiento (50%)** — score medio de todos los procesos
- **Cobertura de auditorías (30%)** — qué proporción de procesos
  tiene cobertura suficiente (≥2 auditorías)
- **Tendencia (20%)** — dirección del sistema (mejorando/estable/empeorando)

---

## 4. Implementación

### 4.1 Módulo creado

audits/strategic_alerts.py

### 4.2 Actualización de executive_dashboard.py

Se añadió el `strategic_block` al dashboard ejecutivo integrando
alertas e indicadores estratégicos:

```python
from .strategic_alerts import evaluate_strategic_alerts

strategic_result = evaluate_strategic_alerts(standard_id=standard_id)
strategic_block = {
    'alerts': strategic_result.get('alerts', []),
    'alerts_summary': strategic_result.get('summary', {}),
    'strategic_indicators': strategic_result.get('strategic_indicators', {}),
}
```

---

## 5. Endpoints Implementados

### GET /audits/get-strategic-alerts/

Devuelve solo el bloque de alertas estratégicas e indicadores,
para consultas ligeras sin necesidad del dashboard completo.

**Parámetro opcional:** `?standard_id=N`

**Respuesta:**
```json
{
    "success": true,
    "summary": {
        "total_active_alerts": 1,
        "critical_alerts": 0,
        "high_alerts": 1,
        "medium_alerts": 0,
        "info_alerts": 0,
        "requires_immediate_action": true
    },
    "alerts": [...],
    "strategic_indicators": {
        "maturity_index": 83.1,
        "maturity_label": "Alto",
        "avg_checklist_compliance_rate": 63.1,
        "risk_exposure_rate": 30.0,
        "processes_under_control": 4,
        "control_rate": 40.0,
        "audit_coverage_rate": 100.0
    }
}
```

### GET /audits/executive-dashboard/

Ahora incluye el `strategic_block` con alertas e indicadores
estratégicos integrados junto a los bloques anteriores.

---

## 6. Verificación Funcional

### GET /audits/get-strategic-alerts/

total_active_alerts: 1
high_alerts: 1
requires_immediate_action: true
alerta activa: HIGH_NPN_UNADDRESSED ✅
maturity_index: 83.1 (Alto) ✅
control_rate: 40.0% ✅
audit_coverage_rate: 100.0% ✅

### GET /audits/executive-dashboard/

strategic_block.alerts: [HIGH_NPN_UNADDRESSED] ✅
strategic_block.strategic_indicators.maturity_index: 83.1 ✅

---

## 7. Propuesta de Evolución Futura

### Nuevas alertas posibles

| Alerta | Criterio |
|--------|----------|
| Sin acciones correctivas abiertas | NC_MAYOR sin CorrectiveAction asociada |
| Proceso sin responsable asignado | ProcessRequirement sin auditoría planificada |
| Cobertura AS9100 insuficiente | Procesos sin requisitos AS9100 asignados |

### Notificaciones externas

En una fase posterior las alertas podrían enviarse por email o
Slack cuando se activen, usando el sistema de comunicaciones
existente en `communications/`.

### Umbrales personalizables por organización

Los umbrales actuales son valores por defecto. En producción podrían
configurarse por organización desde el panel de administración,
almacenándose en un modelo `AlertThreshold`.