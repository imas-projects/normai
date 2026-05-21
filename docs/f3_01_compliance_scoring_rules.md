# Reglas de Evaluación Determinista del Cumplimiento

**Issue:** F3-01 — Definición de reglas de evaluación determinista del cumplimiento  
**Fase:** FASE 3 — Motor de Cumplimiento  
**Dependencias:** F2-02 (Refactorización de preguntas), F2-03 (Detección de brechas)  
**Impacto:** Define el modelo conceptual que implementarán F3-02 y F3-03  

---

## Tabla de Contenidos

1. [Objetivo y principios de diseño](#1-objetivo-y-principios-de-diseño)
2. [Nivel 1 — Evaluación por requisito](#2-nivel-1--evaluación-por-requisito)
3. [Nivel 2 — Agregación por proceso](#3-nivel-2--agregación-por-proceso)
4. [Nivel 3 — Agregación por norma](#4-nivel-3--agregación-por-norma)
5. [Influencia de hallazgos](#5-influencia-de-hallazgos)
6. [Influencia de la criticidad](#6-influencia-de-la-criticidad)
7. [Escala de cumplimiento categorial](#7-escala-de-cumplimiento-categorial)
8. [Coherencia con el modelo de datos](#8-coherencia-con-el-modelo-de-datos)
9. [Criterios de agregación temporal](#9-criterios-de-agregación-temporal)

---

## 1. Objetivo y principios de diseño

### 1.1 Objetivo

Definir un conjunto de reglas deterministas, reproducibles y justificables
para evaluar el cumplimiento de requisitos normativos en NormAI, a nivel
de requisito individual, proceso y norma completa.

### 1.2 Principios de diseño

**Determinismo:** Dados los mismos datos de entrada, el sistema siempre
produce el mismo resultado. No hay aleatoriedad ni ambigüedad en las reglas.

**Trazabilidad:** Cada valor de cumplimiento calculado puede trazarse hasta
los datos concretos que lo originaron: qué auditoría, qué checklist, qué
hallazgo, qué requisito.

**Interpretabilidad:** Los resultados deben ser comprensibles por un auditor
sin necesidad de conocer los detalles técnicos del cálculo.

**Jerarquía:** El cumplimiento se evalúa en tres niveles encadenados:
requisito → proceso → norma. Cada nivel superior se deriva de los inferiores.

**Prudencia:** Ante la duda, el sistema asume incumplimiento. Un requisito
sin evidencia no se cuenta como conforme.

---

## 2. Nivel 1 — Evaluación por requisito

### 2.1 Fuente de datos

La evaluación de cada requisito individual se basa en el estado del
`Checklist` correspondiente en la auditoría más reciente del proceso.

El estado del checklist para un `ProcessRequirement` puede ser uno de
los cuatro estados definidos en F2-03:

| Estado | Condición |
|--------|-----------|
| COMPLIANT | `compliance=True` |
| NON_COMPLIANT | `compliance=False` + evidencia con contenido |
| INSUFFICIENT_EVIDENCE | `compliance=False` + evidencia vacía |
| NOT_EVALUATED | Sin ítem de checklist |

### 2.2 Puntuación por estado

Cada estado se traduce a un valor numérico normalizado entre 0 y 1:

| Estado | Puntuación | Justificación |
|--------|-----------|---------------|
| COMPLIANT | 1.0 | Cumplimiento confirmado con evidencia |
| NON_COMPLIANT | 0.0 | Incumplimiento documentado |
| INSUFFICIENT_EVIDENCE | 0.25 | No se puede confirmar cumplimiento; se penaliza pero menos que un incumplimiento real |
| NOT_EVALUATED | 0.0 | Por principio de prudencia, lo no evaluado no cuenta como conforme |

### 2.3 Justificación de la escala

La asimetría entre `INSUFFICIENT_EVIDENCE` (0.25) y `NON_COMPLIANT` (0.0)
es intencional. Un requisito sin evidencia puede deberse a una auditoría
incompleta, no necesariamente a un problema real. Dar 0.25 en lugar de 0.0
incentiva completar la auditoría sin ocultar que hay trabajo pendiente.

`NOT_EVALUATED` recibe 0.0 porque un requisito que nunca se audita no puede
considerarse conforme bajo ningún criterio de calidad.

---

## 3. Nivel 2 — Agregación por proceso

### 3.1 Fórmula base

El cumplimiento de un proceso respecto a una norma se calcula como la
media ponderada de las puntuaciones de sus requisitos:

compliance_score(proceso, norma) =
Σ (puntuación(req_i) × peso(req_i))
─────────────────────────────────────
Σ peso(req_i)

Donde `peso(req_i)` depende de la criticidad y obligatoriedad del requisito.

### 3.2 Tabla de pesos

| criticality_level | mandatory | Peso |
|------------------|-----------|------|
| high | True | 3 |
| high | False | 2 |
| medium | True | 2 |
| medium | False | 1 |
| low | True | 1 |
| low | False | 0.5 |

### 3.3 Justificación de los pesos

Los requisitos de criticidad alta y obligatorios tienen el mayor peso
porque su incumplimiento representa el mayor riesgo para el sistema de
gestión de calidad. Un incumplimiento en un requisito de criticidad alta
debe penalizar más el score global que un incumplimiento en uno de
criticidad baja.

### 3.4 Ejemplo

Proceso con 3 requisitos:

| Requisito | Estado | Puntuación | Peso | Contribución |
|-----------|--------|-----------|------|-------------|
| 4.1 (high, mandatory) | COMPLIANT | 1.0 | 3 | 3.0 |
| 8.5.1 (high, mandatory) | NON_COMPLIANT | 0.0 | 3 | 0.0 |
| 4.2 (medium, mandatory) | INSUFFICIENT_EVIDENCE | 0.25 | 2 | 0.5 |

score = (3.0 + 0.0 + 0.5) / (3 + 3 + 2) = 3.5 / 8 = 0.4375 → 43.75%

---

## 4. Nivel 3 — Agregación por norma

### 4.1 Fórmula

El cumplimiento de una norma en una organización se calcula como la
media ponderada de los cumplimientos de todos los procesos que tienen
requisitos asignados para esa norma:

compliance_score(norma) =
Σ (compliance_score(proceso_i, norma) × n_requisitos(proceso_i, norma))
────────────────────────────────────────────────────────────────────────
Σ n_requisitos(proceso_i, norma)

Donde `n_requisitos(proceso_i, norma)` es el número de `ProcessRequirement`
del proceso para esa norma, usado como factor de ponderación para dar más
peso a los procesos con mayor cobertura normativa.

### 4.2 Justificación

Un proceso con 20 requisitos asignados debe tener más peso en el score
global de la norma que uno con solo 2 requisitos. Esta ponderación evita
que procesos marginales distorsionen el resultado global.

---

## 5. Influencia de hallazgos

### 5.1 Penalización por hallazgos

Los `Findings` de una auditoría pueden penalizar el score de cumplimiento
del requisito al que están asociados, aplicando un factor de penalización
adicional:

| Clasificación del hallazgo | Factor de penalización |
|---------------------------|----------------------|
| NC_MAYOR | -0.3 sobre la puntuación del requisito |
| NC_MENOR | -0.15 sobre la puntuación del requisito |
| OPORTUNIDAD_MEJORA | 0 (sin penalización adicional) |

### 5.2 Aplicación

La penalización se aplica después de calcular la puntuación base del
requisito, con un mínimo de 0:

puntuación_final(req) = max(0, puntuación_base(req) - penalización_hallazgos(req))

### 5.3 Justificación

Una No Conformidad Mayor sobre un requisito que el checklist marcó como
conforme indica una inconsistencia grave. La penalización reduce el score
de ese requisito para reflejar que el cumplimiento no es tan sólido como
el checklist sugería.

---

## 6. Influencia de la criticidad

La criticidad ya está incorporada en el sistema de pesos del Nivel 2.
Adicionalmente, los requisitos con `is_extension=True` (exclusivos de
AS9100) se tratan con los mismos pesos que los requisitos equivalentes
de ISO 9001, sin discriminación positiva ni negativa por ser extensiones.

---

## 7. Escala de cumplimiento categorial

Además del valor numérico (0.0 a 1.0), el sistema asigna una categoría
cualitativa para facilitar la interpretación:

| Rango numérico | Categoría | Interpretación |
|---------------|-----------|----------------|
| 0.85 – 1.00 | EXCELLENT | Cumplimiento sólido |
| 0.70 – 0.84 | GOOD | Cumplimiento satisfactorio con margen de mejora |
| 0.50 – 0.69 | PARTIAL | Cumplimiento parcial, requiere atención |
| 0.25 – 0.49 | LOW | Cumplimiento bajo, requiere acción correctiva |
| 0.00 – 0.24 | CRITICAL | Cumplimiento crítico, requiere acción inmediata |

### 7.1 Justificación de los umbrales

Los umbrales están calibrados para ser exigentes. Un proceso con el 70%
de sus requisitos conformes no alcanza EXCELLENT porque en un sistema de
gestión de calidad aeroespacial el margen de incumplimiento aceptable es
reducido. El umbral de CRITICAL en 0.24 coincide con la puntuación máxima
que puede obtener un proceso cuyos únicos estados son INSUFFICIENT_EVIDENCE.

---

## 8. Coherencia con el modelo de datos

### 8.1 Relación con modelos existentes

| Regla | Fuente de datos |
|-------|----------------|
| Puntuación por requisito | `Checklist.compliance`, `Checklist.evidence` |
| Penalización por hallazgos | `Findings.classification`, `Findings.requirement` |
| Peso por criticidad | `StandardRequirement.criticality_level`, `StandardRequirement.mandatory` |
| Agregación por proceso | `ProcessRequirement`, `AnnualProgram.standard` |
| Agregación por norma | `Standard`, todos los `ProcessRequirement` de la norma |

### 8.2 Auditoría de referencia

El cálculo siempre se basa en la **auditoría más reciente** de cada proceso
para una norma dada. Si un proceso tiene varias auditorías, solo la más
reciente determina su estado de cumplimiento actual.

Para el histórico temporal (F3-03), se conservan los resultados de cada
auditoría para permitir comparación entre periodos.

---

## 9. Criterios de agregación temporal

### 9.1 Decisión de diseño: persistencia vs. recálculo

Los resultados de cumplimiento se **persisten** en un modelo
`ComplianceSnapshot` en lugar de recalcularse en tiempo real.

**Justificación:**
- El recálculo en tiempo real sobre auditorías históricas sería costoso
- La persistencia permite comparar snapshots de diferentes momentos
- Los datos de origen (checklist, hallazgos) pueden modificarse sin
  afectar el histórico ya registrado

### 9.2 Granularidad temporal

Un `ComplianceSnapshot` se genera por cada `AnnualPlan` completado.
La granularidad es por auditoría, no por día ni por semana.

### 9.3 Modelo propuesto para F3-02 y F3-03

```python
class ComplianceSnapshot(models.Model):
    annual_plan     → FK a AnnualPlan
    process         → FK a Process
    standard        → FK a Standard
    score           → FloatField (0.0 a 1.0)
    category        → CharField (EXCELLENT/GOOD/PARTIAL/LOW/CRITICAL)
    total_reqs      → IntegerField
    compliant_reqs  → IntegerField
    non_compliant_reqs → IntegerField
    insufficient_reqs  → IntegerField
    not_evaluated_reqs → IntegerField
    calculated_at   → DateTimeField
    detail          → JSONField (desglose por requisito)
```

Este modelo se implementará en F3-02 y se consumirá en F3-03.

