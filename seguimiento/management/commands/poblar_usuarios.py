from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from seguimiento.models import (
    PerfilUsuario,
    Coordinador,
    Asesor,
    Alumno,
    ConfiguracionUsuario,
    TelefonoUsuario
)

class Command(BaseCommand):
    help = 'Puebla la base de datos con 5 coordinadores, 25 docentes y 40 alumnos de prueba'

    def handle(self, *args, **options):
        password_comun = '2465'

        nombres_hombres = ['Juan', 'Carlos', 'Luis', 'Pedro', 'Miguel', 'Jorge', 'Fernando', 'Alejandro', 'Daniel', 'Ricardo']
        nombres_mujeres = ['Maria', 'Ana', 'Laura', 'Sofia', 'Diana', 'Patricia', 'Carmen', 'Elena', 'Gabriela', 'Andrea']
        apellidos = ['Gonzalez', 'Rodriguez', 'Hernandez', 'Lopez', 'Martinez', 'Perez', 'Sanchez', 'Ramirez', 'Torres', 'Flores', 'Vazquez', 'Morales', 'Reyes', 'Jimenez', 'Castro']

        self.stdout.write(self.style.WARNING("--- Iniciando sembrado masivo de usuarios de prueba ---"))

        # 1. COORDINADORES (5)
        for i in range(1, 6):
            username = f"coord{i}"
            email = f"coord{i}@buap.mx"
            p_nom = nombres_hombres[(i - 1) % len(nombres_hombres)]
            ap_pat = apellidos[(i - 1) % len(apellidos)]
            ap_mat = apellidos[(i + 2) % len(apellidos)]

            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password(password_comun)
            user.first_name = p_nom
            user.last_name = ap_pat
            user.is_active = True
            user.save()

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': p_nom,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'tipo_usuario': 'COORDINADOR',
                    'cuenta_activa': True
                }
            )
            perfil.tipo_usuario = 'COORDINADOR'
            perfil.cuenta_activa = True
            perfil.save()

            Coordinador.objects.get_or_create(
                perfil=perfil,
                defaults={
                    'cubiculo_oficina': f"Edificio FCC 1 - Cubículo {100 + i}",
                    'telefono_oficina': f"2222295500 Ext 720{i}"
                }
            )
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)

        self.stdout.write(self.style.SUCCESS("[OK] 5 Coordinadores creados."))

        # 2. ASESORES / DOCENTES (25)
        grados = ['Dr.', 'Dra.', 'M.C.', 'Mtro.', 'Lic.']
        for i in range(1, 26):
            username = f"asesor{i}"
            email = f"asesor{i}@buap.mx"
            es_mujer = (i % 2 == 0)
            p_nom = nombres_mujeres[i % len(nombres_mujeres)] if es_mujer else nombres_hombres[i % len(nombres_hombres)]
            ap_pat = apellidos[(i * 2) % len(apellidos)]
            ap_mat = apellidos[(i * 3) % len(apellidos)]
            grado = grados[i % len(grados)]

            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password(password_comun)
            user.first_name = p_nom
            user.last_name = ap_pat
            user.is_active = True
            user.save()

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': p_nom,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'tipo_usuario': 'ASESOR',
                    'cuenta_activa': True
                }
            )
            perfil.tipo_usuario = 'ASESOR'
            perfil.cuenta_activa = True
            perfil.save()

            Asesor.objects.get_or_create(
                perfil=perfil,
                defaults={
                    'numero_empleado': f"100{i:05d}",
                    'grado_academico': grado
                }
            )
            TelefonoUsuario.objects.get_or_create(
                perfil=perfil,
                defaults={'numero_telefono': f"2221{i:06d}"}
            )
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)

        self.stdout.write(self.style.SUCCESS("[OK] 25 Asesores creados."))

        # 3. ALUMNOS (40)
        for i in range(1, 41):
            username = f"alumno{i}"
            email = f"alumno{i}@buap.mx"
            es_mujer = (i % 2 != 0)
            p_nom = nombres_mujeres[i % len(nombres_mujeres)] if es_mujer else nombres_hombres[i % len(nombres_hombres)]
            ap_pat = apellidos[(i + 4) % len(apellidos)]
            ap_mat = apellidos[(i + 7) % len(apellidos)]
            matricula = f"2026{i:05d}"

            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password(password_comun)
            user.first_name = p_nom
            user.last_name = ap_pat
            user.is_active = True
            user.save()

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': p_nom,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'tipo_usuario': 'ALUMNO',
                    'cuenta_activa': True
                }
            )
            perfil.tipo_usuario = 'ALUMNO'
            perfil.cuenta_activa = True
            perfil.save()

            Alumno.objects.get_or_create(
                perfil=perfil,
                defaults={'matricula': matricula}
            )
            TelefonoUsuario.objects.get_or_create(
                perfil=perfil,
                defaults={'numero_telefono': f"2228{i:06d}"}
            )
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)

        self.stdout.write(self.style.SUCCESS("[OK] 40 Alumnos creados."))
        self.stdout.write(self.style.SUCCESS("\n¡Base de datos lista! Contraseña de todos: Demo2026!"))