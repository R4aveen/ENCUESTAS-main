from django import forms
from django.core.exceptions import ValidationError
from core.models import Direccion, Departamento, JefeCuadrilla
from registration.models import Profile
from django.contrib.auth.models import Group

# ==========================
# ======== DIRECCIÓN =======
# ==========================

class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = ["nombre_direccion", "estado", "encargado"]
        widgets = {
            "nombre_direccion": forms.TextInput(attrs={"placeholder": "Nombre de la dirección"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "encargado": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo perfiles cuyo usuario pertenece al grupo "Dirección" y está activo
        self.fields['encargado'].queryset = Profile.objects.filter(
            user__groups__name__iexact="Dirección",
            user__is_active=True
        )

    def clean_nombre_direccion(self):
        nombre = self.cleaned_data.get("nombre_direccion", "").strip()
        if not nombre:
            raise ValidationError("El nombre de la dirección es obligatorio.")
        if Direccion.objects.filter(nombre_direccion__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe una dirección con ese nombre.")
        return nombre

# ==========================
# ======= DEPARTAMENTO =====
# ==========================

class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ["nombre_departamento", "estado", "encargado", "direccion"]
        widgets = {
            "nombre_departamento": forms.TextInput(attrs={"placeholder": "Nombre del departamento"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "encargado": forms.Select(attrs={"class": "form-select"}),
            "direccion": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo perfiles cuyo usuario pertenece al grupo "Departamento" y está activo
        self.fields['encargado'].queryset = Profile.objects.filter(
            user__groups__name__iexact="Departamento",
            user__is_active=True
        )
        # Mostrar solo direcciones activas
        self.fields['direccion'].queryset = Direccion.objects.filter(estado=True)

    def clean_nombre_departamento(self):
        nombre = self.cleaned_data.get("nombre_departamento", "").strip()
        if not nombre:
            raise ValidationError("El nombre del departamento es obligatorio.")
        if Departamento.objects.filter(nombre_departamento__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un departamento con ese nombre.")
        return nombre

# ==========================
# ====== CUADRILLA =========
# ==========================

class JefeCuadrillaForm(forms.ModelForm):
    class Meta:
        model = JefeCuadrilla
        fields = ["nombre_cuadrilla", "usuario", "encargado", "departamento"]
        widgets = {
            "nombre_cuadrilla": forms.TextInput(attrs={
                "placeholder": "Nombre de la cuadrilla",
                "class": "form-control"
            }),
            "usuario": forms.Select(attrs={"class": "form-select"}),
            "encargado": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            'departamento': '⚠️ IMPORTANTE: Selecciona el departamento al que pertenece esta cuadrilla.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo perfiles de usuarios del grupo "Jefe de Cuadrilla" o "Cuadrilla"
        cuadrilla_profiles = Profile.objects.filter(
            user__groups__name__in=["Jefe de Cuadrilla", "Cuadrilla"],
            user__is_active=True
        )
        self.fields['usuario'].queryset = cuadrilla_profiles
        self.fields['encargado'].queryset = cuadrilla_profiles
        
        # Mostrar solo departamentos activos
        self.fields['departamento'].queryset = Departamento.objects.filter(estado=True)
        
        # Hacer departamento requerido
        self.fields['departamento'].required = True

    def clean_nombre_cuadrilla(self):
        nombre = self.cleaned_data.get("nombre_cuadrilla", "").strip()
        if not nombre:
            raise ValidationError("El nombre de la cuadrilla es obligatorio.")
        if JefeCuadrilla.objects.filter(nombre_cuadrilla__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe una cuadrilla con ese nombre.")
        return nombre

