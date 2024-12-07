from flask import render_template, request, redirect, url_for
from hotelapp import app, login

from flask_login import login_user,logout_user
import utils
import cloudinary.uploader

from hotelapp.models import User

#Trang chủ
@app.route('/')
def home():
    return render_template('index.html')

#Tìm phòng
@app.route('/find_room',methods=['GET','POST'])
def find_room():
     return render_template('find_room.html')

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
