# Correcciones de Revisión — Fase 1

**Documento:** Revisión y corrección de issues detectadas por el tutor tras la Fase 1  
**Fase:** FASE 1 — Integración del Dominio Normativo (revisión post-entrega)  
**Fecha:** Mayo 2026  

---

## Tabla de Contenidos

1. [Contexto de la revisión](#1-contexto-de-la-revisión)
2. [Punto 1 — Migración de ProcessRequirement](#2-punto-1--migración-de-processrequirement)
3. [Punto 2 — Historial de migraciones de risks](#3-punto-2--historial-de-migraciones-de-risks)
4. [Punto 3 — Referencias al modelo antiguo en ai_functions](#4-punto-3--referencias-al-modelo-antiguo-en-ai_functions)
5. [Punto 4 — Credenciales hardcodeadas en settings.py](#5-punto-4--credenciales-hardcodeadas-en-settingspy)
6. [Punto 5 — Documentación de onboarding](#6-punto-5--documentación-de-onboarding)
7. [Verificación final](#7-verificación-final)

---

## 1. Contexto de la revisión

Tras la entrega de la Fase 1, el tutor realizó una revisión del trabajo
entregado e identificó cinco puntos que requerían corrección antes de
poder avanzar a la Fase 2. Este documento recoge de forma detallada cada
uno de los problemas detectados, las decisiones tomadas para resolverlos
y los cambios realizados en el código y la documentación.

Los cinco puntos detectados fueron:

1. La migración de `ProcessRequirement` hacia `StandardRequirement` no
   documentaba ni justificaba la estrategia de transición de datos.
2. El historial de migraciones del módulo `risks` había sido compactado
   sin documentar la decisión ni sus implicaciones de compatibilidad.
3. Partes del código en `ai_functions` seguían accediendo al modelo
   antiguo de requisitos con la estructura anterior al refactor.
4. Las credenciales de base de datos y la API key de OpenAI estaban
   escritas directamente en `settings.py` en lugar de leerse desde
   variables de entorno.
5. La documentación de onboarding no era coherente con la estructura
   real del repositorio.

---

## 2. Punto 1 — Migración de ProcessRequirement

### Problema detectado

El tutor señaló que la migración `0008_replace_requirement_charfield_with_fk.py`
del módulo `audits` cambiaba el campo `requirement` de `ProcessRequirement`
de una `ForeignKey(company.Requirement)` a una `ForeignKey(standards.StandardRequirement)`, pero no explicaba
qué ocurría con los datos que pudieran existir previamente en esa tabla.

La pregunta clave era: si existen registros en `ProcessRequirement` cuando
se aplica esta migración, ¿qué pasa con ellos? ¿Siguen apuntando correctamente
a su requisito correspondiente o la relación queda inconsistente?

### Análisis de la situación

Al analizar la situación, se determinó que:

- Antes del cambio, el campo `requirement` era un `CharField(max_length=200)`
  que almacenaba texto plano. No apuntaba a ninguna tabla externa.
- Después del cambio, el campo es un `ForeignKey(StandardRequirement)` que
  apunta a la tabla `tb_standard_requirements`.
- No existe ninguna equivalencia automática entre un texto libre y un ID
  de `StandardRequirement`, por lo que no es posible una migración
  automática de datos.
- Los registros existentes en `ProcessRequirement` en el momento del cambio
  eran únicamente datos de prueba generados durante el desarrollo inicial,
  sin valor productivo.

### Decisión tomada

Se optó por la estrategia de **reconstrucción desde cero**, que consiste en:

1. Eliminar manualmente todos los registros de `ProcessRequirement` antes
   de aplicar la migración, mediante las siguientes operaciones desde el
   shell de Django:

```python
from audits.models import Findings, AuditedEvaluationQuestion, ProcessRequirement
Findings.objects.all().update(requirement=None)
AuditedEvaluationQuestion.objects.all().update(requirement=None)
ProcessRequirement.objects.all().delete()
```

2. Aplicar la migración sobre la tabla vacía, garantizando integridad total.
3. Reconstruir los `ProcessRequirement` manualmente apuntando a los
   `StandardRequirement` correctos del nuevo dominio normativo.

Esta decisión está justificada porque el proyecto se encontraba en fase
de desarrollo con datos de prueba sin valor productivo, y porque intentar
un mapeo automático de texto libre a requisitos estructurados no garantizaría
corrección semántica.

### Cambio realizado

Se añadió un comentario extenso al principio del archivo
`audits/migrations/0008_replace_requirement_charfield_with_fk.py` que
documenta explícitamente la estrategia adoptada, los pasos de limpieza
realizados y las condiciones bajo las que esta migración es segura:

```python
# Migración F1-04 — Refactorización de ProcessRequirement
#
# ESTRATEGIA DE MIGRACIÓN:
# Antes de aplicar esta migración, la tabla tb_audit_process_requirements
# contenía únicamente datos de prueba sin valor productivo, generados
# durante el desarrollo inicial del proyecto.
#
# Estos datos fueron eliminados manualmente antes de ejecutar esta migración
# mediante las siguientes operaciones desde el shell de Django:
#
#   from audits.models import Findings, AuditedEvaluationQuestion, ProcessRequirement
#   Findings.objects.all().update(requirement=None)
#   AuditedEvaluationQuestion.objects.all().update(requirement=None)
#   ProcessRequirement.objects.all().delete()
#
# IMPORTANTE: Esta migración solo es segura en una base de datos donde
# tb_audit_process_requirements esté vacía antes de aplicarla.
# Si existen datos productivos, hay que mapearlos manualmente a
# StandardRequirement antes de ejecutar esta migración.
```

### Por qué esto resuelve el problema

Cualquier persona que revise el repositorio puede leer claramente qué datos
había, por qué se eliminaron, qué hay que hacer si en el futuro hubiera
datos productivos y dónde está la documentación completa de la decisión.
La migración deja de ser una caja negra y pasa a ser trazable.

---

## 3. Punto 2 — Historial de migraciones de risks

### Problema detectado

El tutor señaló que el módulo `risks` solo tenía una migración `0001_initial.py`,
cuando originalmente el proyecto había llegado con 5 migraciones (0001 a 0005).
Esto indicaba que en algún momento se habían eliminado las migraciones originales
y se había reescrito la `0001` con el estado final del modelo.

El problema es que esto rompe la compatibilidad con bases de datos que hubieran
aplicado el historial original: si alguien tenía aplicadas las migraciones
0001 a 0005 del historial antiguo y actualizaba a esta rama, Django detectaría
inconsistencias entre el historial registrado y los archivos disponibles.

### Análisis de la situación

Al comparar las migraciones originales con la migración actual se determinó
que el estado final del modelo era correcto, pero el historial había sido
compactado sin documentar. Las diferencias entre la `0001` original y la
`0001` actual eran las siguientes:

| Aspecto | Original 0001 | 0001 actual |
|---------|--------------|-------------|
| Campo `activity_name` | ✅ existe | ❌ eliminado |
| Campo `process` | ❌ no existe | ✅ añadido |
| Campo `source` | ❌ no existe | ✅ añadido |
| `ContingencyPlanCommunicateTo` | ❌ no existe | ✅ añadido |
| `ContingencyPlanResponsible` | ❌ no existe | ✅ añadido |
| `responsible` y `communicate_to` usan through | ❌ no | ✅ sí |
| Choices de risk_level en español | ❌ no | ✅ sí |

Se intentó restaurar el historial original de 5 migraciones y aplicarlas
mediante `--fake`, pero esto generó errores porque la base de datos ya
tenía el estado final aplicado y Django no podía reconstruir el grafo
de migraciones correctamente.

### Decisión tomada

Se optó por mantener la `0001_initial.py` compactada, que es el estado
real de la base de datos, y añadir un comentario extenso que:

- Explica que originalmente existían 5 migraciones (0001 a 0005)
- Documenta por qué se compactaron (conflicto de migraciones detectado
  al inicio del proyecto, documentado en `docs/estado-proyecto.md`)
- Especifica explícitamente las implicaciones de compatibilidad
- Indica qué debe hacer alguien que parta de una base de datos con el
  historial antiguo

Esta decisión está justificada porque:

1. El conflicto original era incompatible con una migración incremental.
2. Todos los desarrolladores del proyecto partían de una base de datos limpia.
3. El modelo resultante es correcto y está sincronizado con la base de datos.

### Cambio realizado

Se añadió un comentario al principio de
`risks/migrations/0001_initial.py` que documenta la situación completa:

```python
# Migración inicial compactada — risks
#
# HISTORIAL DE MIGRACIONES:
# El módulo risks tenía originalmente 5 migraciones (0001 a 0005).
#
# Al inicio del proyecto se detectó un conflicto en las migraciones
# (documentado en docs/estado-proyecto.md, sección "Problemas detectados",
# punto 1) que impedía ejecutar migrate correctamente.
#
# Como solución documentada, se eliminaron todas las migraciones y se
# regeneró una única migración inicial que representa el estado final
# del modelo.
#
# COMPATIBILIDAD:
# Esta migración es compatible con instalaciones nuevas (base limpia).
# No es compatible con bases de datos que hubieran aplicado el historial
# original de 5 migraciones. Para esos casos, la base de datos debe
# reinicializarse.
```

### Verificación

```bash
python manage.py showmigrations risks
# risks
#  [X] 0001_initial

python manage.py makemigrations --check --dry-run
# No changes detected

python manage.py check
# System check identified no issues (0 silenced).
```

---

## 4. Punto 3 — Referencias al modelo antiguo en ai_functions

### Problema detectado

El tutor señaló que después del refactor de `ProcessRequirement`, partes
del código en `ai_functions/monitoring_functions.py` seguían accediendo
al campo `requirement` como si fuera un string directo, cuando tras el
refactor ese campo es una `ForeignKey(StandardRequirement)`.

La nueva cadena de acceso correcta es:

checklist_obj.question.requirement      → ProcessRequirement
.requirement                        → StandardRequirement
.text                           → texto del requisito
.clause                         → Clause
.code                       → código de la cláusula
.description                → descripción de la cláusula


### Funciones afectadas y correcciones realizadas

#### Función `suggest_compliance_rating`

**Antes:**
```python
requirement_name = checklist_obj.question.requirement.requirement \
    if checklist_obj.question.requirement else "N/A"

clause_description = getattr(checklist_obj.question.requirement, "description", "")
```

**Después:**
```python
process_req = checklist_obj.question.requirement
std_req = process_req.requirement if process_req else None
requirement_name = std_req.text if std_req else "N/A"

clause_description = std_req.clause.description \
    if std_req and std_req.clause else ""
```

**Por qué:** El acceso `.requirement.requirement` intentaba acceder a un
atributo `requirement` sobre un objeto `ProcessRequirement`, que ya no
existe con ese nombre. Ahora se accede correctamente a `.requirement.text`
a través del `StandardRequirement`.

#### Función `suggest_audit_questions`

**Antes:**
```python
clause_identifier = requirement_obj.requirement
```

**Después:**
```python
clause_identifier = requirement_obj.requirement.text \
    if requirement_obj.requirement else str(requirement_obj)
```

**Por qué:** `requirement_obj` es un `ProcessRequirement`. El campo
`requirement` de ese objeto es ahora un `StandardRequirement`, no un
string. Para obtener el texto hay que acceder a `.requirement.text`.

#### Función `classify_finding_ia`

Esta función ya tenía la estructura correcta desde la issue F1-04:

```python
clause_identifier = ""
if requirement_obj:
    std_req = getattr(requirement_obj, "requirement", None)
    if std_req:
        clause_identifier = getattr(std_req, "text", "")
```

Se verificó que no requería cambios adicionales.

### Verificación

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

El servidor arranca sin errores y las funcionalidades de auditoría
y asistencia IA siguen funcionando con el nuevo modelo de requisitos.

---

## 5. Punto 4 — Credenciales hardcodeadas en settings.py

### Problema detectado

El tutor señaló que `velzon/settings.py` tenía escritos directamente:

- La `SECRET_KEY` de Django
- Las credenciales de la base de datos (nombre, usuario, contraseña, host)
- La API key de OpenAI

Esto significa que cualquier persona que acceda al repositorio puede ver
estas credenciales, y que el proyecto no puede ejecutarse en otra máquina
sin editar el código fuente directamente.

### Solución implementada

Se implementó el patrón estándar de configuración mediante variables de
entorno, usando la librería `python-dotenv`.

**Funcionamiento:**

.env (no va al repositorio)     →  valores reales de cada entorno
.env.example (va al repositorio) →  plantilla vacía para otros desarrolladores
settings.py                      →  lee los valores desde el entorno con os.getenv()

### Cambios realizados

#### 1. Instalación de python-dotenv

```bash
pip install python-dotenv
pip freeze > requirements.txt
```

#### 2. Creación de `.env`

Archivo con los valores reales del entorno local. No se sube al repositorio:

```dotenv
DEBUG=True
SECRET_KEY=django-insecure-j%^*y0krq5^-#3lggoecxw!d7ad_gqkab3t5w17&0w06+qf8+8
DB_ENGINE=django.db.backends.postgresql
DB_NAME=normai
DB_USER=postgres
DB_PASSWORD=TFG2026
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=sk-proj-...
```

#### 3. Creación de `.env.example`

Plantilla vacía que sí se sube al repositorio. Cualquier desarrollador
la copia, la rellena con sus propios valores y tiene el proyecto funcionando:

```dotenv
DEBUG=True
SECRET_KEY=
DB_ENGINE=django.db.backends.postgresql
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=
```

#### 4. Modificación de `velzon/settings.py`

Se añadió la carga del `.env` al inicio del archivo:

```python
from dotenv import load_dotenv
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, '.env'))
```

Se sustituyó la `SECRET_KEY` hardcodeada:

```python
# Antes
SECRET_KEY = 'django-insecure-j%^*y0krq5^-#3lggoecxw!d7ad_gqkab3t5w17&0w06+qf8+8'

# Después
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-solo-para-desarrollo')
```

Se sustituyó el bloque `DATABASES` completo eliminando también los
bloques comentados con credenciales antiguas:

```python
# Antes (con credenciales hardcodeadas y bloques comentados con otras credenciales)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "normai",
        "USER": "postgres",
        "PASSWORD": "TFG2026",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Después
DATABASES = {
    "default": {
        "ENGINE": os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        "NAME": os.getenv('DB_NAME', 'normai'),
        "USER": os.getenv('DB_USER', 'postgres'),
        "PASSWORD": os.getenv('DB_PASSWORD', ''),
        "HOST": os.getenv('DB_HOST', 'localhost'),
        "PORT": os.getenv('DB_PORT', '5432'),
    }
}
```

Se sustituyó la API key de OpenAI hardcodeada al final del archivo:

```python
# Antes
OPENAI_API_KEY = "sk-proj-I9H7SQ..."

# Después
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
```

#### 5. Actualización de `.gitignore`

Se añadió `.env` al `.gitignore` para garantizar que las credenciales
reales nunca se suban al repositorio

### Verificación

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py runserver
# Servidor arranca correctamente sin errores
```

---

## 6. Punto 5 — Documentación de onboarding

### Problema detectado

El tutor señaló que el archivo `docs/onboarding.md` no era coherente
con la estructura real del repositorio. Los problemas concretos eran:

- Usaba rutas incorrectas: `backend/requirements.txt` y
  `python backend/manage.py` cuando en realidad `manage.py` y
  `requirements.txt` están en la raíz del proyecto
- No mencionaba el paso de cargar los datos normativos con
  `populate_standards`, que es obligatorio para que el sistema funcione
- No mencionaba el archivo `.env.example` ni el proceso de configuración
  de variables de entorno
- No describía la estructura real del proyecto

### Cambios realizados

Se reescribió completamente el archivo `docs/onboarding.md` para que
refleje exactamente el estado real del proyecto. Los cambios principales
fueron:

| Aspecto | Antes | Después |
|---------|-------|---------|
| Ruta requirements | `backend/requirements.txt` | `requirements.txt` |
| Comando migrate | `python backend/manage.py migrate` | `python manage.py migrate` |
| Variables de entorno | No mencionado | Paso completo con `.env.example` |
| Carga de datos normativos | No mencionado | Paso 7 con `populate_standards` |
| Estructura del proyecto | No descrita | Árbol completo de carpetas |
| Notas importantes | No existían | Sección completa añadida |

La documentación corregida incluye ahora 9 pasos claramente numerados
que una persona puede seguir desde cero para tener el proyecto funcionando,
sin necesidad de adivinar rutas ni corregir comandos.

---

## 7. Verificación final

Tras completar las 5 correcciones se ejecutó una verificación completa
del estado del proyecto:

```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py migrate --check
# (sin output — todas las migraciones están aplicadas)

python manage.py makemigrations --check --dry-run
# No changes detected

python manage.py runserver
# Servidor arranca correctamente sin errores
```

Todos los checks pasan correctamente.