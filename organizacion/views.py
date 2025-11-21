from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.utils import solo_admin
from core.models import Direccion, Departamento, Incidencia, JefeCuadrilla
from .forms import DireccionForm, DepartamentoForm
from django.db.models import Q, Count

# ------------------- CRUD DIRECCIONES -------------------
@login_required
@solo_admin
def direcciones_lista(request):
    q = request.GET.get("q", "").strip()
    qs = Direccion.objects.all().order_by("nombre_direccion")
    if q:
        qs = qs.filter(nombre_direccion__icontains=q)
    return render(request, "organizacion/direcciones_lista.html", {"direcciones": qs, "q": q})

@login_required
@solo_admin
def direccion_crear(request):
    if request.method == "POST":
        form = DireccionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("organizacion:direcciones_lista")
    else:
        form = DireccionForm()
    return render(request, "organizacion/direccion_form.html", {"form": form})

@login_required
@solo_admin
def direccion_editar(request, pk):
    direccion = get_object_or_404(Direccion, pk=pk)
    if request.method == "POST":
        form = DireccionForm(request.POST, instance=direccion)
        if form.is_valid():
            form.save()
            return redirect("organizacion:direcciones_lista")
    else:
        form = DireccionForm(instance=direccion)
    return render(request, "organizacion/direccion_form.html", {"form": form})

@login_required
@solo_admin
def direccion_detalle(request, pk):
    direccion = get_object_or_404(Direccion, pk=pk)
    grupo = None
    if direccion.encargado and direccion.encargado.group:
        grupo = direccion.encargado.group.name
    return render(request, "organizacion/direccion_detalle.html", {"obj": direccion,"grupo": grupo,})

@login_required
@solo_admin
def direccion_eliminar(request, pk):
    obj = get_object_or_404(Direccion, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Dirección eliminada correctamente.")
        return redirect("organizacion:direcciones_lista")
    return render(request, "organizacion/direccion_eliminar.html", {"obj": obj})

@login_required
@solo_admin
def direccion_toggle_estado(request, pk):
    direccion = get_object_or_404(Direccion, pk=pk)
    if request.method == "POST":
        direccion.estado = not direccion.estado
        direccion.save(update_fields=["estado"])
        estado_txt = "desbloqueada" if direccion.estado else "bloqueada"
        messages.success(request, f"Dirección '{direccion.nombre_direccion}' {estado_txt}.")
    return redirect("organizacion:direcciones_lista")

# ------------------- CRUD DEPARTAMENTOS -------------------

@login_required
@solo_admin
def departamentos_lista(request):
    q = request.GET.get("q", "").strip()
    qs = Departamento.objects.all().order_by("nombre_departamento")
    if q:
        qs = qs.filter(nombre_departamento__icontains=q)
    return render(request, "organizacion/departamentos_lista.html", {"departamentos": qs, "q": q})

@login_required
@solo_admin
def departamento_crear(request):
    if request.method == "POST":
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("organizacion:departamentos_lista")
    else:
        form = DepartamentoForm()
    return render(request, "organizacion/departamento_form.html", {"form": form})

@login_required
@solo_admin
def departamento_editar(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == "POST":
        form = DepartamentoForm(request.POST, instance=departamento)
        if form.is_valid():
            form.save()
            return redirect("organizacion:departamentos_lista")
    else:
        form = DepartamentoForm(instance=departamento)
    return render(request, "organizacion/departamento_form.html", {"form": form})

@login_required
@solo_admin
def departamento_detalle(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    grupo = None
    if departamento.encargado and departamento.encargado.group:
        grupo = departamento.encargado.group.name
    return render(request, "organizacion/departamento_detalle.html", {"obj": departamento, "grupo": grupo})

@login_required
@solo_admin
def departamento_eliminar(request, pk):
    obj = get_object_or_404(Departamento, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Departamento eliminado correctamente.")
        return redirect("organizacion:departamentos_lista")
    return render(request, "organizacion/departamento_eliminar.html", {"obj": obj})


@login_required
@solo_admin
def departamento_toggle_estado(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == "POST":
        departamento.estado = not departamento.estado # Alternar estado
        departamento.save()
        if departamento.estado:
            messages.success(request, f"Departamento '{departamento.nombre_departamento}' desbloqueado.")
        else:
            messages.success(request, f"Departamento '{departamento.nombre_departamento}' bloqueado.")
    return redirect("organizacion:departamentos_lista")


# ------------------- ASIGNACIÓN DE CUADRILLAS -------------------

@login_required
def asignar_cuadrilla_view(request, pk):
    """
    Vista para asignar una cuadrilla a una incidencia pendiente.
    Solo usuarios del Departamento pueden acceder.
    """
    incidencia = get_object_or_404(Incidencia, pk=pk)
    roles = set(request.user.groups.values_list("name", flat=True))
    
    # Validar permisos
    if not ("Departamento" in roles or request.user.is_superuser or "Administrador" in roles):
        messages.error(request, "No tienes permisos para asignar cuadrillas")
        return redirect("incidencias:incidencias_lista")
    
    # Validar que esté pendiente
    if incidencia.estado != 'pendiente':
        messages.warning(request, f"Solo se pueden asignar cuadrillas a incidencias pendientes. Estado actual: {incidencia.estado}")
        return redirect("incidencias:incidencia_detalle", pk=pk)
    
    if request.method == "POST":
        cuadrilla_id = request.POST.get('cuadrilla_id')
        
        if not cuadrilla_id:
            messages.error(request, "Debes seleccionar una cuadrilla")
            return redirect("organizacion:asignar_cuadrilla", pk=pk)
        
        try:
            cuadrilla = JefeCuadrilla.objects.get(pk=cuadrilla_id)
            
            # Asignar cuadrilla y cambiar estado
            incidencia.cuadrilla = cuadrilla
            incidencia.estado = 'en_proceso'
            incidencia.save()
            
            messages.success(
                request,
                f"✅ Incidencia asignada a '{cuadrilla.nombre_cuadrilla}' y puesta en proceso."
            )
            return redirect("personas:dashboard_departamento")
            
        except JefeCuadrilla.DoesNotExist:
            messages.error(request, "Cuadrilla no encontrada")
            return redirect("organizacion:asignar_cuadrilla", pk=pk)
    
    # Obtener cuadrillas disponibles del mismo departamento
    if incidencia.departamento:
        cuadrillas = JefeCuadrilla.objects.filter(departamento=incidencia.departamento)
    else:
        cuadrillas = JefeCuadrilla.objects.all()
    
    ctx = {
        'incidencia': incidencia,
        'cuadrillas': cuadrillas,
    }
    
    return render(request, 'organizacion/asignar_cuadrilla.html', ctx)
