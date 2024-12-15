import hashlib
from ctypes.wintypes import DOUBLE
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey,UniqueConstraint
from hotelapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin


class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(45), nullable=False, unique=True)
    users = relationship('User', backref='user_role', lazy=True)

    def __str__(self):
        return self.role_name

class National(db.Model):
    __tablename__ = 'national'
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String(50), nullable=False)
    coefficient = Column(Float, nullable=False)
    booking_notes = relationship('BookingNote', backref='national', lazy=True)

    def __str__(self):
        return self.country_name

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(50))
    birthday = Column(Date, nullable=False)
    avatar = Column(String(100))
    user_role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
    booking_notes = relationship('BookingNote', backref='user', lazy=True)

    def __str__(self):
        return self.name

class Room(db.Model):
    __tablename__ = 'room'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_address = Column(String(50), nullable=False)
    max_people = Column(Integer, nullable=False)
    image = Column(String(100), nullable=False)
    room_type_id = Column(Integer, ForeignKey('room_type.id'), nullable=False)
    room_status_id = Column(Integer, ForeignKey('room_status.id'), nullable=False)
    booking_notes = relationship('BookingNoteDetails', backref='room')

    def __str__(self):
        return self.room_address

class RentalNote(db.Model):
    __tablename__ = 'rental_note'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now(), nullable=False)
    booking_note_id = Column(Integer, ForeignKey('booking_note.id'), nullable=False,unique=True)
    bills = relationship('Bill', back_populates='rental_notes', uselist=False, cascade='all, delete-orphan')
    booking_note = relationship('BookingNote', back_populates='rental_notes',uselist=False)

    def __str__(self):
        return str(self.id)


class BookingNoteDetails(db.Model):
    __tablename__ = 'booking_note_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    checkin_date = Column(DateTime,primary_key=True, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    number_people = Column(Integer, nullable=False)
    booking_note_id = Column(Integer, ForeignKey('booking_note.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('room.id'), nullable=False,primary_key=True)

    __table_args__ = (
        UniqueConstraint('checkin_date', 'room_id', name='_checkin_room_uc'),
    )
    def __str__(self):
        return str(self.id)






class BookingNote(db.Model):
    __tablename__ = 'booking_note'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now(), nullable=False)
    customer_name = Column(String(50), nullable=False)
    phone_number = Column(String(10), nullable=False)
    cccd = Column(String(12), nullable=False)
    email = Column(String(50))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    rooms = relationship('BookingNoteDetails', backref='booking_note')
    rental_notes = relationship('RentalNote', back_populates='booking_note',uselist=False)
    national_id = Column(Integer, ForeignKey('national.id'), nullable=False)

    def __str__(self):
        return str(self.id)

class RoomType(db.Model):
    __tablename__ = 'room_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_type_name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    surcharge = Column(Float, nullable=False)
    rooms = relationship('Room', backref='room_type', lazy=True)
    image=Column(String(100), nullable=False)
    def __str__(self):
        return self.room_type_name

class RoomStatus(db.Model):
    __tablename__ = 'room_status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String(50), nullable=False)
    rooms = relationship('Room', backref='room_status', lazy=True)

    def __str__(self):
        return self.status_name


class Bill(db.Model):
    __tablename__ = 'bill'
    id = Column(Integer, primary_key=True, autoincrement=True)
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
        u1 = User(username='admin', password= password_1, name='admin', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='images/admin.jpg', user_role_id=1)
        password_2 = str(hashlib.md5('employee'.encode('utf-8')).hexdigest())
        u2 = User(username='employee', password=password_2, name='employee', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='images/admin.jpg', user_role_id=2)
        password_3 = str(hashlib.md5('phuc'.encode('utf-8')).hexdigest())
        u3 = User(username='phuc', password=password_3, name='phuc', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='default.jpg', user_role_id=3)
        password_4 = str(hashlib.md5('nhat'.encode('utf-8')).hexdigest())
        u4 = User(username='nhat', password=password_4, name='nhat', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6), avatar='default.jpg', user_role_id=3)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)

        rot1 = RoomType(room_type_name='Classic Sea View', price=550000, surcharge=0.25,image='images/classic.jpg')
        rot2 = RoomType(room_type_name='Penthouse with Sea View', price=1000000, surcharge=0.25,image='images/classic.jpg')
        rot3 = RoomType(room_type_name='Queen Resort Classic Ocean View', price=1200000, surcharge=0.25,image='images/classic.jpg')
        rot4 = RoomType(room_type_name='Queen Classic Panoramic Ocean View', price=1500000, surcharge=0.25,image='images/classic.jpg')
        rot5 = RoomType(room_type_name='King Terrace Suite Ocean View', price=1700000, surcharge=0.25,image='images/classic.jpg')
        rot6 = RoomType(room_type_name='King Club Suite Panoramic Oceanview', price=2000000, surcharge=0.25,image='images/classic.jpg')
        rot7 = RoomType(room_type_name='Bedroom Spa Lagoon Villa', price=3000000, surcharge=0.25,image='images/classic.jpg')
        rot8 = RoomType(room_type_name='Bedroom Sun Peninsula Residence Villa', price=3500000, surcharge=0.25,image='images/classic.jpg')
        rot9 = RoomType(room_type_name='Bedroom Pool Villa Ocean View', price=4000000, surcharge=0.25,image='images/classic.jpg')
        db.session.add(rot1)
        db.session.add(rot2)
        db.session.add(rot3)
        db.session.add(rot4)
        db.session.add(rot5)
        db.session.add(rot6)
        db.session.add(rot7)
        db.session.add(rot8)
        db.session.add(rot9)

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
        r7 = Room(room_address='301', max_people=2, image='img1.jpg', room_type_id=3, room_status_id=1)
        r8 = Room(room_address='302', max_people=3, image='img1.jpg', room_type_id=3, room_status_id=1)
        r9 = Room(room_address='303', max_people=3, image='img1.jpg', room_type_id=3, room_status_id=1)
        r10 = Room(room_address='401', max_people=3, image='img1.jpg', room_type_id=4, room_status_id=1)
        r11 = Room(room_address='402', max_people=3, image='img1.jpg', room_type_id=4, room_status_id=1)
        r12 = Room(room_address='403', max_people=3, image='img1.jpg', room_type_id=4, room_status_id=1)
        r13 = Room(room_address='501', max_people=2, image='img1.jpg', room_type_id=5, room_status_id=1)
        r14 = Room(room_address='502', max_people=2, image='img1.jpg', room_type_id=5, room_status_id=1)
        r15 = Room(room_address='503', max_people=2, image='img1.jpg', room_type_id=5, room_status_id=1)
        r16 = Room(room_address='601', max_people=2, image='img1.jpg', room_type_id=6, room_status_id=1)
        r17 = Room(room_address='602', max_people=2, image='img1.jpg', room_type_id=6, room_status_id=1)
        r18 = Room(room_address='603', max_people=2, image='img1.jpg', room_type_id=6, room_status_id=1)
        r19 = Room(room_address='701', max_people=3, image='img1.jpg', room_type_id=7, room_status_id=1)
        r20 = Room(room_address='702', max_people=3, image='img1.jpg', room_type_id=7, room_status_id=1)
        r21 = Room(room_address='703', max_people=3, image='img1.jpg', room_type_id=7, room_status_id=1)
        r22 = Room(room_address='801', max_people=2, image='img1.jpg', room_type_id=8, room_status_id=1)
        r23 = Room(room_address='802', max_people=2, image='img1.jpg', room_type_id=8, room_status_id=1)
        r24 = Room(room_address='803', max_people=2, image='img1.jpg', room_type_id=8, room_status_id=1)
        r25 = Room(room_address='901', max_people=2, image='img1.jpg', room_type_id=9, room_status_id=1)
        r26 = Room(room_address='902', max_people=2, image='img1.jpg', room_type_id=9, room_status_id=1)
        r27 = Room(room_address='903', max_people=2, image='img1.jpg', room_type_id=9, room_status_id=1)
        db.session.add(r1)
        db.session.add(r2)
        db.session.add(r3)
        db.session.add(r4)
        db.session.add(r5)
        db.session.add(r6)
        db.session.add(r7)
        db.session.add(r8)
        db.session.add(r9)
        db.session.add(r10)
        db.session.add(r11)
        db.session.add(r12)
        db.session.add(r13)
        db.session.add(r14)
        db.session.add(r15)
        db.session.add(r16)
        db.session.add(r17)
        db.session.add(r18)
        db.session.add(r19)
        db.session.add(r20)
        db.session.add(r21)
        db.session.add(r22)
        db.session.add(r23)
        db.session.add(r24)
        db.session.add(r25)
        db.session.add(r26)
        db.session.add(r27)

        b1 = BookingNote(customer_name='Lê Hoàng Phúc', phone_number='0337367643', cccd='051204010012', user_id=3,national_id=1)
        b2 = BookingNote(customer_name='Nguyen Thành Nhật', phone_number='0987654321', cccd='098765432112', user_id=4,national_id=1)
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

        b10 = BookingNote(customer_name='Lê Hoàng Phúc', phone_number='0337367643', cccd='051204010012', user_id=3,
                         national_id=1)
        bnd10 = BookingNoteDetails(checkin_date=datetime(2024, 12, 5), checkout_date=datetime(2024, 12, 6),
                                  number_people=2, booking_note_id=3, room_id=5)
        bnd20 = BookingNoteDetails(checkin_date=datetime(2024, 12, 5), checkout_date=datetime(2024, 12, 6),
                                  number_people=2, booking_note_id=3, room_id=4)
        db.session.add(b10)
        db.session.add(bnd10)
        db.session.add(bnd20)
        b20 = BookingNote(customer_name='Trần Quang Phục', phone_number='0987654321', cccd='051204010012', user_id=3,
                         national_id=1)
        bnd30 = BookingNoteDetails(checkin_date=datetime(2024, 12, 7), checkout_date=datetime(2024, 12, 6),
                                  number_people=2, booking_note_id=4, room_id=5)
        db.session.add(b20)
        db.session.add(bnd30)
        db.session.commit()


    def price(self):
        return self.room_type.price if self.room_type else None
