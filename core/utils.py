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

solo_admin = user_passes_test(es_admin, login_url="/accounts/login/", redirect_field_name=None)
solo_territorial = user_passes_test(es_territorial, login_url="/accounts/login/", redirect_field_name=None)
admin_o_territorial = user_passes_test(es_admin_o_territorial, login_url="/accounts/login/", redirect_field_name=None)
