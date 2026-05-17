# Detección de Brechas de Cumplimiento durante Auditorías

**Issue:** F2-03 — Detección de brechas de cumplimiento durante auditorías  
**Fase:** FASE 2 — Generación Dinámica de Checklists y Detección de Brechas  
**Dependencias:** F2-01 (Generación dinámica de checklists), F2-02 (Refactorización de preguntas de auditoría)  
**Impacto arquitectónico:** Bajo — nuevo endpoint de análisis, sin cambios de modelo ni migraciones  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Diseño de la Solución](#2-diseño-de-la-solución)
3. [Lógica de Detección de Brechas](#3-lógica-de-detección-de-brechas)
4. [Cambios Implementados](#4-cambios-implementados)
5. [Verificación Funcional](#5-verificación-funcional)
6. [Decisiones de Diseño](#6-decisiones-de-diseño)
7. [Reutilización en Informes y Evaluación](#7-reutilización-en-informes-y-evaluación)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Tras F2-01 y F2-02, el sistema era capaz de generar checklists dinámicamente
a partir del dominio normativo y vincular cada ítem con su requisito formal.
Sin embargo, no existía ninguna lógica que analizara los resultados de una
auditoría y determinara sistemáticamente dónde había brechas de cumplimiento.

El sistema almacenaba datos de auditoría (compliance, evidencia) pero no
los interpretaba. Para saber el estado de cumplimiento de un proceso respecto
a una norma, había que revisar manualmente cada ítem del checklist.

### 1.2 Distinción entre tipos de brecha

La nota de la issue establece un requisito de diseño importante:

> *"Conviene distinguir claramente entre incumplimiento real, evidencia
> insuficiente y requisito no aplicable."*

Esto determina la arquitectura de la solución: no basta con un booleano
de cumplimiento, hay que categorizar cada brecha de forma precisa.

---

## 2. Diseño de la Solución

### 2.1 Tipos de brecha definidos

Se definieron cuatro estados posibles para cada requisito analizado:

| Estado | Condición | Significado |
|--------|-----------|-------------|
| `COMPLIANT` | `compliance=True` | Cumplimiento confirmado con evidencia |
| `NON_COMPLIANT` | `compliance=False` + evidencia con contenido | Incumplimiento real documentado |
| `INSUFFICIENT_EVIDENCE` | `compliance=False` + evidencia vacía o nula | No se puede determinar el cumplimiento |
| `NOT_EVALUATED` | Sin ítem de checklist para ese requisito | Requisito no evaluado en esta auditoría |

### 2.2 Por qué estos cuatro estados y no solo dos

Un sistema que solo distingue "conforme / no conforme" oculta información
crítica. La diferencia entre `NON_COMPLIANT` e `INSUFFICIENT_EVIDENCE` es
fundamental para el auditor:

- `NON_COMPLIANT` implica que hay evidencia documentada de un problema real.
  Requiere acción correctiva.
- `INSUFFICIENT_EVIDENCE` implica que el ítem no se pudo evaluar correctamente.
  Requiere completar la auditoría, no necesariamente una acción correctiva.

Y `NOT_EVALUATED` es distinto de ambos: el requisito ni siquiera entró en
el checklist de esta auditoría, lo que puede significar que no se consideró
aplicable o que la auditoría está incompleta.

### 2.3 Arquitectura sin modelo nuevo

Se decidió implementar la detección de brechas como un endpoint de análisis
que lee los datos existentes en tiempo real, sin crear un modelo nuevo ni
persistir los resultados del análisis.

**Ventajas:**
- No requiere migración
- Los resultados son siempre frescos — reflejan el estado actual del checklist
- Evita duplicación de datos (el estado de cumplimiento ya está en Checklist)
- Es reutilizable desde cualquier parte del sistema

---

## 3. Lógica de Detección de Brechas

### 3.1 Flujo del análisis

AnnualPlan (id)
↓
Obtener proceso y norma del AnnualProgram
↓
Obtener todos los ProcessRequirements del proceso para la norma
↓
Obtener todos los Checklist items del plan
↓
Construir índice: process_requirement_id → checklist_item
↓
Para cada ProcessRequirement, determinar estado:
├── Sin checklist item → NOT_EVALUATED
├── compliance=True   → COMPLIANT
├── compliance=False + evidencia con contenido → NON_COMPLIANT
└── compliance=False + evidencia vacía → INSUFFICIENT_EVIDENCE
↓
Calcular resumen y tasa de cumplimiento
↓
Devolver JSON con análisis completo

### 3.2 Cálculo de la tasa de cumplimiento

La tasa de cumplimiento se calcula sobre los requisitos evaluados,
excluyendo los `NOT_EVALUATED`:

```python
evaluated = total - not_evaluated
compliance_rate = (compliant / evaluated * 100) if evaluated > 0 else 0
```

Esto es más preciso que calcular sobre el total, ya que los requisitos
no evaluados no deben penalizar ni bonificar el resultado.

### 3.3 Orden del análisis

Los requisitos se analizan ordenados por `clause__ordering` y luego por
`requirement__ordering`, lo que garantiza que el resultado sigue el orden
lógico de la norma (cláusula 4 antes que cláusula 5, etc.).

---

## 4. Cambios Implementados

### 4.1 Nuevo endpoint `get_gap_analysis` — `audits/views.py`

```python
@login_required
@require_GET
def get_gap_analysis(request, annual_plan_id):
    """
    Analiza las brechas de cumplimiento de un AnnualPlan.
    Devuelve un JSON con el análisis completo y un resumen agregado.
    """
```

El endpoint acepta únicamente peticiones GET y requiere autenticación.
Devuelve un JSON con dos secciones:

**Sección `summary`:**
```json
{
    "total": 6,
    "compliant": 1,
    "non_compliant": 1,
    "insufficient_evidence": 1,
    "not_evaluated": 3,
    "compliance_rate": 33.3
}
```

**Sección `gaps`:** Lista con un objeto por cada `ProcessRequirement`,
incluyendo estado, evidencia, metadatos del requisito, cláusula y norma:

```json
{
    "process_requirement_id": 4,
    "status": "NON_COMPLIANT",
    "compliance": false,
    "evidence": "No se encontró registro de seguimiento.",
    "requirement": {
        "text": "La organización debe implementar...",
        "mandatory": true,
        "criticality_level": "high",
        "is_extension": false
    },
    "clause": {
        "code": "8.5.1",
        "title": "Control de la producción y de la provisión del servicio"
    },
    "standard": {
        "name": "ISO 9001:2015"
    },
    "checklist_item_id": 2
}
```

### 4.2 Nueva URL — `audits/urls.py`

```python
path('get-gap-analysis/<int:annual_plan_id>/',
     views.get_gap_analysis,
     name='get_gap_analysis'),
```

---

## 5. Verificación Funcional

### 5.1 Datos de prueba creados

Para validar la lógica se crearon datos de prueba desde el shell de Django:

- **Norma:** ISO 9001:2015
- **Proceso:** Montaje de Fuselaje Central
- **ProcessRequirements creados:** 6 (cláusulas 4.1, 4.2 y 8.5.1)
- **Checklist items creados:** 3 (con los tres tipos de brecha)
- **Requisitos sin evaluar:** 3 (NOT_EVALUATED)

### 5.2 Resultado del endpoint

GET http://127.0.0.1:8000/audits/get-gap-analysis/1/

Resultado obtenido:

| Estado | Esperado | Obtenido |
|--------|----------|----------|
| COMPLIANT | 1 | ✅ 1 |
| NON_COMPLIANT | 1 | ✅ 1 |
| INSUFFICIENT_EVIDENCE | 1 | ✅ 1 |
| NOT_EVALUATED | 3 | ✅ 3 |
| compliance_rate | 33.3% | ✅ 33.3% |

Los cuatro tipos de brecha se detectan y clasifican correctamente.

### 5.3 Verificación de sistema

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py runserver
# Starting development server at http://127.0.0.1:8000/
```

---

## 6. Decisiones de Diseño

### 6.1 Análisis en tiempo real vs. persistencia de resultados

Se optó por calcular el análisis en tiempo real en lugar de persistirlo
en un modelo nuevo. Esto garantiza que los resultados siempre reflejan
el estado actual del checklist, sin necesidad de sincronización entre
tablas ni lógica de invalidación de caché.

### 6.2 Índice por process_requirement_id

Para evitar N+1 queries al relacionar checklist items con requisitos,
se construye un índice en memoria:

```python
checklist_index = {}
for item in checklist_items:
    if item.question and item.question.requirement:
        pr_id = item.question.requirement.id
        checklist_index[pr_id] = item
```

Esto permite hacer la asociación en O(1) por requisito en lugar de
hacer una query por cada uno.

### 6.3 Gestión de errores explícita

El endpoint devuelve mensajes de error claros y accionables:

- Sin norma en el programa → error con instrucción
- Sin ProcessRequirements para esa norma → error con instrucción
- Plan no encontrado → 404

### 6.4 Metadatos normativos en la respuesta

Cada brecha incluye `mandatory`, `criticality_level` e `is_extension`
del requisito. Esto permite que el consumidor de la API priorice las
brechas por criticidad sin necesidad de consultas adicionales.

---

## 7. Reutilización en Informes y Evaluación

Los resultados del endpoint son directamente reutilizables en:

**Informes de auditoría:**
El resumen de brechas puede incluirse automáticamente en el `AuditReport`,
complementando los hallazgos manuales con un análisis sistemático.

**Motor de cumplimiento (Fase 3):**
El campo `compliance_rate` y la lista de brechas por requisito son la
base del motor de evaluación determinista que se implementará en F3.

**Gap analysis multinorma:**
Usando los `StandardMapping` implementados en F1-03, se puede cruzar
el análisis de brechas de ISO 9001 con los requisitos equivalentes de
AS9100, identificando qué requisitos adicionales del sector aeroespacial
quedan sin cobertura.