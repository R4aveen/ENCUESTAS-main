from django import forms
from core.models import Incidencia, Departamento, JefeCuadrilla, Direccion, TipoIncidencia
from django.core.exceptions import ValidationError

class IncidenciaForm(forms.ModelForm):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('finalizada', 'Finalizada'),
        ('validada', 'Validada'),
        ('rechazada', 'Rechazada'),
    ]

    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    
    TRANSICIONES_PERMITIDAS = {
        'pendiente': ['en_proceso'],
        'en_proceso': ['finalizada'],
        'finalizada': ['validada', 'rechazada'],
        'validada': [],
        'rechazada': ['en_proceso']
    }
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        required=True,
        label="Estado"
    )

    prioridad = forms.ChoiceField(
        choices=PRIORIDAD_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        required=True,
        label="Prioridad"
    )

    class Meta:
        model = Incidencia
        fields = [
            "titulo", "descripcion", "estado", "prioridad", "fecha_cierre",
            "latitud", "longitud", "direccion", "departamento","nombre_vecino","correo_vecino","telefono_vecino",
            "cuadrilla", "tipo_incidencia",
        ]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Título"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "fecha_cierre": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "latitud": forms.NumberInput(attrs={"class": "form-control"}),
            "longitud": forms.NumberInput(attrs={"class": "form-control"}),
            "direccion": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "nombre_vecino": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del vecino"}),
            "correo_vecino": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Correo del vecino"}),
            "telefono_vecino": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono del vecino"}),
            "cuadrilla": forms.Select(attrs={"class": "form-select"}),
            "tipo_incidencia": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["direccion"].queryset = Direccion.objects.filter(estado=True)
        self.fields['departamento'].queryset = Departamento.objects.filter(estado=True)
        self.fields['tipo_incidencia'].queryset = TipoIncidencia.objects.all().order_by("nombre_problema")
        self.fields['titulo'].required = True
        self.fields['descripcion'].required = True
        self.fields['departamento'].required = True
        self.fields['correo_vecino'].required = True
        
        # La cuadrilla no es obligatoria inicialmente
        self.fields['cuadrilla'].required = False
        
        # Filtrar cuadrillas según el departamento
        if self.instance and self.instance.pk and self.instance.departamento:
            # Si la instancia ya existe y tiene departamento, filtrar por ese departamento
            cuadrillas_disponibles = JefeCuadrilla.objects.filter(
                departamento=self.instance.departamento
            )
            # Si la instancia tiene una cuadrilla asignada, incluirla aunque no esté en el filtro
            if self.instance.cuadrilla and self.instance.cuadrilla not in cuadrillas_disponibles:
                cuadrillas_disponibles = cuadrillas_disponibles | JefeCuadrilla.objects.filter(
                    pk=self.instance.cuadrilla.pk
            )
            self.fields['cuadrilla'].queryset = cuadrillas_disponibles
        else:
            # Para nuevas incidencias, mostrar todas las cuadrillas
            self.fields['cuadrilla'].queryset = JefeCuadrilla.objects.all()

        # Preseleccionar dirección según el departamento existente o dato enviado
        if self.instance and self.instance.pk and self.instance.departamento and self.instance.departamento.direccion:
            self.fields["direccion"].initial = self.instance.departamento.direccion
        elif self.data.get("direccion"):
            try:
                self.fields["direccion"].initial = Direccion.objects.get(pk=self.data.get("direccion"))
            except Direccion.DoesNotExist:
                pass

        # Filtrar departamentos por dirección seleccionada si existe
        direccion_id = self.data.get("direccion") or (self.instance.departamento.direccion.pk if self.instance and self.instance.departamento and self.instance.departamento.direccion else None)
        if direccion_id:
            try:
                self.fields['departamento'].queryset = Departamento.objects.filter(direccion_id=direccion_id, estado=True)
            except Exception:
                self.fields['departamento'].queryset = Departamento.objects.filter(estado=True)

        if not self.instance or not getattr(self.instance, 'pk', None):

            self.fields['estado'].initial = 'pendiente'
            self.fields['prioridad'].initial = 'media'

    def clean_titulo(self):
        titulo = self.cleaned_data.get("titulo", "").strip()
        if not titulo:
            raise ValidationError("El título de la incidencia es obligatorio.")
        if Incidencia.objects.filter(titulo__iexact=titulo).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe una incidencia con este título.")
        return titulo

    def clean_estado(self):
        nuevo_estado = self.cleaned_data.get("estado")
        if not nuevo_estado:
            return "pendiente"
            
        if not self.instance.pk:
            if nuevo_estado != 'pendiente':
                raise ValidationError("Una nueva incidencia debe estar en estado pendiente")
            return nuevo_estado
            
        estado_actual = self.instance.estado
        if nuevo_estado not in self.TRANSICIONES_PERMITIDAS.get(estado_actual, []):
            raise ValidationError(
                f"No se puede cambiar el estado de '{estado_actual}' a '{nuevo_estado}'. "
                f"Las transiciones permitidas son: {', '.join(self.TRANSICIONES_PERMITIDAS.get(estado_actual, []))}"
            )
        
        return nuevo_estado

    def clean_prioridad(self):
        prioridad = self.cleaned_data.get("prioridad")
        if not prioridad:
            return "media"
        return prioridad

    def clean(self):
        cleaned = super().clean()
        direccion = cleaned.get("direccion")
        departamento = cleaned.get("departamento")
        if direccion and departamento and departamento.direccion_id != direccion.id:
            raise ValidationError("El departamento seleccionado no pertenece a la dirección elegida.")
        return cleaned

    def save(self, commit=True):
        incidencia = super().save(commit=False)
        incidencia.titulo = incidencia.titulo.strip()
        # Sincronizar dirección con el departamento
        if incidencia.departamento and incidencia.departamento.direccion:
            incidencia.direccion = incidencia.departamento.direccion
        
        # Preservar la cuadrilla si no se cambió en el formulario
        if self.instance.pk and 'cuadrilla' not in self.changed_data:
            # Si la cuadrilla no cambió, mantener la original
            if self.instance.cuadrilla:
                incidencia.cuadrilla = self.instance.cuadrilla
        
        if commit:
            incidencia.save()
        return incidencia


class SubirEvidenciaForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo de evidencia",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*,application/pdf'
        }),
        help_text="Formatos permitidos: imágenes, videos, PDF. Tamaño máximo: 10MB"
    )
    
    nombre = forms.CharField(
        max_length=100,
        label="Nombre de la evidencia",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Foto del problema resuelto'
        })
    )
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño del archivo (10MB máximo)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError("El archivo no puede superar los 10MB")
            
            # Validar tipo de archivo
            tipo_permitido = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'video/mp4', 'video/mpeg', 'video/quicktime',
                'application/pdf'
            ]
            if archivo.content_type not in tipo_permitido:
                raise ValidationError("Tipo de archivo no permitido")
        
        return archivo
