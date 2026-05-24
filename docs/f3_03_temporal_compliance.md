# Incorporación de la Evolución Temporal del Cumplimiento

**Issue:** F3-03 — Incorporación de la evolución temporal del cumplimiento  
**Fase:** FASE 3 — Motor de Cumplimiento  
**Dependencias:** F3-02 (Cálculo del estado de cumplimiento)  
**Impacto arquitectónico:** Bajo — sin modelos nuevos, dos nuevas funciones y dos nuevos endpoints  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Decisión de Diseño — Persistencia vs Recálculo](#2-decisión-de-diseño--persistencia-vs-recálculo)
3. [Funciones Implementadas](#3-funciones-implementadas)
4. [Endpoints Implementados](#4-endpoints-implementados)
5. [Verificación Funcional](#5-verificación-funcional)
6. [Decisiones de Diseño](#6-decisiones-de-diseño)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Tras F3-02, el sistema podía calcular y persistir el cumplimiento de
un proceso en un momento dado. Sin embargo, no existía ningún mecanismo
para observar cómo ese cumplimiento había evolucionado a lo largo del
tiempo ni para comparar el resultado de dos auditorías distintas.

El valor de un sistema de gestión de calidad no se mide solo en un
instante puntual — se mide en su capacidad de mejorar continuamente.
Esta issue añade esa dimensión temporal.

### 1.2 Objetivo

Implementar la lógica que permite observar la evolución temporal del
cumplimiento de un proceso y comparar dos periodos de auditoría,
identificando qué requisitos mejoraron, empeoraron o se mantuvieron.

---

## 2. Decisión de Diseño — Persistencia vs Recálculo

La decisión tomada en F3-01 fue clara: el histórico se **almacena**,
no se recalcula. Cada `ComplianceSnapshot` creado en F3-02 representa
un punto en la serie temporal.

**Ventajas de este enfoque:**
- Los datos de origen (checklist, hallazgos) pueden modificarse sin
  afectar el histórico ya registrado
- La comparación entre periodos es instantánea — no requiere recalcular
  nada, solo leer snapshots existentes
- El campo `detail` de cada snapshot contiene el desglose completo,
  permitiendo comparación a nivel de requisito individual

**Granularidad temporal:** por auditoría. Cada `AnnualPlan` completado
y calculado genera un punto en la serie temporal.

---

## 3. Funciones Implementadas

Se añadieron dos funciones al módulo `audits/compliance_engine.py`.

### 3.1 get_compliance_history(process_id, standard_id, limit=10)

Devuelve la serie temporal de snapshots de un proceso para una norma,
ordenados cronológicamente, con el cálculo de tendencia global.

**Lógica de tendencia:**

| Condición | Tendencia |
|-----------|-----------|
| `score_último - score_primero > 0.05` | IMPROVING |
| `score_último - score_primero < -0.05` | DECLINING |
| Diferencia ≤ 0.05 | STABLE |
| Solo 1 snapshot disponible | INSUFFICIENT_DATA |

**Salida:**
```json
{
    "success": true,
    "process": {"id": 1, "name": "Montaje de Fuselaje Central"},
    "standard": {"id": 3, "name": "ISO 9001:2015"},
    "total_snapshots": 2,
    "trend": "IMPROVING",
    "history": [snapshot_1, snapshot_2]
}
```
### Nota de corrección (F3-04)

El parámetro `limit` obtiene primero los N snapshots más recientes
(ordenando por `calculated_at` descendente) y después los reordena
cronológicamente para la salida. Esto garantiza que:

- Con `limit=2` y 3 snapshots disponibles, se devuelven los 2 más
  recientes, no los 2 más antiguos.
- La tendencia siempre se calcula usando el estado actual del proceso.
- La serie temporal sigue siendo legible en orden cronológico.


### 3.2 compare_compliance_periods(snapshot_id_a, snapshot_id_b)

Compara dos snapshots del mismo proceso y norma, identificando el
cambio en cada requisito individual.

**Tipos de cambio por requisito:**

| Tipo | Condición |
|------|-----------|
| IMPROVED | `score_b - score_a > 0.1` |
| DECLINED | `score_b - score_a < -0.1` |
| STABLE | Diferencia ≤ 0.1 |
| NEW | Requisito presente en B pero no en A |
| REMOVED | Requisito presente en A pero no en B |

Los cambios se ordenan por valor absoluto del delta, mostrando primero
los cambios más significativos.

**Salida:**
```json
{
    "success": true,
    "process": {"id": 1, "name": "Montaje de Fuselaje Central"},
    "standard": {"id": 3, "name": "ISO 9001:2015"},
    "period_a": {
        "snapshot_id": 1,
        "score": 21.9,
        "category": "CRITICAL",
        "calculated_at": "2026-05-21T18:43:02+00:00"
    },
    "period_b": {
        "snapshot_id": 2,
        "score": 71.9,
        "category": "GOOD",
        "calculated_at": "2026-05-21T19:04:39+00:00"
    },
    "summary": {
        "score_delta": 50.0,
        "improved_requirements": 4,
        "declined_requirements": 0,
        "stable_requirements": 2,
        "new_requirements": 0
    },
    "changes": [...]
}
```

---

## 4. Endpoints Implementados

### 4.1 GET /audits/get-compliance-history/\<process_id\>/\<standard_id\>/

Devuelve la evolución temporal del cumplimiento de un proceso para
una norma dada.

**Parámetro opcional:** `?limit=N` para limitar el número de snapshots
devueltos (por defecto 10).

**Casos de error:**
- Proceso no encontrado → 400
- Norma no encontrada → 400
- Sin snapshots para ese proceso y norma → 400

### 4.2 GET /audits/compare-compliance/\<snapshot_id_a\>/\<snapshot_id_b\>/

Compara dos snapshots identificando cambios por requisito.

**Casos de error:**
- Snapshot no encontrado → 400
- Snapshots de procesos diferentes → 400
- Snapshots de normas diferentes → 400

---

## 5. Verificación Funcional

### 5.1 Datos de prueba

Se crearon dos snapshots del mismo proceso (Montaje de Fuselaje Central)
y norma (ISO 9001:2015) para simular dos auditorías en periodos distintos:

| Snapshot | Plan | Score | Categoría | Periodo |
|----------|------|-------|-----------|---------|
| 1 | Plan 1 (mayo 2025) | 21.9% | CRITICAL | Base |
| 2 | Plan 2 (noviembre 2025) | 71.9% | GOOD | Comparado |

### 5.2 Resultado del histórico

GET /audits/get-compliance-history/1/3/
total_snapshots: 2
trend: IMPROVING ✅
history: [snapshot_1 (21.9%), snapshot_2 (71.9%)]

### 5.3 Resultado de la comparación

GET /audits/compare-compliance/1/2/
score_delta: +50.0% ✅
improved_requirements: 4 ✅
declined_requirements: 0 ✅
stable_requirements: 2 ✅

**Desglose de cambios por requisito:**

| Requisito | Status A | Status B | Delta | Tipo |
|-----------|----------|----------|-------|------|
| 8.5.1 | NON_COMPLIANT | COMPLIANT | +1.0 | IMPROVED |
| 8.5.1 | NOT_EVALUATED | COMPLIANT | +1.0 | IMPROVED |
| 4.1 | INSUFFICIENT_EVIDENCE | COMPLIANT | +0.75 | IMPROVED |
| 4.2 | NOT_EVALUATED | INSUFFICIENT_EVIDENCE | +0.25 | IMPROVED |
| 4.1 | COMPLIANT | COMPLIANT | 0.0 | STABLE |
| 4.2 | NOT_EVALUATED | NON_COMPLIANT | 0.0 | STABLE |

---

## 6. Decisiones de Diseño

### 6.1 Sin modelo nuevo

F3-03 no requiere ningún modelo adicional. El modelo `ComplianceSnapshot`
creado en F3-02 ya tiene `calculated_at` que permite construir series
temporales. Añadir un modelo nuevo hubiera duplicado información.

### 6.2 Comparación a nivel de requisito individual

La comparación entre periodos se hace a nivel de `ProcessRequirement`,
no solo a nivel de score global. Esto permite identificar exactamente
qué requisitos mejoraron o empeoraron entre auditorías, que es la
información realmente útil para un auditor.

### 6.3 Umbral de tendencia del 5%

Se eligió un umbral del 5% para distinguir IMPROVING de STABLE. Cambios
menores del 5% se consideran ruido estadístico en el contexto de
auditorías de calidad, donde las variaciones pequeñas pueden deberse
a diferencias en el auditor o en la interpretación de evidencias.

### 6.4 Ordenación por delta absoluto en la comparación

Los cambios se devuelven ordenados por valor absoluto del delta, mostrando
primero los cambios más significativos. Esto facilita que el auditor
identifique rápidamente los requisitos que más han cambiado sin tener
que revisar toda la lista.

### 6.5 Parámetro limit en el histórico

El endpoint de histórico acepta un parámetro `limit` opcional para
limitar el número de snapshots devueltos. Esto es importante para
procesos con muchas auditorías acumuladas donde devolver toda la
historia podría ser costoso.

