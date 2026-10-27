from rest_framework import serializers
from seguimiento.models import PerfilUsuario, Alumno, Asesor

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ['id_usuario', 'primer_nombre', 'apellido_paterno', 'tipo_usuario', 'cuenta_activa']

class AlumnoSerializer(serializers.ModelSerializer):
    perfil = PerfilUsuarioSerializer(read_only=True)

    class Meta:
        model = Alumno
        fields = ['id_alumno', 'matricula', 'perfil']