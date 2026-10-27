import os
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    PerfilUsuario,
    Alumno,
    Asesor,
    TelefonoUsuario,
    Convocatoria,
    ProyectoTesis,
    ConfiguracionUsuario,
)
from .validators import validar_archivo_pdf_estricto


# =============================================================================
# 1. AUTENTICACIÓN Y ACCESO (CU01)
# =============================================================================

class LoginForm(forms.Form):
    """Formulario para inicio de sesión institucional."""
    username = forms.CharField(
        label="Usuario o Correo Institucional",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. matricula@alumno.buap.mx o usuario'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )


# =============================================================================
# 2. REGISTROS POR ROL (ALUMNO, ASESOR, COORDINADOR)
# =============================================================================

class RegistroAlumnoForm(forms.Form):
    """Formulario para registro público de tesistas."""
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. luis.matlalcuatzi'})
    )
    email = forms.EmailField(
        label="Correo institucional",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'alumno@alumno.buap.mx'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'id': 'id_password_alumno'})
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'id': 'id_confirm_password_alumno'})
    )

    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    matricula = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 201743936'}))
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2221234567'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo institucional ya está registrado.")
        return email

    def clean_matricula(self):
        matricula = self.cleaned_data['matricula']
        if Alumno.objects.filter(matricula=matricula).exists():
            raise ValidationError("Esta matrícula ya cuenta con un registro activo.")
        return matricula

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirmar_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden. Verifícalas.')
        return cleaned_data


class RegistroAsesorForm(forms.Form):
    """Formulario para registro de directores docentes (inactivos hasta aprobación)."""
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. jgonzalez'})
    )
    email = forms.EmailField(
        label="Correo institucional",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'profesor@correo.buap.mx'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'id': 'id_password_asesor'})
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'id': 'id_confirm_password_asesor'})
    )

    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_empleado = forms.CharField(
        label="Número de trabajador / empleado",
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 10045678'})
    )
    grado_academico = forms.ChoiceField(
        label="Grado Académico",
        choices=[
            ('Dr.', 'Doctorado (Dr.)'),
            ('Dra.', 'Doctorado (Dra.)'),
            ('M.C.', 'Maestría en Ciencias (M.C.)'),
            ('Mtro.', 'Maestría (Mtro.)'),
            ('Mtra.', 'Maestría (Mtra.)'),
            ('Ing.', 'Ingeniería (Ing.)'),
            ('Lic.', 'Licenciatura (Lic.)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    area_especialidad = forms.CharField(
        label="Área de Especialidad / Línea de Investigación",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Inteligencia Artificial, Ciberseguridad...'})
    )
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2221234567'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo institucional ya está registrado.")
        return email

    def clean_numero_empleado(self):
        num = self.cleaned_data['numero_empleado']
        if Asesor.objects.filter(numero_empleado=num).exists():
            raise ValidationError("Este número de empleado ya está en uso.")
        return num

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirmar_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden. Verifícalas.')
        return cleaned_data


class RegistroCoordinadorForm(forms.Form):
    """Formulario para alta interna de coordinadores."""
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. coord.gonzalez'})
    )
    email = forms.EmailField(
        label="Correo institucional",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'coordinador@correo.buap.mx'})
    )
    password = forms.CharField(
        label="Contraseña temporal",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cubiculo_oficina = forms.CharField(
        label="Cubículo u Oficina",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Edificio FCC 1 - Cubículo 105'})
    )
    telefono_oficina = forms.CharField(
        label="Teléfono de Oficina / Extensión",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2222295500 Ext 7200'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo institucional ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirmar_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden.')
        return cleaned_data


# =============================================================================
# 3. GESTIÓN DE PERFILES Y ADMINISTRACIÓN POR COORDINADOR
# =============================================================================

class MiPerfilForm(forms.Form):
    """Permite al usuario autenticado modificar sus datos, tema y credenciales."""
    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    tema = forms.ChoiceField(
        label="Tema",
        choices=ConfiguracionUsuario.TEMAS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    nueva_password = forms.CharField(
        max_length=128, 
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para no cambiarla'})
    )
    confirmar_password = forms.CharField(
        max_length=128, 
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nueva_password')
        p2 = cleaned_data.get('confirmar_password')

        if p1 or p2:
            if p1 != p2:
                raise ValidationError('Las contraseñas ingresadas no coinciden. Por favor, verifícalas.')
            if len(p1) < 6:
                raise ValidationError('La nueva contraseña debe tener al menos 6 caracteres.')
        return cleaned_data


class EditarAsesorPorCoordinadorForm(forms.Form):
    """Edición administrativa de asesores docentes."""
    email = forms.EmailField(
        label="Correo institucional", 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    nueva_password = forms.CharField(
        label="Asignar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    confirmar_password = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_empleado = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    grado_academico = forms.ChoiceField(
        label="Grado Académico",
        choices=[
            ('Lic.', 'Licenciatura (Lic.)'),
            ('Ing.', 'Ingeniería (Ing.)'),
            ('M.C.', 'Maestría en Ciencias (M.C.)'),
            ('Mtro.', 'Maestría (Mtro.)'),
            ('Mtra.', 'Maestría (Mtra.)'),
            ('Dr.', 'Doctorado (Dr.)'),
            ('Dra.', 'Doctorado (Dra.)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    area_especialidad = forms.CharField(
        label="Área de Especialidad",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nueva_password')
        p2 = cleaned_data.get('confirmar_password')

        if p1 or p2:
            if p1 != p2:
                self.add_error('confirmar_password', 'Las contraseñas no coinciden. Verifícalas.')
        return cleaned_data


class EditarAlumnoPorCoordinadorForm(forms.Form):
    """Edición administrativa de tesistas."""
    email = forms.EmailField(
        label="Correo institucional", 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    nueva_password = forms.CharField(
        label="Asignar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    confirmar_password = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    primer_nombre = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    segundo_nombre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_paterno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido_materno = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    matricula = forms.CharField(
        label="Matrícula escolar",
        max_length=20, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nueva_password')
        p2 = cleaned_data.get('confirmar_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden.')
        return cleaned_data


# =============================================================================
# 4. CONVOCATORIAS Y EXPEDIENTE DE TESIS (CU02)
# =============================================================================

class ConvocatoriaForm(forms.ModelForm):
    """Periodos de recepción de protocolos y dictámenes."""
    class Meta:
        model = Convocatoria
        fields = ['titulo', 'periodo', 'descripcion', 'fecha_inicio', 'fecha_limite_protocolo', 'fecha_cierre', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Convocatoria Titulación Otoño 2026'}),
            'periodo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2026-S2 / Otoño 2026'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Lineamientos y requisitos de postulación...'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_limite_protocolo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_cierre': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class SubirProtocoloForm(forms.ModelForm):
    """Registro y postulación del protocolo inicial en PDF."""
    asesor = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.filter(tipo_usuario='ASESOR', cuenta_activa=True),
        label="Director / Asesor de Tesis",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True}),
        empty_label="-- Selecciona a tu director de tesis registrado --"
    )

    class Meta:
        model = ProyectoTesis
        fields = ['titulo_tesis', 'linea_investigacion', 'asesor', 'archivo_protocolo']
        widgets = {
            'titulo_tesis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Sistema Inteligente de Monitoreo Distribuido',
                'required': True,
            }),
            'linea_investigacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Ingeniería de Software / Ciberseguridad',
                'required': True,
            }),
            'archivo_protocolo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,application/pdf',
                'required': True,
            }),
        }

    def clean_archivo_protocolo(self):
        archivo = self.cleaned_data.get('archivo_protocolo')
        if archivo:
            # Inspección binaria y estricta mediante el validador oficial
            validar_archivo_pdf_estricto(archivo)
        return archivo