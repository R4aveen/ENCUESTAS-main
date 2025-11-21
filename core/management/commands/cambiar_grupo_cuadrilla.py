from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Cambia el grupo del usuario usercuadri a Cuadrilla'

    def handle(self, *args, **options):
        try:
            usuario = User.objects.get(username='usercuadri')
            self.stdout.write(f"\n✅ Usuario encontrado: {usuario.username}")
            self.stdout.write(f"Grupos actuales: {[g.name for g in usuario.groups.all()]}")
            
            # Obtener o crear grupo Cuadrilla
            grupo_cuadrilla, created = Group.objects.get_or_create(name='Cuadrilla')
            if created:
                self.stdout.write(self.style.SUCCESS("✅ Grupo 'Cuadrilla' creado"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Grupo 'Cuadrilla' ya existe"))
            
            # Remover de otros grupos
            usuario.groups.clear()
            self.stdout.write("🗑️ Grupos anteriores removidos")
            
            # Agregar al grupo Cuadrilla
            usuario.groups.add(grupo_cuadrilla)
            self.stdout.write(self.style.SUCCESS("✅ Usuario agregado al grupo 'Cuadrilla'"))
            
            # Verificar
            self.stdout.write(f"\nGrupos actuales: {[g.name for g in usuario.groups.all()]}")
            self.stdout.write(self.style.SUCCESS("\n✅ CAMBIO EXITOSO - Ahora 'usercuadri' está en el grupo 'Cuadrilla'\n"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("\n❌ Usuario 'usercuadri' no encontrado"))
            self.stdout.write("\nUsuarios disponibles:")
            for u in User.objects.all():
                self.stdout.write(f"  - {u.username}")
