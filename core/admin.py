from django.contrib import admin
from .models import Departamento, JefeCuadrilla, Incidencia, Direccion, Multimedia

# Register your models here.

@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_direccion', 'estado', 'creadoEl']
    list_filter = ['estado']
    search_fields = ['nombre_direccion']

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_departamento', 'encargado', 'direccion', 'estado', 'creadoEl']
    list_filter = ['estado', 'direccion']
    search_fields = ['nombre_departamento']
    raw_id_fields = ['encargado']

@admin.register(JefeCuadrilla)
class JefeCuadrillaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_cuadrilla', 'usuario', 'encargado', 'departamento']
    list_filter = ['departamento']
    search_fields = ['nombre_cuadrilla']
    raw_id_fields = ['usuario', 'encargado']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_cuadrilla',)
        }),
        ('Asignaciones', {
            'fields': ('usuario', 'encargado', 'departamento'),
            'description': 'IMPORTANTE: Asigna el departamento para que esta cuadrilla aparezca en las opciones de asignación.'
        }),
    )

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'estado', 'prioridad', 'cuadrilla', 'departamento', 'creadoEl']
    list_filter = ['estado', 'prioridad', 'departamento', 'cuadrilla']
    search_fields = ['titulo', 'descripcion', 'nombre_vecino']
    date_hierarchy = 'creadoEl'
    raw_id_fields = ['cuadrilla', 'respuesta']
    
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'estado', 'prioridad')
        }),
        ('Ubicación', {
            'fields': ('latitud', 'longitud')
        }),
        ('Vecino', {
            'fields': ('nombre_vecino', 'correo_vecino', 'telefono_vecino')
        }),
        ('Asignaciones', {
            'fields': ('departamento', 'cuadrilla', 'respuesta'),
            'description': 'El departamento se asigna automáticamente. La cuadrilla la asigna el usuario Departamento.'
        }),
        ('Gestión', {
            'fields': ('fecha_cierre', 'motivo_rechazo'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Multimedia)
class MultimediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'incidencia', 'tipo', 'creadoEl']
    list_filter = ['tipo', 'creadoEl']
    search_fields = ['nombre']
    raw_id_fields = ['incidencia']

