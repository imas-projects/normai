# Correcciones de Revisión para Cierre de Fase 4

**Documento:** Correcciones post-revisión del tutor  
**Issues relacionados:** F4-01, F4-02, F4-03  
**Commit:** fix(analytics): correcciones de revisión para cierre de Fase 4  

---

## Tabla de Contenidos

- [Correcciones de Revisión para Cierre de Fase 4](#correcciones-de-revisión-para-cierre-de-fase-4)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [1. Resumen de Cambios](#1-resumen-de-cambios)
  - [2. Corrección 1 — Filtrado por norma en get\_full\_dataset\_summary](#2-corrección-1--filtrado-por-norma-en-get_full_dataset_summary)
    - [Problema detectado](#problema-detectado)
    - [Corrección aplicada](#corrección-aplicada)
  - [3. Corrección 2 — Coherencia del filtrado en detección de anomalías](#3-corrección-2--coherencia-del-filtrado-en-detección-de-anomalías)
    - [Problema detectado](#problema-detectado-1)
    - [Corrección aplicada](#corrección-aplicada-1)
  - [4. Corrección 3 — Selección determinista de evaluación de riesgo](#4-corrección-3--selección-determinista-de-evaluación-de-riesgo)
    - [Problema detectado](#problema-detectado-2)
    - [Corrección aplicada](#corrección-aplicada-2)
  - [5. Evidencia de Validación](#5-evidencia-de-validación)
    - [5.1 GET /audits/get-analytics-dataset/?standard\_id=3](#51-get-auditsget-analytics-datasetstandard_id3)
    - [5.2 GET /audits/get-risk-predictions/?standard\_id=3](#52-get-auditsget-risk-predictionsstandard_id3)
    - [5.3 GET /audits/get-anomaly-detection/?standard\_id=3](#53-get-auditsget-anomaly-detectionstandard_id3)
    - [5.4 Verificación de sistema](#54-verificación-de-sistema)
  - [6. Limitaciones que Siguen Existiendo](#6-limitaciones-que-siguen-existiendo)
    - [Volumen de datos](#volumen-de-datos)
    - [Umbrales no calibrados estadísticamente](#umbrales-no-calibrados-estadísticamente)
    - [Sin integración visual](#sin-integración-visual)
    - [Datos de prueba sintéticos](#datos-de-prueba-sintéticos)
  - [7. Criterio de Cierre](#7-criterio-de-cierre)

---

## 1. Resumen de Cambios

| Corrección | Archivo | Tipo |
|------------|---------|------|
| Pasar `standard_id` a `get_full_dataset_summary()` | `analytics_dataset.py`, `views.py` | Funcional |
| Filtrar riesgos por procesos relevantes en `detect_anomalies()` | `anomaly_detector.py` | Funcional |
| Ordenar evaluaciones de riesgo por id explícitamente | `analytics_dataset.py` | Determinismo |

---

## 2. Corrección 1 — Filtrado por norma en get_full_dataset_summary

### Problema detectado

La función `get_full_dataset_summary()` en `analytics_dataset.py`
no aceptaba el parámetro `standard_id`, aunque el endpoint
`get_analytics_dataset()` en `views.py` lo leía de la URL.
El parámetro se leía pero no se pasaba a las funciones internas,
por lo que el filtrado no tenía efecto real.

### Corrección aplicada

**`audits/analytics_dataset.py`** — se añadió `standard_id=None`
a la firma de `get_full_dataset_summary()` y se pasa a las
funciones internas:

```python
# ANTES
def get_full_dataset_summary():
    process_data = get_process_dataset()
    snapshot_data = get_snapshot_dataset()
    ...

# DESPUÉS
def get_full_dataset_summary(standard_id=None):
    process_data = get_process_dataset(standard_id=standard_id)
    snapshot_data = get_snapshot_dataset(standard_id=standard_id)
    ...
```

**`audits/views.py`** — se pasa el parámetro a la función:

```python
# ANTES
summary = get_full_dataset_summary()

# DESPUÉS
summary = get_full_dataset_summary(standard_id=standard_id)
```

---

## 3. Corrección 2 — Coherencia del filtrado en detección de anomalías

### Problema detectado

En `detect_anomalies()`, cuando se llamaba con `?standard_id=N`,
los datasets de proceso y snapshot se filtraban correctamente,
pero el dataset de riesgos se obtenía completo sin filtrar.
Esto podía incluir en el análisis riesgos de procesos ajenos
a la norma seleccionada.

### Corrección aplicada

**`audits/anomaly_detector.py`** — se filtra el dataset de riesgos
para incluir solo los procesos relevantes para la norma:

```python
# ANTES
risk_data = get_risk_dataset()

# DESPUÉS
relevant_process_ids = set(p['process_id'] for p in process_data)
all_risk_data = get_risk_dataset()
risk_data = [
    r for r in all_risk_data
    if r['process_id'] in relevant_process_ids
]
```

---

## 4. Corrección 3 — Selección determinista de evaluación de riesgo

### Problema detectado

En `get_risk_dataset()`, las evaluaciones de riesgo se obtenían
con `.all()` sin orden explícito. El orden implícito de la base
de datos no está garantizado y puede variar entre ejecuciones,
haciendo que la "última evaluación" no fuera reproducible.

### Corrección aplicada

**`audits/analytics_dataset.py`** — se añade ordenación explícita
por `id` para garantizar determinismo:

```python
# ANTES
evaluations = list(risk.evaluations.all())

# DESPUÉS
evaluations = list(risk.evaluations.order_by('id').all())
```

Con esta corrección, la última evaluación es siempre la de mayor
`id`, que corresponde a la creada más recientemente, de forma
reproducible independientemente del motor de base de datos.

---

## 5. Evidencia de Validación

Se verificaron los tres endpoints con `standard_id=3`
(ISO 9001:2015) tras aplicar las correcciones.

### 5.1 GET /audits/get-analytics-dataset/?standard_id=3

**Parámetros:** `standard_id=3` (ISO 9001:2015)

**Resultado esperado:** Dataset filtrado para procesos con
datos de ISO 9001, sin incluir procesos de otras normas.

**Resultado obtenido:**

processes_with_audits: 10
total_snapshots: 10
total_risks_evaluated: 25
avg_compliance_score: 66.2%
processes_improving: 3

✅ Correcto — todos los procesos devueltos tienen datos de ISO 9001.

### 5.2 GET /audits/get-risk-predictions/?standard_id=3

**Parámetros:** `standard_id=3` (ISO 9001:2015)

**Resultado esperado:** Predicciones de riesgo solo para procesos
con datos de cumplimiento en ISO 9001.

**Resultado obtenido:**

model_info.type: HEURISTIC
model_info.data_points: 10
summary.total_processes: 10
predictions: ordenadas por risk_score descendente

✅ Correcto — 10 predicciones, todas para procesos con datos ISO 9001.

### 5.3 GET /audits/get-anomaly-detection/?standard_id=3

**Parámetros:** `standard_id=3` (ISO 9001:2015)

**Resultado esperado:** Anomalías detectadas solo en procesos
relevantes para ISO 9001, sin incluir riesgos de procesos ajenos.

**Resultado obtenido:**

total_anomalies: 4
high_severity: 4
medium_severity: 0
low_severity: 0
affected_processes: 4
detected_types: ["HIGH_NPN_RISK"]

✅ Correcto — 4 anomalías, todas de procesos con datos ISO 9001.

### 5.4 Verificación de sistema

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

---

## 6. Limitaciones que Siguen Existiendo

### Volumen de datos

El dataset actual (10 snapshots, 25 evaluaciones de riesgo)
sigue siendo insuficiente para modelos de machine learning
estadísticamente robustos. Los prototipos de F4-02 y F4-03
son exploratorios y sus resultados deben interpretarse como
señales orientativas.

### Umbrales no calibrados estadísticamente

Los pesos del modelo heurístico (40/20/25/15) y los umbrales
del detector de anomalías son juicios expertos. Con más datos
históricos podrían calibrarse estadísticamente.

### Sin integración visual

Los tres endpoints funcionan correctamente pero no tienen
integración visual en el frontend todavía. La capa de
visualización queda fuera del alcance de la Fase 4.

### Datos de prueba sintéticos

Los datos históricos utilizados para validar los prototipos
son datos de prueba generados mediante script. En producción
real, el sistema usará exclusivamente datos de auditorías reales.

---

## 7. Criterio de Cierre

La Fase 4 puede considerarse cerrada cuando se cumplan estas
condiciones:

| Criterio | Estado |
|----------|--------|
| `python manage.py check` sin incidencias | ✅ |
| Filtrado por `standard_id` aplicado correctamente en los tres endpoints | ✅ |
| Selección determinista de evaluaciones de riesgo | ✅ |
| Evidencia funcional reproducible de los tres endpoints | ✅ |
| Documento de correcciones creado en `docs/` | ✅ |

