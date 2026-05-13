# Onboarding técnico — Puesta en marcha de NormAI

## Objetivo
Ejecutar NormAI en local, comprender su arquitectura general y verificar
que el entorno de desarrollo está correctamente configurado.

---

## Requisitos previos

- Python 3.10 o superior
- PostgreSQL 13 o superior
- Git
- Cuenta en OpenAI (para funcionalidades de IA)

---

## Pasos

### 1. Clonar el repositorio

```bash
git clone https://github.com/imas-projects/normai.git
cd normai
```

### 2. Crear el entorno virtual

En Linux/Mac:
```bash
python -m venv venv
source venv/bin/activate
```

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> El archivo `requirements.txt` se encuentra en la raíz del proyecto,
> no en ninguna subcarpeta.

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus valores:

DEBUG=True
SECRET_KEY=           # Clave secreta de Django
DB_ENGINE=django.db.backends.postgresql
DB_NAME=              # Nombre de tu base de datos PostgreSQL
DB_USER=              # Usuario de PostgreSQL
DB_PASSWORD=          # Contraseña de PostgreSQL
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=       # Clave de la API de OpenAI

### 5. Crear la base de datos PostgreSQL

Conéctate a PostgreSQL y crea la base de datos:

```sql
CREATE DATABASE normai;
```

### 6. Aplicar migraciones

```bash
python manage.py migrate
```

### 7. Cargar datos normativos iniciales

Este paso carga la estructura de ISO 9001:2015 y AS9100 Rev D:

```bash
python manage.py populate_standards
```

> Este comando solo debe ejecutarse una vez, sobre una base de datos limpia.

### 8. Crear superusuario

```bash
python manage.py createsuperuser
```

### 9. Ejecutar el servidor

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000/`  
El panel de administración en `http://127.0.0.1:8000/admin/`

---


## Notas importantes

- El archivo `.env` nunca debe subirse al repositorio. Está incluido
  en `.gitignore`.
- El archivo `.env.example` sirve como plantilla y sí forma parte
  del repositorio.
- Si es la primera vez que ejecutas el proyecto, asegúrate de ejecutar
  `populate_standards` después de `migrate`.
- Las funcionalidades de IA requieren una clave válida de OpenAI
  configurada en la variable `OPENAI_API_KEY`.
