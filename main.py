from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import logging

from data import db_session
from data.users import User
from data.water import WaterIntake
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.water import WaterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация БД
db_session.global_init('db/mars_explorer.db')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/')
def index():
    return render_template('index.html', title="Главная")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Пользователь с такой почтой уже существует.', category='warning')
            return redirect(url_for('register'))
        user = User(
            email=form.email.data,
            name=form.name.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        logger.info(f"New user registered: {user.email}")
        flash('Регистрация прошла успешно!', category='success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Регистрация", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            logger.info(f"User logged in: {user.email}")
            return redirect(request.args.get('next') or url_for('index'))
        flash('Неправильный логин или пароль', category='danger')
    return render_template('login.html', title="Вход", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', category='info')
    return redirect(url_for('login'))

@app.route('/water', methods=['GET', 'POST'])
@login_required
def water():
    form = WaterForm()
    db_sess = db_session.create_session()

    if form.validate_on_submit():
        intake = WaterIntake(
            user_id=current_user.id,
            amount_ml=form.amount_ml.data
        )
        db_sess.add(intake)
        db_sess.commit()
        logger.info(f"Added water intake: {intake.amount_ml} ml for user {current_user.email}")
        return redirect(url_for('water'))
    else:
        if request.method == 'POST':
            logger.warning(f"Form errors: {form.errors}")

    records = db_sess.query(WaterIntake) \
                     .filter(WaterIntake.user_id == current_user.id) \
                     .order_by(WaterIntake.timestamp.desc()) \
                     .all()

    return render_template('water.html',
                           title="Трекер воды",
                           form=form,
                           records=records)

if __name__ == '__main__':
    app.run(debug=True)