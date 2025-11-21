from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from registration.models import Profile
from core.models import JefeCuadrilla, Departamento

class Command(BaseCommand):
    help = 'Asigna el perfil de usercuadri a su cuadrilla'

    def handle(self, *args, **options):
        try:
            # Buscar usuario
            usuario = User.objects.get(username='usercuadri')
            self.stdout.write(f"✅ Usuario encontrado: {usuario.username}")
            
            # Obtener perfil
            profile = usuario.profile
            self.stdout.write(f"✅ Perfil: {profile}")
            
            # Buscar cuadrilla "Cuadrilla de usercuadri"
            cuadrilla = JefeCuadrilla.objects.filter(nombre_cuadrilla__icontains='usercuadri').first()
            
            if not cuadrilla:
                # Si no existe, buscar cualquier cuadrilla
                cuadrilla = JefeCuadrilla.objects.first()
                
                if not cuadrilla:
                    # Crear cuadrilla si no existe ninguna
                    depto = Departamento.objects.first()
                    if not depto:
                        self.stdout.write(self.style.ERROR("❌ No hay departamentos. Crea uno primero."))
                        return
                    
                    cuadrilla = JefeCuadrilla.objects.create(
                        nombre_cuadrilla="Cuadrilla de usercuadri",
                        usuario=profile,
                        encargado=profile,
                        departamento=depto
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Cuadrilla creada: {cuadrilla.nombre_cuadrilla}"))
                else:
                    # Asignar a cuadrilla existente
                    cuadrilla.usuario = profile
                    cuadrilla.encargado = profile
                    cuadrilla.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Asignado a cuadrilla: {cuadrilla.nombre_cuadrilla}"))
            else:
                # Actualizar cuadrilla encontrada
                cuadrilla.usuario = profile
                cuadrilla.encargado = profile
                cuadrilla.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Cuadrilla actualizada: {cuadrilla.nombre_cuadrilla}"))
            
            self.stdout.write(self.style.SUCCESS("\n✅ PROCESO COMPLETADO"))
            self.stdout.write(f"Usuario: {profile}")
            self.stdout.write(f"Cuadrilla: {cuadrilla.nombre_cuadrilla}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Usuario 'usercuadri' no encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
