from django import template

register = template.Library()

@register.filter(name="has_group")
def has_group(user, group_name: str) -> bool:
    """
    Devuelve True si el usuario pertenece al grupo 'group_name'.
    Verifica tanto user.groups (Django) como user.profile.group para compatibilidad.
    Uso en plantilla:  {% if user|has_group:"Administrador" %} ... {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    try:
        # Verificar Django groups
        if user.groups.filter(name=group_name).exists():
            return True
        
        # Fallback: verificar Profile.group
        if hasattr(user, 'profile') and user.profile.group and user.profile.group.name == group_name:
            return True
    except Exception:
        pass
    
    return False


@register.filter(name="startswith")
def startswith(text: str, prefix: str) -> bool:
    """
    Verifica si 'text' comienza con 'prefix' en plantillas.
    Uso: {% if request.path|startswith:"/ruta" %} ... {% endif %}
    """
    if text is None:
        return False
    try:
        return str(text).startswith(prefix)
    except Exception:
        return False
