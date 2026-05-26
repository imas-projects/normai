# Prototipo de Predicción de Riesgo de No Conformidad

**Issue:** F4-02 — Prototipo de predicción de riesgo de no conformidad  
**Fase:** FASE 4 — Analítica Predictiva  
**Dependencias:** F4-01 (Dataset histórico)  
**Impacto arquitectónico:** Bajo — nuevo módulo de predicción, un endpoint  

---

## Tabla de Contenidos

1. [Contexto y Enfoque](#1-contexto-y-enfoque)
2. [Diseño del Modelo Heurístico](#2-diseño-del-modelo-heurístico)
3. [Factores y Normalización](#3-factores-y-normalización)
4. [Implementación](#4-implementación)
5. [Endpoint Implementado](#5-endpoint-implementado)
6. [Verificación Funcional](#6-verificación-funcional)
7. [Limitaciones y Evolución Futura](#7-limitaciones-y-evolución-futura)

---

## 1. Contexto y Enfoque

### 1.1 Limitación del volumen de datos

Con 10 snapshots y 25 evaluaciones de riesgo disponibles, el volumen
de datos históricos es insuficiente para aplicar modelos de machine
learning estadísticamente robustos. Un modelo supervisado mínimamente
fiable requeriría centenares de registros etiquetados.

La nota de la issue establece explícitamente:

> *"Debe evitarse presentar este prototipo como un sistema predictivo
> maduro si la base de datos aún es limitada."*

### 1.2 Enfoque adoptado — Modelo heurístico determinista

Se optó por un modelo heurístico determinista basado en ponderación
de factores históricos. Este enfoque es:

- **Técnicamente honesto** — no simula capacidades estadísticas que
  no existen con el volumen de datos actual
- **Interpretable** — cada factor y su peso están documentados y
  justificados
- **Determinista** — dados los mismos datos, produce siempre el mismo
  resultado
- **Evolutivo** — cuando el histórico sea suficiente, los factores
  y pesos pueden reemplazarse por coeficientes aprendidos

---

## 2. Diseño del Modelo Heurístico

### 2.1 Variable objetivo

El modelo estima la **probabilidad de que un proceso genere no
conformidades en su próxima auditoría**, expresada como un score
de riesgo entre 0 y 100.

### 2.2 Factores y pesos

| Factor | Peso | Justificación |
|--------|------|---------------|
| Score de cumplimiento actual | 40% | Principal indicador del estado del proceso |
| Tendencia del cumplimiento | 20% | Dirección del sistema — un proceso que empeora es más arriesgado |
| Nivel de riesgo del proceso | 25% | Riesgos identificados y evaluados condicionan las NC |
| Historial de no conformidades | 15% | Patrón histórico de problemas es el mejor predictor |

### 2.3 Escala de riesgo

| Rango | Categoría | Interpretación |
|-------|-----------|----------------|
| ≥ 75% | HIGH | Alto riesgo de no conformidad |
| 50–74% | MEDIUM | Riesgo moderado de no conformidad |
| 25–49% | LOW | Bajo riesgo de no conformidad |
| < 25% | MINIMAL | Riesgo mínimo de no conformidad |

---

## 3. Factores y Normalización

Cada factor se normaliza a un valor entre 0 y 1 antes de aplicar
los pesos. Todos los factores se orientan de forma que 1.0 representa
máximo riesgo y 0.0 representa mínimo riesgo.

### 3.1 Factor de cumplimiento

f_compliance = 1.0 - (latest_score / 100.0)

A menor cumplimiento, mayor riesgo. Un proceso con score 25%
tiene f_compliance = 0.75.

### 3.2 Factor de tendencia

IMPROVING  (+1) → 0.2  (tendencia positiva reduce el riesgo)
STABLE      (0) → 0.5  (sin cambio significativo)
DECLINING  (-1) → 0.8  (tendencia negativa aumenta el riesgo)

### 3.3 Factor de nivel de riesgo

f_risk = (risk_score - 1.0) / (3.0 - 1.0)

El `risk_score` es el promedio ponderado de evaluaciones de riesgo
del proceso (High=3, Moderate=2, Low=1), normalizado al rango 0-1.

### 3.4 Factor de historial de hallazgos

weighted = (nc_mayor * 2 + nc_menor * 1) / max(1, num_audits)
f_findings = min(1.0, weighted / 2.0)

Las NC_MAYOR pesan el doble que las NC_MENOR. Se relativiza por
el número de auditorías para no penalizar procesos con más historia.

### 3.5 Score final

risk_score = f_compliance × 0.40
+ f_trend      × 0.20
+ f_risk       × 0.25
+ f_findings   × 0.15

---

## 4. Implementación

### 4.1 Módulo creado

audits/risk_predictor.py

### 4.2 Función principal

```python
def predict_non_conformity_risk(standard_id=None):
    """
    Calcula el riesgo de no conformidad para cada proceso con
    datos históricos disponibles.
    Retorna lista ordenada por riesgo descendente con desglose de factores.
    """
```

---

## 5. Endpoint Implementado

### GET /audits/get-risk-predictions/

Devuelve las predicciones de riesgo para todos los procesos.

**Parámetro opcional:** `?standard_id=N` para filtrar por norma.

**Estructura de respuesta:**
```json
{
    "success": true,
    "model_info": {
        "type": "HEURISTIC",
        "version": "1.0",
        "description": "Modelo heurístico determinista...",
        "weights": {
            "compliance": 0.4,
            "trend": 0.2,
            "risk_level": 0.25,
            "findings_history": 0.15
        },
        "data_points": 10
    },
    "summary": {
        "total_processes": 10,
        "high_risk": 1,
        "medium_risk": 3,
        "low_risk": 4,
        "minimal_risk": 2
    },
    "predictions": [
        {
            "process_id": 2,
            "process_name": "Integración de Sistemas Eléctricos",
            "risk_score": 46.5,
            "risk_category": "LOW",
            "factors": {
                "compliance_factor": 50.0,
                "trend_factor": 20.0,
                "risk_level_factor": 60.0,
                "findings_factor": 50.0
            },
            "source_data": {...}
        },
        ...
    ]
}
```

---

## 6. Verificación Funcional

GET http://127.0.0.1:8000/audits/get-risk-predictions/
model_info.type: HEURISTIC
model_info.data_points: 10
summary.total_processes: 10
predictions: ordenadas por risk_score descendente ✅
factores desglosados por proceso ✅
source_data trazable hasta datos originales ✅

---

## 7. Limitaciones y Evolución Futura

### 7.1 Limitaciones actuales

**Volumen de datos insuficiente para ML:**
Con 10 snapshots no es posible entrenar modelos supervisados.
Los pesos actuales (40/20/25/15) son juicios expertos, no
coeficientes aprendidos estadísticamente.

**Sin validación cruzada:**
No es posible medir la precisión del modelo con el volumen
actual — no hay suficientes datos para dividir en train/test.

**Ausencia de variables temporales avanzadas:**
El modelo no incorpora estacionalidad, ciclos de auditoría
ni variables externas que podrían mejorar la predicción.

### 7.2 Evolución hacia ML

Cuando el histórico supere los 100-200 snapshots, el modelo
heurístico puede evolucionar hacia:

- **Regresión logística** para predecir probabilidad de NC_MAYOR
- **Árboles de decisión** para identificar los factores más
  influyentes en cada proceso
- **Series temporales** (ARIMA o similar) para proyectar la
  evolución del score de cumplimiento

El módulo `risk_predictor.py` está diseñado para que esta
evolución sea un cambio interno sin impacto en la API.

