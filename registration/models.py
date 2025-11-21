from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=1) 
    token_app_session = models.CharField(max_length = 240,null=True, blank=True, default='')
    first_session = models.CharField(max_length = 240,null=True, blank=True, default='Si')
    telefono = models.CharField(max_length=20, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" + (f" ({self.cargo})" if self.cargo else "")

# crear un Profile automáticamente
@receiver(post_save, sender=User)
def crear_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            grupo, _ = Group.objects.get_or_create(name="Administrador")
        else:
            grupo, _ = Group.objects.get_or_create(name="Usuario")
        Profile.objects.create(user=instance, group=grupo)
