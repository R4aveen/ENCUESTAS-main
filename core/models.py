from django.db import models
from registration.models import Profile

class Perfil(models.Model):
    rol = models.CharField(max_length=50)

    def __str__(self):
        return self.rol

class Direccion(models.Model):
    nombre_direccion = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    creadoEl = models.DateTimeField(auto_now_add=True)
    actualizadoEl = models.DateTimeField(auto_now=True)
    encargado = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name='direcciones_encargadas'
    )

    def __str__(self):
        return self.nombre_direccion


class Departamento(models.Model):
    nombre_departamento = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    creadoEl = models.DateTimeField(auto_now_add=True)
    actualizadoEl = models.DateTimeField(auto_now=True)
    encargado = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name='departamentos_encargados'
    )
    direccion = models.ForeignKey(Direccion, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.nombre_departamento


class Encuesta(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    ubicacion = models.CharField(max_length=200)
    estado = models.BooleanField(default=True)
    creadoEl = models.DateTimeField(auto_now_add=True)
    actualizadoEl = models.DateTimeField(auto_now=True)
    prioridad = models.CharField(max_length=50)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    # Multimedia
    imagen_url = models.URLField(null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    audio_url = models.URLField(null=True, blank=True)
    # Datos del vecino
    nombre_vecino = models.CharField(max_length=100, null=True, blank=True)
    celular_vecino = models.CharField(max_length=20, null=True, blank=True)
    email_vecino = models.EmailField(null=True, blank=True)
    # Clasificación
    tipo_incidencia = models.ForeignKey("TipoIncidencia", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.titulo


class PreguntaEncuesta(models.Model):
    texto_pregunta = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=50)
    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE)

    def __str__(self):
        return self.texto_pregunta


class RespuestaEncuesta(models.Model):
    texto_respuesta = models.TextField()
    tipo = models.CharField(max_length=50)
    pregunta = models.ForeignKey(PreguntaEncuesta, on_delete=models.CASCADE)

    def __str__(self):
        return self.texto_respuesta[:50]


class Multimedia(models.Model):
    nombre = models.CharField(max_length=100)
    url = models.URLField()
    tipo = models.CharField(max_length=50)
    formato = models.CharField(max_length=50)
    creadoEl = models.DateTimeField(auto_now_add=True)
    incidencia = models.ForeignKey("Incidencia", on_delete=models.CASCADE, related_name="multimedias")

    def __str__(self):
        return self.nombre


class TipoIncidencia(models.Model):
    nombre_problema = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo_gravedad = models.CharField(
        max_length=1,
        choices=[('A', 'Alta'), ('M', 'Media'), ('B', 'Baja')]
    )

    def __str__(self):
        return self.nombre_problema


class JefeCuadrilla(models.Model):
    nombre_cuadrilla = models.CharField(max_length=100)
    encargado = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name='cuadrillas_encargadas'
    )
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='cuadrillas'
    )

    def __str__(self):
        return self.nombre_cuadrilla


class Incidencia(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50)
    prioridad = models.CharField(max_length=50)
    creadoEl = models.DateTimeField(auto_now_add=True)
    actualizadoEl = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    latitud = models.FloatField()
    longitud = models.FloatField()
    nombre_vecino = models.CharField(max_length=100)
    correo_vecino = models.EmailField()
    telefono_vecino = models.CharField(max_length=20)
    motivo_rechazo = models.TextField(null=True, blank=True)

    direccion = models.ForeignKey(Direccion, on_delete=models.SET_NULL, null=True, blank=True)
    cuadrilla = models.ForeignKey(JefeCuadrilla, on_delete=models.SET_NULL, null=True)
    respuesta = models.ForeignKey(RespuestaEncuesta, on_delete=models.SET_NULL, null=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True)
    encuesta = models.ForeignKey(Encuesta, on_delete=models.SET_NULL, null=True)
    tipo_incidencia = models.ForeignKey(TipoIncidencia, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo


class Territorial(models.Model):
    incidencia = models.ForeignKey(
        Incidencia, on_delete=models.CASCADE, related_name='territoriales'
    )
    usuario = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Territorial de {self.usuario}"


class Derivacion(models.Model):
    fecha_derivacion = models.DateTimeField()
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE)
    jefe_cuadrilla = models.ForeignKey(JefeCuadrilla, on_delete=models.CASCADE)

    def __str__(self):
        return f"Derivación de {self.incidencia}"
