from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.utils import solo_admin
from core.models import TipoIncidencia
from .forms_clasificacion import TipoIncidenciaForm

# ----------------- CRUD Tipos de Incidencia -----------------
@login_required
@solo_admin
def tipo_lista(request):
    tipos = TipoIncidencia.objects.all()
    return render(request, 'tipo/tipo_lista.html', {'tipos': tipos})

@login_required
@solo_admin
def tipo_crear(request):
    if request.method == "POST":
        form = TipoIncidenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de incidencia creado correctamente.")
            return redirect('incidencias:tipo_lista')
    else:
        form = TipoIncidenciaForm()
    return render(request, 'tipo/tipo_form.html', {'form': form})

@login_required
@solo_admin
def tipo_editar(request, pk):
    tipo = get_object_or_404(TipoIncidencia, pk=pk)
    if request.method == "POST":
        form = TipoIncidenciaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de incidencia actualizado correctamente.")
            return redirect('incidencias:tipo_lista')
    else:
        form = TipoIncidenciaForm(instance=tipo)
    return render(request, 'tipo/tipo_form.html', {'form': form})

@login_required
@solo_admin
def tipo_eliminar(request, pk):
    tipo = get_object_or_404(TipoIncidencia, pk=pk)
    if request.method == "POST":
        try:
            tipo.delete()
            messages.success(request, "Tipo de incidencia eliminado correctamente.")
            return redirect('incidencias:tipo_lista')
        except Exception:
            messages.error(request, "No se puede eliminar el tipo porque tiene incidencias asociadas.")
            return redirect('incidencias:tipo_lista')
    return render(request, 'tipo/tipo_eliminar.html', {'obj': tipo})