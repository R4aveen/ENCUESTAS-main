# registration/signals.py
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile 

@receiver(post_save, sender=User)
def ensure_profile_on_create(sender, instance, created, **kwargs):
    """
    Al crear un User, garantizamos que exista su Profile.
    Si el usuario ya tiene un grupo asignado, lo reflejamos en el Profile.
    """
    if created:
        profile, _ = Profile.objects.get_or_create(user=instance)
        first_group = instance.groups.first()
        if first_group:
            profile.group = first_group
            profile.save()

@receiver(m2m_changed, sender=User.groups.through)
def sync_profile_when_groups_change(sender, instance, action, **kwargs):
    """
    Si cambian los grupos del User (p.ej. al editarlo en el panel),
    sincronizamos el Profile.group con el primer grupo asignado.
    """
    if action in ("post_add", "post_remove", "post_clear"):
        profile, _ = Profile.objects.get_or_create(user=instance)
        first_group = instance.groups.first()
        profile.group = first_group 
        profile.save()
