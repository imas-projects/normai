# Generación Dinámica de Checklists según la Norma Seleccionada

**Issue:** F2-01 — Generación dinámica de checklists según la norma seleccionada  
**Fase:** FASE 2 — Generación Dinámica de Checklists y Detección de Brechas  
**Dependencias:** F1-04 (Refactorización de ProcessRequirement), F1-05 (Carga de datos normativos), F1-06 (Análisis de impacto)  
**Impacto arquitectónico:** Medio — nuevo campo en AnnualProgram, dos nuevos endpoints, sin rotura de funcionalidad existente  

---

## Tabla de Contenidos

1. [Contexto y Motivación](#1-contexto-y-motivación)
2. [Análisis del Estado Previo](#2-análisis-del-estado-previo)
3. [Diseño de la Solución](#3-diseño-de-la-solución)
4. [Cambios Implementados](#4-cambios-implementados)
5. [Flujo de Generación Dinámica](#5-flujo-de-generación-dinámica)
6. [Trazabilidad entre Checklist y Requisito](#6-trazabilidad-entre-checklist-y-requisito)
7. [Verificación Funcional](#7-verificación-funcional)
8. [Decisiones de Diseño](#8-decisiones-de-diseño)
9. [Limitaciones y Trabajo Futuro](#9-limitaciones-y-trabajo-futuro)

---

## 1. Contexto y Motivación

### 1.1 Problema de Partida

Antes de esta issue, el módulo de auditorías de NormAI generaba sus
checklists de forma completamente manual. El flujo existente requería
que el auditor crease cada `AuditedEvaluationQuestion` y cada ítem de
`Checklist` uno a uno, sin ninguna conexión formal con el dominio
normativo estructurado implementado en la Fase 1.

Este enfoque presentaba tres problemas fundamentales:

- **Desacoplamiento normativo:** Las preguntas del checklist no estaban
  vinculadas a ningún requisito formal de ninguna norma. Dependían
  exclusivamente del criterio manual del auditor.
- **Sin trazabilidad:** No era posible determinar qué cláusula o norma
  respaldaba cada pregunta del checklist.
- **Sin selección de norma:** El módulo de auditorías no sabía qué norma
  se estaba auditando en cada programa. ISO 9001 y AS9100 eran
  indistinguibles desde el punto de vista del sistema.

### 1.2 Objetivo de la Issue

Implementar la lógica que permita generar checklists de auditoría
dinámicamente a partir de los requisitos formales del dominio normativo,
en función de la norma seleccionada para cada programa de auditoría.

---

## 2. Análisis del Estado Previo

### 2.1 Arquitectura del módulo de auditorías antes de F2-01

El flujo de auditorías existente antes de esta issue era el siguiente:

AuditProgramHeader (cabecera del programa anual)
→ AnnualProgram (proceso + mes)          ← sin campo standard
→ AnnualPlan (fechas de auditoría)
→ Checklist (pregunta + cumplimiento + evidencia)
→ AuditedEvaluationQuestion  ← creada manualmente
→ ProcessRequirement     ← proceso + StandardRequirement

### 2.2 Limitación principal

El modelo `AnnualProgram` no tenía ninguna referencia a `Standard`.
Esto significaba que el sistema no podía saber qué norma se estaba
auditando en cada programa, y por tanto no podía filtrar los requisitos
normativos relevantes para generar el checklist automáticamente.

### 2.3 Lo que ya existía y podíamos aprovechar

Gracias a la Fase 1, el sistema disponía de:

- `Standard` con ISO 9001:2015 y AS9100 Rev D cargados
- `Clause` con toda la jerarquía de cláusulas de ambas normas
- `StandardRequirement` con los requisitos formales de cada cláusula
- `ProcessRequirement` vinculando procesos con `StandardRequirement`

Toda la infraestructura normativa estaba lista. Solo faltaba conectarla
con el flujo de auditorías.

---

## 3. Diseño de la Solución

### 3.1 Punto de entrada: AnnualProgram

El punto natural para introducir la selección de norma es `AnnualProgram`,
ya que es el modelo que define qué proceso se audita y en qué mes. Añadir
una FK a `Standard` en este modelo permite que cada programa de auditoría
especifique explícitamente qué norma se está auditando.

### 3.2 Flujo de generación dinámica diseñado

AnnualProgram (proceso + mes + standard)
↓
AnnualPlan (fechas de la auditoría)
↓
generate_dynamic_checklist (endpoint POST)
↓
ProcessRequirement.filter(process=proceso, requirement__clause__standard=norma)
↓
Para cada ProcessRequirement:
→ Crear AuditedEvaluationQuestion con texto basado en el requisito
→ Crear Checklist vinculado al AnnualPlan y a la pregunta
↓
Checklist generado con trazabilidad completa hacia StandardRequirement

### 3.3 Por qué un endpoint POST y no una vista tradicional

Se decidió implementar la generación dinámica como un endpoint JSON por
las siguientes razones:

- Permite invocar la generación desde cualquier punto de la interfaz
  sin recargar la página completa
- Devuelve información detallada sobre los ítems generados, útil para
  depuración y validación
- Es reutilizable desde diferentes vistas o desde scripts de prueba
- Sigue el patrón ya establecido en el módulo para otras operaciones
  asíncronas como `suggest_audit_questions` o `classify_finding`

---

## 4. Cambios Implementados

### 4.1 Nuevo campo `standard` en `AnnualProgram` — `audits/models.py`

Se añadió una FK opcional a `Standard` en el modelo `AnnualProgram`:

```python
standard = models.ForeignKey(
    'standards.Standard',
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name="annual_programs",
    verbose_name="Norma",
    help_text="Norma que se auditará en este programa"
)
```

**Por qué `null=True, blank=True`:** El campo es opcional para mantener
compatibilidad con los programas de auditoría existentes que no tienen
norma asignada. Los programas antiguos siguen funcionando sin cambios.
La generación dinámica simplemente no estará disponible para ellos hasta
que se les asigne una norma.

**Por qué `on_delete=PROTECT`:** No se debe permitir eliminar una norma
si tiene programas de auditoría asociados, ya que eso rompería la
trazabilidad de las auditorías existentes.

Se actualizó también el método `as_dict()` para incluir la norma en la
serialización:

```python
def as_dict(self):
    return {
        "id": self.id,
        "program_header": self.program_header.as_dict(),
        "process": {
            "id": self.process.id,
            "name": self.process.name,
            "code": self.process.process_code
        },
        "month": self.month,
        "standard": {
            "id": self.standard.id,
            "name": self.standard.name,
        } if self.standard else None,
    }
```

### 4.2 Migración — `audits/migrations/0009_add_standard_to_annual_program.py`

Se generó y aplicó la migración correspondiente:

```bash
python manage.py makemigrations audits --name="add_standard_to_annual_program"
python manage.py migrate
```

Resultado:

Migrations for 'audits':
audits\migrations\0009_add_standard_to_annual_program.py
+ Add field standard to annualprogram
Applying audits.0009_add_standard_to_annual_program... OK

La migración es segura porque el campo es nullable, por lo que no
afecta a ningún registro existente.

### 4.3 Formulario actualizado — `audits/forms.py`

Se añadió el campo `standard` al formulario `AnnualProgramForm`:

```python
class AnnualProgramForm(forms.ModelForm):
    class Meta:
        model = AnnualProgram
        fields = ['program_header', 'process', 'month', 'standard']
        widgets = {
            'program_header': forms.Select(attrs={'class': 'form-control'}),
            'process': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12,
                'placeholder': 'Month (1-12)'
            }),
            'standard': forms.Select(attrs={'class': 'form-control'}),
        }
```

### 4.4 Endpoint de generación dinámica — `audits/views.py`

Se implementó la función `generate_dynamic_checklist`:

```python
@require_POST
@csrf_exempt
@login_required
def generate_dynamic_checklist(request):
    """
    Genera automáticamente AuditedEvaluationQuestions y Checklist items
    para un AnnualPlan dado, basándose en los ProcessRequirements del
    proceso y la norma seleccionada en el AnnualProgram.
    """
```

**Lógica de la función:**

1. Lee el `annual_plan_id` del cuerpo de la petición POST (JSON)
2. Obtiene el `AnnualPlan` con sus relaciones (`process`, `standard`)
3. Verifica que el `AnnualProgram` tiene una norma asignada
4. Filtra los `ProcessRequirement` del proceso para la norma seleccionada
5. Verifica que el proceso tiene requisitos asignados para esa norma
6. Verifica que no existe ya un checklist para ese plan
7. Para cada `ProcessRequirement`, en orden de cláusula y requisito:
   - Crea una `AuditedEvaluationQuestion` con texto estructurado
   - Crea un ítem de `Checklist` vinculado al plan y a la pregunta
8. Devuelve un JSON con el resumen de lo generado

**Texto generado para cada pregunta:**

```python
question_text = (
    f"[{req.clause.code}] ¿La organización cumple con el siguiente "
    f"requisito de {standard.name}?: {req.text}"
)
```

Este formato garantiza que cada pregunta incluye el código de cláusula
y el nombre de la norma, haciendo la trazabilidad visible directamente
en el texto de la pregunta.

**Gestión de errores:**

La función devuelve mensajes de error claros y accionables en los
siguientes casos:

| Situación | Mensaje devuelto |
|-----------|-----------------|
| No se proporciona `annual_plan_id` | Error: falta el parámetro |
| El programa no tiene norma asignada | Error con instrucción de cómo asignarla |
| El proceso no tiene requisitos para esa norma | Error con instrucción de cómo añadirlos |
| Ya existe un checklist para ese plan | Error indicando que hay que eliminarlo primero |
| El plan no existe | Error 404 |

### 4.5 Endpoint de consulta — `audits/views.py`

Se implementó la función `get_checklist_for_plan` que devuelve el
checklist de un plan con trazabilidad completa hacia el requisito
normativo:

```python
@login_required
def get_checklist_for_plan(request, annual_plan_id):
    """
    Devuelve el checklist actual de un AnnualPlan con trazabilidad
    completa hacia el requisito normativo.
    """
```

La respuesta incluye para cada ítem del checklist:

```json
{
  "id": 1,
  "orden": 1,
  "compliance": false,
  "evidence": null,
  "question_text": "[4.1] ¿La organización cumple con...",
  "requirement": {
    "text": "La organización debe determinar...",
    "mandatory": true,
    "criticality_level": "high"
  },
  "clause": {
    "code": "4.1",
    "title": "Comprensión de la organización y de su contexto"
  },
  "standard": {
    "name": "ISO 9001:2015"
  }
}
```

### 4.6 Nuevas URLs — `audits/urls.py`

Se registraron las dos nuevas rutas:

```python
path('generate-dynamic-checklist/', views.generate_dynamic_checklist, name='generate_dynamic_checklist'),
path('get-checklist/<int:annual_plan_id>/', views.get_checklist_for_plan, name='get_checklist_for_plan'),
```

---

## 5. Flujo de Generación Dinámica

El flujo completo de generación dinámica de un checklist es el siguiente:

### Paso 1 — Crear el programa de auditoría con norma

El auditor crea un `AnnualProgram` seleccionando proceso, mes y norma
(ISO 9001:2015 o AS9100 Rev D).

### Paso 2 — Crear el plan de auditoría

El auditor crea un `AnnualPlan` a partir del programa, especificando
las fechas y ubicaciones de apertura y cierre.

### Paso 3 — Invocar la generación dinámica

Se realiza una petición POST al endpoint:

POST /audits/generate-dynamic-checklist/
Content-Type: application/json
{
"annual_plan_id": 1
}

### Paso 4 — El sistema genera el checklist

El sistema:
1. Identifica el proceso y la norma del programa
2. Busca todos los `ProcessRequirement` del proceso para esa norma
3. Los ordena por cláusula y por requisito dentro de la cláusula
4. Genera una `AuditedEvaluationQuestion` por cada `ProcessRequirement`
5. Genera un ítem de `Checklist` por cada pregunta

### Paso 5 — Consultar el checklist generado

GET /audits/get-checklist/1/

El sistema devuelve el checklist completo con trazabilidad hacia
`StandardRequirement`, `Clause` y `Standard`.

---

## 6. Trazabilidad entre Checklist y Requisito

La cadena de trazabilidad completa tras esta issue es:

Checklist
→ AuditedEvaluationQuestion
→ ProcessRequirement
→ StandardRequirement
→ Clause
→ Standard

Esto significa que desde cualquier ítem del checklist se puede llegar
hasta la norma concreta y la cláusula específica que lo origina.

En sentido inverso, desde cualquier requisito normativo se pueden
identificar todos los ítems de checklist que lo evalúan en todas
las auditorías del sistema.

---

## 7. Verificación Funcional

### 7.1 Verificación de sistema

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py runserver
# Starting development server at http://127.0.0.1:8000/
```

### 7.2 Verificación de endpoints

| URL | Método | Resultado esperado | Resultado obtenido |
|-----|--------|-------------------|-------------------|
| `/audits/generate-dynamic-checklist/` | GET | HTTP 405 (solo acepta POST) | ✅ HTTP 405 |
| `/audits/get-checklist/1/` | GET | JSON con error 404 (plan no existe) | ✅ JSON correcto |

El HTTP 405 en `generate-dynamic-checklist` es el comportamiento
correcto: el endpoint está decorado con `@require_POST` y rechaza
peticiones GET tal y como está diseñado.

El error 404 en `get-checklist/1/` es correcto: no existe ningún
`AnnualPlan` con id=1 en la base de datos de desarrollo.

### 7.3 Verificación de migración

```bash
python manage.py showmigrations audits
# [X] 0009_add_standard_to_annual_program
```

---

## 8. Decisiones de Diseño

### 8.1 Campo standard opcional en AnnualProgram

Se decidió hacer el campo `standard` nullable para garantizar la
compatibilidad con los programas de auditoría existentes. Los programas
anteriores a esta issue siguen funcionando sin cambios. La generación
dinámica simplemente no estará disponible hasta que se asigne una norma.

### 8.2 get_or_create para AuditedEvaluationQuestion

Se usa `get_or_create` en lugar de `create` para evitar duplicados si
el endpoint se invoca varias veces. Si ya existe una pregunta con el
mismo `requirement` y `question_text`, se reutiliza en lugar de crear
una nueva.

### 8.3 Orden de generación por cláusula y requisito

Los ítems del checklist se generan ordenados por `clause__ordering` y
luego por `requirement__ordering`. Esto garantiza que el checklist sigue
el orden lógico de la norma (cláusula 4 antes que cláusula 5, etc.),
lo que facilita la navegación durante la auditoría.

### 8.4 Verificación de checklist existente

Antes de generar, el endpoint verifica si ya existe un checklist para
el plan. Si existe, devuelve un error en lugar de duplicar los ítems.
Esto protege la integridad de los datos y evita checklists duplicados.

### 8.5 Protección del endpoint con @require_POST y @login_required

El endpoint de generación está protegido con dos decoradores:

- `@require_POST`: Solo acepta peticiones POST, evitando invocaciones
  accidentales desde el navegador
- `@login_required`: Solo usuarios autenticados pueden invocar la
  generación, manteniendo la seguridad del sistema

---

## 9. Limitaciones y Trabajo Futuro

### 9.1 Integración con la interfaz de usuario

El campo `standard` existe en el modelo y en el formulario, pero la
plantilla HTML de la vista del programa anual no lo muestra todavía.
La integración visual completa es trabajo de fases posteriores.

### 9.2 Invocación manual del endpoint

Actualmente la generación dinámica requiere una petición POST manual
al endpoint. En fases posteriores se añadirá un botón en la interfaz
que invoque el endpoint directamente desde la vista del plan de auditoría.

### 9.3 Regeneración de checklists

Actualmente no es posible regenerar un checklist si ya existe uno.
Hay que eliminarlo manualmente antes de regenerar. En fases posteriores
se puede implementar un mecanismo de regeneración segura que preserve
las respuestas ya introducidas.

### 9.4 Cobertura de requisitos

Esta issue genera preguntas únicamente para los `ProcessRequirement`
que ya existen para el proceso y la norma seleccionada. La detección
de brechas (qué requisitos de la norma no están cubiertos por ningún
proceso) es el objetivo de F2-03.

