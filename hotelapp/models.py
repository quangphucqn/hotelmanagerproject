from ctypes.wintypes import DOUBLE
from sqlalchemy import Column, Integer, Enum, String, Float, Boolean, DateTime,Date, ForeignKey
from hotelapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin
from enum import Enum as UserEnum
from enum import Enum as NationalEnum

# class UserRole(UserEnum):
#     ADMIN = 1
#     USER = 2



class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class UserRole(BaseModel):
    __tablename__ = 'user_role'
    role_name = Column(String(45), nullable=False, unique=True)
    def __str__(self):
        return self.role_name

class National(BaseModel):
    __tablename__ = 'national'
    country = Column(String(45), nullable=False)
    coefficient = Column(Float, nullable=False)
    users = relationship("User", backref="national", lazy=True)


class Bill(BaseModel):
    __tablename__ = 'bill'
    created_date = Column(DateTime, default=datetime.now, nullable=False)
    total_cost = Column(Float, nullable=False)
    customer_name = Column(String(45), nullable=False)
    phone_number = Column(String(10))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    rental_note_id = Column(Integer, ForeignKey("rental_note.id"), nullable=False)


class RentalNote(BaseModel):
    __tablename__ = 'rental_note'
    created_date = Column(DateTime, default=datetime.now, nullable=False)
    customer_name = Column(String(45), nullable=False)
    phone_number = Column(String(10))
    cccd = Column(String(45), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    booking_note_id = Column(Integer, ForeignKey("booking_note.id"), nullable=False)


class BookingNote(BaseModel):
    __tablename__ = 'booking_note'
    created_date = Column(DateTime, default=datetime.now, nullable=False)
    customer_name = Column(String(45), nullable=False)
    phone_number = Column(String(10))
    cccd = Column(String(45), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)



class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    username = Column(String(45), nullable=False, unique=True)
    password = Column(String(45), nullable=False)
    name = Column(String(45), nullable=False)
    email = Column(String(45))
    birthday = Column(Date, nullable=False)
    active = Column(Boolean, default=True)
    avatar = Column(String(100))
    user_role_id = Column(Integer, ForeignKey('user_role.id'))
    national_id = Column(Integer, ForeignKey('national.id'), nullable=False)
    bills = relationship("Bill", backref="user", lazy=True)
    rental_notes = relationship("RentalNote", backref="user", lazy=True)
    booking_notes = relationship("BookingNote", backref="user", lazy=True)

    user_role = relationship("UserRole", backref="user", lazy=True)

    def __str__(self):
        return self.name



class RoomType(BaseModel):
    __tablename__ = 'room_type'
    room_type_name = Column(String(45), nullable=False)
    price = Column(Float, default=0)
    surcharge = Column(Float, default=0)
    rooms = relationship("Room", backref="room_type", lazy=True)


class RoomStatus(BaseModel):
    __tablename__ = 'room_status'
    status_name = Column(String(45), nullable=False)
    rooms = relationship("Room", backref="room_status", lazy=True)


class Room(BaseModel):
    __tablename__ = 'room'
    room_address = Column(String(45), nullable=False)
    max_people = Column(Integer)
    image = Column(String(100))
    room_type_id = Column(Integer, ForeignKey('room_type.id'), nullable=False)
    room_status_id = Column(Integer, ForeignKey('room_status.id'), nullable=False)
    booking_note_details = relationship("BookingNoteDetails", backref="room", lazy=True)


class BookingNoteDetails(BaseModel):
    __tablename__ = 'booking_note_details'
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    number_people = Column(Integer, nullable=False)
    booking_note_id = Column(Integer, ForeignKey("booking_note.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=False, primary_key=True)



if __name__ == '__main__':
    with app.app_context():

        db.create_all()
        nationals = National.query.all()
        users=UserRole.query.all()
        for u in users:
            print(u.role_name)
        for national in nationals:
            print(national.id, national.country)
        db.session.commit()

