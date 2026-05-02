# Carga Inicial de Datos Normativos — ISO 9001:2015 y AS9100 Rev D

**Issue:** F1-05 — Carga inicial de datos normativos de ISO 9001 y AS9100  
**Fase:** FASE 1 — Integración del Dominio Normativo  
**Dependencias:** F1-02 (Modelos Normativos Estructurados), F1-03 (Estrategia de Mapeo), F1-04 (Refactorización de ProcessRequirement)  
**Impacto arquitectónico:** Medio (carga de datos, sin cambios de modelo)  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Mecanismo de Carga Elegido](#2-mecanismo-de-carga-elegido)
3. [Estructura de Datos Cargados](#3-estructura-de-datos-cargados)
4. [Requisitos Exclusivos de AS9100](#4-requisitos-exclusivos-de-as9100)
5. [Mapeos entre Normas](#5-mapeos-entre-normas)
6. [Verificación e Integridad](#6-verificación-e-integridad)
7. [Conclusiones](#7-conclusiones)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Tras la implementación de los modelos `Standard`, `Clause`, `StandardRequirement` y
`StandardMapping` en issues anteriores, las tablas correspondientes en la base de datos
estaban vacías. Sin datos normativos reales, el nuevo dominio no podía ser validado ni
consumido por las integraciones previstas en fases posteriores del proyecto.

Esta issue resuelve esa situación cargando una base estructurada y coherente de datos
normativos para ISO 9001:2015 y AS9100 Rev D.

### 1.2 Objetivo

Poblar el dominio normativo estructurado con datos reales de ambas normas, cubriendo
la totalidad de sus cláusulas principales y un conjunto representativo de requisitos,
priorizando la consistencia estructural frente al volumen exhaustivo de datos.

---

## 2. Mecanismo de Carga Elegido

### 2.1 Management Command de Django

Se optó por implementar un **management command** de Django como mecanismo de carga,
siguiendo las convenciones del framework para este tipo de operaciones.

**Archivo creado:**

standards/
  management/
  init.py
  commands/
    init.py
    populate_standards.py

**Ventajas de este enfoque frente a alternativas:**

| Enfoque | Ventajas | Inconvenientes |
|---------|----------|----------------|
| Management command | Integrado con Django, reproducible, controlable | Requiere estructura de carpetas específica |
| Fixtures JSON | Nativo de Django | Difícil de mantener con volumen de datos |
| Script Python externo | Simple | No integrado con el ORM ni el entorno Django |
| Migración de datos | Automática al migrar | No apropiada para datos de referencia mutables |

El management command se ejecuta con:

```bash
python manage.py populate_standards
```

### 2.2 Protección contra ejecución duplicada

El comando incluye una comprobación inicial que impide la ejecución si ya existen
normas en la base de datos, evitando duplicados accidentales:

```python
if Standard.objects.exists():
    self.stdout.write(self.style.WARNING(
        'Ya existen normas en la base de datos. '
        'Ejecuta este comando solo en una base de datos limpia.'
    ))
    return
```

---

## 3. Estructura de Datos Cargados

### 3.1 Resultado de la ejecución

Iniciando carga de datos normativos...
Creando ISO 9001:2015...
Creando AS9100 Rev D...
Creando mapeos ISO 9001 ↔ AS9100...
Carga completada correctamente.
ISO 9001 clausulas: 79
ISO 9001 requisitos: 82
AS9100 clausulas: 82
AS9100 requisitos: 107
Mapeos creados: 59

### 3.2 Cobertura de ISO 9001:2015

La norma ISO 9001:2015 se ha cargado cubriendo la totalidad de sus secciones
normativas, desde la cláusula 4 hasta la cláusula 10:

| Sección | Título | Cláusulas |
|---------|--------|-----------|
| 4 | Contexto de la organización | 4, 4.1, 4.2, 4.3, 4.4 |
| 5 | Liderazgo | 5, 5.1, 5.1.1, 5.1.2, 5.2, 5.2.1, 5.2.2, 5.3 |
| 6 | Planificación | 6, 6.1, 6.1.1, 6.1.2, 6.2, 6.3 |
| 7 | Apoyo | 7, 7.1–7.1.6, 7.2, 7.3, 7.4, 7.5, 7.5.1–7.5.3 |
| 8 | Operación | 8, 8.1–8.7 y subcláusulas |
| 9 | Evaluación del desempeño | 9, 9.1–9.3 y subcláusulas |
| 10 | Mejora | 10, 10.1, 10.2, 10.2.1, 10.2.2, 10.3 |

### 3.3 Cobertura de AS9100 Rev D

AS9100 Rev D replica la estructura de ISO 9001:2015 y añade cláusulas y requisitos
específicos del sector aeroespacial. Se han cargado las mismas secciones que ISO 9001
más las extensiones aeroespaciales, resultando en 3 cláusulas adicionales y 25
requisitos adicionales respecto a ISO 9001.

### 3.4 Jerarquía de cláusulas

Ambas normas respetan la jerarquía padre-hijo entre cláusulas mediante el campo
`parent` del modelo `Clause`. Por ejemplo:

8 (Operación)
└── 8.5 (Producción y provisión del servicio)
├── 8.5.1 (Control de la producción)
├── 8.5.2 (Identificación y trazabilidad)
└── 8.5.3 (Propiedad del cliente)

Esta jerarquía permite navegar la estructura normativa de forma coherente y
generará checklists correctamente estructurados en fases posteriores.

---

## 4. Requisitos Exclusivos de AS9100

AS9100 Rev D introduce requisitos específicos del sector aeroespacial que no tienen
equivalente en ISO 9001:2015. Estos requisitos están marcados con `is_extension=True`
en el modelo `StandardRequirement`.

Las principales cláusulas exclusivas de AS9100 son:

### 4.1 Cláusula 8.1.1 — Planificación operacional aeroespacial
Exige determinar los riesgos y oportunidades relacionados con el logro de los
requisitos planificados para productos y servicios, con enfoque específico en
la aeronavegabilidad.

### 4.2 Cláusula 8.1.2 — Gestión de la configuración
Requisito exclusivo del sector aeroespacial. Exige establecer, implementar y mantener
un proceso de gestión de la configuración que incluya identificación, control, registro
del estado y auditoría de la configuración.

### 4.3 Cláusula 8.1.3 — Control de productos suministrados externamente
Amplía los requisitos de control de proveedores con obligaciones específicas sobre
calificación de proveedores, listas de proveedores aprobados y seguimiento del
desempeño de la cadena de suministro aeroespacial.

Además, a lo largo de las cláusulas compartidas con ISO 9001, AS9100 añade
requisitos adicionales marcados como extensión, principalmente en:

- Gestión de riesgos de aeronavegabilidad (6.1.1)
- Cualificación del personal de producción (8.5.1)
- Control de documentos de trabajo (8.5.1)
- Notificación externa ante no conformidades (10.2.1)

---

## 5. Mapeos entre Normas

### 5.1 Implementación del mapeo

Se han creado 59 mapeos entre requisitos de ISO 9001:2015 y AS9100 Rev D,
utilizando el modelo `StandardMapping` implementado en F1-03.

La dirección del mapeo es siempre:
- **source**: requisito de ISO 9001:2015
- **target**: requisito equivalente de AS9100 Rev D

### 5.2 Distribución por tipo de mapeo

| Tipo | Descripción | Cantidad |
|------|-------------|----------|
| EQUIVALENT | Requisito idéntico en ambas normas | ~15 |
| SUPERSET | AS9100 amplía el requisito de ISO 9001 | ~44 |

La mayoría de los mapeos son de tipo SUPERSET, lo que refleja la naturaleza de
AS9100: toma ISO 9001 como base y añade obligaciones adicionales del sector
aeroespacial en prácticamente todas las cláusulas.

### 5.3 Utilidad del mapeo para fases posteriores

Los mapeos permiten responder preguntas como:

- ¿Si un proceso cumple ISO 9001 § 8.5.1, qué parte de AS9100 § 8.5.1 cubre?
- ¿Qué requisitos adicionales de AS9100 quedan sin cubrir?
- ¿Qué cláusulas de AS9100 no tienen correspondencia en ISO 9001?

Esto es la base del motor de evaluación de cumplimiento previsto en la Fase 3.

---

## 6. Verificación e Integridad

### 6.1 Verificación en panel de administración

Tras la ejecución del comando se verificó la integridad de los datos cargados
accediendo al panel de administración de Django:

| Modelo | Registros | Estado |
|--------|-----------|--------|
| Standard | 2 | ✅ |
| Clause (ISO 9001) | 79 | ✅ |
| Clause (AS9100) | 82 | ✅ |
| StandardRequirement (ISO 9001) | 82 | ✅ |
| StandardRequirement (AS9100) | 107 | ✅ |
| StandardMapping | 59 | ✅ |

### 6.2 Navegabilidad validada

Se comprobó que los datos son navegables y relacionables desde el admin:

- Filtrado de cláusulas por norma
- Filtrado de requisitos por norma y por cláusula
- Visualización de mapeos con referencias a ambas normas
- Jerarquía padre-hijo correctamente representada en cláusulas

---

## 7. Conclusiones

Esta issue completa la carga inicial del dominio normativo estructurado de NormAI.
El sistema dispone ahora de una base de datos normativa real, coherente y navegable
que cubre la totalidad de ISO 9001:2015 y AS9100 Rev D.

Los datos cargados están listos para ser consumidos por las siguientes fases:

- **F1-06:** Validación del impacto de integración sobre auditorías, riesgos y procesos
- **F2:** Generación dinámica de checklists de auditoría basados en requisitos formales
- **F3:** Motor determinista de evaluación del cumplimiento por norma y por proceso

La decisión de priorizar consistencia estructural frente a volumen exhaustivo de datos
ha resultado acertada: el sistema es completamente funcional con los datos actuales
y puede ampliarse añadiendo requisitos adicionales sin ningún cambio de modelo.

---

