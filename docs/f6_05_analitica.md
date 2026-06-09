# Vista de Analítica Predictiva, Riesgos y Detección de Anomalías

**Issue:** F6-05 — Vista de analítica predictiva, riesgos y detección de anomalías
**Fase:** FASE 6 — Representación Visual para Defensa del TFG
**Dependencias:** F4-01 (Dataset histórico), F4-02 (Predicción de riesgo), F4-03 (Detección de anomalías)
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

La Fase 4 implementó una capa analítica y predictiva con tres módulos:
dataset histórico, predictor de riesgo de no conformidad y detector
de anomalías. Sin una vista web propia, esta capa quedaba completamente
oculta durante la defensa — el tribunal no podía ver los resultados
sin acceder directamente a los endpoints JSON.

### 1.2 Objetivo

Crear una pantalla que muestre visualmente los resultados de la capa
predictiva de forma interpretable para un perfil no técnico,
comunicando claramente el carácter prototípico del enfoque y su
potencial de evolución futura.

---

## 2. Decisiones de Diseño

### 2.1 Comunicación explícita del carácter prototípico

La nota del issue establece:
> *"Debe evitarse exagerar el grado de madurez de la capa predictiva."*

Se tomaron tres decisiones para cumplir este principio:

- **Badge visible** en la cabecera: "Prototipo exploratorio — modelo heurístico"
- **Aviso contextual** en la parte superior explicando qué es el modelo,
  cuántos datos tiene y qué significan los resultados
- **Nota de evolución futura** al pie explicando hacia dónde puede
  evolucionar el prototipo con más datos

### 2.2 Layout de dos columnas

- **Columna izquierda:** predicciones de riesgo de no conformidad
  con ranking, barras de progreso y desglose de factores
- **Columna derecha:** detección de anomalías con resumen por
  severidad, umbrales configurables y detalle de cada anomalía

### 2.3 Desglose de factores del modelo

Para cada proceso se muestran los 4 factores que componen el score
de riesgo (cumplimiento, nivel de riesgo, tendencia, historial NC)
con sus valores individuales. Esto hace interpretable el modelo
heurístico — el tribunal puede ver exactamente por qué un proceso
tiene más o menos riesgo.

### 2.4 Umbrales del detector visibles

Se muestran los umbrales configurables del detector de anomalías
(score crítico, caída brusca, NPN elevado, cobertura mínima).
Esto demuestra que el sistema es transparente y configurable,
no una caja negra.

---

## 3. Implementación

### 3.1 Vista — `demo/views.py`

```python
@login_required
def demo_analytics(request):
    prediction_result = predict_non_conformity_risk(
        standard_id=selected_standard_id
    )
    anomaly_result = detect_anomalies(
        standard_id=selected_standard_id
    )
```

La vista consume directamente los módulos de F4-02 y F4-03 y pasa
los resultados al template sin lógica adicional.

### 3.2 Datos mostrados

| Sección | Fuente | Datos |
|---------|--------|-------|
| Predicciones | `risk_predictor.py` | 4 procesos, ranking por riesgo, desglose de factores |
| Anomalías | `anomaly_detector.py` | 3 anomalías HIGH, umbrales, detalle por proceso |
| Contexto | `model_info` | Tipo de modelo, versión, descripción, data points |

---

## 4. Resultado Final

La vista es accesible desde:
http://127.0.0.1:8000/demo/analitica/

Y desde la tarjeta "Analítica Predictiva" del dashboard F6-01.

### Predicciones de riesgo verificadas

| Proceso | Risk Score | Categoría |
|---------|-----------|-----------|
| Integración de Sistemas Eléctricos | 46.5% | LOW |
| Gestión de Proveedores Críticos | 26.5% | LOW |
| Control Documental | 21.5% | MINIMAL |
| Montaje de Fuselaje Central | 19.0% | MINIMAL |

### Anomalías detectadas

| Proceso | Tipo | NPN | Severidad |
|---------|------|-----|-----------|
| Integración de Sistemas Eléctricos | HIGH_NPN_RISK | 360 | HIGH |
| Control Documental | HIGH_NPN_RISK | 600 | HIGH |
| Gestión de Proveedores Críticos | HIGH_NPN_RISK | 240 | HIGH |

---

## 5. Limitaciones

### Volumen de datos insuficiente para ML

Con 4 procesos y 10 snapshots los modelos son heurísticos.
Esto se comunica explícitamente en la vista mediante el aviso
contextual y el badge de prototipo.

### Solo anomalías HIGH_NPN_RISK detectadas

Con los datos actuales todos los tipos de anomalía evaluados
producen solo alertas de NPN elevado. Los otros tipos
(SCORE_DROP, CRITICAL_COMPLIANCE, etc.) no se activan porque
los datos de prueba no generan esas condiciones.

### Sin evolución temporal de predicciones

La vista muestra el estado actual de las predicciones pero no
su evolución en el tiempo. Con más snapshots podría mostrarse
cómo ha variado el riesgo de cada proceso entre auditorías.