from django.contrib import admin
from .models import Departamento, JefeCuadrilla, Incidencia, Direccion, Multimedia, Territorial

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

class TerritorialInline(admin.TabularInline):
    model = Territorial
    extra = 1
    autocomplete_fields = ['usuario']
    verbose_name = "Asignación territorial"
    verbose_name_plural = "Asignaciones territoriales"


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'estado', 'prioridad', 'cuadrilla', 'departamento', 'creadoEl']
    list_filter = ['estado', 'prioridad', 'departamento', 'cuadrilla']
    search_fields = ['titulo', 'descripcion', 'nombre_vecino']
    date_hierarchy = 'creadoEl'
    raw_id_fields = ['cuadrilla', 'respuesta']
    inlines = [TerritorialInline]
    
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # El campo respuesta (RespuestaEncuesta) es opcional en la incidencia
        if 'respuesta' in form.base_fields:
            form.base_fields['respuesta'].required = False
            form.base_fields['respuesta'].help_text = "Opcional: respuesta asociada a la encuesta (dejar vacío si no aplica)."
        return form

@admin.register(Multimedia)
class MultimediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'incidencia', 'tipo', 'creadoEl']
    list_filter = ['tipo', 'creadoEl']
    search_fields = ['nombre']
    raw_id_fields = ['incidencia']


@admin.register(Territorial)
class TerritorialAdmin(admin.ModelAdmin):
    list_display = ['id', 'incidencia', 'usuario']
    search_fields = ['incidencia__titulo', 'usuario__user__username', 'usuario__user__email']
    raw_id_fields = ['incidencia']
    autocomplete_fields = ['usuario']

