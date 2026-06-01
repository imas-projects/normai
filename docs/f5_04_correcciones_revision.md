# Correcciones de Revisión y Cierre de Fase 5

**Documento:** Correcciones post-revisión del tutor — Fase 5  
**Issues relacionados:** F5-01, F5-02, F5-03  
**Resultado:** 51/51 tests pasando  

---

## Tabla de Contenidos

- [Correcciones de Revisión y Cierre de Fase 5](#correcciones-de-revisión-y-cierre-de-fase-5)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [1. Resumen de Cambios](#1-resumen-de-cambios)
  - [2. Corrección 1 — Filtrado por norma en contadores globales](#2-corrección-1--filtrado-por-norma-en-contadores-globales)
    - [Problema detectado](#problema-detectado)
    - [Corrección aplicada](#corrección-aplicada)
  - [3. Corrección 2 — Ajuste de textos de alertas](#3-corrección-2--ajuste-de-textos-de-alertas)
    - [Problema detectado](#problema-detectado-1)
    - [Corrección aplicada](#corrección-aplicada-1)
  - [4. Tests añadidos para F5](#4-tests-añadidos-para-f5)
  - [5. Alcance de la Fase 5](#5-alcance-de-la-fase-5)
  - [6. Limitaciones documentadas](#6-limitaciones-documentadas)
    - [Datos históricos](#datos-históricos)
    - [Alertas sin verificación de modelos relacionados](#alertas-sin-verificación-de-modelos-relacionados)
    - [Sin capa visual](#sin-capa-visual)
    - [Sin tiempo real](#sin-tiempo-real)
  - [7. Criterio de Cierre](#7-criterio-de-cierre)

---

## 1. Resumen de Cambios

| Corrección | Archivo | Tipo |
|------------|---------|------|
| Filtrar `total_audits` y `Findings` por norma | `executive_dashboard.py` | Funcional |
| Filtrar NC_MAYOR por norma en alerta | `strategic_alerts.py` | Funcional |
| Ajustar texto de `HIGH_NPN_UNADDRESSED` | `strategic_alerts.py` | Precisión |
| Ajustar texto de `NC_MAYOR_ACCUMULATED` | `strategic_alerts.py` | Precisión |
| Añadir `ExecutiveDashboardTestCase` (15 tests) | `tests.py` | Validación |

---

## 2. Corrección 1 — Filtrado por norma en contadores globales

### Problema detectado

En `executive_dashboard.py` los contadores del bloque de auditorías
usaban queries globales sin filtrar por norma:

```python
# ANTES — global, no filtra por norma
total_audits = AnnualPlan.objects.count()
total_findings = Findings.objects.filter(classification='NC_MAYOR').count()
```

Esto hacía que al filtrar por `?standard_id=N` el resumen ejecutivo
mostrara el total de auditorías y hallazgos de toda la organización
en lugar de solo los de la norma seleccionada.

El mismo problema existía en la alerta `NC_MAYOR_ACCUMULATED` de
`strategic_alerts.py`.

### Corrección aplicada

**`executive_dashboard.py`** — se filtra `AnnualPlan` y `Findings`
por norma cuando se especifica `standard_id`:

```python
# DESPUÉS — filtrado por norma
if standard_id:
    audit_plans_qs = AnnualPlan.objects.filter(
        annual_program__standard_id=standard_id
    )
else:
    audit_plans_qs = AnnualPlan.objects.all()

total_audits = audit_plans_qs.count()
nc_mayor_total = Findings.objects.filter(
    audit_plan__in=audit_plans_qs,
    classification='NC_MAYOR'
).count()
```

**`strategic_alerts.py`** — la alerta `NC_MAYOR_ACCUMULATED` aplica
el mismo filtrado:

```python
if standard_id:
    audit_plans_qs = AnnualPlan.objects.filter(
        annual_program__standard_id=standard_id
    )
    nc_mayor_total = Findings.objects.filter(
        audit_plan__in=audit_plans_qs,
        classification='NC_MAYOR'
    ).count()
else:
    nc_mayor_total = Findings.objects.filter(
        classification='NC_MAYOR'
    ).count()
```

---

## 3. Corrección 2 — Ajuste de textos de alertas

### Problema detectado

Dos alertas usaban lenguaje que implicaba comprobaciones que el
sistema no realiza realmente:

- `HIGH_NPN_UNADDRESSED` decía "sin tratamiento" pero no verifica
  el modelo `RiskTreatment`
- `NC_MAYOR_ACCUMULATED` decía "sin resolver" pero no verifica
  el modelo `CorrectiveAction`

### Corrección aplicada

Los textos se ajustaron para describir exactamente lo que el sistema
comprueba, sin implicar verificaciones que no se realizan:

```python
# ANTES
'HIGH_NPN_UNADDRESSED': {
    'name': 'Riesgos con NPN crítico sin tratamiento',
    'description': 'Hay riesgos con NPN superior a 300 que requieren atención prioritaria.',
    ...
}

# DESPUÉS
'HIGH_NPN_UNADDRESSED': {
    'name': 'Riesgos con NPN elevado',
    'description': 'Hay riesgos con NPN superior a 300, indicando alta exposición al riesgo.',
    'action': 'Revisar el estado de tratamiento de los riesgos afectados y priorizar su atención.',
    ...
}
```

```python
# ANTES
'NC_MAYOR_ACCUMULATED': {
    'name': 'No conformidades mayores acumuladas',
    'description': 'El sistema acumula no conformidades mayores sin resolver.',
    ...
}

# DESPUÉS
'NC_MAYOR_ACCUMULATED': {
    'name': 'No conformidades mayores registradas',
    'description': 'El sistema tiene no conformidades mayores registradas en auditorías.',
    'action': 'Verificar si existen acciones correctivas asociadas y su estado de seguimiento.',
    ...
}
```

---

## 4. Tests añadidos para F5

Se añadió la clase `ExecutiveDashboardTestCase` en `audits/tests.py`
con 15 tests que cubren los endpoints de F5-02 y F5-03.

| Test | Qué verifica |
|------|-------------|
| `test_dashboard_requiere_autenticacion` | Acceso denegado sin login |
| `test_dashboard_devuelve_200` | Respuesta correcta con datos |
| `test_dashboard_estructura_bloques` | Presencia de los 6 bloques |
| `test_dashboard_executive_summary` | Campos del resumen ejecutivo |
| `test_dashboard_filtrado_por_norma` | Filtrado correcto por standard_id |
| `test_dashboard_filtrado_norma_inexistente` | Error con norma sin datos |
| `test_alertas_requiere_autenticacion` | Acceso denegado sin login |
| `test_alertas_devuelve_200` | Respuesta correcta |
| `test_alertas_estructura` | Presencia de summary, alerts e indicadores |
| `test_alertas_summary_campos` | Campos del resumen de alertas |
| `test_indicadores_estrategicos` | Campos de indicadores estratégicos |
| `test_alerta_nc_mayor_se_activa` | Alerta NC_MAYOR con hallazgos reales |
| `test_alerta_proceso_sin_auditoria_suficiente` | Alerta con 1 sola auditoría |
| `test_dashboard_compliance_block_estructura` | Estructura del bloque de cumplimiento |
| `test_dashboard_audit_block_filtrado` | Filtrado correcto en bloque de auditorías |

**Resultado:** 51/51 tests pasando.

---

## 5. Alcance de la Fase 5

La Fase 5 implementa una **capa ejecutiva backend/API** del dashboard
de NormAI. El alcance es:

✅ **Incluido:**
- Endpoint JSON `/audits/executive-dashboard/` con 6 bloques de
  información ejecutiva
- Endpoint JSON `/audits/get-strategic-alerts/` con alertas e
  indicadores estratégicos
- Filtrado por norma en todos los bloques
- Alertas con criterios explícitos y acciones recomendadas
- Indicadores estratégicos (índice de madurez, tasa de control,
  exposición al riesgo)

❌ **No incluido en esta fase:**
- Vista HTML/JavaScript integrada en la interfaz de usuario
- Notificaciones externas (email, Slack)
- Umbrales personalizables por organización
- Integración completa con acciones correctivas y tratamientos de
  riesgo en las alertas

La capa visual sobre estos endpoints queda como trabajo futuro.
Los endpoints están listos para ser consumidos por cualquier
frontend que se implemente posteriormente.

---

## 6. Limitaciones documentadas

### Datos históricos

El dashboard se alimenta de 10 snapshots de datos de prueba.
En producción, los indicadores ganarán precisión a medida que
se realicen más auditorías reales.

### Alertas sin verificación de modelos relacionados

Las alertas actuales evalúan datos de cumplimiento y riesgo
directamente. No verifican el estado de modelos relacionados
como `RiskTreatment` o `CorrectiveAction` porque estos modelos
no tienen registros actualmente. Cuando existan datos en esos
modelos, las alertas deberán actualizarse para incorporar
esas verificaciones.

### Sin capa visual

El dashboard es un prototipo funcional backend/API. La
visualización ejecutiva HTML/JS no está implementada en esta
fase.

### Sin tiempo real

El dashboard refleja el estado de los snapshots calculados.
Para actualizar los indicadores hay que ejecutar
`calculate-compliance` para los nuevos planes de auditoría.

---

## 7. Criterio de Cierre

| Criterio | Estado |
|----------|--------|
| `python manage.py check` sin incidencias | ✅ |
| 51/51 tests pasando | ✅ |
| Filtrado por norma coherente en todos los bloques | ✅ |
| Textos de alertas ajustados a lo que realmente se verifica | ✅ |
| Tests específicos para F5 añadidos | ✅ |
| Alcance de F5 documentado explícitamente | ✅ |
| Limitaciones documentadas | ✅ |