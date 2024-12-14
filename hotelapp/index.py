import datetime

from flask import render_template, request, redirect, url_for,flash
from hotelapp import app, login
from flask_login import login_user,logout_user
import utils
import cloudinary.uploader

from hotelapp.models import User

#Trang chủ
@app.route('/')
def home():
    rt = utils.load_room_type()
    rooms=utils.room_list()
    return render_template('index.html',roomtypes=rt,rooms=rooms)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        flash("Không có tệp hình ảnh nào được chọn.", "error")
        return redirect(request.url)

    file = request.files['image']
    if file.filename == '':
        flash("Tệp không có tên.", "error")
        return redirect(request.url)

    if file:
        try:
            # Tải lên Cloudinary
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url']
            flash("Tải ảnh lên thành công!", "success")
            # Cập nhật vào cơ sở dữ liệu hoặc thực hiện thao tác khác
            return redirect('/success')
        except Exception as e:
            flash(f"Lỗi tải ảnh lên: {str(e)}", "error")
            return redirect(request.url)
#Tìm phòng
@app.route('/find_room')
def find_room():
    checkin_date = request.args.get('checkin-date')  # Ngày nhận từ form
    checkout_date = request.args.get('checkout-date')  # Ngày trả từ form
    num_rooms_requested = int(request.args.get('room', 1))  # Số phòng yêu cầu (mặc định là 1)
    adults= int(request.args.get('adults',1)) #Số khách, mặc định là 1
    # Khởi tạo các biến cần thiết
    rt = utils.load_room_type()  # Tải danh sách loại phòng
    available_rooms = []  # Danh sách phòng trống
    err_msg = None  # Thông báo lỗi

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
            if d_in_now >= 0 and d_available <= 28:  # Ngày nhận không quá 28 ngày từ hôm nay
                if d_in_out >= 1:  # Ngày trả phải sau ngày nhận ít nhất 1 ngày
                    # Tìm phòng trống
                    available_rooms = utils.find_room(checkindate, checkoutdate, num_rooms_requested)
                    if not available_rooms:
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
        available_rooms=available_rooms,
        err_msg=err_msg,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        num_rooms_requested=num_rooms_requested,
        adults=adults
    )

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
        national_id = request.form.get('national_id')
        confirm = request.form.get('confirm')
        avatar = request.files.get('avatar')

        avatar_path = None

        try:
            existing_user = User.query.filter(User.username == username.strip()).first()

            if password.strip() == confirm.strip():
                if existing_user:
                    err_msg = 'Username đã được đăng ký, vui lòng chọn username khác.'
                elif not national_id:
                    err_msg = 'Vui lòng chọn quốc tịch.'
                else:

                    if avatar:
                        res = cloudinary.uploader.upload(avatar)
                        avatar_path = res['secure_url']

                    utils.add_user(name=name, username=username, password=password, email=email, avatar=avatar_path,
                                   birthday=birthday, national_id=national_id)
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

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            user = utils.check_login(username=username, password=password)
            if user:
                login_user(user)
                next = request.args.get('next', 'home')
                return redirect(url_for(next))
            else:
                err_msg = 'Username hoặc password KHÔNG chính xác!!!'

        except Exception as ex:
            err_msg = 'Hệ thống đang có lỗi: ' + str(ex)

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

if __name__ == '__main__':
    from hotelapp.admin import*
    app.run(debug=True)
