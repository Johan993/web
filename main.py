from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from datetime import date, timedelta
import logging

from data.db_session import global_init, create_session
from data.users import User
from sqlalchemy import func
from data.water import WaterIntake
from data.habits import habit1, DayStatus, HabitDay
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.water import WaterForm
from forms.habits import habitForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

global_init('db/mars_explorer.db')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    db_sess = create_session()
    try:
        habit_form = habitForm()

        if habit_form.validate_on_submit():
            new_h = habit1(
                name=habit_form.name.data,
                user_id=current_user.id,
                created_date=date.today()
            )
            db_sess.add(new_h)
            db_sess.flush()
            for i in range(28):
                db_sess.add(HabitDay(
                    habit_id=new_h.id,
                    date=date.today() + timedelta(days=i),
                    status=DayStatus.skipped
                ))
            db_sess.commit()
            return redirect(url_for('index'))

        water = db_sess.query(WaterIntake)\
                       .filter_by(user_id=current_user.id)\
                       .order_by(WaterIntake.timestamp.desc())\
                       .first()
        water_amount = water.amount if water else 0
        water_goal = 2000

        user_habits = (
            db_sess.query(habit1)
                   .filter(habit1.user_id == current_user.id)
                   .order_by(habit1.created_date.desc())
                   .all()
        )

        today = date.today()
        habits = []
        for h in user_habits:
            delta = (today - h.created_date.date()).days
            today_idx = delta if 0 <= delta < len(h.days) else None
            for d in h.days:
                d.status = d.status.value
            habits.append((h, today_idx))

        achievements = []
        if user_habits:
            habit = user_habits[0]
            consec = 0
            for d in sorted(habit.days, key=lambda x: x.date, reverse=True):
                if d.status == 'done':
                    consec += 1
                else:
                    break
            if consec >= 7:
                achievements.append('7-дневная серия')
            if consec >= 14:
                achievements.append('14-дневная серия')
            if consec >= 28:
                achievements.append('28-дневная серия')

        return render_template(
            'index.html',
            title='Панель',
            water_amount=water_amount,
            water_goal=water_goal,
            habit_form=habit_form,
            habits=habits,
            achievements=achievements
        )
    finally:
        db_sess.close()

@app.route('/habit/<int:habit_id>/mark', methods=['POST'])
@login_required
def mark_habit(habit_id):
    db_sess = create_session()
    try:
        habit = db_sess.get(habit1, habit_id)
        if not habit or habit.user_id != current_user.id:
            flash("Привычка не найдена или вам не принадлежит.", "danger")
            return redirect(url_for('index'))

        action = request.form.get('action')
        today = date.today()

        if action == 'done':
            habit.mark_done(today)
            flash(f"«{habit.name}» отмечена выполненной за {today}", "success")
        elif action == 'skip':
            habit.mark_skipped(today)
            flash(f"«{habit.name}» отмечена пропущенной за {today}", "warning")
        else:
            flash("Неизвестное действие.", "warning")

        db_sess.commit()
        return redirect(url_for('index'))
    finally:
        db_sess.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = create_session()
        try:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                flash('Пользователь с такой почтой уже существует.', 'warning')
                return redirect(url_for('register'))
            user = User(email=form.email.data, name=form.name.data)
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        finally:
            db_sess.close()
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        try:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(request.args.get('next') or url_for('index'))
            flash('Неправильный логин или пароль', 'danger')
        finally:
            db_sess.close()
    return render_template('login.html', title='Вход', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('login'))

@app.route('/water', methods=['GET', 'POST'])
@login_required
def water():
    db_sess = create_session()
    try:
        form = WaterForm()

        if form.validate_on_submit():
            intake = WaterIntake(
                user_id=current_user.id,
                amount=form.amount_ml.data
            )
            db_sess.add(intake)
            db_sess.commit()
            return redirect(url_for('index'))

        existing = db_sess.query(WaterIntake)\
                          .filter_by(user_id=current_user.id)\
                          .order_by(WaterIntake.timestamp.desc())\
                          .first()
        current_amount = existing.amount if existing else 0

        return render_template('water.html', form=form, current_amount=current_amount)
    finally:
        db_sess.close()


@app.route('/stats')
@login_required
def stats():
    db_sess = create_session()
    try:
        week_ago = date.today() - timedelta(days=6)
        rows = (
            db_sess.query(
                func.date(WaterIntake.timestamp).label('day'),
                func.sum(WaterIntake.amount).label('total')
            )
            .filter(
                WaterIntake.user_id == current_user.id,
                WaterIntake.timestamp >= week_ago
            )
            .group_by('day')
            .order_by('day')
            .all()
        )

        labels = [(week_ago + timedelta(days=i)).isoformat() for i in range(7)]
        data_map = {r.day: r.total for r in rows}
        water_data = [data_map.get(day, 0) for day in labels]

        habits = (
            db_sess.query(habit1)
                   .filter(habit1.user_id == current_user.id)
                   .all()
        )
        habit_labels = []
        habit_data = []
        for h in habits:
            total = len(h.days)
            done = sum(1 for d in h.days if d.status == DayStatus.done)
            habit_labels.append(h.name)
            habit_data.append(round(done / total * 100, 1) if total else 0)

        return render_template(
            'stats.html',
            water_labels=labels,
            water_data=water_data,
            habit_labels=habit_labels,
            habit_data=habit_data
        )
    finally:
        db_sess.close()

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
