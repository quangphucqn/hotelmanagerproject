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
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
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
                avatar=kwargs.get('avatar'),
                user_role_id =user_role.id
              )

#Kiểm tra đăng nhập
def check_login(username, password, role_name=None):
    """
    Kiểm tra đăng nhập người dùng với vai trò linh hoạt.

    Args:
        username (str): Tên đăng nhập của người dùng.
        password (str): Mật khẩu của người dùng.
        role_name (str): Vai trò của người dùng (ADMIN, CUSTOMER, EMPLOYEE).

    Returns:
        User object: Trả về người dùng nếu thông tin hợp lệ, nếu không trả về None.
    """
    if username and password:
        # Mã hóa mật khẩu bằng MD5
        password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()

        # Truy vấn để lấy thông tin người dùng dựa trên tên đăng nhập và mật khẩu
        user = User.query.filter(
            User.username == username.strip(),
            User.password == password
        ).first()

        if user and (role_name is None or user.user_role.role_name == role_name):
            return user

    # Trả về None nếu không tìm thấy hoặc thông tin không hợp lệ
    return None


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
        .join(National,BookingNote.national_id==National.id).all())



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
        national = booking_note.national

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

# TÌM PHÒNG
# Lấy danh sách phòng trống
def find_room(checkin_date, checkout_date, num_rooms_requested):
    # Truy vấn số lượng phòng trống theo loại
    room_counts = db.session.query(
        RoomType.id,
        RoomType.room_type_name,
        RoomType.price,
        func.count(Room.id).label('available_count')
    ).join(
        Room, Room.room_type_id == RoomType.id
    ).join(
        RoomStatus, Room.room_status_id == RoomStatus.id
    ).filter(
        ~db.session.query(BookingNoteDetails).filter(
            BookingNoteDetails.room_id == Room.id,
            (BookingNoteDetails.checkin_date < checkout_date) &
            (BookingNoteDetails.checkout_date > checkin_date)
        ).exists()
    ).group_by(RoomType.id, RoomType.room_type_name, RoomType.price).all()

    # Lọc các loại phòng có đủ số lượng phòng trống
    available_room_types = [
        {'id': rt.id, 'name': rt.room_type_name, 'price': rt.price, 'available_count': rt.available_count}
        for rt in room_counts if rt.available_count >= num_rooms_requested
    ]

    return available_room_types

#ĐẶT PHÒNG
# Lấy danh sách phòng trống chi tiết theo loại, ngày nhận và ngày trả phòng.
def find_rooms_by_type_and_dates(room_type_id, checkin_date, checkout_date, num_rooms_requested):
    checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d')
    checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d')

    # Truy vấn danh sách phòng trống theo loại
    rooms = db.session.query(Room, RoomType, RoomStatus).join(
        RoomType, Room.room_type_id == RoomType.id
    ).join(
        RoomStatus, Room.room_status_id == RoomStatus.id
    ).filter(
        Room.room_type_id == room_type_id,  # Lọc theo loại phòng
    ).filter(
        ~db.session.query(BookingNoteDetails).filter(
            BookingNoteDetails.room_id == Room.id,
            (BookingNoteDetails.checkin_date < checkout_date) &
            (BookingNoteDetails.checkout_date > checkin_date)
        ).exists()
    ).all() # Lấy tất cả các phòng có thể trống

    # Lọc các phòng đủ số lượng yêu cầu
    available_rooms = []
    for room, room_type, room_status in rooms:
        if len(available_rooms)< num_rooms_requested:
            available_rooms.append((room, room_type, room_status))

    return available_rooms

def count_cart(cart):
    total_quantity=0

    if cart:
        for c in cart.values():
            total_quantity +=1
    return {
        'total_quantity': total_quantity
    }

#THỐNG KÊ

# Hàm chuyển đổi từ string sang datetime.date
def convert_to_date(date_value):
    if isinstance(date_value, str):
        return datetime.strptime(date_value, '%Y-%m-%d').date()
    return date_value
def apply_date_filters(query, from_date=None, to_date=None):
    if isinstance(from_date, str):
        from_date = convert_to_date(from_date)
    if isinstance(to_date, str):
        to_date = convert_to_date(to_date)

    # Xử lý từ ngày
    if from_date:
        from_date = datetime.combine(from_date, datetime.min.time())
        query = query.filter(Bill.created_date >= from_date)

    # Xử lý đến ngày
    if to_date:
        to_date = datetime.combine(to_date, datetime.max.time())
        query = query.filter(Bill.created_date <= to_date)

    return query

# Tính tổng doanh thu
def grand_total_revenue(from_date=None, to_date=None):
    # Chuyển đổi ngày nếu là string


    query = db.session.query(func.sum(Bill.total_cost))

    query = apply_date_filters(query, from_date, to_date)

    grand_cost = query.scalar() or 0
    return grand_cost

# Thống kê doanh thu theo tháng
def monthly_revenue_report(from_date=None, to_date=None):
    from_date = convert_to_date(from_date)
    to_date = convert_to_date(to_date)

    query = db.session.query(
        RoomType.room_type_name,
        func.sum(Bill.total_cost).label('total_cost'),
        func.count(BookingNoteDetails.id).label('total_bookings')
    ).join(Room, RoomType.id == Room.room_type_id
    ).join(BookingNoteDetails, Room.id == BookingNoteDetails.room_id
    ).join(BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(RentalNote, BookingNote.id == RentalNote.booking_note_id
    ).join(Bill, RentalNote.id == Bill.rental_note_id)

    query = apply_date_filters(query, from_date, to_date)

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

# Thống kê mật độ sử dụng phòng
def usage_density_report(from_date=None, to_date=None):
    # Truy vấn tổng số ngày thuê của tất cả các loại phòng
    total_days_rented_query = db.session.query(
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label('total_days_rented')
    ).join(Room, Room.id == BookingNoteDetails.room_id
    ).join(RoomType, Room.room_type_id == RoomType.id
    ).join(BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(RentalNote, BookingNote.id == RentalNote.booking_note_id)

    total_days_rented_query = apply_date_filters(total_days_rented_query, from_date, to_date)

    total_days_rented = total_days_rented_query.scalar() or 0  # Cung cấp giá trị mặc định là 0 nếu không có dữ liệu

    # Truy vấn lấy thông tin loại phòng và số ngày thuê
    query = db.session.query(
        RoomType.room_type_name,
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label('total_days_rented')
    ).join(Room, RoomType.id == Room.room_type_id
    ).join(BookingNoteDetails, Room.id == BookingNoteDetails.room_id
    ).join(BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(RentalNote, BookingNote.id == RentalNote.booking_note_id)

    query = apply_date_filters(query, from_date, to_date)

    query = query.group_by(RoomType.room_type_name).order_by(RoomType.room_type_name)

    result = query.all()

    # Tính tỷ lệ thuê phòng so với các loại phòng khác trong Python
    result_with_usage_rate = [
        {
            'room_type_name': r.room_type_name,
            'total_days_rented': r.total_days_rented,
            'usage_rate': round((r.total_days_rented / total_days_rented * 100), 2) if total_days_rented else 0
        }
        for r in result
    ]

    return result_with_usage_rate
if __name__ == '__main__':
    with app.app_context():
        print(monthly_revenue_report())
        print(usage_density_report())




def find_booking_note(customer_name, phone_number):
    results = (
        db.session.query(BookingNote)
        .filter(
            BookingNote.customer_name == customer_name,
            BookingNote.phone_number == phone_number,
            # BookingNote.rental_notes == None  # Loại bỏ các BookingNote đã có RentalNote
        )
        .options(
            joinedload(BookingNote.rooms)  # Load BookingNoteDetails liên kết
            .joinedload(BookingNoteDetails.room)  # Load Room từ BookingNoteDetails
            .joinedload(Room.room_type)  # Load RoomType từ Room
        )
        .all()
    )
    if results:
     return results



def create_rental_note(booking_note_id):
    id = (
        db.session.query(BookingNote)
        .filter(
            BookingNote.id == booking_note_id,
            BookingNote.rental_notes == None
        ).all()
    )
    if id:  # Nếu tìm thấy BookingNote
        rental_note = RentalNote(booking_note_id=id)
        db.session.add(rental_note)
        db.session.commit()
        return rental_note


