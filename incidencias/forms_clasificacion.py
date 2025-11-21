from django import forms
from core.models import  TipoIncidencia


class TipoIncidenciaForm(forms.ModelForm):
    class Meta:
        model = TipoIncidencia
        fields = ['nombre_problema', 'descripcion', 'tipo_gravedad']
        widgets = {
            'nombre_problema': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_gravedad': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
