from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Panel de Administración
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("usuarios/nuevo/", views.usuario_crear, name="usuario_crear"),
    path("usuarios/<int:pk>/", views.usuario_detalle, name="usuario_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/toggle/", views.usuario_toggle_activo, name="usuario_toggle_activo"),
]
