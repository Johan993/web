from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class WaterForm(FlaskForm):
    amount_ml = IntegerField('Объём воды (мл)',
                             validators=[DataRequired(), NumberRange(min=1, message="Введите число ≥ 1")])
    submit = SubmitField('Добавить')