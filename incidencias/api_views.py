import os
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from core.models import Incidencia, JefeCuadrilla, Multimedia
from .serializers import IncidenciaSerializer, ResolverIncidenciaSerializer, RechazarIncidenciaSerializer

class IncidenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar incidencias.
    Incluye acciones para resolver y rechazar incidencias asignadas a la cuadrilla.
    """
    serializer_class = IncidenciaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Incidencia.objects.none() 

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile:
            return Incidencia.objects.none()

        try:
            cuadrillas = JefeCuadrilla.objects.filter(usuario=profile) | JefeCuadrilla.objects.filter(encargado=profile)
        except Exception:
            return Incidencia.objects.none()

        if not cuadrillas.exists():
            return Incidencia.objects.none()

        qs = Incidencia.objects.filter(cuadrilla__in=cuadrillas)

        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        
        return qs.select_related("cuadrilla", "departamento", "tipo_incidencia").prefetch_related("multimedias").order_by("-creadoEl")

    @action(detail=False, methods=['get'])
    def asignadas(self, request):
        """
        Retorna las incidencias asignadas (en_proceso) para la cuadrilla.
        Ruta: /api/incidencias/asignadas/
        """
        qs = self.get_queryset().filter(estado='en_proceso')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=ResolverIncidenciaSerializer)
    def resolver(self, request, pk=None):
        """
        Resuelve la incidencia.
        Ruta: /api/incidencias/{pk}/resolver/
        """
        incidencia = self.get_object()
        serializer = ResolverIncidenciaSerializer(incidencia, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], serializer_class=RechazarIncidenciaSerializer)
    def rechazar(self, request, pk=None):
        """
        Rechaza la incidencia.
        Ruta: /api/incidencias/{pk}/rechazar/
        """
        incidencia = self.get_object()
        serializer = RechazarIncidenciaSerializer(incidencia, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        """
        Inicia el trabajo en una incidencia pendiente -> pasa a en_proceso.
        Ruta: /api/incidencias/{pk}/iniciar/
        """
        incidencia = self.get_object()
        if incidencia.estado != "pendiente":
            return Response(
                {"detail": "Solo se pueden iniciar incidencias en estado 'pendiente'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        incidencia.estado = "en_proceso"
        incidencia.save(update_fields=["estado", "actualizadoEl"])
        serializer = self.get_serializer(incidencia)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="subir-evidencia")
    def subir_evidencia(self, request, pk=None):
        """
        Sube archivos de evidencia y devuelve sus URLs.
        Espera multipart/form-data con campo 'evidencias' (uno o varios archivos).
        """
        incidencia = self.get_object()
        files = request.FILES.getlist("evidencias")
        if not files:
            return Response({"detail": "No se recibieron archivos en 'evidencias'."}, status=status.HTTP_400_BAD_REQUEST)

        base = slugify(incidencia.titulo) or f"incidencia_{incidencia.id}"
        urls = []
        for idx, f in enumerate(files, start=1):
            ext = os.path.splitext(f.name)[1] or ""
            filename = f"{base}_{incidencia.id}_{idx}{ext}".replace(" ", "_")
            path = default_storage.save(f"evidencias/{filename}", ContentFile(f.read()))
            file_url = default_storage.url(path)
            absolute_url = request.build_absolute_uri(file_url)
            urls.append(file_url)
            Multimedia.objects.create(
                incidencia=incidencia,
                nombre=filename,
                url=absolute_url,
                tipo=f.content_type or "",
                formato=ext.lstrip("."),
            )

        return Response({"urls": urls, "absolute_urls": [request.build_absolute_uri(u) for u in urls]}, status=status.HTTP_201_CREATED)
