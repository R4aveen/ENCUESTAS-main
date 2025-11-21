from django.urls import path
from . import views
from . import views_clasificacion
from . import api_views

app_name = "incidencias"

urlpatterns = [
    # API endpoints
    path("api/cuadrillas-por-departamento/<int:departamento_id>/", views.cuadrillas_por_departamento, name="cuadrillas_por_departamento"),

    # URLs de Tipos de Incidencia
    path("tipos/", views_clasificacion.tipo_lista, name="tipo_lista"),
    path("tipos/nuevo/", views_clasificacion.tipo_crear, name="tipo_crear"),
    path("tipos/<int:pk>/editar/", views_clasificacion.tipo_editar, name="tipo_editar"),
    # El toggle de tipo dependía de un campo 'estado' que ya no existe; ruta removida (una correccion en un error durante la construccion de tipó)
    path("tipos/<int:pk>/eliminar/", views_clasificacion.tipo_eliminar, name="tipo_eliminar"),

    path("incidencias/", views.incidencias_lista, name ="incidencias_lista"),
    path("incidencias/nuevo/", views.incidencia_crear, name = "incidencia_crear"),
    path("incidencias/<int:pk>/", views.incidencia_editar, name = "incidencia_editar") ,
    path("incidencias/<int:pk>/detalle/", views.incidencia_detalle, name = "incidencia_detalle"), 
    path("incidencias/<int:pk>/eliminar/", views.incidencia_eliminar, name = "incidencia_eliminar"),
    path("incidencias/<int:pk>/subir-evidencia/", views.subir_evidencia, name = "subir_evidencia"),
    path("incidencias/<int:pk>/finalizar/", views.finalizar_incidencia, name = "finalizar_incidencia"),

    # API Cuadrilla
    path("api/cuadrilla/incidencias/", api_views.CuadrillaIncidenciaListView.as_view(), name="api_cuadrilla_incidencias"),
    path("api/cuadrilla/incidencias/<int:pk>/resolver/", api_views.CuadrillaResolverIncidenciaView.as_view(), name="api_cuadrilla_resolver"),
]
