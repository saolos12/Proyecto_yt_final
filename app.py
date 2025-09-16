import os
import secrets
from PIL import Image
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from database import db
from models import Idea, User
from forms import IdeaForm, LoginForm, RegistrationForm
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'SaolosYolo.1aloyda') # Usar variable de entorno
# Usar variable de entorno para la URI de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ideas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads' # Esto aún es local, ver Paso 5 para solución
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)

    output_size = (400, 400)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/')
def index():
    if current_user.is_authenticated:
        search_query = request.args.get('search')
        filter_status = request.args.get('status')
        
        query = current_user.ideas
        
        if search_query:
            query = query.filter(
                (Idea.title.ilike(f'%{search_query}%')) |
                (Idea.description.ilike(f'%{search_query}%')) |
                (Idea.tags.ilike(f'%{search_query}%'))
            )
        
        if filter_status:
            query = query.filter_by(status=filter_status)
        
        ideas = query.all()
        
        counts = {
            'total': current_user.ideas.count(),
            'pendiente': current_user.ideas.filter_by(status='Pendiente').count(),
            'en_progreso': current_user.ideas.filter_by(status='En Progreso').count(),
            'completada': current_user.ideas.filter_by(status='Completada').count()
        }

        return render_template('index.html', ideas=ideas, search_query=search_query, counts=counts)
    
    return render_template('index.html', ideas=[], search_query=None, counts=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('¡Sesión iniciada con éxito!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Te has registrado con éxito! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_idea():
    form = IdeaForm()
    if form.validate_on_submit():
        picture_filename = None
        if form.image.data:
            picture_filename = save_picture(form.image.data)

        new_idea = Idea(
            title=form.title.data,
            description=form.description.data,
            format=form.format.data,
            tags=form.tags.data,
            status=form.status.data,
            image_filename=picture_filename,
            author=current_user
        )
        db.session.add(new_idea)
        db.session.commit()
        flash('¡Idea agregada con éxito!', 'success')
        return redirect(url_for('index'))
    return render_template('add_idea.html', form=form)

@app.route('/edit/<int:idea_id>', methods=['GET', 'POST'])
@login_required
def edit_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    if idea.author != current_user and not current_user.is_admin:
        flash('No tienes permiso para editar esta idea.', 'danger')
        return redirect(url_for('index'))
    form = IdeaForm(obj=idea)
    if form.validate_on_submit():
        if form.image.data:
            if idea.image_filename:
                old_picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], idea.image_filename)
                if os.path.exists(old_picture_path):
                    os.remove(old_picture_path)
            picture_filename = save_picture(form.image.data)
            idea.image_filename = picture_filename
        
        idea.title = form.title.data
        idea.description = form.description.data
        idea.format = form.format.data
        idea.tags = form.tags.data
        idea.status = form.status.data
        db.session.commit()
        flash('¡Idea actualizada con éxito!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_idea.html', form=form, idea=idea)

@app.route('/delete/<int:idea_id>')
@login_required
def delete_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    if idea.author != current_user and not current_user.is_admin:
        flash('No tienes permiso para eliminar esta idea.', 'danger')
        return redirect(url_for('index'))
    
    if idea.image_filename:
        picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], idea.image_filename)
        if os.path.exists(picture_path):
            os.remove(picture_path)

    db.session.delete(idea)
    db.session.commit()
    flash('¡Idea eliminada con éxito!', 'success')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), filename)

if __name__ == '__main__':
    app.run(debug=True)