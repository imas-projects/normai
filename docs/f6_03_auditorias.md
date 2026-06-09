# Integración Visual de Checklists Dinámicos y Análisis de Brechas en Auditorías

**Issue:** F6-03 — Integración visual de checklists dinámicos y análisis de brechas
**Fase:** FASE 6 — Representación Visual para Defensa del TFG
**Dependencias:** F2-01 (Checklists dinámicos), F2-02 (Preguntas de evaluación), F2-03 (Análisis de brechas)
**Impacto arquitectónico:** Bajo — nueva vista HTML en app demo, función auxiliar de gap analysis

---

## Tabla de Contenidos

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Decisiones de Diseño](#2-decisiones-de-diseño)
3. [Implementación](#3-implementación)
4. [Errores Encontrados y Soluciones](#4-errores-encontrados-y-soluciones)
5. [Resultado Final](#5-resultado-final)
6. [Limitaciones](#6-limitaciones)

---

## 1. Contexto y Objetivo

### 1.1 Problema de Partida

La Fase 2 implementó la lógica de generación dinámica de checklists
y análisis de brechas como endpoints JSON. Sin una vista web propia,
esta funcionalidad quedaba completamente oculta durante la defensa —
el tribunal no podía ver el flujo completo desde la norma hasta las
preguntas y brechas detectadas sin acceder directamente a los endpoints.

### 1.2 Objetivo

Crear una pantalla que muestre visualmente el flujo completo de
auditoría: selección de plan → checklist con trazabilidad normativa
→ análisis de brechas → hallazgos. Todo desde la interfaz web, sin
necesidad de llamadas manuales a endpoints JSON.

---

## 2. Decisiones de Diseño

### 2.1 Vista nueva en app demo sin modificar audits

Se creó una vista nueva `demo_audit_checklists` en `demo/views.py`
en lugar de modificar la vista existente `conduct_internal_audits`.
Esto garantiza que las pantallas operativas del módulo de auditorías
no se ven afectadas.

### 2.2 Layout de dos paneles

- **Panel izquierdo:** lista de planes de auditoría con checklist
  disponible, ordenados por id, con proceso, norma y fecha
- **Panel derecho:** tres pestañas — Checklist, Análisis de Brechas
  y Hallazgos

### 2.3 Trazabilidad normativa por ítem del checklist

Cada ítem del checklist muestra:
- Código de cláusula (badge azul)
- Nivel de criticidad (badge rojo/amarillo/verde)
- Si es obligatorio (badge oscuro)
- Texto del requisito normativo vinculado
- Evidencia registrada
- Estado visual (CONFORME/NO CONFORME/SIN EVIDENCIA)

El color del borde izquierdo refleja el estado del ítem de un vistazo.

### 2.4 Función auxiliar `_get_gap_analysis_data`

La lógica del análisis de brechas estaba implementada en
`audits/views.py::get_gap_analysis` como una vista HTTP que devuelve
un `JsonResponse`. Para reutilizarla en la vista de demo sin hacer
una llamada HTTP interna, se extrajo la lógica en una función auxiliar
`_get_gap_analysis_data` en `demo/views.py` que devuelve un dict
directamente.

---

## 3. Implementación

### 3.1 Función auxiliar — `_get_gap_analysis_data`

```python
def _get_gap_analysis_data(annual_plan):
    """
    Calcula el análisis de brechas para un plan de auditoría.
    Replica la lógica de audits/views.py::get_gap_analysis
    pero devuelve un dict en lugar de JsonResponse.
    """
```

Para cada `ProcessRequirement` del proceso auditado y la norma
seleccionada, determina el estado:

| Estado | Condición |
|--------|-----------|
| `COMPLIANT` | checklist_item.compliance = True |
| `NON_COMPLIANT` | compliance = False con evidencia |
| `INSUFFICIENT_EVIDENCE` | compliance = False sin evidencia |
| `NOT_EVALUATED` | sin ítem de checklist en este plan |

### 3.2 Vista — `demo_audit_checklists`

La vista construye el contexto en cuatro pasos:

1. Obtiene todos los planes con checklist disponible
2. Si hay plan seleccionado, carga el checklist con trazabilidad
3. Calcula el análisis de brechas con `_get_gap_analysis_data`
4. Carga los hallazgos del plan

### 3.3 Estadísticas del checklist

```python
stats = {
    'total': total,
    'compliant': compliant,
    'non_compliant': non_compliant,
    'insufficient': insufficient,
    'compliance_rate': round(compliant / total * 100, 1)
}
```

---

## 4. Errores Encontrados y Soluciones

### Error — ImportError: cannot import name 'get_gap_analysis'

**Causa:** La vista `demo_audit_checklists` intentaba importar
`get_gap_analysis` desde `audits.compliance_engine`, pero esa función
no existe en ese módulo — está implementada como vista HTTP en
`audits/views.py` y devuelve un `JsonResponse`, no un dict reutilizable.

**Síntoma:**
ImportError at /demo/auditorias/
cannot import name 'get_gap_analysis' from 'audits.compliance_engine'

**Solución:** Crear la función auxiliar `_get_gap_analysis_data` en
`demo/views.py` que replica la lógica del gap analysis pero devuelve
un dict en lugar de `JsonResponse`. Eliminar el import incorrecto.

---

## 5. Resultado Final

La vista es accesible desde:
http://127.0.0.1:8000/demo/auditorias/

Y desde la tarjeta "Auditorías y Checklists" del dashboard F6-01.

### Ejemplo verificado — Plan 1 (Montaje de Fuselaje Central)

| Ítem | Cláusula | Estado | Criticidad |
|------|----------|--------|-----------|
| 1 | §4.1 | CONFORME | HIGH |
| 2 | §8.5.1 | NO CONFORME | HIGH |
| 3 | §4.1 | SIN EVIDENCIA | MEDIUM |

**Estadísticas del plan:**
- Conformidad: 33.3%
- Conformes: 1 / No conformes: 1 / Sin evidencia: 1

### Datos disponibles para la demo

| Plan | Proceso | Ítems checklist |
|------|---------|----------------|
| 1 | Montaje de Fuselaje Central | 3 |
| 2 | Montaje de Fuselaje Central | 6 |
| 3 | Control Documental | 4 |
| 4 | Gestión de Proveedores Críticos | 4 |
| 5 | Integración de Sistemas Eléctricos | 4 |
| ... | ... | ... |

---

## 6. Limitaciones

### Sin generación dinámica desde la vista

La vista muestra checklists ya generados. La generación dinámica
desde cero (llamando al endpoint `generate-dynamic-checklist`)
no está integrada en la vista demo — requeriría una llamada POST
con parámetros específicos que queda fuera del alcance de F6-03.

### Trazabilidad parcial en algunos planes

Algunos ítems de checklist muestran `—` en los campos normativos
cuando la pregunta no tiene `ProcessRequirement` vinculado
correctamente. Esto afecta a datos de prueba generados automáticamente
en F4-01 donde la vinculación es menos precisa.