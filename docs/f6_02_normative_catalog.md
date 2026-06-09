# Vista Visual del Catálogo Normativo y Trazabilidad ISO 9001-AS9100

**Issue:** F6-02 — Vista visual del catálogo normativo y trazabilidad ISO 9001-AS9100
**Fase:** FASE 6 — Representación Visual para Defensa del TFG
**Dependencias:** F1-02 (Modelos normativos), F1-03 (Estrategia de mapeo), F1-05 (Carga de datos)
**Impacto arquitectónico:** Bajo — nueva vista HTML en app demo, sin cambios de modelo

---

## Tabla de Contenidos

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Decisiones de Diseño](#2-decisiones-de-diseño)
3. [Implementación](#3-implementación)
4. [Resultado Final](#4-resultado-final)
5. [Limitaciones](#5-limitaciones)

---

## 1. Contexto y Objetivo

### 1.1 Problema de Partida

La integración del dominio normativo estructurado es una de las
aportaciones técnicas más importantes del proyecto — implementada
en la Fase 1. Sin embargo, sin una vista web propia, esta aportación
quedaba completamente invisible durante la defensa: los datos estaban
en la base de datos pero solo eran accesibles desde el panel de
administración de Django o mediante consultas directas.

F6-02 resuelve esto creando una vista web que permite consultar normas,
cláusulas, requisitos y relaciones entre ISO 9001 y AS9100 de forma
visual e interactiva.

### 1.2 Objetivo

Crear una pantalla de catálogo normativo que permita al tribunal
navegar por la estructura de ISO 9001:2015 y AS9100 Rev D, ver los
requisitos con sus atributos y visualizar las correspondencias entre
ambas normas, demostrando la aportación de la Fase 1 sin necesidad
de herramientas externas.

---

## 2. Decisiones de Diseño

### 2.1 Layout de tres paneles

Se diseñó un layout de tres columnas que refleja la jerarquía natural
del dominio normativo:

Panel izquierdo        Panel central         Panel derecho
─────────────────      ─────────────────     ─────────────────
Selector de norma  →   Requisitos de la  →   Trazabilidad
Árbol de cláusulas     cláusula selec.        ISO 9001 ↔ AS9100

Este diseño permite un recorrido guiado durante la defensa: seleccionar
norma → seleccionar cláusula → ver requisitos y correspondencias.

### 2.2 Navegación por parámetros GET

La selección de norma y cláusula se gestiona mediante parámetros GET
(`?standard_id=N&clause_id=M`). Esto permite compartir URLs directas
a cláusulas específicas durante la presentación, sin estado en sesión.

### 2.3 Visualización de atributos de requisitos

Cada requisito se muestra con sus atributos clave mediante badges:

| Atributo | Visualización |
|----------|---------------|
| `criticality_level` | Badge rojo (HIGH), amarillo (MEDIUM), verde (LOW) |
| `mandatory` | Badge "Obligatorio" |
| `is_extension` | Badge "Extensión AS9100" |

El color del borde izquierdo de cada tarjeta refleja la criticidad,
permitiendo identificar requisitos críticos de un vistazo.

### 2.4 Tarjetas de resumen del mapeo

Se añadieron 4 tarjetas en la cabecera que muestran el resumen
agregado de los 59 mapeos disponibles:

- Total de mapeos ISO ↔ AS9100
- Requisitos equivalentes (EQUIVALENT)
- Requisitos donde AS9100 amplía ISO (SUPERSET)
- Requisitos exclusivos de AS9100 (NO_EQUIVALENT)

---

## 3. Implementación

### 3.1 Vista — `demo/views.py`

```python
@login_required
def demo_normative_catalog(request):
    """
    Vista del catálogo normativo — F6-02
    Muestra normas, cláusulas, requisitos y trazabilidad ISO 9001 ↔ AS9100.
    """
```

La vista recibe `standard_id` y `clause_id` como parámetros GET y
construye el contexto en cuatro pasos:

1. Obtiene las normas activas y la norma seleccionada
2. Carga las cláusulas raíz de la norma seleccionada
3. Si hay cláusula seleccionada, carga sus requisitos, subcláusulas
   y mapeos normativos
4. Calcula el resumen de mapeos y estadísticas de la norma

### 3.2 Consulta de mapeos

Los mapeos se obtienen buscando en ambas direcciones — como origen
y como destino — para los requisitos de la cláusula seleccionada:

```python
mappings = list(
    StandardMapping.objects.filter(
        source_requirement_id__in=req_ids
    ).select_related(...) |
    StandardMapping.objects.filter(
        target_requirement_id__in=req_ids
    ).select_related(...)
)
```

### 3.3 Template — `f6_02_normativo.html`

El template implementa los tres paneles con comportamiento interactivo
basado en clases CSS y parámetros GET:

- **Panel izquierdo:** botones de selección de norma + lista de
  cláusulas raíz con marcado `active` para la seleccionada
- **Panel central:** tres estados — sin selección, cláusula con
  subcláusulas, cláusula con requisitos directos
- **Panel derecho:** mapeos con badges de tipo + leyenda de tipos

---

## 4. Resultado Final

La vista es accesible desde:
http://127.0.0.1:8000/demo/normativo/

Y desde la tarjeta "Catálogo Normativo" del dashboard principal F6-01.

### Ejemplo de navegación verificado

Al seleccionar ISO 9001:2015 → Cláusula 4.1:

| Panel | Contenido mostrado |
|-------|-------------------|
| Izquierdo | 7 cláusulas raíz (4-10) con cláusula 4.1 destacada |
| Central | 2 requisitos con badges HIGH/MEDIUM y Obligatorio |
| Derecho | Mapeo EQUIVALENT: ISO §4.1 → AS9100 §4.1 |

### Estadísticas del catálogo

| Dato | ISO 9001:2015 | AS9100 Rev D |
|------|--------------|--------------|
| Cláusulas | 79 | 82 |
| Requisitos | 82 | 107 |
| Mapeos total | 59 | — |
| Equivalentes | 14 | — |
| SUPERSET | 45 | — |
| NO_EQUIVALENT | 0 | — |

---

## 5. Limitaciones

### Sin CRUD de normas

La vista es de solo lectura. La edición de normas, cláusulas y
requisitos sigue haciéndose desde el panel de administración de Django.
Esto es coherente con el objetivo de la Fase 6 — demostración, no
gestión.

### Subcláusulas de segundo nivel

El árbol de cláusulas muestra solo dos niveles (cláusula raíz y sus
hijos directos). Las subcláusulas de tercer nivel (por ejemplo 5.1.1)
se acceden seleccionando primero la cláusula padre (5.1).

### Requisitos vinculados a procesos

La issue menciona "enlazar requisitos con procesos o auditorías cuando
sea posible". Esta vinculación no se implementó en F6-02 — se muestra
en F6-03 (checklists) y F6-04 (cumplimiento) donde el contexto
de proceso es más natural.