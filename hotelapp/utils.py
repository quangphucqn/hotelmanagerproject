from hotelapp import app,db
from flask import current_app
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

#Join bảng lấy dữ liệu để thêm vào quản lý phòng
def get_room_by_id(room_id):
    return Room.query.get(room_id)

def get_rooms():
    return (db.session.query(
        Room.id,
        RoomType.room_type_name,
        RoomStatus.status_name,
        RoomType.price
    ).join(RoomType, Room.room_type_id == RoomType.id) \
     .join(RoomStatus, Room.room_status_id == RoomStatus.id)\
        .join(National,User.national_id==National.id).all())



#Phần xử lí dữ liệu
def add_bill(rental_note_id):
    # Kiểm tra rental_note_id trước
    print(f"Rental Note ID: {rental_note_id}")

    # Sử dụng db.session.get() thay vì query.get()
    rental_note = db.session.get(RentalNote, rental_note_id)
    if not rental_note:
        raise ValueError(f"Phiếu thuê với ID {rental_note_id} không tồn tại!")

    # Lấy thông tin booking_note từ rental_note
    booking_note = rental_note.booking_note
    if not booking_note:
        raise ValueError("Không tìm thấy thông tin đặt phòng liên quan đến phiếu thuê này!")

    total_cost = 0
    # Duyệt qua các chi tiết phòng trong booking_note
    for detail in booking_note.rooms:
        room = detail.room
        room_type = room.room_type
        user = booking_note.user
        national = user.national

        # Tính chi phí cho phòng (giá phòng dành cho 2 người)
        room_cost = room_type.price * detail.number_people

        # Tính phụ thu nếu số người > 2
        if detail.number_people > 2:
            extra_people = detail.number_people - 2
            room_cost += extra_people * room_type.price * 0.25  # Phụ thu 25% cho mỗi khách thêm

        # Nếu khách là người nước ngoài, nhân hệ số quốc gia
        if national.coefficient > 1:
            room_cost *= national.coefficient

        # Cộng chi phí phòng vào tổng chi phí
        total_cost += room_cost

    # Tạo hóa đơn cho rental_note
    bill = Bill(total_cost=total_cost, rental_note_id=rental_note.id)
    db.session.add(bill)
    db.session.commit()

    return bill




# Phần phòng + loại phòng

def get_quantity_RoomType(room_id):
    query = db.session.query(RoomType.id, RoomType.room_type_name, Room.max_people) \
        .join(Room, Room.room_type_id.__eq__(RoomType.id)).filter(Room.id.__eq__(room_id)).first()

    soluong = query.max_people

    return soluong

#Đưa ra danh sách phòng
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


#THỐNG KÊ

#Tính tổng doanh thu
def grand_total_revenue(from_date=None, to_date=None):
    query = db.session.query(
        func.sum(Bill.total_cost)
    )

    if from_date:
        query = query.filter(Bill.created_date >= from_date)
    if to_date:
        query = query.filter(Bill.created_date <= to_date)

    grand_cost= query.scalar() or 0
    return grand_cost

# Thống kê doanh thu theo tháng
def monthly_revenue_report(from_date=None, to_date=None):
    query = db.session.query(
        RoomType.room_type_name,
        func.sum(Bill.total_cost).label('total_cost'),
        func.count(BookingNoteDetails.id).label('total_bookings')
    ).join(
        Room, RoomType.id == Room.room_type_id
    ).join(
        BookingNoteDetails, Room.id == BookingNoteDetails.room_id
    ).join(
        BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(
        RentalNote, BookingNote.id == RentalNote.booking_note_id
    ).join(
        Bill, RentalNote.id == Bill.rental_note_id
    )

    if from_date:
        query = query.filter(Bill.created_date >= from_date)
    if to_date:
        query = query.filter(Bill.created_date <= to_date)

    query = query.group_by(RoomType.room_type_name).order_by(RoomType.room_type_name)

    result = query.all()
    grand_cost = sum(r.total_cost for r in result)
    result_with_total_cost = [
        {
            'room_type_name': r.room_type_name,
            'total_revenue': r.total_cost,
            'total_bookings': r.total_bookings,
            'total_cost_times_bookings': grand_total_revenue(from_date, to_date)
        }
        for r in result
    ]
    return result_with_total_cost, grand_cost



#Thống kê mật độ sử dụng phòng
def usage_density_report(from_date=None, to_date=None):
    # Truy vấn tổng số ngày thuê của tất cả các loại phòng
    total_days_rented_query = db.session.query(
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label('total_days_rented')
    ).join(
        Room, Room.id == BookingNoteDetails.room_id
    ).join(
        RoomType, Room.room_type_id == RoomType.id
    ).join(
        BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(
        RentalNote, BookingNote.id == RentalNote.booking_note_id
    )

    if from_date:
        total_days_rented_query = total_days_rented_query.filter(BookingNoteDetails.checkin_date >= from_date)
    if to_date:
        total_days_rented_query = total_days_rented_query.filter(BookingNoteDetails.checkout_date <= to_date)

    total_days_rented = total_days_rented_query.scalar()

    # Truy vấn lấy thông tin loại phòng và số ngày thuê
    query = db.session.query(
        RoomType.room_type_name,
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label('total_days_rented')
    ).join(
        Room, RoomType.id == Room.room_type_id
    ).join(
        BookingNoteDetails, Room.id == BookingNoteDetails.room_id
    ).join(
        BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(
        RentalNote, BookingNote.id == RentalNote.booking_note_id
    )

    if from_date:
        query = query.filter(BookingNoteDetails.checkin_date >= from_date)
    if to_date:
        query = query.filter(BookingNoteDetails.checkout_date <= to_date)

    query = query.group_by(RoomType.room_type_name).order_by(RoomType.room_type_name)

    result = query.all()

    # Tính tỷ lệ thuê phòng so với các loại phòng khác trong Python
    result_with_usage_rate = [
        {
            'room_type_name': r.room_type_name,
            'total_days_rented': r.total_days_rented,
            'usage_rate': round((r.total_days_rented / total_days_rented * 100),2) if total_days_rented else 0
        }
        for r in result
    ]

    return result_with_usage_rate

if __name__ == '__main__':
    with app.app_context():
        print(monthly_revenue_report())
        print(usage_density_report())

