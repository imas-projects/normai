# Revisión de Cierre de Fase 6 y Preparación Final de la Defensa

**Issue:** F6-07 — Revisión de cierre de Fase 6 y preparación final de la defensa
**Fase:** FASE 6 — Representación Visual para Defensa del TFG
**Dependencias:** F6-01, F6-02, F6-03, F6-04, F6-05, F6-06
**Tests:** 51/51 pasando

---

## Tabla de Contenidos

1. [Verificación del Recorrido Completo](#1-verificación-del-recorrido-completo)
2. [Trazabilidad Visual de F1-F5](#2-trazabilidad-visual-de-f1-f5)
3. [Comprobaciones Técnicas](#3-comprobaciones-técnicas)
4. [Limitaciones y Trabajo Futuro](#4-limitaciones-y-trabajo-futuro)
5. [Decisión de Cierre](#5-decisión-de-cierre)

---

## 1. Verificación del Recorrido Completo

### 1.1 Vistas implementadas en F6

| Issue | Vista | URL | Estado |
|-------|-------|-----|--------|
| F6-01 | Dashboard principal | `/demo/dashboard/` | ✅ |
| F6-02 | Catálogo normativo | `/demo/normativo/` | ✅ |
| F6-03 | Auditorías y checklists | `/demo/auditorias/` | ✅ |
| F6-04 | Motor de cumplimiento | `/demo/cumplimiento/` | ✅ |
| F6-05 | Analítica predictiva | `/demo/analitica/` | ✅ |

### 1.2 Navegación verificada

| Acción | Resultado |
|--------|-----------|
| Entrada "NormAI Demo" en navbar | Lleva a `/demo/dashboard/` ✅ |
| Tarjeta "Catálogo Normativo" en dashboard | Lleva a `/demo/normativo/` ✅ |
| Tarjeta "Auditorías y Checklists" en dashboard | Lleva a `/demo/auditorias/` ✅ |
| Tarjeta "Motor de Cumplimiento" en dashboard | Lleva a `/demo/cumplimiento/` ✅ |
| Tarjeta "Analítica Predictiva" en dashboard | Lleva a `/demo/analitica/` ✅ |
| Botón "← Dashboard" en todas las vistas | Vuelve al dashboard ✅ |
| Selector de norma en dashboard | Filtra todos los bloques ✅ |

### 1.3 Recorrido narrativo verificado
Norma ISO 9001 / AS9100
↓ F6-02
Cláusula 4.1 → Requisitos HIGH/MEDIUM → Mapeo EQUIVALENT con AS9100
↓ F6-03
Plan de auditoría → Checklist con trazabilidad → Brecha §8.5.1
↓ F6-04
Snapshot 21.9% CRITICAL → Snapshot 71.9% GOOD → Delta +50%
↓ F6-05
Predicción riesgo NC → Anomalías NPN elevado
↓ F6-01
Dashboard ejecutivo: score 67.2%, tendencia IMPROVING, alerta activa

El recorrido completo puede realizarse desde la interfaz web sin
necesidad de Postman, admin de Django ni explicaciones abstractas.

---

## 2. Trazabilidad Visual de F1-F5

### F1 — Arquitectura multinorma

| Entregable F1 | Representación visual en F6 |
|---------------|----------------------------|
| Modelos Standard, Clause, Requirement | Catálogo normativo F6-02 |
| StandardMapping ISO↔AS9100 | Panel de trazabilidad F6-02 |
| 59 mapeos normativos | Tarjetas de resumen F6-02 |
| ProcessRequirement | Trazabilidad por ítem en F6-03 |

### F2 — Checklists dinámicos y análisis de brechas

| Entregable F2 | Representación visual en F6 |
|---------------|----------------------------|
| Generación dinámica de checklists | Vista F6-03 — checklist por plan |
| Trazabilidad pregunta→requisito→norma | Badges en cada ítem F6-03 |
| Análisis de brechas | Pestaña "Análisis de Brechas" F6-03 |

### F3 — Motor de cumplimiento

| Entregable F3 | Representación visual en F6 |
|---------------|----------------------------|
| Reglas deterministas de evaluación | Desglose por requisito F6-04 |
| ComplianceSnapshot | Vista de snapshots F6-04 |
| Histórico temporal | Gráfico ApexCharts F6-04 |
| Comparación entre periodos | Pestaña "Comparar" F6-04 |

### F4 — Analítica predictiva

| Entregable F4 | Representación visual en F6 |
|---------------|----------------------------|
| Dataset histórico | Datos consumidos por F6-01 y F6-05 |
| Predictor de riesgo NC | Panel izquierdo F6-05 |
| Detector de anomalías | Panel derecho F6-05 |

### F5 — Dashboard ejecutivo

| Entregable F5 | Representación visual en F6 |
|---------------|----------------------------|
| Endpoint executive-dashboard | Datos del dashboard F6-01 |
| Alertas estratégicas | Panel de alertas F6-01 |
| Indicadores de madurez | Tarjetas inferiores F6-01 |

---

## 3. Comprobaciones Técnicas

### 3.1 Sistema

```bash
python manage.py check
# System check identified no issues (0 silenced). ✅
```

### 3.2 Tests

```bash
python manage.py test audits --verbosity=2
# Ran 51 tests in 21.609s — OK ✅
```

### 3.3 App demo

| Componente | Estado |
|------------|--------|
| `demo/views.py` | 6 vistas implementadas ✅ |
| `demo/urls.py` | 5 rutas registradas ✅ |
| `velzon/urls.py` | `path('demo/', include('demo.urls'))` ✅ |
| `velzon/settings.py` | `'demo'` en `INSTALLED_APPS` ✅ |
| Templates en `mistemplates/demo/` | 5 templates implementados ✅ |
| Entrada en navbar | "NormAI Demo" visible ✅ |

### 3.4 Correcciones aplicadas durante F6

| Problema | Solución | Issue |
|----------|----------|-------|
| `ModuleNotFoundError: standardsdemo` | Coma faltante en `INSTALLED_APPS` | F6-01 |
| `NoReverseMatch` en vistas no implementadas | URLs stub + templates placeholder | F6-01 |
| Procesos duplicados en dashboard (10→4) | `set()` en `get_process_dataset()` | F6-01 |
| `ImportError: get_gap_analysis` | Función auxiliar `_get_gap_analysis_data` | F6-03 |
| JSON crudo en tarjeta de último score | Variables `latest_score`/`latest_category` | F6-04 |

---

## 4. Limitaciones y Trabajo Futuro

### 4.1 Limitaciones del prototipo TFG

**Datos sintéticos:**
Los datos históricos son datos de prueba generados en F4-01.
En producción se usarán exclusivamente datos de auditorías reales.

**Volumen de datos para analítica:**
Con 4 procesos y 10 snapshots los modelos predictivos son heurísticos.
Los resultados son señales orientativas, no predicciones validadas.

**Sin CRUD desde las vistas demo:**
Las vistas de F6 son de solo lectura. La creación y edición de
datos sigue haciéndose desde los módulos operativos de la aplicación.

**Sin permisos por perfil:**
Las vistas demo no implementan control de acceso por rol —
cualquier usuario autenticado puede acceder a todas las vistas.

**Sin exportación de informes:**
No hay funcionalidad de exportación a PDF o Excel desde las
vistas de F6.

### 4.2 Siguientes pasos hacia una aplicación empresarial real

| Área | Descripción |
|------|-------------|
| Capa visual completa | Integrar vistas HTML para todos los módulos operativos (riesgos, acciones correctivas, comunicaciones) |
| Acciones correctivas | Vincular NC_MAYOR con seguimiento de acciones correctivas en la interfaz |
| Tratamiento de riesgos | Vista de planes de tratamiento vinculada al catálogo de riesgos |
| Exportación | Generación de informes de auditoría en PDF desde las vistas de cumplimiento |
| Permisos por rol | Control de acceso diferenciado para auditor, responsable de calidad y dirección |
| Datos reales | Sustituir datos de prueba por auditorías reales de la organización |
| Analítica avanzada | Evolucionar el prototipo heurístico hacia modelos estadísticos cuando el histórico supere 100 snapshots |
| Despliegue | Configuración de producción en AWS EC2 con Apache mod_wsgi y PostgreSQL |
| Notificaciones | Envío de alertas estratégicas por email cuando se activen umbrales críticos |

---

## 5. Decisión de Cierre

### 5.1 Criterios de aceptación verificados

| Criterio | Estado |
|----------|--------|
| La Fase 6 puede darse por cerrada con una demo visual coherente | ✅ |
| El alumno puede mostrar el valor del proyecto sin Postman ni admin de Django | ✅ |
| Todos los bloques principales de F1-F5 tienen representación visual | ✅ |
| Quedan documentados los siguientes pasos hacia una aplicación empresarial real | ✅ |
| La revisión diferencia claramente entre prototipo TFG y producto definitivo | ✅ |
| `python manage.py check` sin incidencias | ✅ |
| 51/51 tests pasando | ✅ |

### 5.2 Valoración final

NormAI es un prototipo funcional de sistema de gestión de calidad
multinorma con las siguientes capacidades demostradas:

- Dominio normativo estructurado para ISO 9001:2015 y AS9100 Rev D
  con trazabilidad de requisitos
- Motor determinista de cumplimiento con persistencia histórica
  y comparación entre periodos
- Generación dinámica de checklists con trazabilidad normativa
  y análisis de brechas
- Capa analítica predictiva basada en heurísticas con predicción
  de riesgo de no conformidad y detección de anomalías
- Dashboard ejecutivo que consolida todos los indicadores
- Capa visual completa accesible desde la interfaz web



