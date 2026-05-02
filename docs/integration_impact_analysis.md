# Análisis de Impacto de Integración — Dominio Normativo Multinorma

**Issue:** F1-06 — Validación del impacto de integración sobre auditorías, riesgos y procesos  
**Fase:** FASE 1 — Integración del Dominio Normativo (cierre)  
**Dependencias:** F1-04 (Refactorización de ProcessRequirement), F1-05 (Carga de datos normativos)  
**Impacto arquitectónico:** Analítico — sin cambios de código en esta issue  

---

## Tabla de Contenidos

1. [Objetivo del análisis](#1-objetivo-del-análisis)
2. [Estado del sistema tras Fase 1](#2-estado-del-sistema-tras-fase-1)
3. [Impacto sobre el módulo de auditorías](#3-impacto-sobre-el-módulo-de-auditorías)
4. [Impacto sobre el módulo de riesgos](#4-impacto-sobre-el-módulo-de-riesgos)
5. [Impacto sobre el módulo de procesos](#5-impacto-sobre-el-módulo-de-procesos)
6. [Puntos de integración natural identificados](#6-puntos-de-integración-natural-identificados)
7. [Tareas derivadas para Fase 2](#7-tareas-derivadas-para-fase-2)
8. [Conclusión de viabilidad](#8-conclusión-de-viabilidad)

---

## 1. Objetivo del análisis

Este documento cierra la Fase 1 del proyecto NormAI evaluando el impacto real
que el nuevo dominio normativo estructurado tiene sobre los módulos operativos
ya existentes: auditorías, riesgos y procesos.

El análisis responde a tres preguntas concretas:

- ¿Qué ha cambiado ya en cada módulo como consecuencia de la Fase 1?
- ¿Qué adaptaciones adicionales serán necesarias en fases posteriores?
- ¿Es viable proceder a la Fase 2 sobre la arquitectura actual?

---

## 2. Estado del sistema tras Fase 1

### 2.1 Lo que se ha construido en Fase 1

| Issue | Entregable | Estado |
|-------|-----------|--------|
| F1-01 | Plan de refactorización arquitectónica | ✅ Completado |
| F1-02 | Modelos Standard, Clause, StandardRequirement | ✅ Completado |
| F1-03 | Modelo StandardMapping + estrategia de mapeo | ✅ Completado |
| F1-04 | Refactorización de ProcessRequirement | ✅ Completado |
| F1-05 | Carga de ISO 9001:2015 y AS9100 Rev D | ✅ Completado |

### 2.2 Cadena de trazabilidad conseguida

Tras la Fase 1, el sistema dispone de trazabilidad normativa completa en ambas
direcciones:

Process → ProcessRequirement → StandardRequirement → Clause → Standard
│
StandardMapping
│
StandardRequirement (AS9100)

Esto significa que desde cualquier hallazgo de auditoría se puede llegar hasta
la norma que lo origina, y desde cualquier norma se pueden identificar todos
los procesos que cubren sus requisitos.

### 2.3 Base de datos normativa disponible

| Entidad | ISO 9001:2015 | AS9100 Rev D |
|---------|--------------|--------------|
| Cláusulas | 79 | 82 |
| Requisitos | 82 | 107 |
| Mapeos | 59 (bidireccionales) | — |

---

## 3. Impacto sobre el módulo de auditorías

### 3.1 Cambios ya realizados en Fase 1

El módulo de auditorías es el más afectado por la Fase 1, ya que
`ProcessRequirement` vive en la app `audits` y es el punto de conexión
entre procesos y requisitos normativos.

Los cambios realizados en F1-04 sobre este módulo fueron:

**`audits/models.py` — ProcessRequirement**
El campo `requirement` pasó de `CharField(max_length=200)` a
`ForeignKey(StandardRequirement)`. Esto conecta formalmente cada
`ProcessRequirement` con un requisito estructurado de la norma.

**`audits/models.py` — AuditedEvaluationQuestion y Findings**
Los métodos `as_dict()` se actualizaron para acceder al texto del requisito
a través de la nueva cadena `self.requirement.requirement.text` en lugar
de un string directo.

**`audits/views.py`**
Las queries que construyen listas de requisitos por proceso se actualizaron
para usar `select_related("process", "requirement")` y acceder a
`pr.requirement.text`.

**`audits/forms.py` — ProcessRequirementForm**
El widget del campo `requirement` cambió de `TextInput` a `Select`, ya que
ahora es una FK que Django renderiza como selector de objetos.

**`ai_functions/monitoring_functions.py` — classify_finding_ia**
La función de clasificación de hallazgos por IA se actualizó para extraer
el texto del requisito a través de la nueva FK en lugar de acceder
directamente a un string.

### 3.2 Impacto sobre el flujo de auditoría actual

El flujo de auditoría existente (programa → plan → checklist → hallazgos →
informe → acciones correctivas) funciona correctamente tras los cambios de
F1-04. No se ha roto ninguna funcionalidad existente.

Sin embargo, el flujo actual presenta limitaciones que deberán abordarse
en Fase 2:

**Limitación 1 — Asignación manual de requisitos**
Actualmente los `ProcessRequirement` se crean manualmente desde el panel
de administración, seleccionando uno a uno los `StandardRequirement`
aplicables a cada proceso. Fase 2 debe introducir generación dinámica
de checklists a partir de los requisitos formales de la norma seleccionada.

**Limitación 2 — Preguntas de auditoría no vinculadas dinámicamente**
Las `AuditedEvaluationQuestion` se crean manualmente o con asistencia de IA,
pero no se generan automáticamente a partir de los requisitos normativos
estructurados. Fase 2 debe conectar la generación de preguntas directamente
con `StandardRequirement`.

**Limitación 3 — Sin filtrado por norma**
Las vistas de auditoría actuales no permiten filtrar o seleccionar por norma
(ISO 9001 vs AS9100). Toda la lógica asume implícitamente una sola norma.
Fase 2 debe introducir la selección de norma en el flujo de planificación
de auditorías.

**Limitación 4 — Detección de brechas no implementada**
No existe todavía un mecanismo que identifique automáticamente qué requisitos
de la norma seleccionada no tienen cobertura en los procesos de la organización.
Esta es una de las capacidades clave de Fase 2.

### 3.3 Modelos de auditorías que requerirán adaptación en Fase 2

| Modelo | Adaptación necesaria |
|--------|---------------------|
| `AnnualProgram` | Añadir referencia a `Standard` para indicar qué norma se audita |
| `AuditedEvaluationQuestion` | Conectar generación dinámica con `StandardRequirement` |
| `Checklist` | Permitir generación automática desde requisitos de la norma |
| `Findings` | Mejorar trazabilidad hacia cláusula y norma en los informes |

---

## 4. Impacto sobre el módulo de riesgos

### 4.1 Cambios realizados en Fase 1

El módulo de riesgos (`risks/`) no ha sido modificado directamente en
la Fase 1. Su arquitectura actual es independiente del dominio normativo.

### 4.2 Estado actual de la relación riesgos — norma

Actualmente los riesgos se identifican vinculados a un área y un proceso,
pero sin referencia formal a ningún requisito normativo. La evaluación,
tratamiento, contingencia y reevaluación de riesgos tampoco referencian
ninguna cláusula o norma.

Las funciones de IA del módulo de riesgos (`suggest_risk_fields`,
`suggest_controls`, `suggest_risk_level`, etc.) trabajan con contexto
textual implícito sobre ISO 9001:2015, sin consumir el dominio normativo
estructurado.

### 4.3 Impacto potencial del dominio normativo en riesgos

La relación natural entre riesgos y norma existe en ISO 9001:2015,
concretamente en la cláusula 6.1 (Acciones para abordar riesgos y
oportunidades). AS9100 amplía esta cláusula con requisitos específicos
sobre riesgos de aeronavegabilidad.

Vincular formalmente los riesgos identificados con los requisitos de
la cláusula 6.1 permitiría:

- Trazabilidad entre riesgo identificado y requisito normativo que lo exige
- Evaluación de cumplimiento de la cláusula 6.1 basada en datos reales
- Informes de auditoría que relacionen hallazgos con riesgos y norma

### 4.4 Adaptaciones necesarias en fases posteriores

| Adaptación | Fase recomendada |
|------------|-----------------|
| Añadir FK opcional `standard_requirement` a `RiskIdentification` | Fase 3 |
| Actualizar funciones IA de riesgos para consumir dominio normativo | Fase 3 |
| Incluir cobertura de cláusula 6.1 en motor de cumplimiento | Fase 3 |

El módulo de riesgos no requiere cambios para Fase 2. Su integración
profunda con el dominio normativo es trabajo de Fase 3.

---

## 5. Impacto sobre el módulo de procesos

### 5.1 Cambios realizados en Fase 1

El módulo de procesos (`processes/`) no ha sido modificado directamente
en la Fase 1. La conexión entre procesos y requisitos normativos se
gestiona a través de `ProcessRequirement` en la app `audits`, que actúa
como tabla de relación.

### 5.2 Estado actual de la relación procesos — norma

Los procesos están vinculados al dominio normativo únicamente a través
de `ProcessRequirement`. Un proceso puede tener asociados varios
`StandardRequirement` de cualquier norma cargada en el sistema.

Esta relación ya es funcional tras F1-04 y permite consultas como:

```python
# Obtener todos los requisitos normativos de un proceso
ProcessRequirement.objects.filter(process=proceso).select_related(
    "requirement__clause__standard"
)

# Obtener todos los procesos que cubren un requisito específico
ProcessRequirement.objects.filter(
    requirement__clause__standard__name="ISO 9001:2015",
    requirement__clause__code="8.5.1"
).select_related("process")
```

### 5.3 Limitaciones actuales

**Limitación 1 — Sin indicador de cobertura normativa por proceso**
No existe un mecanismo que muestre, para un proceso dado, qué porcentaje
de los requisitos de la norma seleccionada tiene cubiertos. Esta métrica
es fundamental para el motor de cumplimiento de Fase 3.

**Limitación 2 — Las funciones IA de procesos no consumen el dominio normativo**
Las funciones `process_iso_compliance_ia`, `process_risk_detector_ia` y
`kpis_detector_ia` trabajan con contexto textual implícito. Conectarlas
al dominio normativo estructurado mejoraría la calidad de sus respuestas
y las haría multinorma.

### 5.4 Adaptaciones necesarias en fases posteriores

| Adaptación | Fase recomendada |
|------------|-----------------|
| Añadir indicador de cobertura normativa en la vista de procesos | Fase 3 |
| Conectar funciones IA de procesos con `StandardRequirement` | Fase 3 |
| Vista de gap analysis por proceso y norma | Fase 3 |

El módulo de procesos no requiere cambios para Fase 2.

---

## 6. Puntos de integración natural identificados

Tras el análisis de los tres módulos, se identifican los siguientes
puntos donde el dominio normativo puede integrarse con mayor naturalidad
en las fases siguientes:

### Punto 1 — AnnualProgram → Standard
Añadir una FK de `AnnualProgram` a `Standard` permitiría que cada
programa de auditoría especifique explícitamente qué norma se está
auditando. Este es el punto de entrada natural para los checklists
dinámicos de Fase 2.

### Punto 2 — ProcessRequirement como generador de checklists
`ProcessRequirement` ya vincula proceso y requisito normativo. En Fase 2,
este modelo puede usarse para generar automáticamente las preguntas de
checklist de una auditoría basándose en los requisitos formales de la norma.

### Punto 3 — StandardRequirement → AuditedEvaluationQuestion
La generación de preguntas de auditoría puede automatizarse conectando
directamente `StandardRequirement` con `AuditedEvaluationQuestion`,
usando el texto del requisito y sus metadatos (criticidad, obligatoriedad)
para generar preguntas relevantes.

### Punto 4 — StandardMapping para gap analysis
Los 59 mapeos ISO 9001 ↔ AS9100 permiten identificar automáticamente
qué requisitos adicionales de AS9100 no están cubiertos por los procesos
de una organización que ya tiene cobertura de ISO 9001. Este es el
fundamento del gap analysis de Fase 3.

### Punto 5 — Findings → StandardRequirement para informes
Los hallazgos de auditoría ya referencian `ProcessRequirement`, que a su
vez referencia `StandardRequirement`. Esto permite generar informes que
muestren qué cláusulas y normas concretas presentan no conformidades,
sin cambios adicionales de modelo.

---

## 7. Tareas derivadas para Fase 2

Las siguientes tareas están listas para ser abordadas en Fase 2,
ordenadas por dependencia:

### F2-01 — Generación dinámica de checklists según norma seleccionada
**Descripción:** Implementar la generación automática de listas de verificación
a partir de los `StandardRequirement` de la norma seleccionada para una
auditoría.  
**Prerequisito:** Añadir FK `standard` a `AnnualProgram`.  
**Modelos afectados:** `AnnualProgram`, `Checklist`, `AuditedEvaluationQuestion`.

### F2-02 — Refactorización de preguntas de auditoría
**Descripción:** Conectar la creación de `AuditedEvaluationQuestion` directamente
con `StandardRequirement`, usando sus metadatos para generar preguntas
estructuradas y relevantes.  
**Prerequisito:** F2-01.  
**Modelos afectados:** `AuditedEvaluationQuestion`, `ProcessRequirement`.

### F2-03 — Detección de brechas de cumplimiento durante auditorías
**Descripción:** Implementar un mecanismo que identifique qué requisitos de
la norma seleccionada no tienen cobertura en los procesos del programa
de auditoría.  
**Prerequisito:** F2-01, F2-02.  
**Modelos afectados:** `ProcessRequirement`, `StandardRequirement`, `AnnualProgram`.

---

## 8. Conclusión de viabilidad

### 8.1 Valoración general

La Fase 1 ha conseguido su objetivo principal: transformar NormAI de una
plataforma mononorma con requisitos en texto plano a una plataforma con
dominio normativo estructurado, extensible y con datos reales cargados.

La valoración por dimensión es la siguiente:

| Dimensión | Valoración |
|-----------|-----------|
| Integridad del modelo de datos | ✅ Alta |
| Trazabilidad normativa | ✅ Completa |
| Compatibilidad con módulos existentes | ✅ Sin roturas |
| Datos normativos disponibles | ✅ ISO 9001 + AS9100 |
| Preparación para Fase 2 | ✅ Lista |

### 8.2 Conclusión

El sistema está en condiciones de proceder a la Fase 2. Los módulos de
auditorías, riesgos y procesos funcionan correctamente con la nueva
arquitectura. Los puntos de integración para Fase 2 están claramente
identificados y no requieren cambios estructurales adicionales antes
de comenzar.

El riesgo principal identificado para Fase 2 es la complejidad de la
generación dinámica de checklists, que requiere coordinar `AnnualProgram`,
`Standard`, `ProcessRequirement` y `AuditedEvaluationQuestion` de forma
coherente. Este riesgo es manejable dado que todos los modelos necesarios
ya están implementados y relacionados correctamente.

---