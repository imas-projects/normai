# Correcciones de Revisión para Cierre de Fase 6

**Documento:** Correcciones post-revisión del tutor — Fase 6
**Issues relacionados:** F6-03, F6-04
**Resultado:** 51/51 tests pasando

---

## 1. Resumen de Cambios

| Corrección | Archivo | Tipo |
|------------|---------|------|
| Generación dinámica de checklist desde la interfaz | `f6_03_auditorias.html`, `demo/views.py` | Funcional |
| Eliminar standard_id = 3 fijo en cumplimiento | `demo/views.py` | Robustez |
| Validación de parámetros GET en todas las vistas | `demo/views.py` | Robustez |

---

## 2. Corrección 1 — Generación dinámica desde la interfaz (F6-03)

### Problema detectado

La vista `/demo/auditorias/` solo mostraba planes que ya tenían
checklist generado. No había ningún mecanismo desde la interfaz
para lanzar la generación dinámica — el criterio de aceptación
de F6-03 quedaba sin cubrir.

### Corrección aplicada

**`demo/views.py`** — se eliminó el filtro `if checklist_count > 0`
para mostrar todos los planes, añadiendo el campo `has_checklist`
al contexto de cada plan.

**`f6_03_auditorias.html`** — los planes sin checklist muestran
un botón **"+ Generar"** que llama al endpoint
`/audits/generate-dynamic-checklist/` mediante JavaScript fetch:

```javascript
fetch('/audits/generate-dynamic-checklist/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': '{{ csrf_token }}',
    },
    body: JSON.stringify({ annual_plan_id: planId })
})
```

Tras la generación exitosa, la página redirige automáticamente
al plan para mostrar el checklist recién creado.

---

## 3. Corrección 2 — standard_id robusto en F6-04

### Problema detectado

En `demo_compliance`, cuando no se especificaba `standard_id`
en la URL se usaba `selected_standard_id = 3` como valor por
defecto. Esto falla si en otra base de datos ISO 9001 tiene
un id distinto.

### Corrección aplicada

Se obtiene el `standard_id` por defecto desde el primer snapshot
disponible en la base de datos:

```python
if not selected_standard_id:
    first_snap = ComplianceSnapshot.objects.select_related(
        'standard'
    ).order_by('id').first()
    if first_snap:
        selected_standard_id = first_snap.standard_id
```

---

## 4. Corrección 3 — Validación de parámetros GET

### Problema detectado

Varias vistas convertían parámetros GET con `int()` directamente.
Un valor no numérico como `?process_id=abc` causaba un error 500.

### Corrección aplicada

Todos los parámetros GET se validan con try/except:

```python
try:
    param = int(param) if param else None
except (ValueError, TypeError):
    param = None
```

Parámetros validados: `standard_id` (en todas las vistas),
`process_id`, `plan_id`, `snapshot_id`, `snap_a`, `snap_b`.

---

## 5. Verificación

### Parámetros inválidos
GET /demo/cumplimiento/?process_id=abc&standard_id=xyz
→ Carga correctamente con el proceso por defecto ✅

### Tests

```bash
python manage.py test audits --verbosity=2
Ran 51 tests in 22.022s — OK ✅
```

### Sistema

```bash
python manage.py check
System check identified no issues (0 silenced). ✅
```