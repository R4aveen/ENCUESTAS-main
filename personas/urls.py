from django.urls import path
from . import views

app_name = "personas" 

urlpatterns = [
    path('check_profile/', views.check_profile, name='check_profile'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/territorial/', views.dashboard_territorial, name='dashboard_territorial'),
    path('dashboard/jefe/', views.dashboard_jefe, name='dashboard_jefeCuadrilla'),
    path('dashboard/direccion/', views.dashboard_direccion, name='dashboard_direccion'),
    path('dashboard/departamento/', views.dashboard_departamento, name='dashboard_departamento'),

    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("usuarios/nuevo/", views.usuario_crear, name="usuario_crear"),
    path("usuarios/<int:pk>/", views.usuario_detalle, name="usuario_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/toggle-activo/", views.usuario_toggle_activo, name="usuario_toggle_activo"),
    path("usuarios/<int:pk>/eliminar/", views.usuario_eliminar, name="usuario_eliminar"),
    
    # Cerrar sesión
    path("cerrar_sesion/", views.cerrar_sesion, name="cerrar_sesion"),
]
