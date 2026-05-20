# Cierre de Fase 2 — Generación Dinámica de Checklists y Detección de Brechas

**Rama:** feature/f2-base  
**Estado:** Completada  
**Fecha de cierre:** Mayo 2026  

---

## Issues Completados

| Issue | Título | Estado |
|-------|--------|--------|
| F2-01 | Generación dinámica de checklists según la norma seleccionada | ✅ Done |
| F2-02 | Refactorización de preguntas de auditoría para vincularlas a requisitos estructurados | ✅ Done |
| F2-03 | Detección de brechas de cumplimiento durante auditorías | ✅ Done |

---

## Endpoints y Cambios Principales Implementados

### Nuevos endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/audits/generate-dynamic-checklist/` | Genera automáticamente un checklist para un AnnualPlan a partir de los ProcessRequirements del proceso y la norma seleccionada |
| GET | `/audits/get-checklist/<id>/` | Devuelve el checklist de un AnnualPlan con trazabilidad completa hacia StandardRequirement, Clause y Standard |
| GET | `/audits/get-gap-analysis/<id>/` | Analiza las brechas de cumplimiento de un AnnualPlan clasificándolas en COMPLIANT, NON_COMPLIANT, INSUFFICIENT_EVIDENCE y NOT_EVALUATED |

### Cambios en modelos

| Modelo | Cambio | Issue |
|--------|--------|-------|
| `AnnualProgram` | Nuevo campo FK `standard` para seleccionar la norma a auditar | F2-01 |
| `AuditedEvaluationQuestion` | Nuevas propiedades `standard_requirement`, `clause` y `standard` para acceso directo sin recorrer la cadena | F2-02 |

### Cambios en lógica de IA

| Función | Cambio | Issue |
|---------|--------|-------|
| `suggest_audit_questions` | Actualizada para consumir el dominio normativo estructurado — incluye código de cláusula, nombre de norma, criticidad y contexto aeroespacial en el prompt | F2-02 |

### Limpieza de código

- Eliminado import huérfano `from company.models import Requirement` en `audits/views.py` (F2-02)

---

## Verificación Realizada

### Verificación de sistema

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py migrate --check
# (sin output — todas las migraciones aplicadas)

python manage.py makemigrations --check --dry-run
# No changes detected
```

### Verificación funcional de endpoints

Se crearon datos de prueba desde el shell de Django para validar
el comportamiento de los tres endpoints:

- **Norma:** ISO 9001:2015
- **Proceso:** Montaje de Fuselaje Central
- **ProcessRequirements:** 6 (cláusulas 4.1, 4.2 y 8.5.1)

Resultado del gap analysis con 3 ítems de checklist y 3 sin evaluar:

| Estado | Resultado |
|--------|-----------|
| COMPLIANT | 1 ✅ |
| NON_COMPLIANT | 1 ✅ |
| INSUFFICIENT_EVIDENCE | 1 ✅ |
| NOT_EVALUATED | 3 ✅ |
| compliance_rate | 33.3% ✅ |

Los cuatro tipos de brecha se detectan y clasifican correctamente.

---

## Limitaciones Conocidas y Trabajo Futuro

### Limitaciones actuales

**Integración con la interfaz de usuario**
Los tres endpoints están implementados y funcionan correctamente,
pero la interfaz de usuario no los invoca todavía. El campo `standard`
en `AnnualProgram` existe en el modelo y en el formulario, pero la
plantilla HTML de la vista del programa anual no lo muestra. La
integración visual completa queda pendiente para fases posteriores.

**Invocación manual de la generación dinámica**
El endpoint `generate-dynamic-checklist` requiere una petición POST
manual. No existe todavía un botón en la interfaz que lo invoque
directamente desde la vista del plan de auditoría.

**Regeneración de checklists**
No es posible regenerar un checklist si ya existe uno para el plan.
Hay que eliminarlo manualmente antes de regenerar. No existe todavía
un mecanismo de regeneración segura que preserve las respuestas ya
introducidas.

**Persistencia del análisis de brechas**
El análisis de brechas se calcula en tiempo real en cada petición.
No se persiste en base de datos, lo que es eficiente para el estado
actual pero puede ser un límite si en el futuro se necesita comparar
análisis históricos.

### Trabajo futuro (Fase 3)

- Motor determinista de evaluación del cumplimiento por norma y proceso
- Cálculo del estado de cumplimiento agregado por cláusula y por norma
- Incorporación de la evolución temporal del cumplimiento
- Gap analysis multinorma cruzando ISO 9001 y AS9100 mediante
  los `StandardMapping` implementados en F1-03
- Integración visual de los endpoints en la interfaz de usuario