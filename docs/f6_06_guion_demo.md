# Preparación de Demo y Guión para el Tribunal

**Issue:** F6-06 — Preparación de datos, navegación y guión de demo para el tribunal
**Fase:** FASE 6 — Representación Visual para Defensa del TFG
**Dependencias:** F6-01, F6-02, F6-03, F6-04, F6-05

---

## Tabla de Contenidos

1. [Recorrido de Demo](#1-recorrido-de-demo)
2. [Guión por Pantalla](#2-guión-por-pantalla)
3. [Datos de Demo Disponibles](#3-datos-de-demo-disponibles)
4. [Checklist de Preparación](#4-checklist-de-preparación)
5. [Plan de Contingencia](#5-plan-de-contingencia)

---

## 1. Recorrido de Demo

El recorrido completo sigue la narrativa del ciclo de calidad de NormAI:
Norma → Cláusula → Requisito → Proceso → Auditoría →
Checklist → Brecha → Cumplimiento → Predicción → Dashboard

### Secuencia recomendada (8-10 minutos)

| Paso | Vista | Duración | Mensaje clave |
|------|-------|----------|---------------|
| 1 | Dashboard | 1 min | Estado global del sistema de calidad |
| 2 | Catálogo Normativo | 2 min | Dominio multinorma estructurado |
| 3 | Auditorías | 2 min | Checklist dinámico con trazabilidad |
| 4 | Cumplimiento | 2 min | Motor determinista y evolución temporal |
| 5 | Analítica | 1 min | Capa predictiva como prototipo académico |
| 6 | Dashboard | 30 seg | Cierre: todo conectado en un panel ejecutivo |

---

## 2. Guión por Pantalla

### Paso 1 — Dashboard principal (`/demo/dashboard/`)

**Abrir con:** `http://127.0.0.1:8000/demo/dashboard/`

**Qué mostrar:**
- Tarjeta de score global: 67.2% PARTIAL, tendencia IMPROVING
- Tabla de cumplimiento: 4 procesos, todos mejorando
- Alerta estratégica activa: riesgos con NPN elevado
- Indicador de madurez: 83.6 (Alto)
- Tarjetas de navegación hacia las vistas de detalle

**Qué decir:**
> "Esta es la pantalla principal de NormAI. De un vistazo podemos ver
> que la organización tiene un cumplimiento global del 67%, categoría
> PARTIAL, con tendencia de mejora. Hay una alerta activa de riesgos
> con NPN elevado. Desde aquí podemos explorar cualquier funcionalidad
> del sistema."

---

### Paso 2 — Catálogo Normativo (`/demo/normativo/`)

**Abrir con:** clic en la tarjeta "Catálogo Normativo" del dashboard

**Qué mostrar:**
1. Tarjetas de resumen: 59 mapeos, 14 equivalentes, 45 SUPERSET
2. Seleccionar ISO 9001:2015 → cláusula 4.1
3. Mostrar 2 requisitos con badges HIGH/MEDIUM y Obligatorio
4. Panel derecho: mapeo EQUIVALENT con AS9100 §4.1
5. Cambiar a AS9100 Rev D y mostrar diferencias

**Qué decir:**
> "NormAI tiene un dominio normativo estructurado con las dos normas
> aeroespaciales principales. Podemos navegar por la jerarquía de
> cláusulas y ver los requisitos con su criticidad. Lo más importante
> es la trazabilidad: este requisito de ISO 9001 es equivalente al
> §4.1 de AS9100. Hay 59 mapeos definidos entre las dos normas."

---

### Paso 3 — Auditorías y Checklists (`/demo/auditorias/`)

**Abrir con:** clic en "Auditorías y Checklists" del dashboard

**Qué mostrar:**
1. Seleccionar Plan 1 (Montaje de Fuselaje Central, mayo 2025)
2. Mostrar checklist con 3 ítems: badges de cláusula, criticidad, evidencia
3. Ítem verde (CONFORME §4.1), rojo (NO CONFORME §8.5.1), amarillo (SIN EVIDENCIA)
4. Clic en pestaña "Análisis de Brechas"
5. Mostrar tabla con estados por requisito

**Qué decir:**
> "Durante una auditoría, el sistema genera dinámicamente el checklist
> según la norma del proceso. Cada pregunta tiene trazabilidad completa
> hasta el requisito normativo. Aquí vemos que el requisito §8.5.1
> no está conforme — eso genera una brecha en el análisis."

---

### Paso 4 — Motor de Cumplimiento (`/demo/cumplimiento/`)

**Abrir con:** clic en "Motor de Cumplimiento" del dashboard

**Qué mostrar:**
1. Seleccionar Montaje de Fuselaje Central
2. Mostrar gráfico de evolución: 21.9% CRITICAL → 71.9% GOOD → 62.5% PARTIAL
3. Tabla con 4 snapshots ordenados cronológicamente
4. Clic en "Snapshots" → seleccionar snapshot 1 → ver desglose por requisito
5. Clic en "Comparar" → seleccionar snapshot 1 y 2 → mostrar delta +50%

**Qué decir:**
> "El motor de cumplimiento calcula y persiste el estado de cada
> auditoría como un snapshot. Aquí vemos la evolución de Montaje de
> Fuselaje: empezó en 21.9% CRITICAL y mejoró a 71.9% GOOD. La
> comparación entre los dos primeros snapshots muestra un delta de
> +50% con 4 requisitos mejorados."

---

### Paso 5 — Analítica Predictiva (`/demo/analitica/`)

**Abrir con:** clic en "Analítica Predictiva" del dashboard

**Qué mostrar:**
1. Señalar el aviso de prototipo en la cabecera
2. Panel de predicciones: ranking de 4 procesos por riesgo de NC
3. Desglose de factores de Integración de Sistemas (46.5% LOW)
4. Panel de anomalías: 3 detectadas HIGH — NPN elevado
5. Señalar la nota de evolución futura al pie

**Qué decir:**
> "La Fase 4 añade una capa analítica predictiva. Este es un prototipo
> heurístico — no machine learning — porque con 4 procesos no hay datos
> suficientes para modelos estadísticos. El valor académico está en la
> arquitectura: cuando haya más datos, los modelos pueden reemplazarse
> sin cambiar la API. Aquí vemos que Integración de Sistemas tiene el
> mayor riesgo de no conformidad, principalmente por su nivel de riesgo
> identificado."

---

### Paso 6 — Cierre en el Dashboard

**Volver a:** `/demo/dashboard/`

**Qué decir:**
> "Volvemos al dashboard ejecutivo, que consolida todo lo que hemos
> visto: cumplimiento por proceso, alertas activas, indicadores de
> madurez y acceso a todas las funcionalidades. Este es el punto de
> entrada natural para un responsable de calidad."

---

## 3. Datos de Demo Disponibles

### Procesos con datos completos

| Proceso | Snapshots | Tendencia | Score actual |
|---------|-----------|-----------|-------------|
| Montaje de Fuselaje Central | 4 | IMPROVING | 62.5% PARTIAL |
| Control Documental | 2 | IMPROVING | 81.2% GOOD |
| Gestión de Proveedores Críticos | 2 | IMPROVING | 75.0% GOOD |
| Integración de Sistemas Eléctricos | 2 | IMPROVING | 50.0% PARTIAL |

### Datos más llamativos para la demo

- **Mayor evolución:** Montaje de Fuselaje Central — de 21.9% CRITICAL a 71.9% GOOD
- **Mejor proceso:** Control Documental — 81.2% GOOD
- **Mayor riesgo NC:** Integración de Sistemas Eléctricos — 46.5%
- **NPN más alto:** Control Documental — NPN 600
- **Trazabilidad visible:** ISO 9001 §4.1 ↔ AS9100 §4.1 (EQUIVALENT)

---

## 4. Checklist de Preparación

### Técnico

- [ ] `python manage.py check` sin errores
- [ ] Servidor arrancado: `python manage.py runserver`
- [ ] Las 5 vistas cargan sin errores
- [ ] El selector de norma filtra correctamente en el dashboard
- [ ] El gráfico de evolución se renderiza en `/demo/cumplimiento/`
- [ ] La comparación de snapshots funciona en la pestaña Comparar

### Datos

- [ ] 4 procesos visibles en el dashboard sin duplicados
- [ ] 10 planes de auditoría en `/demo/auditorias/`
- [ ] Plan 1 tiene checklist con ítems CONFORME/NO CONFORME/SIN EVIDENCIA
- [ ] Snapshot 1 (21.9%) y snapshot 2 (71.9%) comparables en cumplimiento
- [ ] 3 anomalías HIGH visibles en `/demo/analitica/`

### Navegación

- [ ] Todas las tarjetas del dashboard enlazan a sus vistas correctamente
- [ ] El botón "← Dashboard" funciona en todas las vistas de detalle
- [ ] La entrada "NormAI Demo" del navbar lleva al dashboard

---

## 5. Plan de Contingencia

Si durante la defensa hay problemas técnicos:

### Si el servidor no arranca

```bash
# Verificar que no hay otro proceso en el puerto 8000
python manage.py check
python manage.py runserver 8001
```

Acceder desde `http://127.0.0.1:8001/demo/dashboard/`

### Si una vista da error

Cada vista es independiente — si una falla, el resto siguen
funcionando. Omitir esa vista del recorrido y continuar con la
siguiente.

### Capturas de pantalla de respaldo

Guardar capturas de las 5 vistas en un directorio local antes
de la defensa. Si el sistema falla completamente, las capturas
permiten continuar la explicación.

### URLs de respaldo rápido
Dashboard:    /demo/dashboard/
Normativo:    /demo/normativo/?standard_id=3&clause_id=5
Auditorías:   /demo/auditorias/?plan_id=1
Cumplimiento: /demo/cumplimiento/?process_id=1&standard_id=3
Analítica:    /demo/analitica/