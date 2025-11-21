from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from core.models import Incidencia, Departamento, JefeCuadrilla, Multimedia
from .forms import IncidenciaForm, SubirEvidenciaForm
# from categorias.models import Categoria, Tipo
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.utils import solo_admin, admin_o_territorial
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.storage import default_storage
import os
from datetime import datetime

# ----------------- intento de API para cargar cuadrillas por departamento -----------------
@login_required
def cuadrillas_por_departamento(request, departamento_id):
    """Vista AJAX para cargar las cuadrillas de un departamento."""
    cuadrillas = JefeCuadrilla.objects.filter(departamento_id=departamento_id)
    data = [{'id': c.id, 'nombre_cuadrilla': str(c)} for c in cuadrillas]
    return JsonResponse(data, safe=False)

# ----------------- intento de API 2 sjsj para cargar tipos -----------------
@login_required
def cargar_tipos(request):
    """Vista AJAX para cargar los tipos de una categoría."""
    categoria_id = request.GET.get('categoria_id')
    if not categoria_id:
        return JsonResponse({'tipos': []})
    
    tipos = Tipo.objects.filter(
        categoria_id=categoria_id,
        activo=True
    ).values('id', 'nombre', 'prioridad_predeterminada')
    
    return JsonResponse({'tipos': list(tipos)})

# ----------------- Ayudantes de filtrado por rol -----------------
def _roles_usuario(user):
    return set(user.groups.values_list("name", flat=True))

def _filtrar_por_rol(qs, user):
    """
    Restringe el queryset según el rol del usuario.
    Reglas:
      - Admin (is_superuser) o grupo 'Administrador' y 'Dirección' ven todo.
      - 'Departamento' ve todo.
      - 'Jefe de Cuadrilla' -> solo incidencias de sus cuadrillas (pendiente y en_proceso).
      - 'Territorial' -> solo pendiente.
      - Sin grupo -> solo incidencias asociadas a su email.
    """
    roles = _roles_usuario(user)

    if user.is_superuser or "Administrador" in roles or "Dirección" in roles:
        return qs

    if "Departamento" in roles:
        return qs

    if "Jefe de Cuadrilla" in roles:
        # Filtrar todas las incidencias de las cuadrillas donde el usuario es usuario o encargado
        from core.models import JefeCuadrilla
        from django.db.models import Q
        try:
            profile = user.profile
            cuadrillas = JefeCuadrilla.objects.filter(
                Q(usuario=profile) | Q(encargado=profile)
            )
            return qs.filter(
                cuadrilla__in=cuadrillas
            )
        except:
            return qs.none()

    if "Territorial" in roles:
            # Solo incidencias pendientes de cuadrillas donde el usuario es jefe o encargado
            from core.models import JefeCuadrilla
            from django.db.models import Q
            try:
                profile = user.profile
                cuadrillas = JefeCuadrilla.objects.filter(
                    Q(usuario=profile) | Q(encargado=profile)
                )
                return qs.filter(
                    cuadrilla__in=cuadrillas,
                    estado="pendiente"
                )
            except:
                return qs.none()

    # Sin rol: solo ve las suyas (por email)
    return qs.filter(email_usuario=user.email)


# ----------------- LISTA / DETALLE (abiertao a usuarios logueadoops) -----------------
@login_required
def incidencias_lista(request):
    q = (request.GET.get("q") or "").strip()
    estado = request.GET.get("estado")  # 'pendiente' | 'en_proceso' | 'finalizada' | 'validada' | 'rechazada'
    departamento_id = request.GET.get("departamento") #novo filtrasaon
    qs = Incidencia.objects.all().order_by("-creadoEl")

    # Filtro por string yiaa
    if q:
        qs = qs.filter(titulo__icontains=q)

    # Filtro por rol
    qs = _filtrar_por_rol(qs, request.user)

    # Filtro por status
    estados_validos = [e[0] for e in IncidenciaForm.ESTADO_CHOICES]
    if estado in estados_validos:
        qs = qs.filter(estado=estado)
    
    #filtro por departamento
    if departamento_id:
        qs = qs.filter(departamento_id =departamento_id)

    #etiquetas de colores para cada estadoa
    ESTADOS_COLORES = {
    "pendiente": "secondary",
    "en_proceso": "warning",
    "finalizada": "success",
    "validada": "info",
    "rechazada": "danger",
}

    departamento_nombre = None
    if departamento_id:
        try:
            departamento_nombre = Departamento.objects.get(id=departamento_id).nombre_departamento
        except Departamento.DoesNotExist:
            departamento_nombre = None

    ctx = {
        "incidencias": qs,
        "q": q,
        "estado_seleccionado": estado,
        "departamentos": Departamento.objects.all(),
        "departamento_seleccionado": str(departamento_id) if departamento_id else "",
        "departamento_nombre": departamento_nombre,
        "estados_colores" : ESTADOS_COLORES,
    }
    return render(request, "incidencias/incidencias_lista.html", ctx)

@login_required
def incidencia_detalle(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)
    # proteccion de acceso al detalle según rol
    visible = _filtrar_por_rol(Incidencia.objects.filter(pk=pk), request.user).exists()
    if not visible:
        messages.error(request, "No tienes permisos para ver esta incidencia.")
        return redirect("incidencias:incidencias_lista")
    return render(request, "incidencias/incidencia_detalle.html", {"obj": incidencia})


# ----------------- CRUD (solo administrador) -----------------
@login_required
@admin_o_territorial
def incidencia_crear(request):
    if request.method == "POST":
        form = IncidenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Incidencia creada correctamente.")
            return redirect("incidencias:incidencias_lista")
    else:
        form = IncidenciaForm()
    return render(request, "incidencias/incidencia_form.html", {"form": form})


@login_required
def incidencia_editar(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)
    estado_anterior = incidencia.estado
    motivo_rechazo = request.POST.get('motivo_rechazo')
    roles = set(request.user.groups.values_list("name", flat=True))

    if request.method == "POST":
        form = IncidenciaForm(request.POST, instance=incidencia)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado']
            
            # Validar permisos según el rol y el cambio de estado
            puede_cambiar = False
            
            if request.user.is_superuser or 'Administrador' in roles:
                puede_cambiar = True
            elif 'Territorial' in roles:
                # Territorial solo puede crear (pendiente) y validar/rechazar finalizadas
                if estado_anterior == 'finalizada' and nuevo_estado in ['validada', 'rechazada']:
                    puede_cambiar = True
            elif 'Departamento' in roles:
                # Departamento solo puede poner en proceso las pendientes
                if estado_anterior == 'pendiente' and nuevo_estado == 'en_proceso':
                    puede_cambiar = True
            elif 'Jefe de Cuadrilla' in roles:
                # Cuadrilla solo puede finalizar las que están en proceso
                if estado_anterior == 'en_proceso' and nuevo_estado == 'finalizada':
                    puede_cambiar = True
                    
            if not puede_cambiar:
                messages.error(request, "No tienes permisos para realizar este cambio de estado.")
                return redirect("incidencias:incidencias_lista")
            
            incidencia = form.save(commit=False)
            
            # Si se está rechazando la incidencia, guardar el motivo
            if incidencia.estado == 'rechazada' and motivo_rechazo:
                incidencia.motivo_rechazo = motivo_rechazo
            
            incidencia.save()

            if incidencia.estado != estado_anterior:
                departamento = incidencia.departamento
                if departamento and departamento.encargado and departamento.encargado.user.email:
                    destinatario = departamento.encargado.user.email
                else:
                    destinatario = "soporte@municipalidad.local"

                remitente = (
                    request.user.email
                    if request.user.email
                    else "no-reply@municipalidad.local"
                )

                asunto = f"[Notificación] Estado actualizado de incidencia: {incidencia.titulo}"
                cuerpo = (
                    f"Estimado/a {departamento.encargado},\n\n"
                    f"El usuario {request.user.get_full_name() or request.user.username} "
                    f"ha cambiado el estado de la incidencia '{incidencia.titulo}'.\n\n"
                    f"Estado anterior: {estado_anterior}\n"
                    f"Nuevo estado: {incidencia.estado}\n\n"
                    f"Departamento: {departamento.nombre_departamento if departamento else 'No asignado'}\n"
                    f"Descripción: {incidencia.descripcion}\n"
                    f"Fecha del cambio: {incidencia.actualizadoEl.strftime('%d-%m-%Y %H:%M')}\n\n"
                    "Saludos cordiales,\n"
                    "Sistema Municipal de Incidencias"
                )

                send_mail(
                    asunto,
                    cuerpo,
                    remitente,
                    [destinatario],
                    fail_silently=False,
                )

                messages.success(
                    request,
                    f"Incidencia actualizada. Se notificó a {departamento.encargado} ({destinatario})."
                )
            else:
                messages.success(request, "Incidencia actualizada correctamente.")

            return redirect("incidencias:incidencias_lista")
    else:
        form = IncidenciaForm(instance=incidencia)

    return render(request, "incidencias/incidencia_form.html", {"form": form})

@login_required
@solo_admin
def incidencia_eliminar(request, pk):
    obj = get_object_or_404(Incidencia, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Incidencia eliminada correctamente.")
        return redirect("incidencias:incidencias_lista")
    return render(request, "incidencias/incidencia_eliminar.html", {"obj": obj})


# ----------------- SUBIR EVIDENCIAAA -----------------
@login_required
def subir_evidencia(request, pk):
    """
    Vista para que el Jefe de Cuadrilla asignado suba evidencia y finalice la incidencia.
    Solo la cuadrilla asignada puede acceder.
    """
    incidencia = get_object_or_404(Incidencia, pk=pk)
    roles = set(request.user.groups.values_list("name", flat=True))
    
    # DEBUG: Agregar información de depuración
    print(f"\n{'='*60}")
    print(f"DEBUG - SUBIR EVIDENCIA")
    print(f"Usuario: {request.user.username}")
    print(f"Grupos del usuario: {list(roles)}")
    print(f"Es superuser: {request.user.is_superuser}")
    print(f"Incidencia: #{incidencia.id} - {incidencia.titulo}")
    print(f"Estado incidencia: {incidencia.estado}")
    print(f"Cuadrilla asignada: {incidencia.cuadrilla}")
    try:
        print(f"Profile del usuario: {request.user.profile}")
        if incidencia.cuadrilla:
            print(f"Usuario de cuadrilla: {incidencia.cuadrilla.usuario}")
            print(f"Encargado de cuadrilla: {incidencia.cuadrilla.encargado}")
            print(f"¿Coincide con usuario?: {incidencia.cuadrilla.usuario == request.user.profile}")
            print(f"¿Coincide con encargado?: {incidencia.cuadrilla.encargado == request.user.profile}")
    except Exception as e:
        print(f"ERROR al obtener profile: {e}")
    print(f"{'='*60}\n")
    
    # Validación 1: Solo usuarios con rol "Jefe de Cuadrilla", "Cuadrilla" o "Administrador" pueden acceder
    if not (request.user.is_superuser or "Jefe de Cuadrilla" in roles or "Cuadrilla" in roles or "Administrador" in roles):
        messages.error(request, f"No tienes permisos para subir evidencia. Tus grupos son: {list(roles)}")
        return redirect("incidencias:incidencias_lista")
    
    # Validación 2: Solo la cuadrilla asignada puede subir evidencia
    if not request.user.is_superuser and "Administrador" not in roles:
        if not incidencia.cuadrilla:
            messages.error(request, "Esta incidencia no tiene cuadrilla asignada.")
            return redirect("incidencias:incidencias_lista")
        # Verificar que el usuario pertenece a la cuadrilla asignada
        try:
            usuario_es_de_cuadrilla = (
                incidencia.cuadrilla.usuario == request.user.profile or
                incidencia.cuadrilla.encargado == request.user.profile
            )
        except Exception as e:
            messages.error(request, f"Error al verificar perfil: {e}. Contacta al administrador.")
            return redirect("incidencias:incidencias_lista")
            
        if not usuario_es_de_cuadrilla:
            messages.error(
                request,
                f"Solo la cuadrilla '{incidencia.cuadrilla.nombre_cuadrilla}' puede subir evidencia. "
                f"Tu perfil no coincide con el usuario o encargado de esta cuadrilla."
            )
            return redirect("incidencias:incidencias_lista")
    
    # Validación 3: Solo se puede subir evidencia si está en estado "en_proceso"
    if incidencia.estado != "en_proceso":
        messages.warning(
            request,
            f"Solo se puede subir evidencia cuando la incidencia está 'En proceso'. Estado actual: {incidencia.estado}"
        )
        return redirect("incidencias:incidencia_detalle", pk=pk)
    
    if request.method == "POST":
        form = SubirEvidenciaForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            nombre = form.cleaned_data.get('nombre') or archivo.name
            
            # Crear directorio si no existe
            upload_path = 'evidencias/'
            os.makedirs(os.path.join(settings.MEDIA_ROOT, upload_path), exist_ok=True)
            
            # Guardar archivo con un nombre único
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"{timestamp}_{archivo.name}"
            ruta_completa = os.path.join(upload_path, nombre_archivo)
            ruta_guardada = default_storage.save(ruta_completa, archivo)
            
            # Crear registro en Multimedia
            multimedia = Multimedia.objects.create(
                nombre=nombre,
                url=settings.MEDIA_URL + ruta_guardada,
                tipo=archivo.content_type.split('/')[0],
                formato=archivo.name.split('.')[-1],
                incidencia=incidencia
            )
            
            # NO cambiar automáticamente a finalizada - permitir subir múltiples evidencias
            # La cuadrilla debe finalizar manualmente cuando termine
            
            messages.success(
                request,
                f"Evidencia '{nombre}' subida correctamente. Puedes subir más evidencias o finalizar la incidencia cuando termines."
            )
            return redirect("incidencias:incidencia_detalle", pk=pk)
    else:
        form = SubirEvidenciaForm()
    
    ctx = {
        'form': form,
        'incidencia': incidencia
    }
    return render(request, "incidencias/subir_evidencia.html", ctx)


# ----------------- FINALAIZAR INCIDENCIAAS -----------------
@login_required
def finalizar_incidencia(request, pk):
    incidencia = get_object_or_404(Incidencia, pk=pk)
    roles = set(request.user.groups.values_list("name", flat=True))
    
    # Validación 1: Solo cuadrillas o admin
    if not (request.user.is_superuser or "Jefe de Cuadrilla" in roles or "Cuadrilla" in roles or "Administrador" in roles):
        messages.error(request, "No tienes permisos para finalizar incidencias.")
        return redirect("incidencias:incidencias_lista")
    
    # Validación 2: Solo la auadrilla asignada
    if not request.user.is_superuser and "Administrador" not in roles:
        if not incidencia.cuadrilla:
            messages.error(request, "Esta incidencia no tiene cuadrilla asignada.")
            return redirect("incidencias:incidencias_lista")
        
        try:
            usuario_es_de_cuadrilla = (
                incidencia.cuadrilla.usuario == request.user.profile or
                incidencia.cuadrilla.encargado == request.user.profile
            )
        except Exception as e:
            messages.error(request, f"Error al verificar perfil: {e}")
            return redirect("incidencias:incidencias_lista")
            
        if not usuario_es_de_cuadrilla:
            messages.error(request, f"Solo la cuadrilla '{incidencia.cuadrilla.nombre_cuadrilla}' puede finalizar esta incidencia.")
            return redirect("incidencias:incidencias_lista")
    
    # Validación 3: Debe estar en "en_proceso"
    if incidencia.estado != "en_proceso":
        messages.warning(request, f"Solo se pueden finalizar incidencias en estado 'En proceso'. Estado actual: {incidencia.estado}")
        return redirect("incidencias:incidencia_detalle", pk=pk)
    
    # Validación 4: Debe tener al menos una evidencia
    if not incidencia.multimedias.exists():
        messages.error(request, "Debes subir al menos una evidencia antes de finalizar la incidencia.")
        return redirect("incidencias:subir_evidencia", pk=pk)
    
    # Finalizar incidencia
    incidencia.estado = "finalizada"
    incidencia.save()
    
    messages.success(
        request,
        f"¡Incidencia finalizada correctamente! El territorial ahora puede validar o rechazar el trabajo realizado."
    )
    return redirect("incidencias:incidencia_detalle", pk=pk)
