from django.contrib.auth.decorators import user_passes_test

def es_admin(u):
    # Admin por grupo o superusuario Django
    return u.is_authenticated and (u.is_superuser or u.groups.filter(name="Administrador").exists())

solo_admin = user_passes_test(es_admin, login_url="/accounts/login/", redirect_field_name=None)
