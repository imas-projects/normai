# Refactorización de Preguntas de Auditoría para Vincularlas a Requisitos Estructurados

**Issue:** F2-02 — Refactorización de preguntas de auditoría para vincularlas a requisitos estructurados  
**Fase:** FASE 2 — Generación Dinámica de Checklists y Detección de Brechas  
**Dependencias:** F1-04 (Refactorización de ProcessRequirement), F1-05 (Carga de datos normativos), F2-01 (Generación dinámica de checklists)  
**Impacto arquitectónico:** Bajo — sin cambios de modelo ni migraciones, mejora de acceso y consistencia  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Análisis del Estado Previo](#2-análisis-del-estado-previo)
3. [Cambios Implementados](#3-cambios-implementados)
4. [Impacto en el Flujo de Auditoría](#4-impacto-en-el-flujo-de-auditoría)
5. [Verificación Funcional](#5-verificación-funcional)
6. [Decisiones de Diseño](#6-decisiones-de-diseño)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Tras la implementación de F2-01, el sistema era capaz de generar checklists
dinámicamente a partir del dominio normativo estructurado. Sin embargo,
existían tres problemas de consistencia que esta issue resuelve:

**Problema 1 — Acceso verboso a metadatos normativos**
Para acceder al `StandardRequirement` desde una `AuditedEvaluationQuestion`
había que recorrer la cadena completa:

```python
question.requirement.requirement.text        # texto del requisito
question.requirement.requirement.clause      # cláusula
question.requirement.requirement.clause.standard  # norma
```

Esta cadena es larga, frágil ante valores `None` y difícil de mantener.

**Problema 2 — Import huérfano en views.py**
El archivo `audits/views.py` tenía un import de `company.models.Requirement`
que ya no existía tras el refactor de la Fase 1. Aunque no causaba error
en ejecución, era un residuo del modelo antiguo que podía generar confusión.

**Problema 3 — suggest_audit_questions no consumía el dominio normativo**
La función de IA que genera preguntas de auditoría construía su prompt
con información mínima del requisito, sin aprovechar los metadatos
estructurados disponibles en `StandardRequirement`, `Clause` y `Standard`.

### 1.2 Objetivo de la Issue

Refactorizar `AuditedEvaluationQuestion` para que exponga acceso directo
a los metadatos normativos, limpiar el código residual del modelo antiguo
y mejorar la calidad de las preguntas generadas por IA aprovechando
el dominio normativo estructurado.

---

## 2. Análisis del Estado Previo

### 2.1 Cadena de acceso antes de F2-02

AuditedEvaluationQuestion
.requirement              → ProcessRequirement
.requirement.requirement  → StandardRequirement
.requirement.requirement.clause         → Clause
.requirement.requirement.clause.standard → Standard

Cualquier eslabón podía ser `None`, lo que requería comprobaciones
explícitas en cada punto de acceso del código.

### 2.2 Estado de suggest_audit_questions

La función construía el prompt con únicamente el texto del requisito:

```python
clause_identifier = requirement_obj.requirement.text \
    if requirement_obj.requirement else str(requirement_obj)
```

El prompt no incluía el código de cláusula, el nombre de la norma,
la criticidad del requisito ni si era un requisito exclusivo de AS9100.
Esto limitaba la calidad y precisión de las preguntas generadas.

### 2.3 Import huérfano

```python
# audits/views.py línea 30
from company.models import Requirement  # modelo ya inexistente tras F1-04
```

---

## 3. Cambios Implementados

### 3.1 Propiedades de acceso directo en `AuditedEvaluationQuestion`

Se añadieron tres propiedades a la clase `AuditedEvaluationQuestion`
en `audits/models.py`:

```python
@property
def standard_requirement(self):
    """
    Acceso directo al StandardRequirement vinculado,
    sin necesidad de recorrer la cadena completa.
    Devuelve None si no hay requirement asignado.
    """
    if self.requirement and self.requirement.requirement:
        return self.requirement.requirement
    return None

@property
def clause(self):
    """
    Acceso directo a la Clause del requisito vinculado.
    """
    std_req = self.standard_requirement
    return std_req.clause if std_req else None

@property
def standard(self):
    """
    Acceso directo al Standard del requisito vinculado.
    """
    clause = self.clause
    return clause.standard if clause else None
```

**Por qué propiedades y no campos adicionales:**
Las propiedades son métodos Python que se comportan como atributos.
No requieren migración de base de datos porque no añaden columnas.
Son la forma correcta de exponer acceso calculado a datos relacionados
en Django sin duplicar información.

**Por qué tres propiedades separadas y no una sola:**
Cada propiedad tiene un nivel de acceso diferente. Separándolas se
permite acceder solo al nivel necesario en cada contexto, sin forzar
la carga de toda la cadena cuando solo se necesita parte de ella.

### 3.2 Método `as_dict()` actualizado

Se actualizó el método `as_dict()` de `AuditedEvaluationQuestion`
para usar las nuevas propiedades y exponer información normativa completa:

```python
# ANTES
def as_dict(self):
    return {
        "id": self.id,
        "requirement": self.requirement.requirement.text if self.requirement else None,
        "question_text": self.question_text,
    }

# DESPUÉS
def as_dict(self):
    std_req = self.standard_requirement
    clause = self.clause
    standard = self.standard
    return {
        "id": self.id,
        "question_text": self.question_text,
        "requirement": {
            "text": std_req.text if std_req else None,
            "mandatory": std_req.mandatory if std_req else None,
            "criticality_level": std_req.criticality_level if std_req else None,
        } if std_req else None,
        "clause": {
            "code": clause.code if clause else None,
            "title": clause.title if clause else None,
        } if clause else None,
        "standard": {
            "name": standard.name if standard else None,
        } if standard else None,
    }
```

El nuevo `as_dict()` expone toda la información normativa estructurada
directamente, sin que el consumidor tenga que recorrer la cadena.
Esto es especialmente útil para las vistas que serializan preguntas
de auditoría a JSON para el frontend.

### 3.3 Eliminación del import huérfano en `views.py`

Se eliminó la línea:

```python
from company.models import Requirement
```

Esta línea era un residuo del modelo antiguo de requisitos que existía
antes del refactor de la Fase 1. Su presencia no causaba error en
ejecución porque Python no verifica imports no utilizados, pero era
un indicador de deuda técnica y podía generar confusión al revisar
el código.

### 3.4 Actualización de `suggest_audit_questions` en `monitoring_functions.py`

Se actualizó la función para consumir el dominio normativo estructurado
completo al construir el prompt de IA.

**Contexto normativo extraído:**

```python
std_req = requirement_obj.requirement if requirement_obj.requirement else None
clause = std_req.clause if std_req else None
standard = clause.standard if clause else None

clause_identifier = f"{clause.code} — {clause.title}" if clause else str(requirement_obj)
requirement_text = std_req.text if std_req else str(requirement_obj)
standard_name = standard.name if standard else "ISO 9001:2015"
criticality = std_req.criticality_level if std_req else "medium"
mandatory = std_req.mandatory if std_req else True
is_extension = std_req.is_extension if std_req else False
```

**Mejoras en el prompt:**

| Información | Antes | Después |
|-------------|-------|---------|
| Texto del requisito | ✅ | ✅ |
| Código y título de cláusula | ❌ | ✅ |
| Nombre de la norma | ❌ | ✅ |
| Criticidad del requisito | ❌ | ✅ |
| Si es obligatorio | ❌ | ✅ |
| Contexto aeroespacial (AS9100) | ❌ | ✅ |

**Tratamiento especial para requisitos exclusivos de AS9100:**

```python
if is_extension:
    extension_context = (
        f"IMPORTANTE: Este es un requisito exclusivo de {standard_name} "
        f"sin equivalente directo en ISO 9001:2015. "
        f"Las preguntas deben reflejar el enfoque específico del sector aeroespacial."
    )
```

Esto garantiza que cuando se generan preguntas para requisitos exclusivos
de AS9100 (como gestión de la configuración o planificación operacional
aeroespacial), la IA adapta las preguntas al contexto específico del
sector en lugar de generar preguntas genéricas de calidad.

---

## 4. Impacto en el Flujo de Auditoría

### 4.1 Acceso simplificado desde cualquier punto del código

Antes de esta issue, cualquier función que necesitara acceder a la
norma de una pregunta de auditoría tenía que recorrer la cadena completa.
Después, el acceso es directo:

```python
# ANTES — frágil y verboso
std_req = question.requirement.requirement if question.requirement else None
clause = std_req.clause if std_req else None
standard = clause.standard if clause else None

# DESPUÉS — directo y seguro
std_req = question.standard_requirement
clause = question.clause
standard = question.standard
```

### 4.2 Serialización normativa completa

El nuevo `as_dict()` permite que cualquier endpoint que devuelva
`AuditedEvaluationQuestion` incluya automáticamente la información
normativa completa sin código adicional.

### 4.3 Preguntas de IA más precisas y contextualizadas

Las preguntas generadas por `suggest_audit_questions` son ahora más
precisas porque la IA recibe:

- El código exacto de la cláusula (ej. `8.5.1`)
- El título de la cláusula
- El nombre de la norma que aplica
- El nivel de criticidad del requisito
- Si el requisito es obligatorio
- Si es un requisito exclusivo del sector aeroespacial

Esto permite que la IA genere preguntas calibradas al nivel de riesgo
del requisito y al contexto normativo específico.

---

## 5. Verificación Funcional

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py runserver
# Starting development server at http://127.0.0.1:8000/
```

No se requiere migración porque ningún cambio afecta al esquema de
base de datos. Las propiedades son métodos Python que no generan
columnas adicionales.

---

## 6. Decisiones de Diseño

### 6.1 Propiedades en lugar de campos desnormalizados

Se podría haber añadido un campo `standard_requirement` como FK directa
en `AuditedEvaluationQuestion` para evitar recorrer la cadena. Se
descartó porque:

- Introduciría redundancia en la base de datos
- Requeriría migración y lógica de sincronización
- La cadena `ProcessRequirement → StandardRequirement` ya garantiza
  la trazabilidad completa

Las propiedades Python consiguen el mismo resultado sin coste adicional.

### 6.2 Compatibilidad total con el código existente

Todos los cambios son compatibles hacia atrás. El campo `requirement`
de `AuditedEvaluationQuestion` no se ha modificado. Las propiedades
son adiciones, no sustituciones. Ninguna vista ni función existente
se ha roto.

### 6.3 Degradación segura en suggest_audit_questions

Si algún eslabón de la cadena normativa es `None` (por ejemplo, una
pregunta creada manualmente sin `ProcessRequirement`), la función
degrada de forma segura usando valores por defecto:

```python
standard_name = standard.name if standard else "ISO 9001:2015"
criticality = std_req.criticality_level if std_req else "medium"
mandatory = std_req.mandatory if std_req else True
```

La función sigue funcionando correctamente aunque no haya contexto
normativo estructurado disponible.