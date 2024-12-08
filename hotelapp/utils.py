from hotelapp import app,db
from flask import current_app
from hotelapp.models import User, Room, RoomType, RoomStatus, UserRole, National, BookingNote, BookingNoteDetails, Bill, \
    RentalNote
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.sql import extract
import hashlib

#Tải quốc tịch
def load_nationals():
    return National.query.all()


def load_room_type():
    return RoomType.query.order_by(RoomType.id).all()

def load_room():
    return Room.query.all()

#Thêm người dùng
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

#Kiểm tra đăng nhập
def check_login(username, password, role_name="CUSTOMER"):
    if username and password:
        password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
        role = UserRole.query.filter_by(role_name=role_name).first()
        if role:
            return User.query.filter(
                User.username == username.strip(),
                User.password == password,
                User.user_role_id == role.id
            ).first()


#Hàm tải người dùng
def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_room_by_id(room_id):
    return Room.query.get(room_id)
#Join bảng lấy dữ liệu để thêm vào quản lý phòng
def get_rooms():
    return (db.session.query(
        Room.id,
        RoomType.room_type_name,
        RoomStatus.status_name,
        RoomType.price
    ).join(RoomType, Room.room_type_id == RoomType.id) \
     .join(RoomStatus, Room.room_status_id == RoomStatus.id)\
        .join(National,User.national_id==National.id).all())

# PHẦN PHÒNG + LOẠI PHÒNG

def get_soluong_RoomType(room_id):
    query = db.session.query(RoomType.id, RoomType.room_type_name, Room.max_people) \
        .join(Room, Room.room_type_id.__eq__(RoomType.id)).filter(Room.id.__eq__(room_id)).first()

    soluong = query.max_people

    return soluong



# PHẦN LOAD DANH SACH PHÒNG
# Lấy danh sách phòng đã đặt

ROOM_STATUS_WAITING = 'Chờ nhận phòng'
ROOM_STATUS_EMPTY = 'Trống'
ROOM_STATUS_BOOKED = 'Đã đặt'
ROOM_STATUS_RENTED = 'Đang thuê'

def load_booked(checkin_date=None, checkout_date=None):
    if checkin_date and checkout_date:
        query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_BOOKED) \
            .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
            .filter(BookingNoteDetails.checkin_date.between(checkin_date, checkout_date) |
                    BookingNoteDetails.checkout_date.between(checkin_date, checkout_date))
        return query.all()
    return []

# Lấy danh sách phòng đang thuê
def load_booking(checkin_date=None, checkout_date=None):
    if checkin_date and checkout_date:
        query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_RENTED) \
            .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
            .filter(BookingNoteDetails.checkin_date <= checkout_date,
                    BookingNoteDetails.checkout_date >= checkin_date)
        return query.all()
    return []

# Lấy danh sách phòng trống
def load_empty(checkin_date=None, checkout_date=None):
    booked_rooms = [r[0] for r in load_booked(checkin_date, checkout_date)]
    rented_rooms = [r[0] for r in load_booking(checkin_date, checkout_date)]
    unavailable_rooms = set(booked_rooms + rented_rooms)

    query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_EMPTY) \
        .filter(Room.id.notin_(unavailable_rooms))
    return query.all()

# Tổng hợp danh sách tất cả phòng
def load_all(checkin_date=None, checkout_date=None):
    booked = load_booked(checkin_date, checkout_date)
    rented = load_booking(checkin_date, checkout_date)
    empty = load_empty(checkin_date, checkout_date)
    return sorted(booked + rented + empty, key=lambda x: x[0])


# def room_type_stats(kw=None, from_date=None, to_date=None):
#     with current_app.app_context():
#         query = db.session.query(
#             Room.room_type_id,
#             RoomType.room_type_name,
#             (func.count(BookingNoteDetails.id) * func.sum(Bill.total_cost))
#         ).join(RoomType, Room.room_type_id == RoomType.id) \
#             .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
#             .join(BookingNote, BookingNote.id == BookingNoteDetails.booking_note_id) \
#             .join(RentalNote, RentalNote.booking_note_id == BookingNote.id) \
#             .join(Bill, Bill.rental_note_id == RentalNote.id) \
#             .group_by(Room.room_type_id, RoomType.room_type_name)
#
#         # Lọc theo từ khóa
#         if kw:
#             query = query.filter(RoomType.room_type_name.contains(kw))
#
#         # Lọc theo ngày bắt đầu
#         if from_date:
#             query = query.filter(BookingNote.created_date >= from_date)
#
#         # Lọc theo ngày kết thúc
#         if to_date:
#             query = query.filter(BookingNote.created_date <= to_date)
#
#         # Nhóm kết quả theo loại phòng
#         query = query.group_by(Room.room_type_id, RoomType.room_type_name)
#
#         return query.all()
#
#
# def room_month_stats(year):
#     return db.session.query(
#             extract('month', BookingNoteDetails.checkin_date).label('month'),  # Lấy tháng từ ngày check-in
#             func.sum(BookingNoteDetails.id * Bill.total_cost)) \
#             .join(Room, Room.id == BookingNoteDetails.room_id) \
#             .filter(extract('year', BookingNoteDetails.checkin_date) == year) \
#             .group_by(extract('month', BookingNoteDetails.checkin_date))  \
#             .order_by(extract('month', BookingNoteDetails.checkin_date))  \
#             .all()
#
from sqlalchemy import func

def monthly_revenue_report(from_date=None, to_date=None):
    query = db.session.query(
        func.date_format(Bill.created_date, '%Y-%m').label('month'),  # Group by month (format YYYY-MM)
        func.sum(Bill.total_cost).label('total_revenue')             # Sum of total_cost
    )

    if from_date:
        query = query.filter(Bill.created_date >= from_date)
    if to_date:
        query = query.filter(Bill.created_date <= to_date)

    query = query.group_by(func.date_format(Bill.created_date, '%Y-%m')) \
                 .order_by(func.date_format(Bill.created_date, '%Y-%m'))

    return query.all()


def room_type_usage_report(from_date=None, to_date=None):
    query = db.session.query(
        func.date_format(BookingNoteDetails.checkin_date, '%Y-%m').label('month'),  # Group by month
        RoomType.room_type_name,                                                   # Room type name
        func.count(BookingNoteDetails.room_id).label('usage_frequency')            # Count of bookings
    ).join(Room, Room.id == BookingNoteDetails.room_id) \
     .join(RoomType, Room.room_type_id == RoomType.id)

    if from_date:
        query = query.filter(BookingNoteDetails.checkin_date >= from_date)
    if to_date:
        query = query.filter(BookingNoteDetails.checkin_date <= to_date)

    query = query.group_by(
        func.date_format(BookingNoteDetails.checkin_date, '%Y-%m'),
        RoomType.room_type_name
    ).order_by(func.date_format(BookingNoteDetails.checkin_date, '%Y-%m'), RoomType.room_type_name)

    return query.all()

if __name__ == '__main__':
    with app.app_context():
        print(room_type_usage_report())
