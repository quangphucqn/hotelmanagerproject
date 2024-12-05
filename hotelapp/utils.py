from hotelapp import app,db
from hotelapp.models import User, Room, RoomType, RoomStatus, UserRole, National
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.sql import extract
import hashlib


def load_nationals():
    return National.query.all()

def add_user(name,username,password,**kwargs):
    password=hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user_role = UserRole.query.filter_by(role_name="USER").first()
    user=User(name=name.strip(),
                username=username.strip(),
                password=password,
                email=kwargs.get('email'),
                birthday=kwargs.get('birthday'),
                national_id=kwargs.get('national_id'),
                avatar=kwargs.get('avatar'),
                user_role_id =user_role.id
              )

def check_login(username, password, role_name="USER"):
    if username and password:
        password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()

        role = UserRole.query.filter_by(role_name=role_name).first()

        return User.query.filter(User.username.__eq__(username.strip()),
                                     User.password.__eq__(password),
                                     User.user_role == role).first()



def get_user_by_id(user_id):
    return User.query.get(user_id)
