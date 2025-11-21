# Sistema de Gestión de Incidencias Municipales
## Documentación Técnica — Backend Django

Sistema web para centralizar incidencias, cuadrillas, departamentos y encuestas territoriales. Este repositorio contiene solo el backend en **Django + PostgreSQL**, con vistas renderizadas y una API REST (DRF) para consumo externo (ej. React/TypeScript).

---
## 1. Introducción
- Público objetivo: municipalidades, equipos territoriales, cuadrillas operativas, direcciones/departamentos y apps móviles que consumen la API.
- Frontend incluido: vistas Django por rol. API expuesta: tokens + endpoints de cuadrilla.
- Arquitectura: modular por apps, separando dominio (core/incidencias/organizacion/territorial_app/personas/registration).

---
## 2. Tecnologías y Dependencias
Componente | Tecnología | Versión
-----------|------------|--------
Lenguaje   | Python     | 3.11 (probado)
Backend    | Django     | 5.2.4
API REST   | Django REST Framework | 3.15.2
Auth Token | DRF TokenAuth (SimpleJWT instalado pero no configurado) | 5.3.1
Base de Datos | PostgreSQL | —
Driver DB  | psycopg / psycopg-binary | 3.2.12
ASGI/Utils | asgiref | 3.10.0
JWT lib    | PyJWT | 2.10.1
SQL parse  | sqlparse | 0.5.3
Tz data    | tzdata | 2025.2

Requerimientos completos en `requirements.txt`.

---
## 3. Arquitectura por Aplicaciones (resumen y cómo se usan)

### 3.1. `encuestas/` (configuración)
- Contiene `settings.py`, `urls.py`, WSGI/ASGI. Registra todas las apps y rutas globales. Configura BD, templates y apps instaladas. Seguridad general (CSRF, auth, etc.).

### 3.2. `core/` (dominio base)
- Modelos clave: `Direccion`, `Departamento`, `Encuesta`, `PreguntaEncuesta`, `RespuestaEncuesta`, `TipoIncidencia`, `Incidencia`, `JefeCuadrilla`, `Multimedia`.
- Formularios y utilidades de roles (`solo_admin`, etc.).
- Sin BaseModel genérico; los modelos tienen sus propios campos de timestamps.

### 3.3. `personas/` (usuarios, dashboards por rol)
- Dashboards para: Administrador, Dirección, Departamento, Jefe de Cuadrilla, Territorial.
- CRUD de usuarios (con teléfono/cargo en Profile) y asignación a grupos.

### 3.4. `organizacion/` (estructura municipal)
- CRUD de Direcciones y Departamentos; toggles de estado; asignación de encargados.
- Vista para asignar cuadrilla a incidencias pendientes (cambia estado a `en_proceso`).

### 3.5. `incidencias/` (gestión de incidencias)
- CRUD de incidencias (campos: título, descripción, estado, prioridad, dirección, departamento, cuadrilla, tipo_incidencia, datos de vecino, lat/long, evidencias).
- Estados usados: `pendiente`, `en_proceso`, `finalizada`, `validada`, `rechazada`.
- Subida de evidencias y finalización (cuadrilla/admin); validación/rechazo según rol.
- API DRF para cuadrillas (listado y resolver incidencias asignadas).

### 3.6. `territorial_app/` (encuestas y acciones territoriales)
- CRUD de encuestas (activa/bloqueada; edición bloqueada si activa).
- Permisos para Admin, Territorial, Dirección, Departamento.
- Validar/rechazar/reasignar incidencias desde vistas territoriales.

### 3.7. `registration/` (autenticación extendida)
- Login/logout, recuperación/cambio de contraseña con vistas Django, creación de perfiles (`Profile`) junto al usuario. Formularios personalizados.

### 3.8. `templates/`
- `base.html` con navbar dinámico, botón volver (no en login/dashboard), modal de imágenes, estilos responsivos básicos para tablas (scroll horizontal).
- Vistas por app en carpetas: personas, incidencias, organizacion, territorial_app, registration, etc.

---
## 4. Modelos Principales (dónde se usan)
- Dirección (`core.models.Direccion`): nombre, estado, encargado (Profile). Vistas CRUD en `organizacion`.
- Departamento (`core.models.Departamento`): nombre, estado, encargado, dirección FK. Vistas CRUD en `organizacion`.
- TipoIncidencia (`core.models.TipoIncidencia`): clasificación de incidencias. CRUD en `incidencias/views_clasificacion.py`.
- JefeCuadrilla (`core.models.JefeCuadrilla`): cuadrilla con usuario/encargado/departamento. Relaciona incidencias.
- Incidencia (`core.models.Incidencia`): estado, prioridad, dirección/departamento/cuadrilla, tipo_incidencia, datos de vecino, evidencias (`Multimedia`). CRUD y flujos en `incidencias/views.py`, listados en dashboards por rol, y API de cuadrilla.
- Encuesta (`core.models.Encuesta`): título, descripción, ubicación, prioridad, estado, departamento, multimedia URLs, datos de vecino, tipo_incidencia. CRUD en `territorial_app`.
- Multimedia (`core.models.Multimedia`): evidencias ligadas a incidencia. Consumido en formularios/vistas y en la API.

---
## 5. Flujos por Rol (vista web)
- **Administrador**: gestiona usuarios, direcciones, departamentos, incidencias, encuestas, tipos; asigna cuadrillas; puede ver todos los estados.
- **Territorial**: crea incidencias, valida/rechaza finalizadas, reasigna; CRUD de encuestas (no edita si activa).
- **Dirección/Departamento**: dashboards filtrados; Departamento asigna cuadrilla a pendientes (cambia a `en_proceso`).
- **Jefe de Cuadrilla**: ve incidencias de sus cuadrillas, sube evidencias, finaliza en `en_proceso`; en la API solo ve las suyas.

Estados de incidencia permitidos: `pendiente` → `en_proceso` → `finalizada` → (`validada`/`rechazada`).

---
## 6. API REST disponible
Autenticación API:
- `POST /api/auth/token/`  
  Body: `{"username": "...", "password": "..."}` → `{"token": "abc123"}`  
  Header: `Authorization: Token abc123` (TokenAuth). *JWT está instalado pero no configurado en settings/urls.*

Rutas de cuadrilla (DRF):
- `GET /incidencias/api/cuadrilla/incidencias/?estado=en_proceso`  
  Devuelve incidencias asignadas a la(s) cuadrilla(s) del usuario autenticado. `estado` opcional: `pendiente|en_proceso|finalizada|validada|rechazada`.
- `POST|PATCH /incidencias/api/cuadrilla/incidencias/<id>/resolver/`  
  Body opcional: `{"evidencia_urls": ["https://..."], "comentario": "texto"}`. Cambia a `finalizada` si estaba en `en_proceso` y pertenece a su cuadrilla.

Endpoints adicionales (web, no API) están en las apps respectivas; no hay `/api/users/` ni `/api/organizacion/` expuestos aún.

---
## 7. Seguridad aplicada
- Sesiones Django para vistas web; TokenAuth para API.
- Permisos por grupo y decoradores (`@solo_admin`, filtros por rol en incidencias).
- CSRF activo en vistas web; para exponer la API a otros orígenes, agregar CORS en settings.
- Recuperación/cambio de contraseña con las vistas estándar (templates en `registration/`).

---
## 8. Instalación y despliegue (local)
```bash
# Crear y activar entorno virtual (Windows)
python -m venv venv
./venv/Scripts/activate

# Instalar dependencias
pip install -r requirements.txt

# Migrar la base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```
Configura la conexión a PostgreSQL en `encuestas/settings.py` (ENGINE, NAME, USER, PASSWORD, HOST, PORT). Puedes cambiar a SQLite para pruebas rápidas.

---
## 9. Checklist de pruebas rápidas
- Jefe de Cuadrilla: crear user+cuadrilla, asignar incidencia en `en_proceso`, llamar a `GET /incidencias/api/cuadrilla/incidencias/` con el token y ver datos.
- Encuestas: crear/editar y verificar bloqueo de edición cuando están activas.
- Flujo incidencias: Departamento asigna cuadrilla a pendiente → pasa a `en_proceso` → cuadrilla sube evidencias y finaliza → Territorial valida/rechaza.

---
## 10. Dependencias principales (requirements.txt)
- asgiref==3.10.0  
- Django==5.2.4  
- djangorestframework==3.15.2  
- djangorestframework-simplejwt==5.3.1 *(instalada; no configurada)*  
- psycopg / psycopg-binary==3.2.12  
- PyJWT==2.10.1  
- sqlparse==0.5.3  
- tzdata==2025.2  
- pip==25.2  

---
## 11. Notas finales
- Diseño responsivo básico en `base.html`; para mobile avanzado (ocultar columnas, menús compactos) habría que ajustar cada template.
- La API ahora expone solo autenticación por token y endpoints de cuadrilla; si necesitas endpoints adicionales (usuarios, organización, encuestas) hay que implementarlos en DRF.
