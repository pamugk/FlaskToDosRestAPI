from sqlalchemy import Column, ForeignKey, UniqueConstraint, Integer, String, Text, Boolean
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(Text, nullable=False)

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def __repr__(self):
        return '<Пользователь %r>' % (self.login)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(50), nullable=False)
    description = Column(Text)
    finished = Column(Boolean)
    __table_args__ = (UniqueConstraint('user_id', 'title', name='_user_task_uc'),)

    def __init__(self, user_id, title, description):
        self.user_id = user_id
        self.title = title
        self.description = description
        self.finished = False

    def __repr__(self):
        return '<Задача \'%r\'>' % (self.title)
