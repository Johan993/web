from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum
from .db_session import SqlAlchemyBase

class DayStatus(enum.Enum):
    done = 'done'
    skipped = 'skipped'

class habit1(SqlAlchemyBase):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    days = relationship('HabitDay', back_populates='habit', cascade='all, delete-orphan')
    user = relationship('User', back_populates='habits')

    def mark_done(self, mark_date: date):
        for d in self.days:
            if d.date == mark_date:
                d.status = DayStatus.done
                return
        self.days.append(HabitDay(date=mark_date, status=DayStatus.done))

    def mark_skipped(self, mark_date: date):
        for d in self.days:
            if d.date == mark_date:
                d.status = DayStatus.skipped
                return
        self.days.append(HabitDay(date=mark_date, status=DayStatus.skipped))

class HabitDay(SqlAlchemyBase):
    __tablename__ = 'habit_days'

    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    date = Column(Date, nullable=False)
    status = Column(Enum(DayStatus), nullable=False)

    habit = relationship('habit1', back_populates='days')