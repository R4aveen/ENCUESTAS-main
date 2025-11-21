from django.core.management.base import BaseCommand
from core.models import Incidencia, JefeCuadrilla

class Command(BaseCommand):
    help = 'Asigna cuadrilla a incidencias y las pone en proceso'

    def handle(self, *args, **options):
        # Buscar cuadrilla
        cuadrilla = JefeCuadrilla.objects.filter(nombre_cuadrilla__icontains='usercuadri').first()
        
        if not cuadrilla:
            cuadrilla = JefeCuadrilla.objects.first()
        
        if not cuadrilla:
            self.stdout.write(self.style.ERROR("❌ No hay cuadrillas en el sistema"))
            return
        
        self.stdout.write(f"✅ Usando cuadrilla: {cuadrilla.nombre_cuadrilla}")
        
        # Asignar a incidencias sin cuadrilla
        incidencias_sin_cuadrilla = Incidencia.objects.filter(cuadrilla__isnull=True)
        count = 0
        for inc in incidencias_sin_cuadrilla:
            inc.cuadrilla = cuadrilla
            inc.save()
            count += 1
            self.stdout.write(f"  ✅ #{inc.id} - {inc.titulo} → asignada")
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ {count} incidencias asignadas"))
        
        # Cambiar pendientes a en_proceso
        pendientes = Incidencia.objects.filter(cuadrilla=cuadrilla, estado='pendiente')
        count2 = 0
        for inc in pendientes:
            inc.estado = 'en_proceso'
            inc.save()
            count2 += 1
            self.stdout.write(f"  ✅ #{inc.id} → en_proceso")
        
        if count2 > 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ {count2} incidencias cambiadas a 'en_proceso'"))
        
        # Resumen
        total = Incidencia.objects.filter(cuadrilla=cuadrilla, estado='en_proceso').count()
        self.stdout.write(self.style.SUCCESS(f"\n✅ TOTAL: {total} incidencias listas para subir evidencia"))
