import datetime
from flask import render_template, request, redirect, url_for,jsonify
from tabnanny import check

from flask import render_template, request, redirect, url_for,session,jsonify,flash
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

@app.route('/view_profile')
def view_profile():
    pass

#TÌM PHÒNG
#định dang hiển thị tiền khi in ra giao diện
@app.template_filter('format_money')
def format_money(value):
    return "{:,.0f}".format(value)
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
#tự động chọn phòng vào giỏ hàng
@app.route('/booking_room/<int:room_type_id>', methods=['GET', 'POST'])
def booking_room(room_type_id):
    checkin_date = request.args.get('checkin_date')
    checkout_date = request.args.get('checkout_date')
    num_rooms_requested = int(request.args.get('num_rooms_requested', 1))

    # Lấy danh sách phòng trống chi tiết theo loại
    available_rooms = utils.find_rooms_by_type_and_dates(room_type_id, checkin_date, checkout_date, num_rooms_requested)
    cart = session.get('cart', {})
    for room in available_rooms[:num_rooms_requested]:
        room_id = str(room.id)
        if room_id not in cart:
            cart[room_id] = {
                'room_id': room.id,
                'room_address': room.room_address,
                'room_type_id': room.room_type.id,
                'room_type_name': room.room_type.room_type_name,
                'room_price': room.room_type.price,
                'checkin_date': checkin_date,
                'checkout_date': checkout_date,
                'number_people': 1,  # Mặc định là 1 người
            }
    session['cart'] = cart

    return render_template(
        'booking_room.html',
        room_type_id=room_type_id,
        cart=cart,
        available_rooms=available_rooms,
        checkin_date=checkin_date,
        checkout_date=checkout_date
    )
#form nhập thông tin khách ở và xác nhận đặt phòng
@app.route('/confirm_booking', methods=['GET', 'POST'])
def confirm_booking():
    cart = session.get('cart', {})  # Lấy giỏ hàng từ session

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        customer_name = request.form.get('customer_name')
        phone_number = request.form.get('phone_number')
        cccd = request.form.get('cccd')
        email = request.form.get('email')
        national_id = int(request.form.get('national_id'))
        user_id= current_user.id
        # Lưu booking note và lấy id
        booking_note_id = utils.create_booking_note(customer_name, phone_number, cccd, email, national_id,user_id)

        # Lấy dữ liệu phòng từ giỏ hàng
        room_data = []
        for room_id, room in cart.items():
            number_people = int(request.form.get(f'number_people_{room_id}', 1))
            room_data.append({
                'room_id': room_id,
                'checkin_date': room['checkin_date'],
                'checkout_date': room['checkout_date'],
                'number_people': number_people
            })

        # Lưu booking note details
        utils.create_booking_note_details(room_data, booking_note_id)

        # Xóa giỏ hàng và hiển thị thông báo thành công
        session.pop('cart', None)
        flash('Đặt phòng thành công!', 'success')
        return redirect(url_for('confirm_booking'))

    return render_template('confirm_booking.html', cart=cart)

#cập nhật lại số khách ở và tính tạm tiền phòng
@app.route('/api/calculate_room_price', methods=['POST'])
def calculate_room_price():
    try:
        data = request.get_json()
        room_id = data['room_id']
        number_people = data['number_people']

        room_data = session['cart'].get(room_id)

        if not room_data:
            return jsonify({'error': 'Room not found in cart'}), 400

        # Lấy giá phòng và số ngày ở
        room_price = room_data['room_price']
        checkin_date = room_data['checkin_date']
        checkout_date = room_data['checkout_date']

        # Tính số ngày ở
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        num_days = (checkout - checkin).days

        # Áp dụng logic giá phòng nhân với 1.25 nếu số người là 3
        if number_people == 3:
            room_price *= 1.25

        room_total_price = room_price * num_days

        # Cập nhật lại tổng tiền cho phòng trong giỏ hàng
        room_data['total_price'] = room_total_price

        # Cập nhật giỏ hàng vào session
        session.modified = True

        return jsonify({'status': 'success', 'room_total_price': room_total_price})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

#tính tạm tổng tiền phòng cho khách xem
@app.route('/api/calculate_total_price', methods=['POST'])
def calculate_total_price():
    try:
        total_cost = 0

        if 'cart' not in session:
            return jsonify({'error': 'No rooms in cart'}), 400

        # Duyệt qua các phòng trong giỏ hàng để tính toán giá
        for room_id, room_data in session['cart'].items():
            room_total_price = room_data.get('total_price', 0)
            total_cost += room_total_price

        # Lấy tỷ lệ hệ số quốc tịch
        national_coefficient = float(request.json.get('national_coefficient', 1.0))

        # Áp dụng hệ số quốc tịch nếu cần
        if national_coefficient == 2:
            total_cost *= 1.5  # Nếu quốc tịch là "Khác", áp dụng hệ số 1.5
        # Trả lại kết quả cho client
        return jsonify({
            'total_cost': total_cost
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    return render_template('cart.html', cart=cart)
#xóa session và trở về find_room.html
@app.route('/clear_session')
def clear_session():
    checkin_date = request.args.get('checkin_date')
    checkout_date = request.args.get('checkout_date')
    num_rooms_requested = int(request.args.get('num_rooms_requested', 1))
    session.pop('cart', None)  # Xóa toàn bộ session
    return redirect(url_for('find_room',checkin_date=checkin_date, checkout_date=checkout_date,num_rooms_requested=num_rooms_requested))


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
    err_msg = ""

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
                elif user.user_role.role_name=='ADMIN':
                    return redirect('/admin')
                elif user.user_role.role_name=='CUSTOMER':
                    next = request.args.get('next')
                    if next:
                        return redirect(next)  # Nếu có 'next' thì chuyển hướng tới trang đó
                    return redirect(url_for('home'))  # Nếu không có 'next' thì chuyển hướng về trang home
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
