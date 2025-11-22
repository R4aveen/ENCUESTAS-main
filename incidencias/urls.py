from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_clasificacion
from . import api_views

app_name = "incidencias"

router = DefaultRouter()
# API para cuadrilla: /incidencias/api/cuadrilla/incidencias/ y acciones resolver/rechazar
router.register(r'api/cuadrilla/incidencias', api_views.IncidenciaViewSet, basename='api_cuadrilla_incidencias')
# Alias general: /incidencias/api/incidencias/ (mismo ViewSet y acciones)
router.register(r'api/incidencias', api_views.IncidenciaViewSet, basename='api_incidencias')

urlpatterns = [
    # API endpoints (Router)
    path('', include(router.urls)),

    # API endpoints (Legacy/Manual - if any needed, but ViewSet covers them)
    path("api/cuadrillas-por-departamento/<int:departamento_id>/", views.cuadrillas_por_departamento, name="cuadrillas_por_departamento"),

    # URLs de Tipos de Incidencia
    path("tipos/", views_clasificacion.tipo_lista, name="tipo_lista"),
    path("tipos/nuevo/", views_clasificacion.tipo_crear, name="tipo_crear"),
    path("tipos/<int:pk>/editar/", views_clasificacion.tipo_editar, name="tipo_editar"),
    path("tipos/<int:pk>/eliminar/", views_clasificacion.tipo_eliminar, name="tipo_eliminar"),

    # URLs de Vistas (Templates)
    path("incidencias/", views.incidencias_lista, name ="incidencias_lista"),
    path("incidencias/nuevo/", views.incidencia_crear, name = "incidencia_crear"),
    path("incidencias/<int:pk>/", views.incidencia_editar, name = "incidencia_editar") ,
    path("incidencias/<int:pk>/detalle/", views.incidencia_detalle, name = "incidencia_detalle"), 
    path("incidencias/<int:pk>/eliminar/", views.incidencia_eliminar, name = "incidencia_eliminar"),
    path("incidencias/<int:pk>/subir-evidencia/", views.subir_evidencia, name = "subir_evidencia"),
    path("incidencias/<int:pk>/finalizar/", views.finalizar_incidencia, name = "finalizar_incidencia"),
]
