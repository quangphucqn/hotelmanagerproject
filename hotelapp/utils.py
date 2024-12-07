from hotelapp import app,db
from hotelapp.models import User, Room, RoomType, RoomStatus, UserRole, National, BookingNote, BookingNoteDetails, Bill, \
    RentalNote
from flask_login import current_user
from flask import render_template, session, redirect, url_for, flash, request
from datetime import datetime
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


def room_list():
    # Join bảng room với room_type và room_status
    rooms = db.session.query(Room, RoomType, RoomStatus).join(
        RoomType, Room.room_type_id == RoomType.id
    ).join(
        RoomStatus, Room.room_status_id == RoomStatus.id
    ).all()
    return rooms

# Lấy danh sách phòng trống
def find_room(checkin_date, checkout_date, num_rooms_requested):
    # Truy vấn phòng trống theo loại và trạng thái
    rooms = db.session.query(Room, RoomType, RoomStatus).join(
        RoomType, Room.room_type_id == RoomType.id
    ).join(
        RoomStatus, Room.room_status_id == RoomStatus.id
    ).filter(
        RoomStatus.status_name == 'trống'
    ).filter(
        ~db.session.query(BookingNoteDetails).filter(
            BookingNoteDetails.room_id == Room.id,
            (BookingNoteDetails.checkin_date < checkout_date) &
            (BookingNoteDetails.checkout_date > checkin_date)
        ).exists()
    ).all()

    # Đếm số phòng trống theo loại
    available_rooms_by_type = {}
    for room, room_type, room_status in rooms:
        if room_type.id not in available_rooms_by_type:
            available_rooms_by_type[room_type.id] = {
                'room_type': room_type,
                'available_count': 0
            }
        available_rooms_by_type[room_type.id]['available_count'] += 1

    # Lọc các loại phòng có đủ số lượng phòng trống
    available_rooms = []
    for room, room_type, room_status in rooms:
        if available_rooms_by_type[room_type.id]['available_count'] >= num_rooms_requested:
            available_rooms.append((room, room_type, room_status))

    return available_rooms

# PHẦN LOAD DANH SACH PHÒNG
# Lấy danh sách phòng đã đặt

# ROOM_STATUS_WAITING = 'Chờ nhận phòng'
# ROOM_STATUS_EMPTY = 'Trống'
# ROOM_STATUS_BOOKED = 'Đã đặt'
# ROOM_STATUS_RENTED = 'Đang thuê'
#
# def load_booked(checkin_date=None, checkout_date=None):
#     if checkin_date and checkout_date:
#         query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_BOOKED) \
#             .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
#             .filter(BookingNoteDetails.checkin_date.between(checkin_date, checkout_date) |
#                     BookingNoteDetails.checkout_date.between(checkin_date, checkout_date))
#         return query.all()
#     return []
#
# # Lấy danh sách phòng đang thuê
# def load_booking(checkin_date=None, checkout_date=None):
#     if checkin_date and checkout_date:
#         query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_RENTED) \
#             .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
#             .filter(BookingNoteDetails.checkin_date <= checkout_date,
#                     BookingNoteDetails.checkout_date >= checkin_date)
#         return query.all()
#     return []
#
# # Lấy danh sách phòng trống
# def load_empty(checkin_date=None, checkout_date=None):
#     booked_rooms = [r[0] for r in load_booked(checkin_date, checkout_date)]
#     rented_rooms = [r[0] for r in load_booking(checkin_date, checkout_date)]
#     unavailable_rooms = set(booked_rooms + rented_rooms)
#
#     query = db.session.query(Room.id, Room.room_type_id, ROOM_STATUS_EMPTY) \
#         .filter(Room.id.notin_(unavailable_rooms))
#     return query.all()
#
# # Tổng hợp danh sách tất cả phòng
# def load_all(checkin_date=None, checkout_date=None):
#     booked = load_booked(checkin_date, checkout_date)
#     rented = load_booking(checkin_date, checkout_date)
#     empty = load_empty(checkin_date, checkout_date)
#     return sorted(booked + rented + empty, key=lambda x: x[0])


def room_type_stats(kw=None, from_date=None, to_date=None):
    query = db.session.query(
        Room.room_type_id,
        RoomType.room_type_name,
        func.sum(Bill.id*Bill.total_cost)
        ).join(RoomType, Room.room_type_id == RoomType.id) \
            .join(BookingNoteDetails, BookingNoteDetails.room_id == Room.id) \
            .join(BookingNote, BookingNote.id == BookingNoteDetails.booking_note_id) \
            .join(RentalNote, RentalNote.booking_note_id == BookingNote.id)  \
            .join(Bill, Bill.rental_note_id == RentalNote.id)


    if kw:
        query = query.filter(RoomType.room_type_name.contains(kw))

    if from_date:
        query = query.filter(BookingNote.created_date >= from_date)
    if to_date:
        query = query.filter(BookingNote.created_date <= to_date)

    query = query.group_by(Room.room_type_id, RoomType.room_type_name)

    return query.all()

def room_month_stats(year):
    return db.session.query(
            extract('month', BookingNoteDetails.checkin_date).label('month'),  # Lấy tháng từ ngày check-in
            func.sum(Bill.id * Bill.total_cost)) \
            .join(Room, Room.id == BookingNoteDetails.room_id) \
            .filter(extract('year', BookingNoteDetails.checkin_date) == year) \
            .group_by(extract('month', BookingNoteDetails.checkin_date))  \
            .order_by(extract('month', BookingNoteDetails.checkin_date))  \
            .all()
