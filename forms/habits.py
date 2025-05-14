from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class habitForm(FlaskForm):
    name = StringField('Название привычки', validators=[DataRequired(message="Введите название привычки"),
                                                       Length(max=100)])
    submit = SubmitField('Добавить')