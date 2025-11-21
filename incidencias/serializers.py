from rest_framework import serializers
from core.models import Incidencia, Multimedia


class MultimediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Multimedia
        fields = ["id", "nombre", "url", "tipo", "formato"]


class IncidenciaSerializer(serializers.ModelSerializer):
    multimedias = MultimediaSerializer(many=True, read_only=True)
    cuadrilla_nombre = serializers.CharField(source="cuadrilla.nombre_cuadrilla", read_only=True)

    class Meta:
        model = Incidencia
        fields = [
            "id",
            "titulo",
            "descripcion",
            "estado",
            "prioridad",
            "creadoEl",
            "actualizadoEl",
            "departamento",
            "cuadrilla",
            "cuadrilla_nombre",
            "tipo_incidencia",
            "latitud",
            "longitud",
            "multimedias",
        ]


class ResolverIncidenciaSerializer(serializers.ModelSerializer):
    evidencia_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="Lista de URLs de evidencias (imágenes/videos) ya subidas por el cliente.",
    )
    comentario = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Incidencia
        fields = ["estado", "comentario", "evidencia_urls"]
        read_only_fields = ["estado"]

    def validate(self, attrs):
        incidencia: Incidencia = self.instance
        if incidencia.estado != "en_proceso":
            raise serializers.ValidationError("Solo puedes finalizar incidencias en estado 'en_proceso'.")
        return attrs

    def update(self, instance, validated_data):
        urls = validated_data.pop("evidencia_urls", [])
        comentario = validated_data.pop("comentario", None)

        for url in urls:
            Multimedia.objects.create(
                nombre="Evidencia",
                url=url,
                tipo="image",
                formato=url.split(".")[-1][:10] if "." in url else "",
                incidencia=instance,
            )

        if comentario:
            # reutilizamos motivo_rechazo como nota de resolución si existe
            instance.motivo_rechazo = comentario

        instance.estado = "finalizada"
        instance.save(update_fields=["estado", "motivo_rechazo", "actualizadoEl"])
        return instance
