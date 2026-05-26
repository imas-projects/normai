# Preparación del Dataset Histórico para Analítica Predictiva

**Issue:** F4-01 — Preparación del dataset histórico para analítica predictiva  
**Fase:** FASE 4 — Analítica Predictiva  
**Dependencias:** F3-02 (ComplianceSnapshot), F3-03 (Evolución temporal)  
**Impacto arquitectónico:** Bajo — nuevo módulo de extracción, un endpoint, sin cambios de modelo  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Fuentes de Datos Identificadas](#2-fuentes-de-datos-identificadas)
3. [Variables Definidas](#3-variables-definidas)
4. [Arquitectura del Módulo](#4-arquitectura-del-módulo)
5. [Endpoint Implementado](#5-endpoint-implementado)
6. [Verificación Funcional](#6-verificación-funcional)
7. [Limitaciones y Consideraciones](#7-limitaciones-y-consideraciones)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

La capa predictiva de NormAI (F4-02, F4-03) solo es viable si existe
una base de datos histórica suficientemente estructurada y coherente.
Antes de aplicar cualquier modelo o heurística predictiva es necesario
identificar qué datos están disponibles, qué variables son relevantes
y cómo estructurarlos de forma reutilizable.

### 1.2 Estado de los datos antes de F4-01

| Entidad | Registros disponibles |
|---------|----------------------|
| AnnualPlans | 2 |
| ComplianceSnapshots | 2 |
| RiskIdentifications | 25 |
| RiskEvaluations | 0 |
| Findings | 0 |

La base histórica era insuficiente para cualquier análisis predictivo.
Como parte de F4-01 se generaron datos de prueba representativos que
simulan un histórico realista de auditorías.

### 1.3 Estado después de F4-01

| Entidad | Registros disponibles |
|---------|----------------------|
| AnnualPlans | 10 |
| ComplianceSnapshots | 10 |
| RiskIdentifications | 25 |
| RiskEvaluations | 25 |
| Findings | 2 |
| Procesos con auditorías | 5 |

## 1.4 Generación de datos de prueba

Dado que la base de datos histórica era insuficiente para cualquier
análisis predictivo, se generaron datos de prueba representativos
mediante un script Python ejecutado sobre la base de datos de desarrollo.

### Datos generados

**Evaluaciones de riesgo:**
Se crearon 25 evaluaciones de riesgo para los 25 riesgos identificados
existentes, asignando valores aleatorios de severidad, ocurrencia y
detección (escala 1-10) con semilla fija (`random.seed(42)`) para
garantizar reproducibilidad. El nivel de riesgo se calculó
automáticamente a partir del NPN:

| NPN | Nivel |
|-----|-------|
| ≥ 200 | High |
| 80 – 199 | Moderate |
| < 80 | Low |

**Auditorías y snapshots:**
Se crearon 8 planes de auditoría adicionales cubriendo 4 procesos
distintos en meses diferentes de 2025, con resultados de checklist
variados para simular distintos escenarios de cumplimiento:

| Proceso | Mes | Score | Categoría |
|---------|-----|-------|-----------|
| Control Documental | Feb | 56.2% | PARTIAL |
| Gestión de Proveedores Críticos | Mar | 56.2% | PARTIAL |
| Integración de Sistemas Eléctricos | Abr | 25.0% | LOW |
| Montaje de Fuselaje Central | May | 62.5% | PARTIAL |
| Control Documental | Jun | 81.2% | GOOD |
| Gestión de Proveedores Críticos | Jul | 75.0% | GOOD |
| Integración de Sistemas Eléctricos | Ago | 50.0% | PARTIAL |
| Montaje de Fuselaje Central | Sep | 62.5% | PARTIAL |

**Hallazgos:**
Se generaron 2 hallazgos automáticamente para los planes con score
inferior al 50%, clasificados como NC_MAYOR si el score era menor
del 25% y como NC_MENOR en caso contrario.

### Reproducibilidad

Los datos de prueba se generaron mediante el script `temp_f4_data.py`,
eliminado tras su ejecución. Para regenerar los datos en una base de
datos limpia, los pasos son:

1. Ejecutar `python manage.py populate_standards` para cargar ISO 9001
   y AS9100
2. Crear manualmente al menos un `AuditProgramHeader` desde el admin
3. Recrear el script con la lógica descrita y ejecutarlo

### Nota sobre los datos de producción

Los datos generados son datos de prueba para validar el funcionamiento
del sistema. En un entorno de producción real, el dataset se construirá
exclusivamente a partir de auditorías reales realizadas por la
organización. La calidad y continuidad del dato histórico real
condicionará el valor de cualquier capa predictiva posterior.

---

## 2. Fuentes de Datos Identificadas

Se identificaron cuatro fuentes de datos históricas disponibles en
el sistema:

### 2.1 ComplianceSnapshot

Fuente principal de datos de cumplimiento. Cada snapshot representa
el resultado de una auditoría completa con:
- Score numérico (0-100%)
- Categoría cualitativa (EXCELLENT/GOOD/PARTIAL/LOW/CRITICAL)
- Desglose por requisito en el campo `detail`
- Fecha de cálculo

### 2.2 Findings

Hallazgos de auditoría clasificados en NC_MAYOR, NC_MENOR y
OPORTUNIDAD_MEJORA. Vinculados a un plan de auditoría y a un
`ProcessRequirement` específico.

### 2.3 RiskIdentification + RiskEvaluation

Riesgos identificados por proceso y área, con evaluación de
severidad, ocurrencia y detección. El NPN (Número de Prioridad
de Riesgo) = severidad × ocurrencia × detección es la variable
numérica más relevante para análisis predictivo.

### 2.4 Checklist

Resultados de evaluación ítem a ítem de cada auditoría. Permite
calcular la tasa de conformidad real a nivel de plan, independientemente
del score ponderado del snapshot.

---

## 3. Variables Definidas

### 3.1 Variables a nivel de proceso (dataset de proceso)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `process_id` | ID | Identificador del proceso |
| `process_name` | Texto | Nombre del proceso |
| `latest_score` | Float | Score de cumplimiento más reciente (0-100) |
| `latest_category` | Categórica | EXCELLENT/GOOD/PARTIAL/LOW/CRITICAL |
| `latest_category_value` | Numérica | Valor numérico de la categoría (1-5) |
| `num_audits` | Entero | Número de auditorías realizadas |
| `trend` | Categórica | IMPROVING/DECLINING/STABLE/INSUFFICIENT_DATA |
| `trend_value` | Numérica | 1=mejora, 0=estable, -1=declive |
| `score_delta` | Float | Diferencia entre primer y último score |
| `avg_score` | Float | Score medio histórico |
| `min_score` | Float | Score mínimo histórico |
| `max_score` | Float | Score máximo histórico |
| `nc_mayor_count` | Entero | No conformidades mayores históricas |
| `nc_menor_count` | Entero | No conformidades menores históricas |
| `total_findings` | Entero | Total de hallazgos históricos |
| `total_risks` | Entero | Riesgos identificados en el proceso |
| `high_risks` | Entero | Riesgos de nivel alto |
| `moderate_risks` | Entero | Riesgos de nivel moderado |
| `risk_score` | Float | Score de riesgo agregado (1-3) |
| `normative_coverage` | Entero | Número de requisitos normativos asignados |
| `checklist_compliance_rate` | Float | Tasa de conformidad en checklist (0-100) |

### 3.2 Variables a nivel de snapshot (dataset temporal)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `snapshot_id` | ID | Identificador del snapshot |
| `process_id` | ID | Proceso auditado |
| `score` | Float | Score de cumplimiento (0-100) |
| `category_value` | Numérica | Valor numérico de la categoría (1-5) |
| `calculated_at` | Datetime | Fecha del cálculo |
| `total_requirements` | Entero | Total de requisitos evaluados |
| `compliant_count` | Entero | Requisitos conformes |
| `non_compliant_count` | Entero | Requisitos no conformes |
| `nc_mayor_count` | Entero | NC_MAYOR en este plan |
| `nc_menor_count` | Entero | NC_MENOR en este plan |
| `has_findings` | Booleano | Si el plan tiene hallazgos |

### 3.3 Variables a nivel de riesgo (dataset de riesgos)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `risk_id` | ID | Identificador del riesgo |
| `process_id` | ID | Proceso asociado |
| `severity` | Numérica (0-10) | Severidad del riesgo |
| `occurrence` | Numérica (0-10) | Probabilidad de ocurrencia |
| `detection` | Numérica (0-10) | Capacidad de detección |
| `npn` | Numérica (0-1000) | Número de Prioridad de Riesgo |
| `risk_level` | Categórica | High/Moderate/Low |
| `risk_level_value` | Numérica | 3=High, 2=Moderate, 1=Low |

---

## 4. Arquitectura del Módulo

### 4.1 Módulo creado

audits/analytics_dataset.py

### 4.2 Funciones implementadas

| Función | Descripción |
|---------|-------------|
| `get_process_dataset(standard_id)` | Dataset agregado por proceso |
| `get_snapshot_dataset(standard_id)` | Dataset temporal por snapshot |
| `get_risk_dataset()` | Dataset de riesgos por proceso |
| `get_full_dataset_summary()` | Resumen completo de los tres datasets |

### 4.3 Diseño del módulo

El módulo es **stateless** — no persiste nada en base de datos,
solo extrae y estructura datos existentes. Esto permite:

- Invocar las funciones desde cualquier módulo del sistema
- Obtener siempre datos actualizados sin sincronización
- Reutilizar en F4-02 y F4-03 sin dependencias adicionales

---

## 5. Endpoint Implementado

### GET /audits/get-analytics-dataset/

Devuelve el dataset completo estructurado en tres secciones.

**Parámetro opcional:** `?standard_id=N` para filtrar por norma.

**Estructura de respuesta:**
```json
{
    "dataset_summary": {
        "processes_with_audits": 10,
        "total_snapshots": 10,
        "total_risks_evaluated": 25,
        "avg_compliance_score": 66.2,
        "processes_improving": 3,
        "processes_declining": 0,
        "processes_stable": 0,
        "high_risk_processes": 6
    },
    "process_dataset": [...],
    "snapshot_dataset": [...],
    "risk_dataset": [...]
}
```

---

## 6. Verificación Funcional

GET http://127.0.0.1:8000/audits/get-analytics-dataset/
dataset_summary:
processes_with_audits: 10
total_snapshots: 10
total_risks_evaluated: 25
avg_compliance_score: 66.2%

Los tres datasets devuelven datos correctamente estructurados
con todas las variables definidas en la sección 3.

---

## 7. Limitaciones y Consideraciones

### 7.1 Volumen de datos

El dataset actual contiene 10 snapshots y 25 evaluaciones de riesgo.
Este volumen es suficiente para prototipos exploratorios (F4-02, F4-03)
pero insuficiente para modelos de machine learning estadísticamente
robustos. Cualquier resultado predictivo debe interpretarse como
exploración, no como predicción validada.

### 7.2 Continuidad del histórico

La calidad del análisis predictivo mejorará proporcionalmente con
el número de auditorías realizadas. Cada nuevo `ComplianceSnapshot`
calculado enriquece automáticamente el dataset sin ninguna acción
adicional.

### 7.3 Variables objetivo para F4-02 y F4-03

Las variables más relevantes para predicción de no conformidades son:
- `risk_score` — nivel de riesgo agregado del proceso
- `nc_mayor_count` — historial de no conformidades graves
- `trend_value` — dirección del cumplimiento
- `npn` — número de prioridad de riesgo por evaluación

Para detección de anomalías las variables más relevantes son:
- `score` a nivel de snapshot — para detectar caídas bruscas
- `checklist_compliance_rate` — tasa de conformidad real
- `has_findings` — presencia de hallazgos en la auditoría