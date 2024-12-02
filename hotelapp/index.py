from flask import render_template, request, redirect, url_for
from hotelapp import app

# from flask_login import login_user
import utils
import cloudinary.uploader
=======


@app.route('/')
def home():
    return render_template('index.html')


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
            if password.strip().__eq__(confirm.strip()):
                avatar=request.files.get('avatar')
                if avatar:
                    res= cloudinary.uploader.upload(avatar)
                    avatar_path=res['secure_url']

                utils.add_user(name=name,username=username, password=password, email=email,avatar=avatar_path)
                return redirect(url_for('user_signin'))
            else:
                err_msg='Mat khau KHONG khop!!!'
        except Exception as ex:
            err_msg='He thong dang co loi: ' + str(ex)

    return render_template('register.html',err_msg=err_msg)


# @app.route('/user_login',methods=['GET','POST'])
# def user_login():
#     err_msg=""
#
#     if request.method.__eq__('POST'):
#         try:
#             username=request.form.get('username')
#             password=request.form.get('password')
#
#             user=utils.check_login(username=username,password=password)
#             if user:
#                 login_user(user=user)
#
#                 next=request.args.get('next','index')
#                 return redirect(url_for(next))
#             else:
#                 err_msg='Username hoac password KHONG chinh xac!!!'
#
#         except Exception as ex:
#                     err_msg='He thong dang co loi: ' + str(ex)
#
#         return render_template('login.html',err_msg=err_msg)



if __name__ == '__main__':
    app.run(debug=True)
