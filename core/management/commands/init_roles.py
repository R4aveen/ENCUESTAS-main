from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

ROLES = ["Administrador", "dirección", "depto", "jefe_cuadrilla", "territorial"]

class Command(BaseCommand):
    help = "Crea/asegura los grupos base del sistema."
    def handle(self, *args, **kwargs):
        for name in ROLES:
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Grupos creados/asegurados."))
