from hotelapp import app,db
from hotelapp.models import User, Room,RoomType,RoomStatus,UserRole
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.sql import extract
import hashlib




def add_user(name,username,password,**kwargs):
    password=hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user=User(name=name.strip(),
                username=username.strip(),
                password=password,
                email=kwargs.get('email'),
                avatar=kwargs.get('avatar'))

    db.session.add(user)
    db.session.commit()


def check_login(username,password,role=UserRole.USER):
    if username and password:
        password=hashlib.md5(password.strip().encode('utf-8')).hexdigest()

        return User.query.filter(User.username.__eq__(username.strip()),
                                 User.password.__eq__(password),
                                User.user_role.__eq__(role)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)
