from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length, Email

class RegisterForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired(), Length(2, 30)])
    name = StringField('Имя', validators=[DataRequired(), Length(2, 30)])
    age = IntegerField('Возраст', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = StringField('Пол', validators=[DataRequired(), Length(1, 10)])
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password_repeat = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')