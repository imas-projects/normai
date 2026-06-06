# Pantalla de Cumplimiento Normativo, Histórico y Comparación de Snapshots

**Issue:** F6-04 — Pantalla de cumplimiento normativo, histórico y comparación de snapshots  
**Fase:** FASE 6 — Representación Visual para Defensa del TFG  
**Dependencias:** F3-01, F3-02, F3-03, F3-04  
**Impacto arquitectónico:** Bajo — nueva vista HTML en app demo, sin cambios de modelo  

---

## Tabla de Contenidos

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Decisiones de Diseño](#2-decisiones-de-diseño)
3. [Implementación](#3-implementación)
4. [Errores Encontrados y Soluciones](#4-errores-encontrados-y-soluciones)
5. [Resultado Final](#5-resultado-final)
6. [Limitaciones](#6-limitaciones)

---

## 1. Contexto y Objetivo

### 1.1 Problema de Partida

El motor determinista de cumplimiento implementado en la Fase 3 es una
de las aportaciones técnicas más importantes del proyecto. Sin una
vista web propia, su valor quedaba completamente oculto — los snapshots
existían en la base de datos pero solo eran consultables mediante
endpoints JSON o el panel de administración de Django.

### 1.2 Objetivo

Crear una pantalla que permita al tribunal ver visualmente cómo funciona
el motor de cumplimiento: calcular snapshots, ver la evolución temporal
con un gráfico, consultar el desglose por requisito de cada snapshot
y comparar dos periodos de auditoría identificando qué requisitos
mejoraron o empeoraron.

---

## 2. Decisiones de Diseño

### 2.1 Layout de dos paneles con tres pestañas

- **Panel izquierdo:** lista de procesos con su score más reciente
- **Panel derecho:** tres pestañas — Histórico, Snapshots y Comparar

Este diseño permite navegar por el sistema de forma guiada durante
la defensa, mostrando primero la evolución temporal y luego el
detalle de cada snapshot.

### 2.2 Gráfico de evolución con ApexCharts

Se utilizó ApexCharts para el gráfico de línea del histórico,
con líneas de referencia horizontales para cada categoría
(EXCELLENT/GOOD/PARTIAL/LOW). Esto permite ver visualmente en qué
categoría se encuentra el proceso en cada momento y si está
mejorando o empeorando.

### 2.3 Navegación por parámetros GET con tab activo

La selección de proceso, norma, snapshot y pestaña activa se gestiona
mediante parámetros GET. Esto permite compartir URLs directas a
vistas específicas durante la presentación.

### 2.4 Comparación a nivel de requisito individual

La pestaña de comparación muestra el cambio estado a estado de cada
requisito entre dos snapshots — no solo el delta global de score.
Esto demuestra la trazabilidad completa del motor de cumplimiento.

---

## 3. Implementación

### 3.1 Vista — `demo/views.py`

La vista `demo_compliance` construye el contexto en cinco pasos:

1. Obtiene los procesos únicos con snapshots disponibles
2. Carga el histórico del proceso seleccionado con
   `get_compliance_history()`
3. Prepara los datos del gráfico como JSON para ApexCharts
4. Carga los snapshots disponibles para la pestaña de comparación
5. Si hay dos snapshots seleccionados, ejecuta
   `compare_compliance_periods()`

### 3.2 Datos del gráfico

Los datos del gráfico se preparan en la vista como JSON y se pasan
al template para ser consumidos por ApexCharts:

```python
chart_data = []
for snap in history_result.get('history', []):
    chart_data.append({
        'x': snap['calculated_at'][:10],
        'y': snap['score'],
        'category': snap['category'],
        'snapshot_id': snap['id'],
    })
```

### 3.3 Pestañas implementadas

| Pestaña | Contenido |
|---------|-----------|
| Histórico | Gráfico ApexCharts + tabla de snapshots con barras de progreso |
| Snapshots | Lista de snapshots clicables + desglose por requisito |
| Comparar | Selector de dos snapshots + tabla de cambios por requisito |

---

## 4. Errores Encontrados y Soluciones

### Error — JSON crudo en el resumen de tendencia

**Causa:** El template usaba `{{ h|last }}` para mostrar el último
elemento de la lista `history_data.history`. El filtro `|last` de
Django imprime el objeto dict completo como string en lugar de un
campo específico.

**Síntoma:** El panel de "Último score" mostraba el JSON completo
del snapshot en lugar del valor numérico.

**Solución:** Calcular `latest_score` y `latest_category` directamente
en la vista y pasarlos como variables independientes al contexto:

```python
latest_score = None
latest_category = None
if history_data and history_data.get('history'):
    last_snap = history_data['history'][-1]
    latest_score = last_snap.get('score')
    latest_category = last_snap.get('category')
```

---

## 5. Resultado Final

La vista es accesible desde:
http://127.0.0.1:8000/demo/cumplimiento/

Y desde la tarjeta "Motor de Cumplimiento" del dashboard F6-01.

### Datos verificados — Montaje de Fuselaje Central

| Snapshot | Fecha | Score | Categoría |
|----------|-------|-------|-----------|
| 1 | 2026-05-21 | 21.9% | CRITICAL |
| 2 | 2026-05-21 | 71.9% | GOOD |
| 6 | 2026-05-26 | 62.5% | PARTIAL |
| 10 | 2026-05-26 | 62.5% | PARTIAL |

**Resumen mostrado:**
- Auditorías realizadas: 4
- Último score: 62.5%
- Tendencia global: IMPROVING ✅

### Gráfico de evolución

El gráfico muestra la evolución temporal con líneas de referencia
por categoría, permitiendo identificar visualmente en qué umbral
se encuentra el proceso en cada momento.

---

## 6. Limitaciones

### Todos los snapshots son ISO 9001:2015

Los datos de prueba generados en F4-01 son todos para ISO 9001:2015.
La pestaña de comparación no puede demostrar comparaciones entre
normas distintas con los datos actuales.

### Fechas coincidentes en algunos snapshots

Los snapshots 1 y 2 tienen la misma fecha (2026-05-21) porque fueron
creados en la misma sesión de pruebas. En producción cada snapshot
correspondería a una auditoría en una fecha distinta.

### Sin cálculo de nuevo snapshot desde la vista

La vista muestra snapshots ya calculados. El cálculo de un nuevo
snapshot desde la interfaz (llamando al endpoint
`calculate-compliance`) no está integrado en la vista demo.