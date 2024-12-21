from hotelapp import app, db
from flask import current_app
from hotelapp.models import User, Room, RoomType, RoomStatus, UserRole, National, BookingNote, BookingNoteDetails, Bill, \
    RentalNote
from flask_login import current_user
from flask import render_template, session, redirect, url_for, flash, request
from datetime import datetime, timedelta
import os, ezgmail,locale
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy import func
from sqlalchemy.sql import extract
import hashlib
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import locale

#set format kiêu vn
locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

# format giá qua tiền vnd
def format_currency(value):
    return locale.currency(value, grouping=True)

#Tải quốc tịch
def load_nationals():
    return National.query.all()


def load_room_type():
    return RoomType.query.order_by(RoomType.id).all()


def load_room():
    return Room.query.all()


# Thêm người dùng
def add_user(name, username, password, **kwargs):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user_role = UserRole.query.filter_by(role_name="CUSTOMER").first()
    user = User(name=name.strip(),
                username=username.strip(),
                password=password,
                email=kwargs.get('email'),
                birthday=kwargs.get('birthday'),
                avatar=kwargs.get('avatar'),
                user_role_id=user_role.id
                )
    db.session.add(user)
    db.session.commit()
    return user


# Kiểm tra đăng nhập
def check_login(username, password, role_name=None):

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
    return None


# Hàm tải người dùng
def get_user_by_id(user_id):
    return User.query.get(user_id)


# Join bảng lấy dữ liệu để thêm vào quản lý phòng
def get_room_by_id(room_id):
    return Room.query.get(room_id)


def get_rooms():
    return (db.session.query(
        Room.id,
        RoomType.room_type_name,
        RoomStatus.status_name,
        RoomType.price
    ).join(RoomType, Room.room_type_id == RoomType.id) \
            .join(RoomStatus, Room.room_status_id == RoomStatus.id) \
            .join(National, BookingNote.national_id == National.id).all())


# Phần phòng + loại phòng

def get_quantity_RoomType(room_id):
    query = db.session.query(RoomType.id, RoomType.room_type_name, Room.max_people) \
        .join(Room, Room.room_type_id.__eq__(RoomType.id)).filter(Room.id.__eq__(room_id)).first()

    soluong = query.max_people

    return soluong


# Đưa ra danh sách phòng
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

#tìm những phòng trống theo loại phòng đã chọn - trả về phòng trống
def find_rooms_by_type_and_dates(room_type_id, checkin_date, checkout_date, num_rooms_requested):
    rooms = db.session.query(Room).filter(
        Room.room_type_id == room_type_id,
        ~db.session.query(BookingNoteDetails).filter(
            BookingNoteDetails.room_id == Room.id,
            BookingNoteDetails.checkin_date < checkout_date,
            BookingNoteDetails.checkout_date > checkin_date
        ).exists()
    ).limit(num_rooms_requested)

    return rooms

#tính tiền
def calculate_room_price(room_data, number_people):
    """
    Tính tổng tiền cho một phòng dựa trên số người và số ngày ở.
    """
    try:

        # Lấy giá phòng và số ngày ở
        room_type_id = room_data['room_type_id']
        room_price = room_data['room_price']
        checkin_date = room_data['checkin_date']
        checkout_date = room_data['checkout_date']
        max_people = room_data['max_people']
        room_type = db.session.query(RoomType).filter(RoomType.id == room_type_id).first()  # lấy tỉ lệ phụ phí

        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        num_days = (checkout - checkin).days

        # Áp dụng logic giá phòng
        if number_people == max_people:
            room_price *= (1+room_type.surcharge)

        room_total_price = room_price * num_days
        return room_total_price
    except Exception as e:
        raise Exception(f"Error in calculate_room_price: {str(e)}")
    #tính tổng tiền phòng
def calculate_total_cart_price(cart, national_id):
    try:
        total_cost = 0
        national = db.session.query(National).filter(National.id == national_id).first()
        for room_id, room_data in cart.items():
            room_total_price = room_data.get('total_price', 0)
            total_cost += room_total_price

        # Áp dụng hệ số quốc tịch nếu cần
        if national_id == national.id:  # Hệ số "Khác"
            total_cost *= national.coefficient
        return total_cost
    except Exception as e:
        raise Exception(f"Error in calculate_total_cart_price: {str(e)}")

#gửi mail bằng sendgrid
def send_email(to_email, customer_name, cart, total_price, phone_number):
    try:
        # Soạn tiêu đề
        subject = f"ĐẶT PHÒNG THÀNH CÔNG - Pearl Natureystic Hotel"

        # Soạn nội dung chi tiết phòng từ cart
        room_details_html = "<br>".join([
            f"Phòng: {room['room_address']} ({room['room_type_name']}) - Ngày nhận: {room['checkin_date']} - Ngày trả: {room['checkout_date']}"
            for room_id, room in cart.items()
        ])

        # Soạn nội dung email
        content = f"""
            <h1>Xác nhận bạn đã đặt phòng</h1>
            <p>Xin chào {customer_name},</p>
            <p>Cảm ơn bạn đã đặt phòng với chúng tôi. Thông tin chi tiết:</p>
            <p>{room_details_html}</p>
            <p><strong>Tổng tiền: {total_price} VNĐ</strong></p>
            <p>SDT: {phone_number}</p>
            <p>Email: {to_email}</p>
            <p>Khi đến nhận phòng hãy đọc tên và SDT để nhân viên kiểm tra bạn nhé.</p>
            <p>Chúc bạn một kỳ nghỉ tuyệt vời!</p>
            <p>Trân trọng, Pearl Natureystic Hotel</p>
        """

        # Tạo email
        message = Mail(
            from_email='pearlnatureystic@gmail.com',
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        # điền api key để gửi mail

        response = sg.send(message)
        print(f"Email sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
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
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label(
            'total_days_rented')
    ).join(Room, Room.id == BookingNoteDetails.room_id
    ).join(RoomType, Room.room_type_id == RoomType.id
    ).join(BookingNote, BookingNoteDetails.booking_note_id == BookingNote.id
    ).join(RentalNote, BookingNote.id == RentalNote.booking_note_id)

    total_days_rented_query = apply_date_filters(total_days_rented_query, from_date, to_date)

    total_days_rented = total_days_rented_query.scalar() or 0  # Cung cấp giá trị mặc định là 0 nếu không có dữ liệu

    # Truy vấn lấy thông tin loại phòng và số ngày thuê
    query = db.session.query(
        RoomType.room_type_name,
        func.sum(func.datediff(BookingNoteDetails.checkout_date, BookingNoteDetails.checkin_date)).label(
            'total_days_rented')
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


def create_booking_note(customer_name, phone_number, cccd, email, national_id, user_id):
    # Tạo một đối tượng BookingNote mới
    booking_note = BookingNote(
        customer_name=customer_name,
        phone_number=phone_number,
        cccd=cccd,
        email=email,
        national_id=national_id,
        created_date=datetime.now(),
        user_id=user_id  # Thêm user_id vào đây
    )


    db.session.add(booking_note)
    # Chưa commit
    db.session.flush()  # Flush để lấy ID của booking_note
    return booking_note.id  # Trả về ID của booking_note


def create_booking_note_details(room_data, booking_note_id):
    # Lưu chi tiết phòng vào BookingNoteDetails
    for data in room_data:
        booking_detail = BookingNoteDetails(
            checkin_date=data['checkin_date'],
            checkout_date=data['checkout_date'],
            number_people=data['number_people'],
            booking_note_id=booking_note_id,  # Gán booking_note.id vào đây
            room_id=data['room_id']
        )
        db.session.add(booking_detail)

    # Chưa commit


def find_booking_note(customer_name, phone_number):
    results = (
        db.session.query(BookingNote)
        .filter(
            BookingNote.customer_name == customer_name,
            BookingNote.phone_number == phone_number,
            # BookingNote.created_date >= datetime.now() - timedelta(days=28),
            BookingNote.rental_notes == None,  # Loại bỏ các BookingNote đã có RentalNote
            BookingNote.rooms!=None
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


def delete_old_booking_notes():
    from datetime import datetime, timedelta

    # Lấy thời gian giới hạn 28 ngày trước
    limit_date = datetime.now() - timedelta(days=30)

    # Lấy tất cả các booking note có ngày tạo quá 28 ngày và chưa có RentalNote
    old_booking_notes = db.session.query(BookingNote).filter(
        BookingNote.created_date < limit_date,
        BookingNote.rental_notes== None
    ).all()

    for booking_note in old_booking_notes:
        # Xóa tất cả các BookingNoteDetails liên quan đến BookingNote này
        for room_detail in booking_note.rooms[:]:
            db.session.delete(room_detail)

        # Xóa chính BookingNote
        db.session.delete(booking_note)

    # Thực hiện commit để lưu thay đổi vào cơ sở dữ liệu
    db.session.commit()


def delete_old_bookingnote_details():
    # Lấy ngày hiện tại
    current_date = datetime.now()
    # Lấy tất cả các BookingNote cùng với các BookingNoteDetails và RentalNotes
    booking_notes = BookingNote.query.options(joinedload(BookingNote.rooms), joinedload(BookingNote.rental_notes)).all()
    # Duyệt qua từng BookingNote
    for booking_note in booking_notes:
        # Kiểm tra nếu BookingNote chưa có RentalNote
        if not booking_note.rental_notes:
            # Duyệt qua tất cả các BookingNoteDetails của BookingNote
            for booking_note_detail in booking_note.rooms[:]:
                # Kiểm tra nếu ngày checkin_date sớm hơn ngày hiện tại
                if booking_note_detail.checkin_date < current_date:
                    # Xóa BookingNoteDetail này
                    db.session.delete(booking_note_detail)
            # Kiểm tra nếu BookingNote không còn BookingNoteDetail nào
            if not booking_note.rooms:
                # Xóa BookingNote nếu không còn BookingNoteDetail nào
                db.session.delete(booking_note)
    # Commit các thay đổi vào cơ sở dữ liệu
    db.session.commit()

def create_rental_note(booking_note_id):
    id = (
        db.session.query(BookingNote)
        .filter(
            BookingNote.id == booking_note_id,
            BookingNote.rental_notes == None,
            BookingNote.created_date >= datetime.now() - timedelta(days=28)
        ).all()
    )
    if id:  # Nếu tìm thấy BookingNote
        rental_note = RentalNote(booking_note_id=id)
        db.session.add(rental_note)
        db.session.commit()
        return rental_note


def find_to_payment(customer_name, phone_number):
    bills = (
        db.session.query(BookingNote)
        .join(BookingNote.rental_notes)
        .filter(
            BookingNote.customer_name == customer_name,
            BookingNote.phone_number == phone_number,
            BookingNote.rental_notes != None,
            RentalNote.bills == None
        )
        .all()
    )
    if bills:
     return bills

def add_bill(rental_note_id):
    rental_note = (
        db.session.query(RentalNote)
        .filter(
            RentalNote.id == rental_note_id,
            RentalNote.booking_note != None,
            RentalNote.bills== None
        )
        .first()  # Dùng first() để chỉ lấy 1 kết quả duy nhất
    )
    if rental_note:
        booking_note = rental_note.booking_note
        total_cost = 0
        # Duyệt qua các chi tiết phòng trong booking_note
        for detail in booking_note.rooms:
            room = detail.room
            room_type = room.room_type
            national = booking_note.national

            # Tính số ngày ở
            num_days = (detail.checkout_date - detail.checkin_date).days
            if num_days < 1:
                num_days = 1  # Đảm bảo ít nhất 1 ngày

            # Tính tiền phòng
            if detail.number_people < room.max_people:
                room_cost = room_type.price * num_days
            else:
                room_cost = room_type.price * num_days
                room_cost += room_type.price * num_days * room_type.surcharge
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
