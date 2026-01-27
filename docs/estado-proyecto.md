# Estado actual del proyecto NormAI
NormAI es una aplicación web desarrollada con Django 3.2 que utiliza PostgreSQL como base de datos. 
El proyecto sigue una arquitectura modular típica de Django, dividido en múltiples aplicaciones independientes que gestionan diferentes aspectos del cumplimiento normativo y gestión de riesgos.

## Arquitectura general

### Backend
El backend está construido completamente en Django y organizado en las siguientes apps principales:

* accounts/: Gestión de direcciones de email
* audits/: Sistema completo de auditorías con planes anuales, programas, reportes y evaluaciones
* authentication/: Sistema de autenticación con grupos, permisos y usuarios
* communications/: Sistema de comunicaciones con canales, tablas, tipos, mensajes y periodicidad
* company/: Gestión integral de empresas (áreas, documentaciones, clientes/proveedores externos, posiciones, requisitos, roles, posiciones de usuario)
* processes/: Gestión de procesos de negocio (indicadores de rendimiento, actividades, entradas/salidas, mediciones, posiciones, procesos generales, mediciones de productos)
* risks/: Gestión completa de riesgos (planes de contingencia, reevaluaciones, evaluaciones de riesgo, identificación de riesgos, tratamientos de riesgo)
* sites/: Gestión de sitios/ubicaciones
* social_accounts/: Autenticación social (cuentas sociales, tokens de aplicación, aplicaciones sociales)
* ai_functions/: Módulo dedicado a las funcionalidades de inteligencia artificial

### Apps auxiliares

* apps/: Aplicaciones auxiliares generales
* dashboards/: Dashboards y visualizaciones
* pages/: Páginas estáticas y dinámicas
* components/, layouts/: Componentes y layouts reutilizables

### Frontend
El frontend utiliza el template Velzon y está integrado con Django a través de:

* Templates HTML en la carpeta templates/
* Archivos estáticos (CSS, JS) en static/ y staticfiles/
* Sistema de build con Gulp (gulpfile.js)
* Dependencias Node.js gestionadas con npm/yarn

### Flujo principal identificado

1. El usuario se autentica en el sistema (con posibilidad de autenticación social)
2. Se vincula a una empresa/organización con un rol y posición específicos
3. Define y documenta procesos de negocio con sus actividades, entradas, salidas y mediciones
4. Identifica y evalúa riesgos asociados a los procesos
5. Crea planes de contingencia y tratamientos de riesgo
6. Realiza auditorías según planes anuales y programas establecidos
7. Gestiona comunicaciones a través de diferentes canales
8. La IA asiste en análisis y generación de contenido relacionado con estos procesos


## Funcionalidades existentes

1. Sistema de autenticación (AUTHENTICATION AND AUTHORIZATION)

2. Gestión de empresas (COMPANY)

3. Gestión de procesos (PROCESSES)

4. Gestión de riesgos (RISKS)

5. Sistema de auditorías (AUDITS)

6. Sistema de comunicaciones (COMMUNICATIONS)

7. Gestión de sitios (SITES)

8. Cuentas de correo (ACCOUNTS)

9. Panel de administración Django

* Interface completa y personalizada del Django Admin
* Visualización y edición de todos los modelos

## Uso actual de IA

El proyecto tiene un módulo dedicado ai_functions/ que gestiona la integración con la API de OpenAI.
Configuración:

La API key se configura mediante la variable de entorno OPENAI_API_KEY en el archivo .env
Actualmente la clave está pendiente de configurar para pruebas en el entorno local

### Casos de uso previstos (basados en la arquitectura del sistema):

Análisis automatizado de riesgos

Identificación de riesgos potenciales en procesos

Evaluación de probabilidad e impacto

Generación de planes de contingencia

Asistencia en documentación de procesos

Generación de descripciones de actividades

Sugerencias de KPIs relevantes

Identificación de entradas y salidas del proceso

Generación de contenido para auditorías

Creación de checklists personalizados

Generación de preguntas de evaluación

Redacción de reportes de auditoría

Análisis de requisitos normativos

Interpretación de normativas aplicables

Mapeo de requisitos legales a procesos

Sugerencias de cumplimiento

Optimización de comunicaciones

Redacción de mensajes estandarizados

Nota: No se ha podido probar la funcionalidad de IA en detalle debido a que se requiere configurar una API key válida de OpenAI.

## Problemas detectados
### Conflicto de migraciones inicial

Problema: Al intentar ejecutar python manage.py migrate por primera vez, se producía el error:

Causa: Las migraciones existentes en el repositorio estaban diseñadas para una configuración de base de datos diferente o tenían conflictos internos relacionados con el campo communicate_to del modelo ContingencyPlan.

- Solución aplicada:

Eliminar todos los archivos de migración (excepto __init__.py) de todas las apps:


Ejecutar python manage.py makemigrations para regenerar migraciones limpias

Ejecutar python manage.py migrate para aplicarlas a la base de datos PostgreSQL limpia


### Problema: El archivo settings.py contenía múltiples configuraciones de base de datos comentadas:

Configuración para SQLite (comentada)

Configuración para PostgreSQL local con credenciales diferentes (comentada)

Configuración activa apuntando a AWS RDS con credenciales hardcodeadas

- Solución aplicada:

Instalar python-dotenv para gestión de variables de entorno

Modificar settings.py para leer variables desde .env:

### Problema: Las instrucciones del onboarding (docs/onboarding.md) asumen una estructura con carpeta backend/, pero el proyecto tiene todos los archivos Django en la raíz.

### Problema: Existen tres carpetas de entornos virtuales en el proyecto:

### Problema: La variable OPENAI_API_KEY está vacía en el .env, lo que impide probar las funcionalidades de IA del sistema.



## Dudas técnicas
-
