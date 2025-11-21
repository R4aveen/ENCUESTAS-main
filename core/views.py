from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UsuarioCrearForm, UsuarioEditarForm
from .utils import solo_admin
from .models import Incidencia

@login_required
@solo_admin
def dashboard_admin(request):
    """Vista del panel de administración principal."""
    return render(request, "personas/dashboards/admin.html")


@login_required
@solo_admin
def usuarios_lista(request):
    q = request.GET.get("q", "").strip()
    qs = (
        User.objects
        .all()
        .order_by("id")
        .prefetch_related("groups")  # para mostrar rápido los grupos 
    )
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    return render(request, "core/usuarios_lista.html", {"usuarios": qs, "q": q})


@login_required
@solo_admin
@transaction.atomic
def usuario_crear(request):
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario '{user.username}' creado.")
            return redirect("core:usuarios_lista")
    else:
        # Puedes quitar is_staff del initial si ya no lo usas en el form
        form = UsuarioCrearForm(initial={"is_active": True, "is_staff": False})
    return render(request, "core/usuario_form.html", {"form": form, "modo": "crear"})


@login_required
@solo_admin
@transaction.atomic
def usuario_editar(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario '{user.username}' actualizado.")
            return redirect("core:usuarios_lista")
    else:
        form = UsuarioEditarForm(instance=user)
    return render(
        request,
        "core/usuario_form.html",
        {"form": form, "modo": "editar", "obj": user},
    )


@login_required
@solo_admin
@transaction.atomic
def usuario_toggle_activo(request, pk):
    user = get_object_or_404(User, pk=pk)

    # No permitir que un usuario se desactive a sí mismo
    if user.pk == request.user.pk:
        messages.warning(request, "No puedes activarte/desactivarte a ti mismo.")
        return redirect("core:usuarios_lista")

    # No permitir que alguien que no es superusuario cambie a un superusuario
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para cambiar el estado de un superusuario.")
        return redirect("core:usuarios_lista")

    if request.method in ("POST", "GET"):
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        estado = "activado" if user.is_active else "desactivado"
        messages.success(request, f"Usuario '{user.username}' {estado}.")
        return redirect("core:usuarios_lista")

    # Si llegara por otro método HTTP, muestra confirmación simple
    return render(request, "core/usuario_toggle_confirm.html", {"obj": user})


@login_required
@solo_admin
def usuario_detalle(request, pk):
    user = get_object_or_404(User, pk=pk)
    groups = list(user.groups.values_list("name", flat=True))
    return render(request, "core/usuario_detalle.html", {"obj": user, "groups": groups})
