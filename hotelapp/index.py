import datetime
from flask import render_template, request, redirect, url_for,jsonify
from tabnanny import check

from flask import render_template, request, redirect, url_for,session,jsonify
from hotelapp import app, login
from flask_login import login_user,logout_user,login_required
import utils
import cloudinary.uploader
from hotelapp.models import User

#Trang chủ
@app.route('/')
def home():
    rt = utils.load_room_type()
    rooms=utils.room_list()
    return render_template('index.html',roomtypes=rt,rooms=rooms)

#Tìm phòng
@app.route('/find_room',methods=['GET', 'POST'])
def find_room():
    checkin_date = request.args.get('checkin-date')  # Ngày nhận từ form
    checkout_date = request.args.get('checkout-date')  # Ngày trả từ form
    num_rooms_requested = int(request.args.get('room', 1))  # Số phòng yêu cầu (mặc định là 1)
    adults= int(request.args.get('adults',1)) #Số khách, mặc định là 1
    # Khởi tạo các biến cần thiết
    rt = utils.load_room_type()  # Tải danh sách loại phòng
    available_room_types = [] #loại phòng trống đủ điều kiện
    err_msg = None #lỗi

    # Kiểm tra nếu người dùng đã nhập ngày
    if checkin_date and checkout_date:
        try:
            # Chuyển đổi chuỗi thành datetime
            checkindate = datetime.strptime(checkin_date, '%Y-%m-%d')
            checkoutdate = datetime.strptime(checkout_date, '%Y-%m-%d')
            d_now = datetime.today()

            # Tính khoảng cách giữa các ngày
            d_in_now = (checkindate - d_now).days
            d_in_out = (checkoutdate - checkindate).days
            d_available= (checkoutdate - d_now).days
            # Ràng buộc kiểm tra ngày hợp lệ
            if d_in_now >= -1 and d_available <= 28:  # Ngày nhận không quá 28 ngày từ hôm nay
                if d_in_out >= 1:  # Ngày trả phải sau ngày nhận ít nhất 1 ngày
                    # Tìm phòng trống
                    available_room_types = utils.find_room(checkindate, checkoutdate, num_rooms_requested)
                    if not available_room_types:
                        err_msg = 'Không có phòng nào phù hợp với yêu cầu của bạn.'
                else:
                    err_msg = 'Lỗi! Ngày trả phòng phải sau ngày nhận phòng.'
            else:
                err_msg = 'Lỗi! Ngày nhận phòng phải sau ngày hôm nay và không quá 28 ngày từ hôm nay.'
        except ValueError:
            err_msg = 'Lỗi định dạng ngày tháng. Vui lòng nhập đúng định dạng.'
    else:
        err_msg = 'Lỗi! Vui lòng chọn ngày nhận và ngày trả phòng.'

    # Trả về giao diện
    return render_template(
        'find_room.html' if not err_msg else 'find_room.html',
        roomtypes=rt,
        available_room_types=available_room_types,
        err_msg=err_msg,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        num_rooms_requested=num_rooms_requested,
        adults=adults
    )
# Chọn phòng vào giỏ hàng
@app.route('/booking_room/<int:room_type_id>')
def booking_room(room_type_id):
    checkin_date = request.args.get('checkin_date')
    checkout_date = request.args.get('checkout_date')
    num_rooms_requested = int(request.args.get('num_rooms_requested',1))

    # Lấy danh sách phòng trống chi tiết theo loại
    available_rooms = utils.find_rooms_by_type_and_dates(room_type_id, checkin_date, checkout_date, num_rooms_requested)
    cart = session.get('cart', {})

    return render_template('booking_room.html',cart=cart, available_rooms=available_rooms, checkin_date=checkin_date, checkout_date=checkout_date)

@app.route('/api/add-cart',methods=['POST'])
def add_to_cart():
    data = request.json
    room_id = str(data.get('room_id'))
    checkin_date = data.get('checkin_date')
    checkout_date = data.get('checkout_date')
    action = data.get('action')
    cart= session.get('cart')
    if not cart:
        cart={}
        session['cart'] = cart

    if action == 'add':
        if room_id in cart:
            return jsonify({'error': 'Phòng này đã có trong giỏ hàng!'})
        else:
            cart[room_id] = {
                'room_id': room_id,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
            }
            session['cart'] = cart
            return jsonify({'message': 'Đã thêm phòng vào giỏ hàng!'})
    elif action == 'remove':
        if room_id in cart:  # Kiểm tra nếu phòng có trong giỏ hàng
            del cart[room_id]  # Xóa phòng khỏi giỏ hàng
            session['cart'] = cart  # Cập nhật session
            return jsonify({'message': 'Đã xóa phòng khỏi giỏ hàng!'})
        else:
            return jsonify({'error': 'Phòng này không tồn tại trong giỏ hàng!'})
    return jsonify({'error': 'Hành động không hợp lệ!'})

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    return render_template('cart.html', cart=cart)
@app.route('/clear_session')
def clear_session():
    session.clear()  # Xóa toàn bộ session
    return 'Session đã được xóa!'


#Đăng ký
@app.route('/register', methods=['GET', 'POST'])
def user_register():
    err_msg = ""
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        birthday = request.form.get('birthday')
        confirm = request.form.get('confirm')
        avatar = request.files.get('avatar')

        avatar_path = None

        try:
            existing_user = User.query.filter(User.username == username.strip()).first()

            if password.strip() == confirm.strip():
                if existing_user:
                    err_msg = 'Username đã được đăng ký, vui lòng chọn username khác.'
                else:

                    if avatar:
                        res = cloudinary.uploader.upload(avatar)
                        avatar_path = res['secure_url']

                    utils.add_user(name=name, username=username, password=password, email=email, avatar=avatar_path,
                                   birthday=birthday)
                    return redirect(url_for('user_login'))
            else:
                err_msg = 'Mật khẩu xác nhận không khớp.'

        except Exception as ex:
            err_msg = 'Hệ thống đang có lỗi: ' + str(ex)


    return render_template('register.html', err_msg=err_msg)
#Đăng nhập trang người dùng
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    err_msg = ""  # Khởi tạo thông báo lỗi

    if request.method == 'POST':  # Khi người dùng gửi form đăng nhập
        try:
            # Lấy tên đăng nhập và mật khẩu từ form
            username = request.form.get('username')
            password = request.form.get('password')

            # Gọi hàm check_login để kiểm tra người dùng
            user = utils.check_login(username=username, password=password)

            if user:  # Nếu tìm thấy người dùng
                login_user(user)  # Đăng nhập người dùng

                # Kiểm tra vai trò của người dùng
                if user.user_role.role_name == 'EMPLOYEE':
                    return redirect(url_for('employee'))
                elif user.user_role.role_name=='CUSTOMER':
                    next = request.args.get('next', 'home')
                    return redirect(url_for(next))
            else:  # Nếu không tìm thấy người dùng
                err_msg = 'Username hoặc password KHÔNG chính xác!!!'

        except Exception as ex:  # Bắt lỗi nếu có vấn đề
            err_msg = 'Hệ thống đang có lỗi: ' + str(ex)  # Thông báo lỗi hệ thống

    # Render lại trang đăng nhập với thông báo lỗi (nếu có)
    return render_template('login.html', err_msg=err_msg)


#Đăng nhập admin
@app.route('/admin_login', methods=['POST'])
def login_admin():
    username = request.form.get('username')
    password = request.form.get('password')

    user = utils.check_login(username=username,
                                 password=password,
                                 role_name="ADMIN")

    if user:
            login_user(user=user)
            return redirect('/admin')
    else:
            return redirect(url_for('login_admin'))

#Đăng xuất
@app.route('/user_logout')
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))

@app.context_processor
def common_response():
    return {
      'nationals': utils.load_nationals()
    }

#Tải thông tin người dùng
@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)



@app.route('/employee')
@login_required
def employee():
    return render_template('giaodiennhanvien.html')


#Lập phiếu thuê đã có phiếu đặt
# @app.route('/rental_note', methods=['GET', 'POST'])
# def rental_note():
#     if request.method == 'GET':
#         customer_name = request.args.get('customer-name')
#         phone_number = request.args.get('phone-number')
#         if customer_name== "ll" and phone_number=="kk":
#             u = utils.create_rental_note(5)
#             return u
#         booking_notes = utils.find_booking_note(customer_name,phone_number)
#         return render_template('lapphieuthuephong.html',booking_notes=booking_notes)
#
@app.route('/rental_note', methods=['GET', 'POST'])
def rental_note():
    message = None  # Biến lưu thông báo trạng thái
    booking_notes = []
    if request.method == 'POST':
        # Xử lý khi nhấn "Lập Phiếu Thuê"
        booking_note_id = request.form.get('bk-id')
        if booking_note_id:
            result = utils.create_rental_note(booking_note_id)
            if result:
                message = "Lập phiếu thành công!"
            else:
                message = "Lập phiếu thất bại!"
        # Cập nhật danh sách BookingNote sau khi lập phiếu
        customer_name = request.args.get('customer-name')
        phone_number = request.args.get('phone-number')
        booking_notes = utils.find_booking_note(customer_name, phone_number) or []
        booking_notes = [note for note in booking_notes if str(note.id) != booking_note_id]

    elif request.method == 'GET':
        # Xử lý tìm kiếm BookingNote
        customer_name = request.args.get('customer-name')
        phone_number = request.args.get('phone-number')
        if customer_name or phone_number:
            booking_notes = utils.find_booking_note(customer_name, phone_number) or []
            if not booking_notes:
                message = "Không tìm thấy phiếu đặt phòng nào. Vui lòng kiểm tra lại thông tin! "
    return render_template(
        'lapphieuthuephong.html',
        booking_notes=booking_notes,
        message=message
    )

if __name__ == '__main__':
    from hotelapp.admin import*
    app.run(debug=True)
