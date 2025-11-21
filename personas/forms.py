from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from registration.models import Profile

# Definimos los roles disponibles
ROL_CHOICES = [
    ("Administrador", "Administrador"),
    ("Dirección", "Dirección"),
    ("Departamento", "Departamento"),
    ("Jefe de Cuadrilla", "Jefe de Cuadrilla"),
    ("Territorial", "Territorial"),
]

def validar_email_unico_ci(value, usuario=None):
    qs = User.objects.filter(email__iexact=value)
    if usuario:
        qs = qs.exclude(pk=usuario.pk)
    if qs.exists():
        raise ValidationError("Ya existe un usuario con este correo (no distingue mayúsculas/minúsculas).")

class UsuarioCrearForm(forms.ModelForm):
    cargo = forms.CharField(max_length=100, required=False, label="Cargo")
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono")
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=True,
        min_length=8,
        help_text="Mínimo 8 caracteres."
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=True
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label="Rol (grupo)")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]
        widgets = {
            "is_active": forms.CheckboxInput(),
            "is_staff": forms.CheckboxInput(),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise ValidationError("El correo es obligatorio.")
        validar_email_unico_ci(email)
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

            # Asignar rol (grupo)
            user.groups.clear()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data["rol"])
            user.groups.add(group)

            # Crear o actualizar profile
            cargo = self.cleaned_data.get("cargo", "").strip()
            telefono = self.cleaned_data.get("telefono", "").strip()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.cargo = cargo
            profile.telefono = telefono
            profile.save()

        return user

class UsuarioEditarForm(forms.ModelForm):
    cargo = forms.CharField(max_length=100, required=False, label="Cargo")
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono")
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        min_length=8,
        help_text="Déjalo en blanco si no deseas cambiarla."
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label="Rol (grupo)")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        groups = list(self.instance.groups.values_list("name", flat=True))
        if groups:
            self.fields["rol"].initial = groups[0]
        if hasattr(self.instance, "profile"):
            self.fields["cargo"].initial = self.instance.profile.cargo
            self.fields["telefono"].initial = self.instance.profile.telefono

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise ValidationError("El correo es obligatorio.")
        validar_email_unico_ci(email, usuario=self.instance)
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 or p2:
            if not p1 or not p2:
                self.add_error("password2", "Debes completar ambas contraseñas si vas a cambiarla.")
            elif p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)

        if commit:
            user.save()

            # Actualizar rol
            user.groups.clear()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data["rol"])
            user.groups.add(group)

            # Actualizar cargo
            cargo = self.cleaned_data.get("cargo", "").strip()
            telefono = self.cleaned_data.get("telefono", "").strip()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.cargo = cargo
            profile.telefono = telefono
            profile.save()

        return user
