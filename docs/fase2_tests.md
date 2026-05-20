# Tests Automatizados — Fase 2

**Archivo:** `audits/tests.py`  
**Fase:** FASE 2 — Generación Dinámica de Checklists y Detección de Brechas  
**Resultado:** 20/20 tests pasando  

---

## Tabla de Contenidos

1. [Qué son los tests y para qué sirven](#1-qué-son-los-tests-y-para-qué-sirven)
2. [Cómo funcionan los tests en Django](#2-cómo-funcionan-los-tests-en-django)
3. [Estructura general del archivo de tests](#3-estructura-general-del-archivo-de-tests)
4. [GapAnalysisTestCase — Tests del endpoint get_gap_analysis](#4-gapanalysistestcase--tests-del-endpoint-get_gap_analysis)
5. [GenerateDynamicChecklistTestCase — Tests del endpoint generate_dynamic_checklist](#5-generatedynamicchecklisttestcase--tests-del-endpoint-generate_dynamic_checklist)
6. [Cómo ejecutar los tests](#6-cómo-ejecutar-los-tests)
7. [Resultado de la ejecución](#7-resultado-de-la-ejecución)

---

## 1. Qué son los tests y para qué sirven

Los tests automatizados son código que verifica automáticamente que el
sistema funciona correctamente. En lugar de probar manualmente cada
funcionalidad en el navegador, los tests lo hacen de forma automática
y reproducible en segundos.

### Ventajas principales

**Detección temprana de errores:** Si un cambio futuro rompe una
funcionalidad existente, los tests lo detectan inmediatamente al
ejecutarse, antes de que el error llegue a producción.

**Documentación viva:** Cada test describe con precisión qué debe
hacer el sistema. Leer los tests es una forma de entender el
comportamiento esperado de cada endpoint.

**Confianza en los cambios:** Con tests en verde, se puede modificar
el código con la seguridad de que si algo se rompe, los tests lo
detectarán.

**Reproducibilidad:** Los tests crean su propia base de datos temporal,
ejecutan las comprobaciones y la destruyen. No dependen de datos
existentes ni dejan rastro en la base de datos real.

---

## 2. Cómo funcionan los tests en Django

### Base de datos de prueba

Cuando se ejecutan los tests, Django crea automáticamente una base de
datos temporal separada de la base de datos real. En este proyecto se
llama `test_normai`. Todos los datos creados en los tests existen solo
en esa base de datos temporal y se destruyen al terminar.

Base de datos real: normai        (no se toca durante los tests)
Base de datos de prueba: test_normai  (se crea y destruye automáticamente)

### Estructura de un test

Cada test sigue este patrón:

```python
def test_nombre_descriptivo(self):
    # 1. Preparar datos o condiciones
    url = reverse('audits:get_gap_analysis', args=[self.plan.id])

    # 2. Ejecutar la acción
    response = self.client.get(url)

    # 3. Comprobar que el resultado es el esperado
    self.assertEqual(response.status_code, 200)
```

Si la comprobación falla, Django muestra exactamente qué test falló,
qué valor se esperaba y qué valor se obtuvo.

### El método setUp

```python
def setUp(self):
    # Se ejecuta antes de CADA test
    # Crea todos los datos necesarios
```

`setUp` se ejecuta antes de cada test individual, garantizando que
cada test parte de un estado limpio y conocido. Los datos creados en
`setUp` están disponibles en todos los métodos del test como
`self.plan`, `self.process`, etc.

---

## 3. Estructura general del archivo de tests

El archivo `audits/tests.py` contiene dos clases de tests, cada una
cubriendo un endpoint diferente:

audits/tests.py
├── GapAnalysisTestCase (12 tests)
│   └── Prueba: GET /audits/get-gap-analysis/<id>/
│
└── GenerateDynamicChecklistTestCase (8 tests)
└── Prueba: POST /audits/generate-dynamic-checklist/

### Datos de prueba comunes

Ambas clases crean una jerarquía completa de datos de prueba en su
`setUp`:

User (usuario autenticado)
└── Area → Position → Process
└── ProcessRequirement → StandardRequirement
└── Clause → Standard
AuditProgramHeader
└── AnnualProgram (proceso + norma)
└── AnnualPlan
└── Checklist → AuditedEvaluationQuestion → ProcessRequirement

---

## 4. GapAnalysisTestCase — Tests del endpoint get_gap_analysis

### Datos de prueba creados en setUp

Se crean 4 `ProcessRequirement` y 3 `Checklist` items, cada uno con
un estado diferente para cubrir los cuatro tipos de brecha:

| ProcessRequirement | Checklist | compliance | evidence | Estado esperado |
|-------------------|-----------|------------|----------|-----------------|
| pr1 (req1) | ✅ existe | True | Con texto | COMPLIANT |
| pr2 (req2) | ✅ existe | False | Con texto | NON_COMPLIANT |
| pr3 (req3) | ✅ existe | False | Vacía | INSUFFICIENT_EVIDENCE |
| pr4 (req4) | ❌ no existe | — | — | NOT_EVALUATED |

### Tests implementados

#### `test_gap_analysis_requiere_autenticacion`
**Qué verifica:** Un usuario no autenticado no puede acceder al endpoint.  
**Cómo funciona:** Crea un cliente anónimo sin login y hace una petición GET.  
**Resultado esperado:** Código de respuesta distinto de 200 (redirección al login).

#### `test_gap_analysis_plan_no_existe`
**Qué verifica:** El endpoint devuelve error si el plan no existe.  
**Cómo funciona:** Hace una petición con el id 99999, que no existe en la base de datos.  
**Resultado esperado:** Código 404 y JSON con clave `error`.

#### `test_gap_analysis_devuelve_200`
**Qué verifica:** El endpoint devuelve 200 para un plan válido.  
**Cómo funciona:** Hace una petición GET con el id del plan creado en setUp.  
**Resultado esperado:** Código 200.

#### `test_gap_analysis_estructura_respuesta`
**Qué verifica:** La respuesta contiene todas las claves esperadas.  
**Cómo funciona:** Parsea el JSON de la respuesta y comprueba que existen las claves `success`, `summary`, `gaps`, `process` y `standard`.  
**Resultado esperado:** Todas las claves presentes y `success=True`.

#### `test_gap_analysis_resumen_correcto`
**Qué verifica:** El resumen cuenta correctamente cada tipo de brecha.  
**Cómo funciona:** Lee el campo `summary` del JSON y comprueba cada contador.  
**Resultado esperado:**
```json
{
    "total": 4,
    "compliant": 1,
    "non_compliant": 1,
    "insufficient_evidence": 1,
    "not_evaluated": 1
}
```

#### `test_gap_analysis_compliance_rate`
**Qué verifica:** La tasa de cumplimiento se calcula correctamente.  
**Cómo funciona:** Lee `compliance_rate` del resumen. Se calcula sobre los requisitos evaluados (3), no sobre el total (4). 1 conforme de 3 evaluados = 33.3%.  
**Resultado esperado:** `compliance_rate ≈ 33.3`

#### `test_gap_analysis_clasifica_compliant`
**Qué verifica:** El requisito con `compliance=True` se clasifica como COMPLIANT.  
**Cómo funciona:** Busca en la lista de brechas el gap correspondiente a `pr1` y comprueba su estado.  
**Resultado esperado:** `status = "COMPLIANT"` y `compliance = true`.

#### `test_gap_analysis_clasifica_non_compliant`
**Qué verifica:** El requisito con `compliance=False` y evidencia con contenido se clasifica como NON_COMPLIANT.  
**Cómo funciona:** Busca el gap de `pr2` (compliance=False, evidence="No se encontró registro.").  
**Resultado esperado:** `status = "NON_COMPLIANT"`, `compliance = false`, `evidence` no nula.

#### `test_gap_analysis_clasifica_insufficient_evidence`
**Qué verifica:** El requisito con `compliance=False` y evidencia vacía se clasifica como INSUFFICIENT_EVIDENCE.  
**Cómo funciona:** Busca el gap de `pr3` (compliance=False, evidence="").  
**Resultado esperado:** `status = "INSUFFICIENT_EVIDENCE"`.

#### `test_gap_analysis_clasifica_not_evaluated`
**Qué verifica:** El requisito sin ítem de checklist se clasifica como NOT_EVALUATED.  
**Cómo funciona:** Busca el gap de `pr4`, que no tiene ningún `Checklist` asociado.  
**Resultado esperado:** `status = "NOT_EVALUATED"` y `checklist_item_id = null`.

#### `test_gap_analysis_trazabilidad_normativa`
**Qué verifica:** Cada brecha incluye información completa de requisito, cláusula y norma.  
**Cómo funciona:** Toma el primer gap de la lista y comprueba que contiene los campos normativos esperados.  
**Resultado esperado:** Presencia de `requirement.text`, `requirement.criticality_level`, `clause.code` y `standard.name`.

#### `test_gap_analysis_sin_norma_en_programa`
**Qué verifica:** El endpoint devuelve error si el programa de auditoría no tiene norma seleccionada.  
**Cómo funciona:** Crea un `AnnualProgram` con `standard=None` y un `AnnualPlan` asociado.  
**Resultado esperado:** JSON con clave `error`.

---

## 5. GenerateDynamicChecklistTestCase — Tests del endpoint generate_dynamic_checklist

### Datos de prueba creados en setUp

Se crean 2 `ProcessRequirement` vinculados al proceso de prueba y a
la norma seleccionada en el programa. El plan de auditoría no tiene
checklist al inicio — cada test parte de un estado limpio.

### Tests implementados

#### `test_generate_requiere_autenticacion`
**Qué verifica:** Un usuario no autenticado no puede invocar la generación.  
**Cómo funciona:** Hace una petición POST con un cliente anónimo.  
**Resultado esperado:** Código distinto de 200.

#### `test_generate_solo_acepta_post`
**Qué verifica:** El endpoint rechaza peticiones GET con 405 Method Not Allowed.  
**Cómo funciona:** Hace una petición GET al endpoint que está decorado con `@require_POST`.  
**Resultado esperado:** Código 405.

#### `test_generate_crea_checklist`
**Qué verifica:** La generación crea el número correcto de ítems de checklist.  
**Cómo funciona:** Hace una petición POST y comprueba el campo `total_items` del JSON y el número de `Checklist` en base de datos.  
**Resultado esperado:** `total_items = 2` y `Checklist.objects.filter(audit_plan=self.plan).count() = 2`.

#### `test_generate_crea_preguntas_vinculadas`
**Qué verifica:** Las preguntas generadas están correctamente vinculadas a `ProcessRequirement` y tienen acceso al `StandardRequirement`.  
**Cómo funciona:** Tras la generación, consulta todas las `AuditedEvaluationQuestion` del proceso y comprueba que tienen `requirement` y `standard_requirement`.  
**Resultado esperado:** 2 preguntas, todas con `requirement` y `standard_requirement` no nulos.

#### `test_generate_no_duplica_checklist`
**Qué verifica:** El endpoint rechaza la generación si ya existe un checklist para el plan.  
**Cómo funciona:** Invoca el endpoint dos veces seguidas para el mismo plan.  
**Resultado esperado:** La segunda llamada devuelve JSON con `error`, y sigue habiendo solo 2 ítems en base de datos.

#### `test_generate_sin_norma_devuelve_error`
**Qué verifica:** El endpoint devuelve error si el programa no tiene norma seleccionada.  
**Cómo funciona:** Crea un programa sin norma y un plan asociado, e intenta generar el checklist.  
**Resultado esperado:** JSON con clave `error`.

#### `test_generate_texto_pregunta_incluye_clausula`
**Qué verifica:** El texto de las preguntas generadas incluye el código de cláusula entre corchetes.  
**Cómo funciona:** Tras la generación, comprueba que el `question_text` de cada pregunta contiene `[8.5]`.  
**Resultado esperado:** Todas las preguntas contienen el código de cláusula en su texto.

#### `test_generate_plan_no_existe`
**Qué verifica:** El endpoint devuelve error si el plan no existe.  
**Cómo funciona:** Envía `annual_plan_id = 99999`.  
**Resultado esperado:** JSON con clave `error`.

---

## 6. Cómo ejecutar los tests

### Ejecutar todos los tests de audits

```bash
python manage.py test audits --verbosity=2
```

### Ejecutar solo un grupo de tests

```bash
python manage.py test audits.tests.GapAnalysisTestCase --verbosity=2
python manage.py test audits.tests.GenerateDynamicChecklistTestCase --verbosity=2
```

### Ejecutar un test específico

```bash
python manage.py test audits.tests.GapAnalysisTestCase.test_gap_analysis_resumen_correcto
```

### Opciones útiles

```bash
# Sin detalle (solo OK o FAIL)
python manage.py test audits

# Con detalle de cada test
python manage.py test audits --verbosity=2

# Detener al primer fallo
python manage.py test audits --failfast
```

---

## 7. Resultado de la ejecución

Found 20 test(s).
Creating test database for alias 'default' ('test_normai')...
...
System check identified no issues (0 silenced).
test_gap_analysis_clasifica_compliant ... ok
test_gap_analysis_clasifica_insufficient_evidence ... ok
test_gap_analysis_clasifica_non_compliant ... ok
test_gap_analysis_clasifica_not_evaluated ... ok
test_gap_analysis_compliance_rate ... ok
test_gap_analysis_devuelve_200 ... ok
test_gap_analysis_estructura_respuesta ... ok
test_gap_analysis_plan_no_existe ... ok
test_gap_analysis_requiere_autenticacion ... ok
test_gap_analysis_resumen_correcto ... ok
test_gap_analysis_sin_norma_en_programa ... ok
test_gap_analysis_trazabilidad_normativa ... ok
test_generate_crea_checklist ... ok
test_generate_crea_preguntas_vinculadas ... ok
test_generate_no_duplica_checklist ... ok
test_generate_plan_no_existe ... ok
test_generate_requiere_autenticacion ... ok
test_generate_sin_norma_devuelve_error ... ok
test_generate_solo_acepta_post ... ok
test_generate_texto_pregunta_incluye_clausula ... ok

Ran 20 tests in 8.545s
OK
Destroying test database for alias 'default' ('test_normai')...

**20 tests ejecutados, 20 pasando, 0 fallos.**