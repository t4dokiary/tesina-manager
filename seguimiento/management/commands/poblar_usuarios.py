import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone

from seguimiento.models import (
    PerfilUsuario,
    Coordinador,
    Asesor,
    Alumno,
    ConfiguracionUsuario,
    TelefonoUsuario,
    Convocatoria,
    ProyectoTesis,
    EntregableVersion,
    MensajeEntrega,
    MinutaAsesoria,
    CompromisoAcuerdo,
    MaterialApoyoMinuta,
    AlertaRezago,
)


class Command(BaseCommand):
    help = 'Puebla la BD profesionalmente probando CU01 a CU04 con inactividad escalonada (0 a 45 dias)'

    def handle(self, *args, **options):
        password_comun = '2465'
        hoy = date.today()

        nombres_hombres = ['Juan', 'Carlos', 'Luis', 'Pedro', 'Miguel', 'Jorge', 'Fernando', 'Alejandro', 'Daniel', 'Ricardo']
        nombres_mujeres = ['Maria', 'Ana', 'Laura', 'Sofia', 'Diana', 'Patricia', 'Carmen', 'Elena', 'Gabriela', 'Andrea']
        apellidos = ['Gonzalez', 'Rodriguez', 'Hernandez', 'Lopez', 'Martinez', 'Perez', 'Sanchez', 'Ramirez', 'Torres', 'Flores', 'Vazquez', 'Morales', 'Reyes', 'Jimenez', 'Castro']

        lineas_investigacion = [
            'Sistemas Distribuidos y Aplicaciones Web',
            'Inteligencia Artificial y Aprendizaje Automático',
            'Ciberseguridad y Redes Confiables',
            'Interacción Humano-Computadora y Accesibilidad',
            'Ciencia de Datos y Análisis Predictivo'
        ]

        temas_tesis = [
            'Plataforma Distribuida para el Seguimiento Académico en Posgrados',
            'Detección Temprana de Intrusiones Mediante Algoritmos de Machine Learning',
            'Optimización de Tráfico Vehicular Urbano Usando Redes de Sensores IoT',
            'Framework Ligero para Autenticación Biométrica en Entornos Móviles',
            'Análisis Predictivo del Desempeño Escolar Mediante Minería de Datos',
            'Sistema de Respaldo Inmutable Basado en Criptografía Asimétrica',
            'Diseño de Interfaces Accesibles para Estudiantes con Discapacidad Sensorial',
            'Monitoreo y Alerta Temprana en Entornos Hospitalarios Mediante IoT'
        ]

        pdf_dummy = ContentFile(b"%PDF-1.4\n%Muestra ficticia para pruebas CU02\n%%EOF")

        self.stdout.write(self.style.WARNING("\n=== INICIANDO SEMBRADO COMPLETO Y PROFESIONAL ==="))

        # ==============================================================================
        # 1. COORDINADORES (5)
        # ==============================================================================
        coordinadores_perfiles = []
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
            user.is_staff = True
            user.is_active = True
            user.save()

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': p_nom,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'tipo_usuario': 'COORDINADOR',
                    'estado_registro': 'ACTIVO',
                    'cuenta_activa': True
                }
            )
            perfil.tipo_usuario = 'COORDINADOR'
            perfil.estado_registro = 'ACTIVO'
            perfil.cuenta_activa = True
            perfil.save()

            Coordinador.objects.get_or_create(
                perfil=perfil,
                defaults={
                    'cubiculo_oficina': f"Edificio FCC 1 - Cubículo {100 + i}",
                    'telefono_oficina': f"2222295500 Ext 720{i}"
                }
            )
            TelefonoUsuario.objects.get_or_create(perfil=perfil, numero_telefono=f"222229550{i}")
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)
            coordinadores_perfiles.append(perfil)

        self.stdout.write(self.style.SUCCESS("[OK] 5 Coordinadores registrados."))

        # ==============================================================================
        # 2. CONVOCATORIA INSTITUCIONAL
        # ==============================================================================
        convocatoria, _ = Convocatoria.objects.get_or_create(
            periodo='2026-S2',
            defaults={
                'titulo': 'Convocatoria de Titulación Posgrado Otoño 2026',
                'descripcion': 'Periodo semestral oficial para registro de protocolos y borradores de titulación.',
                'fecha_inicio': hoy - timedelta(days=90),
                'fecha_limite_protocolo': hoy + timedelta(days=20),
                'fecha_cierre': hoy + timedelta(days=90),
                'activa': True,
                'estado': 'ABIERTA',
                'creada_por': coordinadores_perfiles[0]
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Convocatoria oficial activa vinculada."))

        # ==============================================================================
        # 3. ASESORES / DOCENTES (25)
        # ==============================================================================
        grados = ['Dr.', 'Dra.', 'M.C.', 'Mtro.', 'Lic.']
        asesores_perfiles = []

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

            # Los primeros 22 activos, los últimos 3 en estado PENDIENTE para probar el panel del Coordinador
            estado_reg = 'ACTIVO' if i <= 22 else 'PENDIENTE'

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': p_nom,
                    'apellido_paterno': ap_pat,
                    'apellido_materno': ap_mat,
                    'tipo_usuario': 'ASESOR',
                    'estado_registro': estado_reg,
                    'cuenta_activa': (estado_reg == 'ACTIVO')
                }
            )
            perfil.tipo_usuario = 'ASESOR'
            perfil.estado_registro = estado_reg
            perfil.cuenta_activa = (estado_reg == 'ACTIVO')
            perfil.save()

            Asesor.objects.get_or_create(
                perfil=perfil,
                defaults={
                    'numero_empleado': f"100{i:05d}",
                    'grado_academico': grado,
                    'area_especialidad': lineas_investigacion[i % len(lineas_investigacion)]
                }
            )
            TelefonoUsuario.objects.get_or_create(perfil=perfil, defaults={'numero_telefono': f"2221{i:06d}"})
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)
            
            if estado_reg == 'ACTIVO':
                asesores_perfiles.append(perfil)

        self.stdout.write(self.style.SUCCESS("[OK] 25 Asesores registrados (22 activos y 3 pendientes de validación)."))

        # ==============================================================================
        # 4. ALUMNOS (40) CON ESCALONAMIENTO EXACTO DE 0 A 45 DÍAS DE INACTIVIDAD
        # ==============================================================================
        # Generamos una distribución de 40 valores de inactividad de 0 hasta 45 días
        # Primeros 25: Activos (0 a 25 días)
        # Siguientes 5: Umbral (28 a 30 días)
        # Últimos 10: En rezago severo (31 a 45 días)
        dias_distribucion = [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25,
            28, 29, 29, 30, 30,
            31, 32, 34, 36, 38, 40, 41, 43, 44, 45
        ]

        alumnos_creados = 0
        proyectos_en_rezago = 0

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
                    'estado_registro': 'ACTIVO',
                    'cuenta_activa': True
                }
            )
            perfil.tipo_usuario = 'ALUMNO'
            perfil.save()

            Alumno.objects.get_or_create(perfil=perfil, defaults={'matricula': matricula})
            TelefonoUsuario.objects.get_or_create(perfil=perfil, defaults={'numero_telefono': f"2228{i:06d}"})
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)

            # Asignación escalonada de inactividad
            dias_inactivo = dias_distribucion[i - 1]
            fecha_avance = hoy - timedelta(days=dias_inactivo)

            asesor_asignado = asesores_perfiles[(i - 1) % len(asesores_perfiles)]
            coordinador_asignado = coordinadores_perfiles[(i - 1) % len(coordinadores_perfiles)]

            # Estados del proyecto según el alumno
            if i == 1:
                estado_proy = 'PENDIENTE'  # Para probar aprobación por el Coordinador
            elif i == 2:
                estado_proy = 'RECHAZADO'
            elif i == 40:
                estado_proy = 'CONCLUIDO'
            else:
                estado_proy = 'APROBADO'

            proyecto, _ = ProyectoTesis.objects.get_or_create(
                alumno=perfil,
                defaults={
                    'asesor': asesor_asignado,
                    'coordinador': coordinador_asignado,
                    'convocatoria': convocatoria,
                    'titulo_tesis': f"{temas_tesis[(i - 1) % len(temas_tesis)]} (Caso de Estudio #{i})",
                    'linea_investigacion': lineas_investigacion[(i - 1) % len(lineas_investigacion)],
                    'estado_proyecto': estado_proy,
                    'fecha_ultimo_avance': fecha_avance,
                    'observaciones_coordinador': 'Protocolo revisado y validado en sesión colegiada.' if estado_proy == 'APROBADO' else None,
                    'fecha_dictamen_coordinador': hoy - timedelta(days=60) if estado_proy == 'APROBADO' else None
                }
            )

            # Para proyectos ya existentes, aseguramos la fecha de prueba
            proyecto.fecha_ultimo_avance = fecha_avance
            proyecto.estado_proyecto = estado_proy
            proyecto.save(update_fields=['fecha_ultimo_avance', 'estado_proyecto'])

            # ==============================================================================
            # CU02: ENTREGABLES Y VERSIONES PDF
            # ==============================================================================
            if estado_proy in ['APROBADO', 'CONCLUIDO']:
                v1, _ = EntregableVersion.objects.get_or_create(
                    proyecto=proyecto,
                    numero_version=1,
                    defaults={
                        'ruta_archivo_pdf': 'entregables_tesis/muestra_v1.pdf',
                        'comentario_alumno': f'Borrador inicial de marco conceptual entregado hace {dias_inactivo + 5} días.',
                        'retroalimentacion_asesor': 'Estructura aceptada. Se requiere mayor profundidad en la formulación del problema.'
                    }
                )
                MensajeEntrega.objects.get_or_create(
                    entregable=v1,
                    emisor=asesor_asignado,
                    mensaje='Favor de revisar las anotaciones al pie de página antes de redactar el siguiente capítulo.'
                )

                # ==============================================================================
                # CU03: MINUTAS Y COMPROMISOS DE ASESORÍA
                # ==============================================================================
                minuta, _ = MinutaAsesoria.objects.get_or_create(
                    proyecto=proyecto,
                    fecha_reunion=fecha_avance,
                    defaults={
                        'modalidad': 'PRESENCIAL' if i % 2 == 0 else 'VIRTUAL',
                        'lugar_reunion': f'Cubículo {100 + (i % 5)} FCC' if i % 2 == 0 else 'https://teams.microsoft.com/meet/posgrado-tesina',
                        'resumen_temas': f'Sesión de asesoría técnica para evaluar avances metodológicos y cronograma de entregables.',
                        'firmada_asesor': True,
                        'firmada_alumno': (dias_inactivo < 30) # Los alumnos en abandono no han firmado
                    }
                )

                CompromisoAcuerdo.objects.get_or_create(
                    minuta=minuta,
                    numero_acuerdo=1,
                    defaults={
                        'descripcion_tarea': 'Ajustar el estado del arte con 15 referencias de revistas indexadas (JCR/Scopus).',
                        'responsable': 'ALUMNO',
                        'fecha_limite': fecha_avance + timedelta(days=15),
                        'estado': 'CUMPLIDO' if dias_inactivo < 15 else 'PENDIENTE',
                        'estado_cumplido': (dias_inactivo < 15)
                    }
                )

            # ==============================================================================
            # CU04: ALERTAS POR REZAGO (> 30 DÍAS)
            # ==============================================================================
            if proyecto.tiene_alerta_rezago and estado_proy == 'APROBADO':
                proyectos_en_rezago += 1
                AlertaRezago.objects.get_or_create(
                    proyecto=proyecto,
                    defaults={
                        'dias_acumulados': dias_inactivo,
                        'estado_alerta': 'Pendiente de Contacto'
                    }
                )

            alumnos_creados += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] {alumnos_creados} Alumnos creados con proyectos, entregables y minutas vinculadas."))
        self.stdout.write(self.style.WARNING(f"[CU04] {proyectos_en_rezago} Alumnos colocados en rezago estricto (> 30 hasta 45 días sin avance)."))
        self.stdout.write(self.style.SUCCESS(f"\n¡Base de datos sembrada al 100%! Contraseña unificada: {password_comun}\n"))