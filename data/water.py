import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

class WaterIntake(SqlAlchemyBase):
    __tablename__ = 'water_intake'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime,default=datetime.datetime.utcnow)

    user = orm.relationship('User')