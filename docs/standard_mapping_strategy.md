# Estrategia de Mapeo Normativo: ISO 9001:2015 ↔ AS9100 Rev D

## 1. Objetivo

Definir cómo NormAI representa las correspondencias entre requisitos de
ISO 9001:2015 y AS9100 Rev D, de forma estructurada y no ambigua, para
habilitar auditorías multinorma, análisis de brechas y evaluación de
cumplimiento cruzado en fases posteriores del proyecto.

---

## 2. Contexto normativo

AS9100 Rev D es la norma de gestión de calidad del sector aeroespacial.
Toma ISO 9001:2015 como base y añade requisitos específicos del sector.

La relación entre ambas normas tiene tres grandes patrones:

- Aproximadamente el 80% de AS9100 replica o amplía requisitos de ISO 9001.
- Un porcentaje de requisitos de AS9100 son extensiones específicas del
  sector aeroespacial sin equivalente directo en ISO 9001.
- ISO 9001 no contiene requisitos exclusivos respecto a AS9100, ya que
  AS9100 la engloba completamente.

---

## 3. Criterios de correspondencia

Para establecer el tipo de relación entre dos requisitos se aplican
los siguientes criterios:

### Criterio 1 — Identidad textual o funcional
Si el texto del requisito de AS9100 replica íntegramente el de ISO 9001,
la relación es EQUIVALENT.

### Criterio 2 — Ampliación
Si AS9100 parte del mismo requisito de ISO 9001 pero añade obligaciones
adicionales, la relación es SUPERSET.
El requisito ISO queda cubierto pero AS9100 exige más.

### Criterio 3 — Especificación parcial
Si AS9100 toma solo una parte del ámbito de un requisito ISO y lo
desarrolla de forma específica, la relación es SUBSET.

### Criterio 4 — Temática común, enfoque diferente
Si ambos requisitos tratan el mismo dominio (ej: gestión del riesgo)
pero desde ángulos distintos sin solapamiento directo, la relación es
RELATED.

### Criterio 5 — Sin correspondencia
Si un requisito de AS9100 no tiene equivalente identificable en ISO 9001,
la relación es NO_EQUIVALENT. Este tipo se aplica principalmente a
requisitos exclusivos del sector aeroespacial.

---

## 4. Tipos de relación definidos

| Tipo | Descripción |
|------|-------------|
| EQUIVALENT | Requisito idéntico o funcionalmente equivalente en ambas normas |
| SUPERSET | AS9100 incluye el requisito ISO 9001 y añade obligaciones adicionales |
| SUBSET | AS9100 desarrolla específicamente una parte de un requisito ISO más amplio |
| RELATED | Mismo dominio temático, distinto enfoque o alcance |
| NO_EQUIVALENT | Requisito exclusivo de una norma, sin correspondencia en la otra |

---

## 5. Representación técnica

El mapeo se implementa mediante el modelo `StandardMapping` en la app
`standards`.

### Estructura del modelo

StandardRequirement (ISO 9001)
│
│  source_requirement (FK)
▼
StandardMapping ──── mapping_type (EQUIVALENT / SUPERSET / ...)
│                     └── notes (texto libre opcional)
│  target_requirement (FK)
▼
StandardRequirement (AS9100)

### Decisiones de diseño

- El mapeo es a nivel de `StandardRequirement`, no de `Clause`.
  Esto garantiza granularidad máxima y evita ambigüedad.
- La dirección del mapeo es siempre: source = ISO 9001, target = AS9100.
  Esta convención es consistente y no ambigua.
- `unique_together` sobre (source_requirement, target_requirement) evita
  duplicados y garantiza integridad referencial.
- El campo `notes` permite documentar matices sin perder estructura formal.
  No es obligatorio y no sustituye al tipo de relación.
- El campo `is_extension` en `StandardRequirement` complementa el mapeo
  marcando directamente los requisitos exclusivos de AS9100.

---

## 6. Ejemplos representativos

### EQUIVALENT — ISO 9001 § 4.1 ↔ AS9100 § 4.1
Ambas normas exigen que la organización determine las cuestiones externas
e internas pertinentes para su propósito. El texto es funcionalmente
idéntico.

### SUPERSET — ISO 9001 § 8.5.1 ↔ AS9100 § 8.5.1
ISO 9001 establece condiciones controladas para la producción y prestación
del servicio. AS9100 incluye todo eso y añade requisitos específicos como
documentación de trabajo, control de cambios, verificación de primer
artículo (FAI) y gestión de la configuración.

### NO_EQUIVALENT — AS9100 § 8.1.1 (sin equivalente en ISO 9001)
AS9100 requiere planificación operacional específica para proyectos
aeroespaciales, incluyendo revisiones de riesgos de producto, planes de
control y criterios de aceptación formales. ISO 9001 no contempla este
nivel de especificidad.

### NO_EQUIVALENT — AS9100 § 8.1.2 (Gestión de la configuración)
Requisito exclusivo del sector aeroespacial. Exige identificar, documentar
y controlar la configuración física y funcional de los productos a lo largo
de su ciclo de vida. ISO 9001 no tiene un equivalente directo.

---

## 7. Utilidad para fases posteriores

| Fase | Uso del mapeo |
|------|---------------|
| F2 — Checklists dinámicos | Generar preguntas de auditoría para AS9100 identificando qué requisitos son extensiones sobre ISO 9001 |
| F3 — Motor de cumplimiento | Calcular cumplimiento cruzado: si un proceso cumple ISO 9001 § X, ¿cubre también AS9100 § Y? |
| Gap analysis | Identificar qué cláusulas de AS9100 no tienen cobertura en los procesos actuales de la organización |

---

## 8. Limitaciones y notas

- El mapeo completo entre todas las cláusulas de ambas normas se realizará
  en F1-05 junto con la carga de datos normativos.
- En esta fase se define la estrategia y se valida con ejemplos
  representativos, no se completa el mapeo exhaustivo.
- Un mal mapeo comprometería las fases F2 y F3. Por ello la estrategia
  debe aprobarse antes de la carga masiva de datos.