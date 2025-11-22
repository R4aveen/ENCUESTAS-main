from django.contrib.auth.decorators import user_passes_test

def es_admin(u):
    # Admin por grupo o superusuario Django
    return u.is_authenticated and (u.is_superuser or u.groups.filter(name="Administrador").exists())

def es_territorial(u):
    # Verifica si el usuario es Territorial
    return u.is_authenticated and u.groups.filter(name="Territorial").exists()

def es_admin_o_territorial(u):
    # Admin o Territorial pueden acceder
    return u.is_authenticated and (
        u.is_superuser or 
        u.groups.filter(name__in=["Administrador", "Territorial"]).exists()
    )

def es_direccion(u):
    # Verifica si el usuario tiene rol Dirección
    return u.is_authenticated and u.groups.filter(name="Dirección").exists()

def es_departamento(u):
    # Verifica si el usuario tiene rol Departamento
    return u.is_authenticated and u.groups.filter(name="Departamento").exists()

def es_admin_o_direccion(u):
    """
    Admin o Dirección pueden acceder.
    Verifica tanto Django groups como Profile.group para mayor compatibilidad.
    """
    if not u.is_authenticated:
        return False
    
    # Si es superuser, siempre puede
    if u.is_superuser:
        return True
    
    # Verificar Django groups
    if u.groups.filter(name__in=["Administrador", "Dirección"]).exists():
        return True
    
    # Fallback: verificar Profile.group
    try:
        if u.profile.group and u.profile.group.name in ["Administrador", "Dirección"]:
            return True
    except:
        pass
    
    return False

def es_admin_o_departamento(u):
    """
    Admin o Departamento pueden acceder.
    Verifica tanto Django groups como Profile.group para mayor compatibilidad.
    """
    if not u.is_authenticated:
        return False
    
    # Si es superuser, siempre puede
    if u.is_superuser:
        return True
    
    # Verificar Django groups
    if u.groups.filter(name__in=["Administrador", "Departamento"]).exists():
        return True
    
    # Fallback: verificar Profile.group
    try:
        if u.profile.group and u.profile.group.name in ["Administrador", "Departamento"]:
            return True
    except:
        pass
    
    return False

solo_admin = user_passes_test(es_admin, login_url="/accounts/login/", redirect_field_name=None)
solo_territorial = user_passes_test(es_territorial, login_url="/accounts/login/", redirect_field_name=None)
admin_o_territorial = user_passes_test(es_admin_o_territorial, login_url="/accounts/login/", redirect_field_name=None)
admin_o_direccion = user_passes_test(es_admin_o_direccion, login_url="/accounts/login/", redirect_field_name=None)
admin_o_departamento = user_passes_test(es_admin_o_departamento, login_url="/accounts/login/", redirect_field_name=None)
