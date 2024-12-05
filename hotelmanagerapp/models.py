from email.policy import default
from xml.etree.ElementTree import parse

from sqlalchemy import Column, Integer, String, Float,ForeignKey, Double,Enum, Date,DateTime
from hotelmanagerapp import db,app
from sqlalchemy.orm import relationship, Relationship
from datetime import datetime

class User(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(50))
    birthday = Column(Date, nullable=False)
    avatar = Column(String(100))
    user_role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
    national_id=Column(Integer, ForeignKey('national.id') ,nullable=False)
    booking_notes= Relationship('Booking_note', backref='user', lazy=True)
    def __str__(self):
        return self.name
class User_role(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), nullable=False)
    users= Relationship('User', backref='user_role',lazy=True)
    def __str__(self):
        return self.role_name
class National(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String(50), nullable=False)
    coefficient= Column(Double, nullable=False)
    users=Relationship('User', backref='national',lazy=True)
    def __str__(self):
        return self.country_name
class Booking_note(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date=Column(DateTime, default=datetime.now())
    customer_name=Column(String(50),nullable=False)
    phone_number=Column(String(10),nullable=False)
    cccd=Column(String(12),nullable=False)
    user_id=Column(Integer, ForeignKey('user.id'), nullable=False)
    rooms=Relationship('Booking_note_details',backref='booking_note')
    rental_notes=Relationship('Rental_note',uselist=False,backref='booking_note')
    def __str__(self):
        return self.id
class Room_type(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_type_name=Column(String(50), nullable=False)
    price=Column(Float, nullable=False)
    surcharge=Column(Double, nullable=False)
    rooms=Relationship('Room', backref='room_type',lazy=True)
    def __str__(self):
        return self.room_type_name
class Room_status(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    status_name=Column(String(50), nullable=False)
    rooms=Relationship('Room', backref='room_status',lazy=True)
    def __str__(self):
        return self.status_name
class Room(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_address=Column(String(50), nullable=False)
    max_people=Column(Integer, nullable=False)
    image=Column(String(100), nullable=False)
    room_type_id=Column(Integer, ForeignKey('room_type.id'), nullable=False)
    room_staus_id=Column(Integer, ForeignKey('room_status.id'), nullable=False)
    booking_notes=relationship('Booking_note_details', backref='room')
    def __str__(self):
        return self.room_address
class Booking_note_details(db.Model):
    checkin_date=Column(DateTime, primary_key=True,nullable=False)
    checkout_date=Column(DateTime, nullable=False)
    number_people=Column(Integer, nullable=False)
    booking_note_id=Column(Integer, ForeignKey('booking_note.id'), nullable=False)
    room_id=Column(Integer,ForeignKey('room.id'), primary_key=True)
class Rental_note(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date=Column(DateTime, default=datetime.now())
    booking_note_id=Column(Integer, ForeignKey('booking_note.id'), nullable=False,unique=True)
    bills=relationship('Bill',uselist=False,backref='rental_note')
    booking_notes=relationship('Booking_note',backref='rental_note',uselist=False)
    def __str__(self):
        return self.id

class Bill(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date=Column(DateTime, default=datetime.now())
    total_cost=Column(Float, nullable=False)
    rental_note_id=Column(Integer, ForeignKey('rental_note.id'), nullable=False, unique=True)
    rental_notes=relationship('Rental_note',uselist=False,backref='bill')
    def __str__(self):
        return self.id
if __name__ == '__main__':
 # with app.app_context():
    db.create_all()
    # n1=National(country_name='Việt Nam',coefficient=1.0)
    # n2 = National(country_name='Khác', coefficient=1.2)
    # db.session.add(n1)
    # db.session.add(n2)

    # r1=User_role(role_name='admin')
    # r2=User_role(role_name='employee')
    # r3=User_role(role_name='customer')
    # db.session.add(r1)
    # db.session.add(r2)
    # db.session.add(r3)
    #
    # u1=User(username='admin', password='admin', name='admin',email='plehoang641@gmail.com',birthday=datetime(2004,2,6),avatar='default.jpg',user_role_id=1, national_id=1)
    # u2 = User(username='employee', password='employee', name='employee', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6),
    #           avatar='default.jpg', user_role_id=2, national_id=1)
    # u3 = User(username='phuc', password='phuc', name='phuc', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6),avatar='default.jpg', user_role_id=3, national_id=1)
    # u4 = User(username='nhat', password='nhat', name='nhat', email='plehoang641@gmail.com', birthday=datetime(2004, 2, 6),
    #           avatar='default.jpg', user_role_id=3, national_id=2)
    # db.session.add(u1)
    # db.session.add(u2)
    # db.session.add(u3)
    # db.session.add(u4)

    # rot1=Room_type(room_type_name='Vip',price=1000000,surcharge=0.25)
    # rot2 = Room_type(room_type_name='Thường', price=550000, surcharge=0.25)
    # db.session.add(rot1)
    # db.session.add(rot2)

    # ros1=Room_status(status_name='trống')
    # ros2 = Room_status(status_name='đang thuê')
    # ros3 = Room_status(status_name='đang đặt')
    # db.session.add(ros1)
    # db.session.add(ros2)
    # db.session.add(ros3)

    # r1=Room(room_address='101',max_people=3,image='img1.jpg',room_type_id=1,room_staus_id=1)
    # r2 = Room(room_address='102', max_people=3, image='img1.jpg', room_type_id=1, room_staus_id=1)
    # r3 = Room(room_address='103', max_people=3, image='img1.jpg', room_type_id=1, room_staus_id=1)
    # r4 = Room(room_address='201', max_people=3, image='img1.jpg', room_type_id=2, room_staus_id=1)
    # r5 = Room(room_address='202', max_people=3, image='img1.jpg', room_type_id=2, room_staus_id=1)
    # r6 = Room(room_address='203', max_people=3, image='img1.jpg', room_type_id=2, room_staus_id=1)
    # db.session.add(r1)
    # db.session.add(r2)
    # db.session.add(r3)
    # db.session.add(r4)
    # db.session.add(r5)
    # db.session.add(r6)
    #
    # b1=Booking_note(customer_name='Lê Hoàng Phúc',phone_number='0337367643',cccd='051204010012',user_id=3)
    # b2 = Booking_note(customer_name='Nguyen Thành Nhật', phone_number='0987654321', cccd='098765432112', user_id=4)
    # db.session.add(b1)
    # db.session.add(b2)

    # bnd1=Booking_note_details(checkin_date=datetime(2024,12,5),checkout_date=datetime(2024,12,6),number_people=2,booking_note_id=1, room_id=1)
    # bnd2 = Booking_note_details(checkin_date=datetime(2024, 12, 5), checkout_date=datetime(2024, 12, 6),number_people=2,
    #                             booking_note_id=1, room_id=2)
    # bnd3 = Booking_note_details(checkin_date=datetime(2024, 12, 7), checkout_date=datetime(2024, 12, 8),number_people=2,
    #                             booking_note_id=2, room_id=1)
    # bnd4 = Booking_note_details(checkin_date=datetime(2024, 12, 7), checkout_date=datetime(2024, 12, 8),number_people=2,
    #             booking_note_id=2, room_id=6)
    # bnd5 = Booking_note_details(checkin_date=datetime(2024, 12, 30), checkout_date=datetime(2024, 12, 8),
    #                             number_people=2,booking_note_id=1, room_id=1)
    # db.session.add(bnd1)
    # db.session.add(bnd2)
    # db.session.add(bnd3)
    # db.session.add(bnd4)
    # db.session.add(bnd5)

    # re1=Rental_note(booking_note_id=1)
    # re2 = Rental_note( booking_note_id=2)
    # db.session.add(re1)
    # db.session.add(re2)

    # db.session.commit()




