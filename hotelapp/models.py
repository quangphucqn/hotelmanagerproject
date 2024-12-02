from sqlalchemy import Column,Integer,Enum,String,Float,Boolean,DateTime,ForeignKey
from hotelapp import db,app
from datetime import datetime
from flask_login import UserMixin
from enum import Enum as UserEnum

class BaseModel(db.Model):
    __abstract__=True
    id = Column(Integer, primary_key=True, autoincrement=True)

class UserRole(UserEnum):
    ADMIN=1
    USER=2


class User(BaseModel,UserMixin):
    name=Column(String(50),nullable=False)
    username=Column(String(50),nullable=False,unique=True)
    password=Column(String(50),nullable=False)
    avatar=Column(String(100))
    email=Column(String(50))
    active=Column(Boolean,default=True)
    joined_date=Column(DateTime,default=datetime.now())
    user_role=Column(Enum(UserRole),default=UserRole.USER)
    #receipts=relationship("Receipt",backref="user",lazy=True)
    def __str__(self):
        return self.name




    if __name__ == '__main__':
        with app.app_context():
            db.create_all()
            db.session.commit()
