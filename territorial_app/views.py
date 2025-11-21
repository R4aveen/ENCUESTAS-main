from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from core.models import Incidencia, JefeCuadrilla, Departamento, Encuesta
from .forms import RechazarIncidenciaForm, ReasignarIncidenciaForm, EncuestaForm
from core.utils import solo_admin, admin_o_territorial


def _puede_gestionar_encuestas(user):
    roles = set(user.groups.values_list("name", flat=True))
    return user.is_superuser or bool(
        roles.intersection({"Administrador", "Territorial", "Dirección", "Departamento"})
    )

# ============================================
# VISTAS DE INCIDENCIAS (Existentes)
# ============================================

@login_required
@admin_o_territorial
def lista_incidencias(request):
    user = request.user
    if user.groups.filter(name='Administrador').exists():
        incidencias = Incidencia.objects.all().order_by('-creadoEl')
    elif user.groups.filter(name='Territorial').exists():
        incidencias = Incidencia.objects.filter(cuadrilla__usuario=user.profile).order_by('-creadoEl')
    else:
        incidencias = Incidencia.objects.none()
    return render(
        request,
        'territorial_app/lista_incidencias.html',
        {'incidencias': incidencias}
    )

@login_required
@admin_o_territorial
def validar_incidencia(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)
    incidencia.estado = 'validada'
    incidencia.fecha_cierre = timezone.now()
    incidencia.save()
    messages.success(request, f"Incidencia '{incidencia.titulo}' validada.")
    return redirect('territorial_app:incidencias_lista')

@login_required
@admin_o_territorial
def rechazar_incidencia(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)
    if request.method == 'POST':
        form = RechazarIncidenciaForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            incidencia.estado = 'rechazada'
            incidencia.motivo_rechazo = motivo
            incidencia.fecha_cierre = timezone.now()
            incidencia.save()
            messages.success(request, f"Incidencia '{incidencia.titulo}' rechazada.")
            return redirect('territorial_app:incidencias_lista')
    else:
        form = RechazarIncidenciaForm()
    return render(
        request,
        'territorial_app/rechazar_incidencia.html',
        {'form': form, 'incidencia': incidencia}
    )

@login_required
@admin_o_territorial
def reasignar_incidencia(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)

    if request.method == 'POST':
        form = ReasignarIncidenciaForm(request.POST, instance=incidencia)
        if form.is_valid():
            incidencia_obj = form.save(commit=False)
            incidencia_obj.cuadrilla = form.cleaned_data['cuadrilla']
            incidencia_obj.save()

            messages.success(
                request,
                f"Incidencia '{incidencia.titulo}' reasignada a departamento '{incidencia.departamento}'."
            )
            return redirect('territorial_app:incidencias_lista')
    else:
        form = ReasignarIncidenciaForm(instance=incidencia)

    return render(
        request,
        'territorial_app/reasignar_incidencia.html',
        {'form': form, 'incidencia': incidencia}
    )


# ============================================
# VISTAS DE ENCUESTAS (CRUD para Territorial)
# ============================================

@login_required
def encuestas_lista(request):
    """
    Lista todas las encuestas.
    Territorial y Admin pueden verlas todas.
    """
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado")  # 'activo' | 'inactivo' | None
    
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para ver encuestas.")
        return redirect("personas:check_profile")

    qs = Encuesta.objects.all().select_related('departamento').order_by('-creadoEl')
    
    # Filtro por búsqueda de texto
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) | 
            Q(descripcion__icontains=q) |
            Q(departamento__nombre_departamento__icontains=q)
        )
    
    # Filtro por estado
    if estado == 'activo':
        qs = qs.filter(estado=True)
    elif estado == 'inactivo':
        qs = qs.filter(estado=False)
    
    ctx = {
        "encuestas": qs,
        "q": q,
        "estado_seleccionado": estado,
    }
    return render(request, "territorial_app/encuestas_lista.html", ctx)


@login_required
def encuesta_detalle(request, pk):
    """
    Muestra el detalle de una encuesta.
    """
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para ver encuestas.")
        return redirect("personas:check_profile")
    encuesta = get_object_or_404(Encuesta, pk=pk)
    return render(request, "territorial_app/encuesta_detalle.html", {"encuesta": encuesta})


@login_required
def encuesta_crear(request):
    """
    Crea una nueva encuesta.
    Solo Territorial y Admin pueden crear.
    """
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para crear encuestas.")
        return redirect("personas:check_profile")
    if request.method == "POST":
        form = EncuestaForm(request.POST)
        if form.is_valid():
            encuesta = form.save()
            messages.success(request, f"Encuesta '{encuesta.titulo}' creada correctamente.")
            return redirect("territorial_app:encuestas_lista")
    else:
        form = EncuestaForm(initial={'estado': True, 'prioridad': 'Normal'})
    
    return render(request, "territorial_app/encuesta_form.html", {
        "form": form,
        "modo": "crear"
    })


@login_required
def encuesta_editar(request, pk):
    """
    Edita una encuesta existente.
    Según requerimientos: solo se puede editar si está bloqueada (inactiva).
    """
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para editar encuestas.")
        return redirect("personas:check_profile")
    encuesta = get_object_or_404(Encuesta, pk=pk)
    
    # Validación: no se puede editar una encuesta activa
    if encuesta.estado:
        messages.error(request, "No se puede editar una encuesta activa. Debes desactivarla primero.")
        return redirect("territorial_app:encuesta_detalle", pk=pk)
    
    if request.method == "POST":
        form = EncuestaForm(request.POST, instance=encuesta)
        if form.is_valid():
            encuesta = form.save()
            messages.success(request, f"Encuesta '{encuesta.titulo}' actualizada correctamente.")
            return redirect("territorial_app:encuestas_lista")
    else:
        form = EncuestaForm(instance=encuesta)
    
    return render(request, "territorial_app/encuesta_form.html", {
        "form": form,
        "modo": "editar",
        "encuesta": encuesta
    })


@login_required
def encuesta_toggle_estado(request, pk):
    """
    Activa o desactiva (bloquea) una encuesta.
    Según requerimientos: cambiar entre activa/bloqueada.
    """
    if request.method != "POST":
        messages.error(request, "Método no permitido.")
        return redirect("territorial_app:encuestas_lista")
    
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para cambiar el estado de encuestas.")
        return redirect("personas:check_profile")
    encuesta = get_object_or_404(Encuesta, pk=pk)
    encuesta.estado = not encuesta.estado
    encuesta.save(update_fields=['estado', 'actualizadoEl'])
    
    estado_texto = "activada" if encuesta.estado else "bloqueada"
    messages.success(request, f"Encuesta '{encuesta.titulo}' {estado_texto} correctamente.")
    
    return redirect("territorial_app:encuestas_lista")


@login_required
def encuesta_eliminar(request, pk):
    """
    Elimina una encuesta.
    Opcional: podrías requerir que esté bloqueada para eliminarla.
    """
    if not _puede_gestionar_encuestas(request.user):
        messages.error(request, "No tienes permiso para eliminar encuestas.")
        return redirect("personas:check_profile")
    encuesta = get_object_or_404(Encuesta, pk=pk)
    
    # Opcional: solo permitir eliminar si está bloqueada
    if encuesta.estado:
        messages.error(request, "No se puede eliminar una encuesta activa. Debes desactivarla primero.")
        return redirect("territorial_app:encuesta_detalle", pk=pk)
    
    if request.method == "POST":
        titulo = encuesta.titulo
        encuesta.delete()
        messages.success(request, f"Encuesta '{titulo}' eliminada correctamente.")
        return redirect("territorial_app:encuestas_lista")
    
    return render(request, "territorial_app/encuesta_eliminar.html", {"encuesta": encuesta})
