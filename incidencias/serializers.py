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
        child=serializers.CharField(max_length=1024),
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
        # Limpia vacíos en evidencia_urls
        urls = attrs.get("evidencia_urls", [])
        if urls:
            urls = [u for u in urls if u and str(u).strip()]
            attrs["evidencia_urls"] = urls
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
            # OJO: El modelo Incidencia tiene 'motivo_rechazo', pero no 'comentario_resolucion'.
            # Si el usuario pide 'comentario', lo guardamos donde podamos o asumimos que es motivo_rechazo?
            # El prompt dice: "Debe recibir 'evidencia_urls' y 'comentario'".
            # En el código existente ya usaban motivo_rechazo para esto. Lo mantendré.
            instance.motivo_rechazo = comentario

        instance.estado = "finalizada"
        instance.save(update_fields=["estado", "motivo_rechazo", "actualizadoEl"])
        return instance


class RechazarIncidenciaSerializer(serializers.ModelSerializer):
    motivo_rechazo = serializers.CharField(required=True)

    class Meta:
        model = Incidencia
        fields = ["estado", "motivo_rechazo"]
        read_only_fields = ["estado"]

    def validate(self, attrs):
        incidencia: Incidencia = self.instance
        # Asumo que se puede rechazar si está 'en_proceso' o 'pendiente' (si se asignó mal).
        # El prompt dice: "Debe recibir un motivo y cambiar el estado a 'Rechazada' (o devolverla al estado anterior)."
        # Voy a permitir rechazar si está en_proceso (asignada a cuadrilla).
        if incidencia.estado not in ["en_proceso", "pendiente"]:
             raise serializers.ValidationError("No se puede rechazar una incidencia en este estado.")
        return attrs

    def update(self, instance, validated_data):
        motivo = validated_data.get("motivo_rechazo")
        instance.motivo_rechazo = motivo
        instance.estado = "rechazada"
        instance.save(update_fields=["estado", "motivo_rechazo", "actualizadoEl"])
        return instance


class FinalizarIncidenciaSerializer(serializers.ModelSerializer):
    """
    Solo se encarga de cambiar el estado y guardar el comentario.
    NO maneja archivos, porque esos ya se subieron con el endpoint 'subir_evidencia'.
    """
    comentario = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Incidencia
        fields = ["estado", "comentario"]
        read_only_fields = ["estado"]

    def validate(self, attrs):
        incidencia = self.instance
        if incidencia.estado != "en_proceso":
            raise serializers.ValidationError("Solo puedes finalizar incidencias que están 'en_proceso'.")
        return attrs

    def update(self, instance, validated_data):
        comentario = validated_data.pop("comentario", None)

        # Guardamos el comentario (usando motivo_rechazo o un campo nuevo si tu modelo lo tiene)
        # Asumiendo que usas 'motivo_rechazo' como campo genérico de texto de resolución:
        if comentario:
            instance.motivo_rechazo = comentario 

        instance.estado = "finalizada"
        instance.save(update_fields=["estado", "motivo_rechazo", "actualizadoEl"])
        return instance