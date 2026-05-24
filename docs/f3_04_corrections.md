# Correcciones de Cierre de Fase 3

**Issue:** F3-04 — Correcciones necesarias para cerrar Fase 3  
**Fase:** FASE 3 — Motor de Cumplimiento (cierre)  
**Issues relacionados:** F3-02, F3-03  
**Resultado:** 36/36 tests pasando  

---

## Tabla de Contenidos

1. [Contexto](#1-contexto)
2. [Corrección 1 — get_compliance_history con limit](#2-corrección-1--get_compliance_history-con-limit)
3. [Validación automatizada del motor de cumplimiento](#3-validación-automatizada-del-motor-de-cumplimiento)
4. [Resultado de los tests](#4-resultado-de-los-tests)

---

## 1. Contexto

Tras la revisión de la Fase 3 por parte del tutor, se identificaron
dos aspectos que debían completarse antes de dar la fase por cerrada:

**Aspecto 1 — Corrección funcional en `get_compliance_history()`:**
El parámetro `limit` aplicaba el límite sobre los snapshots ordenados
de más antiguo a más reciente, devolviendo los snapshots más antiguos
en lugar de los más recientes. Esto hacía que la tendencia pudiera
calcularse sin tener en cuenta el estado actual del proceso.

**Aspecto 2 — Validación automatizada del motor de cumplimiento:**
No existían tests automatizados que cubrieran los casos principales
del motor de cálculo: ponderación por criticidad, penalización por
hallazgos, comportamiento del overwrite, agregado por norma y
comparación temporal.

---

## 2. Corrección 1 — get_compliance_history con limit

### 2.1 Problema

La implementación original ordenaba los snapshots de más antiguo a
más reciente y luego aplicaba el límite:

```python
# ANTES — devuelve los más ANTIGUOS
snapshots = ComplianceSnapshot.objects.filter(
    process=process,
    standard=standard,
).order_by('calculated_at')[:limit]

snapshots_list = list(snapshots)
```

Con 3 snapshots (scores: 20%, 50%, 90%) y `limit=2`, devolvía
los de 20% y 50% en lugar de los de 50% y 90%.

### 2.2 Corrección aplicada

Se invirtió el orden de la query para obtener primero los más
recientes, y luego se reordenaron cronológicamente para la salida:

```python
# DESPUÉS — devuelve los más RECIENTES en orden cronológico
snapshots_qs = ComplianceSnapshot.objects.filter(
    process=process,
    standard=standard,
).order_by('-calculated_at')[:limit]

snapshots_list = list(reversed(list(snapshots_qs)))
```

### 2.3 Impacto de la corrección

| Comportamiento | Antes | Después |
|----------------|-------|---------|
| `limit=2` con 3 snapshots | Devuelve los 2 más antiguos | Devuelve los 2 más recientes |
| Orden de la salida | Cronológico (correcto) | Cronológico (correcto) |
| Cálculo de tendencia | Puede ignorar estado actual | Siempre usa estado actual |

---

## 3. Validación Automatizada del Motor de Cumplimiento

Se añadió la clase `ComplianceEngineTestCase` en `audits/tests.py`
con 16 tests que cubren todos los casos principales del motor.

### 3.1 Tests de cálculo por proceso

| Test | Qué verifica |
|------|-------------|
| `test_calculo_proceso_ambos_conformes` | Dos requisitos COMPLIANT → score 100% EXCELLENT |
| `test_calculo_proceso_ninguno_conforme` | Dos requisitos NON_COMPLIANT → score 0% CRITICAL |
| `test_calculo_proceso_ponderacion_por_peso` | req_high COMPLIANT (peso 3) + req_medium NON_COMPLIANT (peso 2) → score 60% PARTIAL |
| `test_calculo_proceso_insufficient_evidence` | req_high INSUFFICIENT (0.25, peso 3) + req_medium COMPLIANT (peso 2) → score 55% PARTIAL |

**Verificación de la ponderación:**

req_high (peso 3) COMPLIANT + req_medium (peso 2) NON_COMPLIANT:
score = (1.0×3 + 0.0×2) / (3+2) = 3/5 = 0.6 → 60% PARTIAL ✅

### 3.2 Tests de persistencia y overwrite

| Test | Qué verifica |
|------|-------------|
| `test_persistencia_snapshot` | El snapshot se guarda en base de datos |
| `test_no_duplica_sin_overwrite` | Sin overwrite, el segundo cálculo devuelve error |
| `test_overwrite_recalcula` | Con overwrite=True, el snapshot se recalcula y solo queda uno |
| `test_trazabilidad_detail` | El campo detail contiene desglose por requisito con todos los campos esperados |

### 3.3 Tests de penalización por hallazgos

| Test | Qué verifica |
|------|-------------|
| `test_penalizacion_nc_mayor` | NC_MAYOR (-0.3) sobre req_high COMPLIANT → score 82% GOOD |
| `test_penalizacion_nc_menor` | NC_MENOR (-0.15) sobre req_high COMPLIANT → score 91% EXCELLENT |

**Verificación de la penalización:**

req_high COMPLIANT (1.0) con NC_MAYOR (-0.3) → final_score 0.7
req_medium COMPLIANT (1.0) sin hallazgo → final_score 1.0
score = (0.7×3 + 1.0×2) / 5 = 4.1/5 = 0.82 → 82% GOOD ✅

### 3.4 Tests de agregado por norma

| Test | Qué verifica |
|------|-------------|
| `test_agregado_por_norma` | El agregado por norma devuelve el score global correcto |
| `test_agregado_sin_snapshots` | Sin snapshots, get_compliance_by_standard devuelve error |

### 3.5 Tests de comparación temporal

| Test | Qué verifica |
|------|-------------|
| `test_comparacion_temporal` | Plan 1 (0%) → Plan 2 (100%): delta +100%, 2 improved, 0 declined |
| `test_comparacion_procesos_distintos_da_error` | No se pueden comparar snapshots de procesos diferentes |

### 3.6 Tests de histórico con limit

| Test | Qué verifica |
|------|-------------|
| `test_historico_limit_devuelve_mas_recientes` | Con limit=2 y 3 snapshots, devuelve los 2 más recientes en orden cronológico |
| `test_historico_tendencia_usa_estado_actual` | La tendencia se calcula usando el snapshot más reciente disponible |

**Verificación del limit:**

Con 3 snapshots (scores: 20%, 50%, 90%) y `limit=2`:
- Resultado esperado: snapshots de 50% y 90% (los 2 más recientes)
- Tendencia esperada: IMPROVING (de 50% a 90%)

Para garantizar orden determinista en los tests, los snapshots
se crean con fechas explícitas usando `timedelta`:

```python
now = timezone.now()
ComplianceSnapshot.objects.filter(pk=snap1.pk).update(
    calculated_at=now - timedelta(days=60)  # más antiguo
)
ComplianceSnapshot.objects.filter(pk=snap2.pk).update(
    calculated_at=now - timedelta(days=30)  # intermedio
)
ComplianceSnapshot.objects.filter(pk=snap3.pk).update(
    calculated_at=now                        # más reciente
)
```

Esto es necesario porque `auto_now_add=True` en `calculated_at`
asigna el mismo timestamp a todos los snapshots creados en el
mismo instante durante los tests, haciendo el orden no determinista.

---

## 4. Resultado de los Tests

```bash
python manage.py test audits --verbosity=2

Ran 36 tests in 15.686s
OK
```

| Clase de tests | Tests | Resultado |
|----------------|-------|-----------|
| GapAnalysisTestCase | 12 | ✅ |
| GenerateDynamicChecklistTestCase | 8 | ✅ |
| ComplianceEngineTestCase | 16 | ✅ |
| **Total** | **36** | **✅ OK** |

