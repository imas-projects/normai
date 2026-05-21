# Cálculo del Estado de Cumplimiento por Norma y por Proceso

**Issue:** F3-02 — Cálculo del estado de cumplimiento por norma y por proceso  
**Fase:** FASE 3 — Motor de Cumplimiento  
**Dependencias:** F3-01 (Reglas de evaluación determinista)  
**Impacto arquitectónico:** Medio — nuevo modelo, nuevo módulo de lógica, tres nuevos endpoints  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Arquitectura de la Solución](#2-arquitectura-de-la-solución)
3. [Modelo ComplianceSnapshot](#3-modelo-compliancesnapshot)
4. [Motor de Cálculo — compliance_engine.py](#4-motor-de-cálculo--compliance_enginepy)
5. [Endpoints Implementados](#5-endpoints-implementados)
6. [Verificación Funcional](#6-verificación-funcional)
7. [Decisiones de Diseño](#7-decisiones-de-diseño)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Tras F2-03, el sistema podía detectar brechas de cumplimiento en tiempo
real para un plan de auditoría concreto. Sin embargo, ese análisis:

- No persistía — cada consulta recalculaba desde cero
- No agregaba — no había un score numérico por proceso ni por norma
- No era trazable — el resultado no quedaba registrado en ninguna tabla

F3-02 resuelve los tres problemas implementando un motor de cálculo que
aplica las reglas definidas en F3-01 y persiste los resultados en un
modelo `ComplianceSnapshot`.

### 1.2 Objetivo

Implementar la lógica de cálculo de cumplimiento por proceso y por norma,
persitir los resultados para su reutilización y exponer tres endpoints
que permitan calcular y consultar el estado de cumplimiento.

---

## 2. Arquitectura de la Solución

### 2.1 Componentes creados

audits/
compliance_engine.py    ← Motor de cálculo (lógica pura)
models.py               ← Nuevo modelo ComplianceSnapshot
views.py                ← Tres nuevos endpoints
urls.py                 ← Tres nuevas rutas
migrations/
0010_add_compliance_snapshot.py

### 2.2 Flujo de cálculo

POST /audits/calculate-compliance/
↓
compliance_engine.calculate_compliance_for_plan(annual_plan_id)
↓
Obtener ProcessRequirements del proceso para la norma
↓
Para cada ProcessRequirement:
├── Determinar estado (COMPLIANT/NON_COMPLIANT/INSUFFICIENT/NOT_EVALUATED)
├── Calcular puntuación base (reglas F3-01)
├── Aplicar penalización por hallazgos
└── Ponderar por criticidad y obligatoriedad
↓
Calcular score global ponderado
↓
Asignar categoría cualitativa
↓
Persistir ComplianceSnapshot
↓
Devolver JSON con resultado completo

---

## 3. Modelo ComplianceSnapshot

### 3.1 Definición

```python
class ComplianceSnapshot(models.Model):
    annual_plan          → FK a AnnualPlan
    process              → FK a Process
    standard             → FK a Standard
    score                → FloatField (0.0 a 1.0)
    category             → CharField (EXCELLENT/GOOD/PARTIAL/LOW/CRITICAL)
    total_requirements   → IntegerField
    compliant_count      → IntegerField
    non_compliant_count  → IntegerField
    insufficient_count   → IntegerField
    not_evaluated_count  → IntegerField
    calculated_at        → DateTimeField (auto_now_add)
    detail               → JSONField (desglose por requisito)
```

### 3.2 Campo detail

El campo `detail` es un JSONField que almacena el desglose completo
del cálculo por cada `ProcessRequirement`. Para cada requisito incluye:

```json
{
    "process_requirement_id": 2,
    "clause_code": "4.1",
    "clause_title": "Comprensión de la organización y de su contexto",
    "requirement_text": "La organización debe determinar...",
    "mandatory": true,
    "criticality_level": "high",
    "is_extension": false,
    "status": "COMPLIANT",
    "base_score": 1.0,
    "penalty": 0.0,
    "final_score": 1.0,
    "weight": 3
}
```

Esto garantiza trazabilidad completa: dado un snapshot, se puede
reconstruir exactamente cómo se calculó cada puntuación.

### 3.3 Migración

audits/migrations/0010_add_compliance_snapshot.py

Create model ComplianceSnapshot

---

## 4. Motor de Cálculo — compliance_engine.py

### 4.1 Constantes de las reglas F3-01

```python
SCORE_BY_STATUS = {
    'COMPLIANT': 1.0,
    'NON_COMPLIANT': 0.0,
    'INSUFFICIENT_EVIDENCE': 0.25,
    'NOT_EVALUATED': 0.0,
}

FINDING_PENALTY = {
    'NC_MAYOR': 0.3,
    'NC_MENOR': 0.15,
    'OPORTUNIDAD_MEJORA': 0.0,
}

WEIGHT_TABLE = {
    ('high', True): 3,
    ('high', False): 2,
    ('medium', True): 2,
    ('medium', False): 1,
    ('low', True): 1,
    ('low', False): 0.5,
}

CATEGORY_THRESHOLDS = [
    (0.85, 'EXCELLENT'),
    (0.70, 'GOOD'),
    (0.50, 'PARTIAL'),
    (0.25, 'LOW'),
    (0.00, 'CRITICAL'),
]
```

### 4.2 Función principal — calculate_compliance_for_plan

**Entrada:** `annual_plan_id`, `overwrite=False`

**Proceso:**

1. Obtiene el `AnnualPlan` con sus relaciones
2. Verifica que el programa tiene norma seleccionada
3. Verifica si ya existe un snapshot (si existe y `overwrite=False`, devuelve error)
4. Obtiene los `ProcessRequirement` del proceso para la norma
5. Construye un índice `process_requirement_id → checklist_item`
6. Para cada `ProcessRequirement`:
   - Determina el estado del checklist
   - Calcula la puntuación base
   - Calcula la penalización por hallazgos
   - Calcula el peso según criticidad y obligatoriedad
   - Acumula en el score ponderado
7. Calcula el score global y la categoría
8. Persiste el `ComplianceSnapshot`

**Salida:** Dict con `success` y `snapshot` serializado.

### 4.3 Función get_compliance_by_standard

**Entrada:** `standard_id`

**Proceso:**

1. Obtiene el snapshot más reciente de cada proceso para la norma
2. Calcula el score global ponderado por número de requisitos:

score_norma = Σ(score_proceso × n_requisitos) / Σ(n_requisitos)

**Salida:** Dict con `global_score`, `global_category` y desglose por proceso.

---

## 5. Endpoints Implementados

### 5.1 POST /audits/calculate-compliance/

Calcula y persiste el snapshot de cumplimiento para un `AnnualPlan`.

**Request:**
```json
{
    "annual_plan_id": 1,
    "overwrite": false
}
```

**Response (éxito):**
```json
{
    "success": true,
    "snapshot": {
        "id": 1,
        "annual_plan_id": 1,
        "process": {"id": 1, "name": "Montaje de Fuselaje Central"},
        "standard": {"id": 3, "name": "ISO 9001:2015"},
        "score": 21.9,
        "category": "CRITICAL",
        "total_requirements": 6,
        "compliant_count": 1,
        "non_compliant_count": 1,
        "insufficient_count": 1,
        "not_evaluated_count": 3,
        "calculated_at": "2026-05-21T18:43:02.492605+00:00",
        "detail": [...]
    }
}
```

### 5.2 GET /audits/get-compliance-snapshot/\<annual_plan_id\>/

Devuelve el snapshot más reciente de un `AnnualPlan`.

**Response (sin snapshot):**
```json
{
    "error": "No hay snapshot calculado para este plan. Invoca calculate-compliance primero."
}
```

### 5.3 GET /audits/get-standard-compliance/\<standard_id\>/

Devuelve el cumplimiento agregado de una norma basado en los snapshots
más recientes de cada proceso.

**Response:**
```json
{
    "success": true,
    "standard": {"id": 3, "name": "ISO 9001:2015"},
    "global_score": 21.9,
    "global_category": "CRITICAL",
    "total_processes": 1,
    "processes": [...]
}
```

---

## 6. Verificación Funcional

### 6.1 Cálculo desde el shell

```python
from audits.compliance_engine import calculate_compliance_for_plan
result = calculate_compliance_for_plan(1)
```

**Resultado obtenido:**

| Campo | Valor |
|-------|-------|
| score | 21.9% |
| category | CRITICAL |
| total_requirements | 6 |
| compliant_count | 1 |
| non_compliant_count | 1 |
| insufficient_count | 1 |
| not_evaluated_count | 3 |

**Verificación manual del cálculo:**

| Requisito | Estado | Score base | Peso | Contribución |
|-----------|--------|-----------|------|-------------|
| 4.1 (high, mandatory) | COMPLIANT | 1.0 | 3 | 3.0 |
| 8.5.1 (high, mandatory) | NON_COMPLIANT | 0.0 | 3 | 0.0 |
| 4.1 (medium, mandatory) | INSUFFICIENT_EVIDENCE | 0.25 | 2 | 0.5 |
| 8.5.1 (high, mandatory) | NOT_EVALUATED | 0.0 | 3 | 0.0 |
| 4.2 (high, mandatory) | NOT_EVALUATED | 0.0 | 3 | 0.0 |
| 4.2 (medium, mandatory) | NOT_EVALUATED | 0.0 | 2 | 0.0 |

score = (3.0 + 0.0 + 0.5 + 0.0 + 0.0 + 0.0) / (3 + 3 + 2 + 3 + 3 + 2)
score = 3.5 / 16 = 0.21875 → 21.9% → CRITICAL ✅

### 6.2 Verificación de endpoints

| URL | Resultado |
|-----|-----------|
| `GET /audits/get-compliance-snapshot/1/` | ✅ Snapshot con score 21.9% |
| `GET /audits/get-standard-compliance/3/` | ✅ ISO 9001 global 21.9% CRITICAL |

---

## 7. Decisiones de Diseño

### 7.1 Motor separado en compliance_engine.py

La lógica de cálculo se implementó en un módulo separado en lugar de
directamente en `views.py`. Esto permite:

- Invocar el cálculo desde el shell, tests o tareas programadas sin
  necesidad de simular una petición HTTP
- Testear la lógica de cálculo de forma aislada
- Mantener `views.py` centrado en la capa HTTP

### 7.2 Persistencia en lugar de recálculo

Los snapshots se persisten en base de datos en lugar de calcularse en
tiempo real. Esto es fundamental para F3-03, que necesita comparar
resultados de diferentes momentos en el tiempo.

### 7.3 Campo overwrite

El endpoint `calculate-compliance` tiene un parámetro `overwrite` que
por defecto es `False`. Esto protege contra recálculos accidentales que
sobreescribirían un snapshot válido. Para recalcular hay que indicarlo
explícitamente.

### 7.4 Trazabilidad completa en detail

El campo `detail` del snapshot almacena el desglose completo del cálculo
por requisito. Esto garantiza que dado cualquier snapshot histórico se
puede explicar exactamente cómo se obtuvo ese score, sin depender de
los datos actuales del checklist.