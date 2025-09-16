# FileName: /proyecto py/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=25)], render_kw={"autocomplete": "off"})
    password = PasswordField('Contraseña', validators=[DataRequired()], render_kw={"autocomplete": "new-password"})
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')], render_kw={"autocomplete": "new-password"})
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()], render_kw={"autocomplete": "username"}) # Usar 'username' para que el navegador pueda sugerir nombres de usuario guardados si el usuario lo desea, pero no autocompletar con cualquier cosa.
    password = PasswordField('Contraseña', validators=[DataRequired()], render_kw={"autocomplete": "current-password"}) # 'current-password' es el estándar para campos de contraseña en formularios de login.
    submit = SubmitField('Iniciar Sesión')

class IdeaForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()], render_kw={"autocomplete": "off"})
    description = TextAreaField('Descripción', validators=[DataRequired()], render_kw={"autocomplete": "off"})
    format = StringField('Formato (Ej: Tutorial, Vlog)', validators=[DataRequired()], render_kw={"autocomplete": "off"})
    tags = StringField('Etiquetas (separadas por coma)', render_kw={"autocomplete": "off"})
    status = SelectField('Estado', choices=[('Pendiente', 'Pendiente'), ('En Progreso', 'En Progreso'), ('Completada', 'Completada')])
    image = FileField('Imagen (opcional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes (JPG, PNG, JPEG)!')])
    submit = SubmitField('Guardar Idea')
