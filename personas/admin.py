from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

@admin.action(description="Activar usuarios seleccionados")
def activar_usuarios(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Desactivar usuarios seleccionados")
def desactivar_usuarios(modeladmin, request, queryset):

    queryset.exclude(pk=request.user.pk).update(is_active=False)

class CustomUserAdmin(UserAdmin):
    actions = [activar_usuarios, desactivar_usuarios]

# Reemplazar el admin por defecto del User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

