from flask import render_template, request, redirect, url_for
from hotelapp import app, login

from flask_login import login_user,logout_user
import utils
import cloudinary.uploader

from hotelapp.models import User


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/find_room',methods=['GET','POST'])
def find_room():
     return render_template('find_room.html')


@app.route('/register',methods=['GET','POST'])
def user_register():
    err_msg=""
    if request.method.__eq__('POST'):
        name=request.form.get('name')
        username=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')
        confirm=request.form.get('confirm')
        avatar=request.form.get('avatar')
        avatar_path=None

        try:
            existing_user = User.query.filter(User.username == username.strip()).first()

            if password.strip().__eq__(confirm.strip()) and not existing_user:
                avatar=request.files.get('avatar')
                if avatar:
                    res= cloudinary.uploader.upload(avatar)
                    avatar_path=res['secure_url']

                utils.add_user(name=name,username=username, password=password, email=email,avatar=avatar_path)
                return redirect(url_for('user_login'))
            else:
                err_msg='Mat khau KHONG khop!!!'
                err_msg="Username đã được đăng ký, vui lòng chọn username khác."
        except Exception as ex:
            err_msg='He thong dang co loi: ' + str(ex)

    return render_template('register.html',err_msg=err_msg)

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

@app.route('/admin_login',methods=['POST'])
def login_admin():
            username = request.form.get('username')
            password = request.form.get('password')

            user = utils.check_login(username=username,
                                     password=password,
                                     role=User_role.ADMIN)
            if user:
                login_user(user=user)

            return redirect('/admin')



@app.route('/user_logout')
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


if __name__ == '__main__':
    from hotelapp.admin import*
    app.run(debug=True)
