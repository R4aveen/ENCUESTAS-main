from rest_framework import generics, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from core.models import Incidencia, JefeCuadrilla
from .serializers import IncidenciaSerializer, ResolverIncidenciaSerializer


class CuadrillaIncidenciaListView(generics.ListAPIView):
    """
    Lista incidencias asignadas a la cuadrilla del usuario autenticado.
    Por defecto filtra por estado 'en_proceso' (derivada a cuadrilla), pero puede recibir ?estado=<valor>.
    """

    serializer_class = IncidenciaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile:
            return Incidencia.objects.none()

        try:
            cuadrillas = JefeCuadrilla.objects.filter(usuario=profile) | JefeCuadrilla.objects.filter(encargado=profile)
        except Exception:
            cuadrillas = JefeCuadrilla.objects.none()

        estado = self.request.query_params.get("estado") or "en_proceso"
        estados_validos = ["pendiente", "en_proceso", "finalizada", "validada", "rechazada"]
        if estado not in estados_validos:
            estado = "en_proceso"

        return (
            Incidencia.objects.filter(cuadrilla__in=cuadrillas, estado=estado)
            .select_related("cuadrilla", "departamento", "tipo_incidencia")
            .prefetch_related("multimedias")
            .order_by("-creadoEl")
        )


class CuadrillaResolverIncidenciaView(generics.UpdateAPIView):
    """
    Permite a la cuadrilla marcar la incidencia como finalizada y adjuntar evidencias (URLs).
    """

    serializer_class = ResolverIncidenciaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Incidencia.objects.select_related("cuadrilla", "departamento").prefetch_related("multimedias")
    http_method_names = ["patch", "post"]

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile:
            raise PermissionDenied("No tienes perfil asociado.")

        cuadrillas = JefeCuadrilla.objects.filter(usuario=profile) | JefeCuadrilla.objects.filter(encargado=profile)
        if not cuadrillas.filter(pk=obj.cuadrilla_id).exists():
            raise PermissionDenied("No puedes gestionar esta incidencia.")
        return obj
