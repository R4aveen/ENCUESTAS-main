from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from registration.models import Profile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_POST
from .forms import UsuarioCrearForm, UsuarioEditarForm
from .utils import solo_admin
from core.models import Incidencia

@login_required
def dashboard_admin(request):
    from core.models import Incidencia
    stats = {
        "usuarios_total": User.objects.count(),
        "incidencias_total": Incidencia.objects.count(),
    }
    estados = ["pendiente", "en_proceso", "finalizada", "validada", "rechazada"]
    stats["incidencias_por_estado"] = {
        e: Incidencia.objects.filter(estado=e).count() for e in estados
    }
    return render(request, "personas/dashboards/admin.html", {"stats": stats})

@login_required
def dashboard_territorial(request):
    # Obtener las últimas 10 incidencias para mostrar en el dashboard
    incidencias = Incidencia.objects.all().order_by('-creadoEl')[:10]
    estados = ["pendiente", "en_proceso", "finalizada", "validada", "rechazada"]
    stats = {e: Incidencia.objects.filter(estado=e).count() for e in estados}
    return render(request, "personas/dashboards/territorial.html", {
        'incidencias': incidencias,
        'stats': stats,
    })

@login_required
def dashboard_jefe(request):
    """
    Dashboard para Jefe de Cuadrilla.
    Muestra las incidencias asignadas a su cuadrilla.
    """
    # Obtener el profile del usuario actual
    try:
        profile = request.user.profile
    except:
        profile = None
    
    # Buscar las cuadrillas donde el usuario es el encargado o el usuario asignado
    from core.models import JefeCuadrilla
    
    if profile:
        cuadrillas = JefeCuadrilla.objects.filter(
            Q(usuario=profile) | Q(encargado=profile)
        )
    else:
        cuadrillas = JefeCuadrilla.objects.none()
    
    # Obtener las incidencias asignadas a las cuadrillas del usuario
    incidencias_pendientes = []
    incidencias_en_proceso = []
    incidencias_finalizadas = []
    
    if cuadrillas.exists():
        # Filtrar incidencias por las cuadrillas del usuario
        incidencias_pendientes = Incidencia.objects.filter(
            cuadrilla__in=cuadrillas,
            estado='pendiente'
        ).order_by('-creadoEl')
        
        incidencias_en_proceso = Incidencia.objects.filter(
            cuadrilla__in=cuadrillas,
            estado='en_proceso'
        ).order_by('-creadoEl')
        
        incidencias_finalizadas = Incidencia.objects.filter(
            cuadrilla__in=cuadrillas,
            estado__in=['finalizada', 'validada', 'rechazada']
        ).order_by('-actualizadoEl')[:10]  # Últimas 10 finalizadas
    
    return render(request, "personas/dashboards/jefeCuadrilla.html", {
        'cuadrillas': cuadrillas,
        'incidencias_pendientes': incidencias_pendientes,
        'incidencias_en_proceso': incidencias_en_proceso,
        'incidencias_finalizadas': incidencias_finalizadas,
    })

@login_required
def dashboard_direccion(request):
    from core.models import Direccion, Incidencia
    try:
        direcciones = Direccion.objects.filter(encargado=request.user.profile)
    except Exception:
        direcciones = Direccion.objects.none()
    incidencias = Incidencia.objects.filter(departamento__direccion__in=direcciones) if direcciones else Incidencia.objects.none()
    estados = ["pendiente", "en_proceso", "finalizada", "validada", "rechazada"]
    stats = {e: incidencias.filter(estado=e).count() for e in estados} if direcciones else {}
    return render(request, "personas/dashboards/direccion.html", {"stats": stats, "direcciones": direcciones})

@login_required
@login_required
def dashboard_departamento(request):
    """
    Dashboard para usuarios del grupo Departamento.
    Muestra incidencias pendientes para asignar a cuadrillas.
    """
    from core.models import Incidencia, JefeCuadrilla, Departamento
    from django.db.models import Q, Count
    
    roles = set(request.user.groups.values_list("name", flat=True))
    
    if not ("Departamento" in roles or request.user.is_superuser or "Administrador" in roles):
        messages.error(request, "No tienes acceso a este dashboard")
        return redirect("incidencias:incidencias_lista")
    
    # Obtener departamento del usuario
    try:
        departamento = Departamento.objects.get(encargado=request.user.profile)
    except:
        departamento = None
    
    # Incidencias del departamento
    if departamento:
        incidencias_pendientes = Incidencia.objects.filter(
            departamento=departamento,
            estado='pendiente'
        ).order_by('-creadoEl')
        
        incidencias_en_proceso = Incidencia.objects.filter(
            departamento=departamento,
            estado='en_proceso'
        ).order_by('-creadoEl')
        
        incidencias_finalizadas = Incidencia.objects.filter(
            departamento=departamento,
            estado='finalizada'
        ).order_by('-creadoEl')
        
        # Cuadrillas del departamento
        cuadrillas = JefeCuadrilla.objects.filter(departamento=departamento)
    else:
        # Si es admin, ver todas
        incidencias_pendientes = Incidencia.objects.filter(estado='pendiente').order_by('-creadoEl')
        incidencias_en_proceso = Incidencia.objects.filter(estado='en_proceso').order_by('-creadoEl')
        incidencias_finalizadas = Incidencia.objects.filter(estado='finalizada').order_by('-creadoEl')
        cuadrillas = JefeCuadrilla.objects.all()
    
    ctx = {
        'departamento': departamento,
        'incidencias_pendientes': incidencias_pendientes,
        'incidencias_en_proceso': incidencias_en_proceso,
        'incidencias_finalizadas': incidencias_finalizadas,
        'cuadrillas': cuadrillas,
        'total_pendientes': incidencias_pendientes.count(),
        'total_en_proceso': incidencias_en_proceso.count(),
        'total_finalizadas': incidencias_finalizadas.count(),
    }
    
    return render(request, 'personas/dashboards/departamento.html', ctx)


@login_required
def check_profile(request):
    """
    Redirige al usuario al dashboard correspondiente según su rol.
    """
    user = request.user
    
    # Si es superusuario, va directo al admin
    if user.is_superuser:
        return redirect("personas:dashboard_admin")

    try:
        profile = Profile.objects.select_related('group').get(user=user)
    except Profile.DoesNotExist:
        messages.error(request, "No se encontró un perfil asociado a este usuario.")
        logout(request)
        return redirect("login")

    # Obtener el nombre del grupo y limpiarlo
    if not profile.group:
        messages.error(request, "Tu usuario no tiene un grupo/rol asignado. Contacta al administrador.")
        logout(request)
        return redirect("login")
    
    rol = profile.group.name.strip()
    
    # Debug: puedes comentar esto después de probar
    print(f"Usuario: {user.username}, Rol: '{rol}'")
    
    # Redirección según el rol
    if rol == "Administrador":
        return redirect("personas:dashboard_admin")
    elif rol == "Territorial":
        return redirect("personas:dashboard_territorial")
    elif rol == "Jefe de Cuadrilla":
        return redirect("personas:dashboard_jefeCuadrilla")
    elif rol == "Dirección":
        return redirect("personas:dashboard_direccion")
    elif rol == "Departamento":
        return redirect("personas:dashboard_departamento")
    else:
        messages.error(request, f"Rol '{rol}' no reconocido. Contacta al administrador.")
        logout(request)
        return redirect("login")
    

@login_required
@solo_admin
def usuarios_lista(request):
    q = request.GET.get("q", "").strip()
    qs = User.objects.all().order_by("id")
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )
    return render(request, "personas/usuarios_lista.html", {"usuarios": qs, "q": q})

@login_required
@solo_admin
def usuario_crear(request):
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario '{user.username}' creado.")
            return redirect("personas:usuarios_lista")
    else:
        form = UsuarioCrearForm(initial={"is_active": True, "is_staff": False})
    return render(request, "personas/usuario_form.html", {"form": form, "modo": "crear"})

@login_required
@solo_admin
def usuario_editar(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario '{user.username}' actualizado.")
            return redirect("personas:usuarios_lista")
    else:
        form = UsuarioEditarForm(instance=user)
    return render(request, "personas/usuario_form.html", {"form": form, "modo": "editar", "obj": user})

@login_required
@solo_admin
@require_POST
def usuario_toggle_activo(request, pk):
    user = get_object_or_404(User, pk=pk)

    if user == request.user and user.is_active:
        messages.warning(request, "No puedes desactivar tu propio usuario mientras estás conectado.")
        return redirect("personas:usuarios_lista")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    estado = "activado" if user.is_active else "desactivado"
    messages.success(request, f"Usuario '{user.username}' {estado}.")
    return redirect("personas:usuarios_lista")

@login_required
@solo_admin
def usuario_detalle(request, pk):
    user = get_object_or_404(User, pk=pk)
    groups = list(user.groups.values_list("name", flat=True))
    return render(request, "personas/usuario_detalle.html", {"obj": user, "groups": groups})

@login_required
@solo_admin
def usuario_eliminar(request, pk):
    """
    Eliminación suave: desactiva el usuario para impedir inicio de sesión.
    Permite revertir con el toggle de activo.
    """
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if user == request.user:
            messages.error(request, "No puedes eliminar tu propio usuario estando conectado.")
            return redirect("personas:usuarios_lista")
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"Usuario '{user.username}' desactivado.")
        return redirect("personas:usuarios_lista")
    return render(request, "personas/usuario_confirm_delete.html", {"obj": user})

def cerrar_sesion(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("/accounts/login/")
