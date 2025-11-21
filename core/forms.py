from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from registration.models import Profile
from core.models import JefeCuadrilla, Departamento


# Los nombres deben coincidir EXACTO con los Group.name creados en DB
ROL_CHOICES = [
    ("Administrador", "Administrador"),
    ("Dirección", "Dirección"),
    ("Departamento", "Departamento"),
    ("Jefe de Cuadrilla", "Jefe de Cuadrilla"),
    ("Territorial", "Territorial"),
]


# ---------- Validadores utilitarios ----------

def validar_email_unico_ci(value: str, exclude_pk: int | None = None):
    qs = User.objects.filter(email__iexact=value)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(
            "Ya existe un usuario con este correo (no distingue mayúsculas/minúsculas)."
        )


def validar_username_unico_ci(value: str, exclude_pk: int | None = None):
    qs = User.objects.filter(username__iexact=value)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(
            "Ya existe un usuario con este nombre de usuario (no distingue mayúsculas/minúsculas)."
        )


# ---------- Creación ----------

class UsuarioCrearForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=True,
        min_length=8,
        help_text="Mínimo 8 caracteres.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=True,
    )
    telefono = forms.CharField(
        label="Teléfono",
        required=False,
        max_length=20,
        help_text="Opcional, formato libre corto."
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label="Rol (grupo)")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]
        widgets = {
            "is_active": forms.CheckboxInput(),
            "is_staff": forms.CheckboxInput(),
        }
        help_texts = {
            "is_active": "Si está desmarcado, el usuario no podrá iniciar sesión (bloqueado).",
            "is_staff": "Solo marca para dar acceso al admin de Django (no confundir con roles).",
        }

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        validar_username_unico_ci(username)
        return username

    def clean_first_name(self):
        return (self.cleaned_data.get("first_name") or "").strip()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("El correo es obligatorio.")
        validar_email_unico_ci(email)
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = user.username.strip()
        user.first_name = (user.first_name or "").strip()
        user.last_name = (user.last_name or "").strip()
        user.email = user.email.strip()

        if commit:
            user.save()
            user.groups.clear()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data["rol"])
            user.groups.add(group)

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.group = group
            profile.telefono = (self.cleaned_data.get("telefono") or "").strip()
            profile.save()

        # crear automáticamente JefeCuadrilla si el rol es "Jefe de Cuadrilla"
            if group.name == "Jefe de Cuadrilla":
            # Tomamos un departamento por defecto (puede ser el primero)
                depto = Departamento.objects.first()

                JefeCuadrilla.objects.get_or_create(
                    usuario=profile,
                    defaults={
                        "nombre_cuadrilla": f"Cuadrilla de {user.username}",
                        "encargado": profile,
                        "departamento": depto,
                    },
                )
        return user

# ---------- Edición ----------

class UsuarioEditarForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        min_length=8,
        help_text="Déjalo en blanco si no deseas cambiarla.",
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )
    telefono = forms.CharField(
        label="Teléfono",
        required=False,
        max_length=20,
        help_text="Opcional, formato libre corto."
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label="Rol (grupo)")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]
        help_texts = {
            "is_active": "Si está desmarcado, el usuario no podrá iniciar sesión (bloqueado).",
            "is_staff": "Solo marca para dar acceso al admin de Django (no confundir con roles).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        groups = list(self.instance.groups.values_list("name", flat=True))
        if groups:
            self.fields["rol"].initial = groups[0]
        if hasattr(self.instance, "profile"):
            self.fields["telefono"].initial = self.instance.profile.telefono

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        validar_username_unico_ci(username, exclude_pk=self.instance.pk)
        return username

    def clean_first_name(self):
        return (self.cleaned_data.get("first_name") or "").strip()

    def clean_last_name(self):
        return (self.cleaned_data.get("last_name") or "").strip()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("El correo es obligatorio.")
        validar_email_unico_ci(email, exclude_pk=self.instance.pk)
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
        # trims
        user.username = user.username.strip()
        user.first_name = (user.first_name or "").strip()
        user.last_name = (user.last_name or "").strip()
        user.email = user.email.strip()

        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)

        if commit:
            user.save()
            # rol
            user.groups.clear()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data["rol"])
            user.groups.add(group)

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.telefono = (self.cleaned_data.get("telefono") or "").strip()
            profile.group = group
            profile.save()
        return user


# ---------- Confirmación Activar/Desactivar ----------

class UsuarioToggleActivoForm(forms.Form):
    confirmar = forms.BooleanField(
        required=True,
        label="Confirmo el cambio de estado",
        help_text="Esta acción cambiará la disponibilidad del usuario para iniciar sesión.",
    )

    def next_state_label(self, user: User) -> str:
        return "Desactivar" if user.is_active else "Activar"
