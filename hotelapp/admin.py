import csv
from datetime import datetime
from idlelib.autocomplete_w import HIDE_VIRTUAL_EVENT_NAME
from io import StringIO
from hotelapp import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from hotelapp.models import RoomStatus, RoomType, Room, UserRole, National
from flask_login import current_user, logout_user
from flask import redirect, request, current_app,url_for,flash
from flask_admin.form.upload import FileUploadField
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import cloudinary
from cloudinary.uploader import upload
from markupsafe import Markup

import utils, os


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.role_name == 'ADMIN'

# Hàm tải ảnh lên Cloudinary
def upload_latest_image(folder_path):
    latest_file = None
    latest_mtime = 0

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime > latest_mtime:
                latest_file = file_path
                latest_mtime = file_mtime

    if latest_file:
        try:
            upload_result = upload(latest_file)
            os.remove(latest_file)
            return upload_result["url"]
        except Exception as e:
            print(f"Error uploading {latest_file}: {e}")
            return None
    return None


def format_image(image_url, alt_text="Image", width=100):
    if image_url:
        return Markup(f'<img src="{image_url}" style="width: {width}px; height:auto;" alt="{alt_text}">')
    return "Không có ảnh"


class RoomView(AuthenticatedModelView):
    column_list = ['room_address', 'room_type', 'price', 'room_status', 'max_people']
    form_columns = ['room_address', 'max_people', 'image', 'room_type_id', 'room_status_id']
    column_labels = {
        'room_address': 'Địa chỉ phòng',
        'room_type': 'Loại phòng',
        'price': 'Giá phòng',
        'room_status': 'Trạng thái phòng',
        'max_people': 'Số người tối đa',
        'image': 'Ảnh phòng',
        'room_type_id': 'Mã loại phòng',
        'room_status_id': 'Mã trạng thái phòng'
    }

    # Tải ảnh mới và kiểm tra khi model thay đổi
    def on_model_change(self, form, model, is_created):
        try:
            if is_created:
                file_data = request.files.get('image')
                if not file_data or file_data.filename == '':
                    flash("Ảnh không được để trống khi tạo mới.", "error")
                    raise ValueError("Ảnh không được để trống khi tạo mới.")
            folder_path = os.path.join(app.root_path, 'static/images/rooms')
            uploaded_url = upload_latest_image(folder_path)
            if uploaded_url:
                model.image = uploaded_url
        except IntegrityError as e:
                flash("Lỗi lưu dữ liệu: Ảnh không thể để trống.", "error")
                print(f"IntegrityError: {e}")
    def format_price(view, context, model, name):
        return f"{model.room_type.price:,.1f} VND" if model.room_type else 'Lỗi'
    # Format ảnh để hiển thị
    column_formatters = {
        'price':format_price,
        'image':format_image
    }

    form_extra_fields = {
        'image': FileUploadField(
            'Ảnh phòng',
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
            base_path=os.path.join(app.root_path, 'static/images/rooms'),
        )
    }

class RoomTypeView(AuthenticatedModelView):
    column_list = ['id', 'room_type_name', 'price', 'surcharge']
    form_columns = ['room_type_name', 'price', 'surcharge', 'image']
    column_labels = {
        'id': 'Mã loại phòng',
        'room_type_name': 'Tên loại phòng',
        'price': 'Giá phòng',
        'surcharge': 'Tỷ lệ phụ thu',
        'image': 'Ảnh loại phòng'
    }

    # Tải ảnh mới và kiểm tra khi model thay đổi
    def on_model_change(self, form, model, is_created):
            try:
                if is_created:
                    file_data = request.files.get('image')
                    if not file_data or file_data.filename == '':
                        flash("Ảnh không được để trống khi tạo mới.", "error")
                        raise ValueError("Ảnh không được để trống khi tạo mới.")
                folder_path = os.path.join(app.root_path, 'static/images/roomtype')
                uploaded_url = upload_latest_image(folder_path)
                if uploaded_url:
                    model.image = uploaded_url
            except IntegrityError as e:
                flash("Lỗi lưu dữ liệu: Ảnh không thể để trống.", "error")
                print(f"IntegrityError: {e}")
    def format_price(view, context, model, name):
        return f"{model.price:,.1f} VND" if model else 'Lỗi'

    # Format ảnh để hiển thị
    column_formatters = {
        'price': format_price,
        'image': format_image
    }

    form_extra_fields = {
        'image': FileUploadField(
            'Ảnh loại phòng',
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
            base_path=os.path.join(app.root_path, 'static/images/roomtype')
        )
    }

class RegulationView(AuthenticatedModelView):
    column_list = ['id', 'country_name', 'coefficient']
    column_labels = {
        'id': 'Mã quốc gia',
        'country_name': 'Tên quốc gia',
        'coefficient': 'Hệ số giá'
    }
    form_columns = ['country_name', 'coefficient']

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('user_login'))

    def is_accessible(self):
        return current_user.is_authenticated

class StatsView(BaseView):
    @expose('/')
    def index(self):
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        month_stats, grand_cost = utils.monthly_revenue_report(from_date=from_date, to_date=to_date)
        density_stats = utils.usage_density_report(from_date=from_date, to_date=to_date)

        return self.render('admin/stats.html',
                           month_stats=month_stats,
                           grand_cost=grand_cost,
                           density_stats=density_stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.role_name == 'ADMIN'

class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

admin = Admin(app, name="Hotel Administration", template_mode='bootstrap4')
admin.add_view(RoomView(Room, db.session, name="Quản lý phòng"))
admin.add_view(RoomTypeView(RoomType, db.session, name="Quản lý loại phòng"))
admin.add_view(RegulationView(National, db.session, name="Quản lý quy định"))
admin.add_view(StatsView(name="Thống kê"))
admin.add_view(LogoutView(name='Đăng xuất'))


