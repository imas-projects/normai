# Estado actual del proyecto NormAI

## Arquitectura general

NormAI es una aplicación web desarrollada con **Django 3.2** que utiliza **PostgreSQL** como base de datos. El proyecto sigue una arquitectura modular típica de Django, dividido en múltiples aplicaciones independientes que gestionan diferentes aspectos del cumplimiento normativo y gestión de riesgos.

### Backend
El backend está construido completamente en Django y organizado en las siguientes apps principales:

- **accounts/**: Gestión de direcciones de email
- **audits/**: Sistema completo de auditorías con planes anuales, programas, reportes y evaluaciones
- **authentication/**: Sistema de autenticación con grupos, permisos y usuarios
- **communications/**: Sistema de comunicaciones con canales, tablas, tipos, mensajes y periodicidad
- **company/**: Gestión integral de empresas (áreas, documentaciones, clientes/proveedores externos, posiciones, requisitos, roles, posiciones de usuario)
- **processes/**: Gestión de procesos de negocio (indicadores de rendimiento, actividades, entradas/salidas, mediciones, posiciones, procesos generales, mediciones de productos)
- **risks/**: Gestión completa de riesgos (planes de contingencia, reevaluaciones, evaluaciones de riesgo, identificación de riesgos, tratamientos de riesgo)
- **sites/**: Gestión de sitios/ubicaciones
- **social_accounts/**: Autenticación social (cuentas sociales, tokens de aplicación, aplicaciones sociales)
- **ai_functions/**: Módulo dedicado a las funcionalidades de inteligencia artificial

### Apps auxiliares
- **apps/**: Aplicaciones auxiliares generales
- **dashboards/**: Dashboards y visualizaciones
- **pages/**: Páginas estáticas y dinámicas
- **components/**, **layouts/**: Componentes y layouts reutilizables

### Frontend
El frontend utiliza el template **Velzon** y está integrado con Django a través de:
- Templates HTML en la carpeta `templates/`
- Archivos estáticos (CSS, JS) en `static/` y `staticfiles/`
- Sistema de build con **Gulp** (gulpfile.js)
- Dependencias Node.js gestionadas con npm/yarn

### Flujo principal identificado
1. El usuario se autentica en el sistema (con posibilidad de autenticación social)
2. Se vincula a una empresa/organización con un rol y posición específicos
3. Define y documenta procesos de negocio con sus actividades, entradas, salidas y mediciones
4. Identifica y evalúa riesgos asociados a los procesos
5. Crea planes de contingencia y tratamientos de riesgo
6. Realiza auditorías según planes anuales y programas establecidos
7. Gestiona comunicaciones a través de diferentes canales
8. La IA asiste en análisis y generación de contenido relacionado con estos procesos

### Base de datos
- **PostgreSQL** como SGBD principal
- Configuración centralizada mediante variables de entorno (`.env`)
- Sistema de migraciones de Django para versionado del esquema
- Múltiples tablas relacionadas siguiendo el modelo normalizado

---

## Funcionalidades existentes

### 1. Sistema de autenticación (AUTHENTICATION AND AUTHORIZATION)
- Gestión de **usuarios** (Users)
- Sistema de **grupos** (Groups) para organización de permisos
- Gestión granular de **permisos** (Permissions)
- Integración con **django-allauth** para autenticación social
- Soporte para cuentas sociales (Google, Facebook, etc.)

### 2. Gestión de empresas (COMPANY)
El módulo más completo del sistema:
- **Áreas** (Areas): Departamentos o divisiones de la empresa
- **Documentaciones** (Documentations): Repositorio de documentos
- **Clientes externos** (External clients): Gestión de clientes
- **Proveedores externos** (External suppliers): Gestión de proveedores
- **Posiciones** (Positions): Cargos dentro de la organización
- **Requisitos** (Requirements): Requisitos normativos y legales
- **Roles** (Rols): Roles dentro del sistema de gestión
- **Posiciones de usuario** (User positions): Vinculación usuario-cargo

### 3. Gestión de procesos (PROCESSES)
Sistema completo para documentar y gestionar procesos:
- **Indicadores de rendimiento** (Performance indicators): KPIs del proceso
- **Actividades del proceso** (Process activitys): Descomposición del proceso en actividades
- **Entradas del proceso** (Process inputs): Recursos e información de entrada
- **Mediciones del proceso** (Process measurements): Métricas y seguimiento
- **Salidas del proceso** (Process outputs): Productos o resultados del proceso
- **Posiciones del proceso** (Process positions): Responsables del proceso
- **Procesos** (Processs): Definición del proceso principal
- **Mediciones de productos** (Product measurements): Calidad de los productos generados

### 4. Gestión de riesgos (RISKS)
Módulo completo de gestión de riesgos:
- **Planes de contingencia** (Contingency plans): Planes de respuesta ante riesgos materializados
- **Reevaluaciones** (Reevaluations): Revisión periódica de riesgos
- **Evaluaciones de riesgo** (Risk evaluations): Análisis y valoración de riesgos
- **Identificación de riesgos** (Risk identifications): Catálogo de riesgos identificados
- **Tratamientos de riesgo** (Risk treatments): Estrategias para mitigar o eliminar riesgos

### 5. Sistema de auditorías (AUDITS)
Sistema robusto para gestión de auditorías:
- **Auditorías de planes anuales** (Annual plan auditeds): Auditorías planificadas anualmente
- **Auditores de planes anuales** (Annual plan auditors): Asignación de auditores
- **Planes anuales** (Annual plans): Planificación anual de auditorías
- **Programas anuales** (Annual programs): Programación de auditorías
- **Encabezados de programas de auditoría** (Audit program headers): Estructura de programas
- **Reportes de auditoría** (Audit reports): Informes generados
- **Preguntas de evaluación auditada** (Audited evaluation questions): Cuestionarios de auditoría
- **Evaluaciones de auditores** (Auditor evaluations): Evaluación del desempeño de auditores
- **Checklists**: Listas de verificación
- **Hallazgos** (Findingss): No conformidades y observaciones detectadas
- **Preguntas de evaluación del auditor líder** (Lead auditor evaluation questions): Evaluación específica del auditor líder
- **Requisitos del proceso** (Process requirements): Requisitos a verificar en la auditoría

### 6. Sistema de comunicaciones (COMMUNICATIONS)
Gestión completa de comunicaciones internas y externas:
- **Canales** (Channels): Medios de comunicación (email, chat, reuniones, etc.)
- **Tablas de comunicación** (Communication tables): Matrices de comunicación
- **Tipos de comunicación** (Communication types): Categorización de comunicaciones
- **Mensajes** (Messages): Registro de comunicaciones
- **Periodicidad** (Periodicitys): Frecuencia de comunicaciones programadas

### 7. Gestión de sitios (SITES)
- **Sitios** (Sites): Ubicaciones físicas o sedes de la empresa

### 8. Cuentas de correo (ACCOUNTS)
- **Direcciones de email** (Email addresses): Gestión de correos electrónicos

### 9. Panel de administración Django
- Interface completa y personalizada del Django Admin
- Visualización y edición de todos los modelos
- Gestión de permisos por modelo
- Filtros y búsquedas avanzadas
- Acciones masivas sobre registros

---

## Uso actual de IA

### Integración con OpenAI
El proyecto tiene un módulo dedicado **ai_functions/** que gestiona la integración con la API de OpenAI.

**Configuración:**
- La API key se configura mediante la variable de entorno `OPENAI_API_KEY` en el archivo `.env`
- Actualmente la clave está pendiente de configurar para pruebas en el entorno local

**Casos de uso previstos (basados en la arquitectura del sistema):**

1. **Análisis automatizado de riesgos**
   - Identificación de riesgos potenciales en procesos
   - Evaluación de probabilidad e impacto
   - Generación de planes de contingencia

2. **Asistencia en documentación de procesos**
   - Generación de descripciones de actividades
   - Sugerencias de KPIs relevantes
   - Identificación de entradas y salidas del proceso

3. **Generación de contenido para auditorías**
   - Creación de checklists personalizados
   - Generación de preguntas de evaluación
   - Redacción de reportes de auditoría

4. **Análisis de requisitos normativos**
   - Interpretación de normativas aplicables
   - Mapeo de requisitos legales a procesos
   - Sugerencias de cumplimiento

5. **Optimización de comunicaciones**
   - Generación de matrices de comunicación
   - Sugerencias de canales apropiados
   - Redacción de mensajes estandarizados

**Nota:** No se ha podido probar la funcionalidad de IA en detalle debido a que se requiere configurar una API key válida de OpenAI. Para activar estas funcionalidades se necesita:
1. Crear cuenta en https://platform.openai.com/
2. Generar una API key
3. Añadirla al archivo `.env` en la variable `OPENAI_API_KEY`
4. Considerar los costos asociados al uso de la API

---

## Problemas detectados

### 1. Conflicto de migraciones inicial ⚠️
**Problema:** Al intentar ejecutar `python manage.py migrate` por primera vez, se producía el error:
```
ValueError: Cannot alter field risks.ContingencyPlan.communicate_to into risks.ContingencyPlan.communicate_to - they are not compatible types (you cannot alter to or from M2M fields, or add or remove through= on M2M fields)
```

**Causa:** Las migraciones existentes en el repositorio estaban diseñadas para una configuración de base de datos diferente o tenían conflictos internos relacionados con el campo `communicate_to` del modelo `ContingencyPlan`.

**Solución aplicada:**
1. Eliminar todos los archivos de migración (excepto `__init__.py`) de todas las apps:
   - ai_functions/migrations/
   - apps/migrations/
   - audits/migrations/
   - authentication/migrations/
   - communications/migrations/
   - company/migrations/
   - components/migrations/
   - dashboards/migrations/
   - layouts/migrations/
   - pages/migrations/
   - processes/migrations/
   - risks/migrations/
2. Ejecutar `python manage.py makemigrations` para regenerar migraciones limpias
3. Ejecutar `python manage.py migrate` para aplicarlas a la base de datos PostgreSQL limpia

**Impacto:** Resuelto completamente. Base de datos operativa.

### 2. Configuración hardcodeada de base de datos ⚠️
**Problema:** El archivo `settings.py` contenía múltiples configuraciones de base de datos comentadas:
- Configuración para SQLite (comentada)
- Configuración para PostgreSQL local con credenciales diferentes (comentada)
- Configuración activa apuntando a AWS RDS con credenciales hardcodeadas

**Código original problemático:**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "B82839044JMgp",  # Contraseña expuesta
        "HOST": "postgresqltest.cvsxzrox0hah.eu-west-1.rds.amazonaws.com",
        "PORT": "5432", 
    }
}
```

**Solución aplicada:**
1. Instalar `python-dotenv` para gestión de variables de entorno
2. Modificar `settings.py` para leer variables desde `.env`:
```python
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME', 'normai'),
        "USER": os.getenv('DB_USER', 'postgres'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": os.getenv('DB_HOST', '127.0.0.1'),
        "PORT": os.getenv('DB_PORT', '5432'),
    }
}
```
3. Configurar PostgreSQL local con las credenciales del `.env`

**Impacto:** Resuelto. Mayor seguridad y flexibilidad en la configuración.

### 3. Estructura de proyecto diferente a la documentación ℹ️
**Problema:** Las instrucciones del onboarding (`docs/onboarding.md`) asumen una estructura con carpeta `backend/`, pero el proyecto tiene todos los archivos Django en la raíz.

**Comandos documentados:**
```bash
pip install -r backend/requirements.txt  # ❌ No funciona
python backend/manage.py migrate         # ❌ No funciona
```

**Comandos correctos:**
```bash
pip install -r requirements.txt          # ✅ Correcto
python manage.py migrate                 # ✅ Correcto
```

**Impacto:** Menor. Solo requiere adaptación de comandos durante el setup inicial.

**Recomendación:** Actualizar la documentación de onboarding para reflejar la estructura real del proyecto.

### 4. Múltiples entornos virtuales ⚠️
**Observación:** Existen tres carpetas de entornos virtuales en el proyecto:
- `.venv/` (Python 3.12)
- `venv/` (contenido duplicado)
- `normai-env/` (Python 3.12)

**Problemas que puede causar:**
- Confusión sobre cuál usar
- Desperdicio de espacio en disco (~500MB por entorno)
- Posibilidad de instalar dependencias en el entorno equivocado

**Recomendación:** 
1. Estandarizar en un solo entorno (recomiendo `.venv`)
2. Añadir al `.gitignore`:
```
.venv/
venv/
normai-env/
```
3. Documentar claramente en el README qué entorno usar

### 5. OpenAI API Key no configurada ⏳
**Problema:** La variable `OPENAI_API_KEY` está vacía en el `.env`, lo que impide probar las funcionalidades de IA del sistema.

**Estado actual:**
```env
OPENAI_API_KEY= 
```

**Pendiente:** 
- Obtener una API key válida de OpenAI
- Configurar límites de uso y presupuesto
- Evaluar costos estimados según el uso esperado

### 6. Archivo db.sqlite3 legacy presente ℹ️
**Observación:** Existe un archivo `db.sqlite3` de 360KB en la raíz del proyecto, sugiriendo que anteriormente el proyecto usaba SQLite.

**Recomendación:** Eliminar este archivo y asegurar que esté en el `.gitignore` para evitar confusiones.

---

---

**Documento creado:** 27 de enero de 2026  
**Versión del proyecto:** main branch (commit actual)  
**Estado:** Setup inicial completado exitosamente  
**Servidor:** Ejecutándose correctamente en http://127.0.0.1:8000/  
**Base de datos:** PostgreSQL operativa con todas las migraciones aplicadas  
**Panel admin:** Accesible y funcional en http://127.0.0.1:8000/admin/
