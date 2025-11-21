from django import template

register = template.Library()

@register.filter(name="has_group")
def has_group(user, group_name: str) -> bool:
    """
    Devuelve True si el usuario pertenece al grupo 'group_name'.
    Uso en plantilla:  {% if user|has_group:"Administrador" %} ... {% endif %}
    """
    try:
        return user.is_authenticated and user.groups.filter(name=group_name).exists()
    except Exception:
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
