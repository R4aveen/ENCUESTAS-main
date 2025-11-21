from django import forms
from core.models import Incidencia, JefeCuadrilla, Encuesta, Departamento
from registration.models import Profile

class RechazarIncidenciaForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo de rechazo",
        widget=forms.Textarea(attrs={"rows": 3, "cols": 40}),
        max_length=500,
        required=True,
    )

class ReasignarIncidenciaForm(forms.ModelForm):
    cuadrilla = forms.ModelChoiceField(
        queryset=JefeCuadrilla.objects.all(),
        required=True,
        label="Cuadrilla",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Incidencia
        fields = ['departamento', 'cuadrilla']
        widgets = {
            'departamento': forms.Select(attrs={'class': 'form-control'}),
        }


class EncuestaForm(forms.ModelForm):
    """
    Formulario para crear/editar encuestas.
    """
    PRIORIDAD_CHOICES = [
        ('Alta', 'Alta'),
        ('Normal', 'Normal'),
        ('Baja', 'Baja'),
    ]

    prioridad = forms.ChoiceField(
        choices=PRIORIDAD_CHOICES,
        required=True,
        label="Prioridad",
        widget=forms.Select()
    )

    class Meta:
        model = Encuesta
        fields = [
            'titulo', 'descripcion', 'ubicacion', 'prioridad', 'departamento', 'estado',
            'imagen_url', 'video_url', 'audio_url',
            'nombre_vecino', 'celular_vecino', 'email_vecino',
            'tipo_incidencia'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Título de la encuesta',
                'maxlength': '100'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descripción detallada de la encuesta'
            }),
            'ubicacion': forms.TextInput(attrs={
                'placeholder': 'Ubicación de la encuesta',
                'maxlength': '200'
            }),
            'departamento': forms.Select(),
            'estado': forms.CheckboxInput(),
            'imagen_url': forms.URLInput(attrs={'placeholder': 'URL de imagen'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'URL de video'}),
            'audio_url': forms.URLInput(attrs={'placeholder': 'URL de audio'}),
            'nombre_vecino': forms.TextInput(attrs={'placeholder': 'Nombre del vecino'}),
            'celular_vecino': forms.TextInput(attrs={'placeholder': 'Celular del vecino'}),
            'email_vecino': forms.EmailInput(attrs={'placeholder': 'Email del vecino'}),
            'tipo_incidencia': forms.Select(),
        }
        labels = {
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'ubicacion': 'Ubicación',
            'prioridad': 'Prioridad',
            'departamento': 'Departamento',
            'estado': 'Activa',
            'imagen_url': 'Imagen',
            'video_url': 'Video',
            'audio_url': 'Audio',
            'nombre_vecino': 'Nombre vecino',
            'celular_vecino': 'Celular vecino',
            'email_vecino': 'Email vecino',
            'tipo_incidencia': 'Tipo de incidencia',
        }
        help_texts = {
            'estado': 'Marcar si la encuesta está activa',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo departamentos activos
        self.fields['departamento'].queryset = Departamento.objects.filter(estado=True)
