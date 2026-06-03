# Dashboard Principal de Demostración para Defensa del TFG

**Issue:** F6-01 — Dashboard principal de demostración para defensa del TFG  
**Fase:** FASE 6 — Representación Visual para Defensa del TFG  
**Dependencias:** F5-01, F5-02, F5-03  
**Impacto arquitectónico:** Medio — nueva app Django, nueva vista HTML/JS, corrección en analytics_dataset  

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

Tras las Fases F1-F5, NormAI disponía de una base técnica completa con
modelos, endpoints y lógica de evaluación. Sin embargo, toda esa
funcionalidad solo era accesible a través de endpoints JSON o del panel
de administración de Django — ninguna de las dos opciones es adecuada
para una defensa del TFG ante un tribunal.

F6-01 resuelve esto creando una pantalla principal de demostración que
permite explicar el valor completo de NormAI en menos de un minuto,
sin necesidad de herramientas externas ni conocimientos técnicos.

### 1.2 Objetivo

Crear una página web accesible desde la navegación principal que muestre
visualmente los indicadores ejecutivos del sistema, integrando datos
reales de todas las fases anteriores y proporcionando enlaces hacia
las vistas de detalle de F6-02 a F6-05.

---

## 2. Decisiones de Diseño

### 2.1 Nueva app Django `demo`

Se creó una nueva app Django llamada `demo` para organizar todas las
vistas de la Fase 6. Esta decisión mantiene la separación de
responsabilidades — las vistas de demostración no contaminan las apps
existentes (audits, risks, processes).

### 2.2 Reutilización del endpoint existente

La vista no implementa lógica propia — consume directamente la función
`get_executive_dashboard()` de `audits/executive_dashboard.py`. Esto
garantiza que los datos mostrados son siempre coherentes con los
endpoints JSON de F5.

### 2.3 Estilo visual integrado con la aplicación

El template extiende `mistemplates/mi_base.html` y sigue el mismo
patrón visual que el resto de la aplicación (Bootstrap 5, Velzon theme,
Boxicons, Bootstrap Icons). Esto hace que el dashboard se integre
naturalmente en la navegación existente sin parecer una página externa.

### 2.4 Selector de norma en la cabecera

Se añadió un selector de norma (ISO 9001:2015 / AS9100 Rev D / Todas)
en la cabecera del dashboard. Cuando se selecciona una norma, todos los
bloques se filtran automáticamente para mostrar solo datos de esa norma.

### 2.5 Navegación hacia vistas de detalle

Se incluyeron 4 tarjetas de navegación en la parte inferior que enlazan
hacia las vistas de F6-02 (Catálogo Normativo), F6-03 (Auditorías),
F6-04 (Cumplimiento) y F6-05 (Analítica). Esto permite un recorrido
guiado durante la defensa.

---

## 3. Implementación

### 3.1 Estructura creada
demo/
init.py
views.py
urls.py
apps.py
...
templates/mistemplates/demo/
f6_01_dashboard.html
f6_02_normativo.html      (stub temporal)
f6_03_auditorias.html     (stub temporal)
f6_04_cumplimiento.html   (stub temporal)
f6_05_analitica.html      (stub temporal)

### 3.2 Vista principal — `demo/views.py`

```python
@login_required
def demo_dashboard(request):
    standard_id = request.GET.get('standard_id')
    if standard_id:
        standard_id = int(standard_id)
    dashboard_data = get_executive_dashboard(standard_id=standard_id)
    standards = Standard.objects.filter(is_active=True)
    return render(request, 'mistemplates/demo/f6_01_dashboard.html', {
        'dashboard_data': dashboard_data,
        'standards': standards,
        'selected_standard_id': standard_id,
    })
```

### 3.3 URLs registradas

```python
# demo/urls.py
urlpatterns = [
    path('dashboard/', views.demo_dashboard, name='demo_dashboard'),
    path('normativo/', views.demo_normative_catalog, name='demo_normative_catalog'),
    path('auditorias/', views.demo_audit_checklists, name='demo_audit_checklists'),
    path('cumplimiento/', views.demo_compliance, name='demo_compliance'),
    path('analitica/', views.demo_analytics, name='demo_analytics'),
]

# velzon/urls.py
path('demo/', include('demo.urls')),
```

### 3.4 Entrada en el navbar

Se añadió una entrada directa en `mi_navbar.html`:

```html
<li class="nav-item">
    <a class="nav-link menu-link" href="{% url 'demo:demo_dashboard' %}" role="button">
        <i class="bx bx-shield-quarter"></i> <span>NormAI Demo</span>
    </a>
</li>
```

### 3.5 Bloques del dashboard

El template `f6_01_dashboard.html` organiza la información en 5 bloques:

| Bloque | Contenido |
|--------|-----------|
| KPI principales | Score global, procesos auditados, riesgos, auditorías |
| Cumplimiento por proceso | Tabla con score, barra de progreso, categoría, tendencia |
| Alertas estratégicas | Alertas activas con descripción y acción recomendada |
| Indicadores de madurez | Cobertura, exposición al riesgo, conformidad, NPN máximo |
| Navegación | 4 tarjetas hacia vistas de detalle F6-02 a F6-05 |

### 3.6 Corrección en `audits/analytics_dataset.py`

Durante la implementación se detectó y corrigió un bug en
`get_process_dataset()` que producía filas duplicadas. Ver sección 4.

---

## 4. Errores Encontrados y Soluciones

### Error 1 — ModuleNotFoundError: No module named 'standardsdemo'

**Causa:** En `velzon/settings.py`, `'standards'` y `'demo'` estaban
escritos sin coma entre ellos, haciendo que Python los interpretara
como un único módulo `'standardsdemo'`.

**Síntoma:**
ModuleNotFoundError: No module named 'standardsdemo'

**Solución:** Añadir la coma faltante:
```python
# ANTES
'standards'
'demo',

# DESPUÉS
'standards',
'demo',
```

---

### Error 2 — NoReverseMatch: demo_normative_catalog not found

**Causa:** El template `f6_01_dashboard.html` usaba
`{% url 'demo:demo_normative_catalog' %}` pero esas URLs no existían
todavía en `demo/urls.py` porque las vistas de F6-02 a F6-05 aún no
estaban implementadas.

**Síntoma:**
NoReverseMatch at /demo/dashboard/
Reverse for 'demo_normative_catalog' not found.

**Solución:** Registrar URLs stub para todas las vistas de F6 en
`demo/urls.py` y crear vistas temporales que renderizaran templates
de placeholder, permitiendo que F6-01 funcionara mientras se
implementaban las vistas siguientes.

---

### Error 3 — Procesos duplicados en la tabla de cumplimiento

**Causa:** `get_process_dataset()` en `analytics_dataset.py` obtenía
los `process_id` únicos con `.distinct()`, pero como el mismo proceso
tenía snapshots para ISO 9001 y AS9100, aparecía una vez por cada
norma. El `.distinct()` de Django opera a nivel de fila completa, no
solo sobre el campo `process_id`.

**Síntoma:** La tabla mostraba 10 filas con procesos repetidos en lugar
de 4 procesos únicos.

**Diagnóstico:**
```python
ids = list(ComplianceSnapshot.objects.values_list(
    'process_id', flat=True
).distinct())
# Resultado: [1, 2, 5, 4, 1, 2, 5, 4, 1, 1]  ← duplicados
```

**Solución:** Usar `set()` para deduplicar los `process_id` antes de
iterar:

```python
# ANTES
process_ids = ComplianceSnapshot.objects.filter(
    **filters
).values_list('process_id', flat=True).distinct()

# DESPUÉS
if standard_id:
    process_ids = list(set(
        ComplianceSnapshot.objects.filter(
            standard_id=standard_id
        ).values_list('process_id', flat=True)
    ))
else:
    process_ids = list(set(
        ComplianceSnapshot.objects.values_list(
            'process_id', flat=True
        )
    ))
```

**Resultado tras la corrección:**
```python
ids = list(set(ComplianceSnapshot.objects.values_list(
    'process_id', flat=True
)))
# Resultado: [1, 2, 4, 5]  ← 4 únicos ✅
```

---

## 5. Resultado Final

El dashboard ejecutivo es accesible desde:
http://127.0.0.1:8000/demo/dashboard/

Y desde la entrada **NormAI Demo** en la barra de navegación principal.

### Indicadores mostrados

| Indicador | Valor (datos de prueba) |
|-----------|------------------------|
| Score global | 67.2% PARTIAL |
| Tendencia | IMPROVING |
| Procesos auditados | 4 |
| Riesgos identificados | 20 |
| Auditorías realizadas | 10 |
| Índice de madurez | 83.6 (Alto) |
| Exposición al riesgo | 30.0% |
| NPN máximo | 600 |
| Alertas activas | 1 (HIGH) |

---

## 6. Limitaciones

### Vistas de detalle pendientes

Las 4 tarjetas de navegación (Catálogo Normativo, Auditorías,
Cumplimiento, Analítica) enlazan a páginas stub con el mensaje
"Próximamente". Se implementarán en F6-02 a F6-05.

### Datos de prueba sintéticos

Los indicadores mostrados se basan en datos de prueba generados
durante F4-01. En producción se mostrarán datos de auditorías reales.

### Sin gráficos de evolución temporal

El dashboard actual muestra el estado actual pero no incluye gráficos
de evolución temporal. Estos se implementarán en F6-04 junto con
el motor de cumplimiento.