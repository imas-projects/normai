# Onboarding técnico — Semana 1

## Objetivo
Ejecutar NormAI en local, comprender su arquitectura general y documentar el estado actual del proyecto.

NO se desarrolla funcionalidad nueva en esta fase.

---

## Requisitos
- Python 3.10+
- PostgreSQL
- Cuenta en OpenAI
- Git

---

## Pasos

### 1. Clonar el repositorio
```bash
git clone https://github.com/imas-projects/normai.git
cd normai
```
### 2. Crear entorno virtual
```
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```
### 3. Configurara variables de entorno
```
cp .env.example .env
```
Editar .env:
- Credenciales PostgreSQL
- OPENAI_API_KEY

### 4. Preparar base de datos
- Crear base de datos PostgreSQL
- Ejecutal:
  ```
python backend/manage.py migrate
python backend/manage.py createsuperuser
```
### 5. Ejecutar servidor
```python backend/manage.py runserver
```
## Entregable Semana 1
- Proyecto ejecutado en local
- Documentodocs/estado-proyecto.md
- Issue creado con dudas técnicas detectadas






