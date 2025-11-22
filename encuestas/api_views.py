from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def health(request):
    """
    Endpoint sencillo para que el frontend verifique
    que el backend está vivo.
    Ruta: /api/health/
    """
    return Response({"status": "ok"})

