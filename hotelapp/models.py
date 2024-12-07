import hashlib
from ctypes.wintypes import DOUBLE
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from hotelapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class UserRole(BaseModel):
    __tablename__ = 'user_role'
    role_name = Column(String(45), nullable=False, unique=True)
    users = relationship('User', backref='user_role', lazy=True)

    def __str__(self):
        return self.role_name

class National(BaseModel):
    __tablename__ = 'national'
    country_name = Column(String(50), nullable=False)
    coefficient = Column(Float, nullable=False)
    users = relationship('User', backref='national', lazy=True)

    def __str__(self):
        return self.country_name

class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(50))
    birthday = Column(Date, nullable=False)
    avatar = Column(String(100))
    user_role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
    national_id = Column(Integer, ForeignKey('national.id'), nullable=False)
    booking_notes = relationship('BookingNote', backref='user', lazy=True)

    def __str__(self):
        return self.name

class BookingNoteDetails(BaseModel):
    __tablename__ = 'booking_note_details'
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    number_people = Column(Integer, nullable=False)
    booking_note_id = Column(Integer, ForeignKey('booking_note.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('room.id'), nullable=False, primary_key=True)

class BookingNote(BaseModel):
    __tablename__ = 'booking_note'
    created_date = Column(DateTime, default=datetime.now(), nullable=False)
    customer_name = Column(String(50), nullable=False)
    phone_number = Column(String(10), nullable=False)
    cccd = Column(String(12), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    rooms = relationship('BookingNoteDetails', backref='booking_note')
    rental_notes = relationship('RentalNote', back_populates='booking_note',uselist=False)

    def __str__(self):
        return str(self.id)

class RoomType(BaseModel):
    __tablename__ = 'room_type'
    room_type_name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    surcharge = Column(Float, nullable=False)
    rooms = relationship('Room', backref='room_type', lazy=True)

    def __str__(self):
        return self.room_type_name

class RoomStatus(BaseModel):
    __tablename__ = 'room_status'
    status_name = Column(String(50), nullable=False)
    rooms = relationship('Room', backref='room_status', lazy=True)

    def __str__(self):
        return self.status_name

class Room(BaseModel):
    __tablename__ = 'room'
    room_address = Column(String(50), nullable=False)
    max_people = Column(Integer, nullable=False)
    image = Column(String(100), nullable=False)
    room_type_id = Column(Integer, ForeignKey('room_type.id'), nullable=False)
    room_status_id = Column(Integer, ForeignKey('room_status.id'), nullable=False)
    booking_notes = relationship('BookingNoteDetails', backref='room')

    def __str__(self):
        return self.room_address

class RentalNote(BaseModel):
    __tablename__ = 'rental_note'
    created_date = Column(DateTime, default=datetime.now(), nullable=False)
    booking_note_id = Column(Integer, ForeignKey('booking_note.id'), nullable=False,unique=True)
    bills = relationship('Bill', back_populates='rental_notes', uselist=False, cascade='all, delete-orphan')
    booking_note = relationship('BookingNote', back_populates='rental_notes',uselist=False)

    def __str__(self):
        return str(self.id)

class Bill(BaseModel):
    __tablename__ = 'bill'
    created_date = Column(DateTime, default=datetime.now(), nullable=False)
    total_cost = Column(Float, nullable=False)
    rental_note_id = Column(Integer, ForeignKey('rental_note.id'), nullable=False, unique=True)
    rental_notes = relationship('RentalNote', back_populates='bills',uselist=False)

    def __str__(self):
        return str(self.id)


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        n1 = National(country_name='Việt Nam', coefficient=1.0)
        n2 = National(country_name='Khác', coefficient=1.2)
        db.session.add(n1)
        db.session.add(n2)

        r1 = UserRole(role_name='ADMIN')
        r2 = UserRole(role_name='EMPLOYEE')
        r3 = UserRole(role_name='CUSTOMER')
        db.session.add(r1)
        db.session.add(r2)
        db.session.add(r3)
        password_1 = str(hashlib.md5('admin'.encode('utf-8')).hexdigest())
        u1 = User(username='admin', password=password_1, name='admin', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='images/admin.jpg', user_role_id=1, national_id=1)
        password_2 = str(hashlib.md5('employee'.encode('utf-8')).hexdigest())
        u2 = User(username='employee', password=password_2, name='employee', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='images/admin.jpg', user_role_id=2, national_id=1)
        password_3 = str(hashlib.md5('phuc'.encode('utf-8')).hexdigest())
        u3 = User(username='phuc', password=password_3, name='phuc', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='default.jpg', user_role_id=3, national_id=1)
        password_4 = str(hashlib.md5('nhat'.encode('utf-8')).hexdigest())
        u4 = User(username='nhat', password=password_4, name='nhat', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='default.jpg', user_role_id=3, national_id=2)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)

        rot1 = RoomType(room_type_name='Vip', price=1000000, surcharge=0.25)
        rot2 = RoomType(room_type_name='Thường', price=550000, surcharge=0.25)
        db.session.add(rot1)
        db.session.add(rot2)

        ros1 = RoomStatus(status_name='trống')
        ros2 = RoomStatus(status_name='đang thuê')
        ros3 = RoomStatus(status_name='đang đặt')
        db.session.add(ros1)
        db.session.add(ros2)
        db.session.add(ros3)

        r1 = Room(room_address='101', max_people=3, image='img1.jpg', room_type_id=1, room_status_id=1)
        r2 = Room(room_address='102', max_people=3, image='img1.jpg', room_type_id=1, room_status_id=1)
        r3 = Room(room_address='103', max_people=3, image='img1.jpg', room_type_id=1, room_status_id=1)
        r4 = Room(room_address='201', max_people=3, image='img1.jpg', room_type_id=2, room_status_id=1)
        r5 = Room(room_address='202', max_people=3, image='img1.jpg', room_type_id=2, room_status_id=1)
        r6 = Room(room_address='203', max_people=3, image='img1.jpg', room_type_id=2, room_status_id=1)
        db.session.add(r1)
        db.session.add(r2)
        db.session.add(r3)
        db.session.add(r4)
        db.session.add(r5)
        db.session.add(r6)

        b1 = BookingNote(customer_name='Lê Hoàng Phúc', phone_number='0337367643', cccd='051204010012', user_id=3)
        b2 = BookingNote(customer_name='Nguyen Thành Nhật', phone_number='0987654321', cccd='098765432112', user_id=4)
        db.session.add(b1)
        db.session.add(b2)

        bnd1 = BookingNoteDetails(checkin_date=datetime(2024, 12, 5), checkout_date=datetime(2024, 12, 6), number_people=2, booking_note_id=1, room_id=1)
        bnd2 = BookingNoteDetails(checkin_date=datetime(2024, 12, 5), checkout_date=datetime(2024, 12, 6), number_people=2, booking_note_id=1, room_id=2)
        bnd3 = BookingNoteDetails(checkin_date=datetime(2024, 12, 7), checkout_date=datetime(2024, 12, 8), number_people=2, booking_note_id=2, room_id=1)
        bnd4 = BookingNoteDetails(checkin_date=datetime(2024, 12, 7), checkout_date=datetime(2024, 12, 8), number_people=2, booking_note_id=2, room_id=6)
        bnd5 = BookingNoteDetails(checkin_date=datetime(2024, 12, 30), checkout_date=datetime(2024, 12, 31), number_people=2, booking_note_id=1, room_id=1)
        db.session.add(bnd1)
        db.session.add(bnd2)
        db.session.add(bnd3)
        db.session.add(bnd4)
        db.session.add(bnd5)

        re1 = RentalNote(booking_note_id=1)
        re2 = RentalNote(booking_note_id=2)
        db.session.add(re1)
        db.session.add(re2)

        db.session.commit()


    def price(self):
        return self.room_type.price if self.room_type else None
