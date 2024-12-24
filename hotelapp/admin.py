import csv
import hashlib
from datetime import datetime
from idlelib.autocomplete_w import HIDE_VIRTUAL_EVENT_NAME
from io import StringIO
from hotelapp import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from hotelapp.models import RoomType, Room, UserRole,User, National
from flask_login import current_user, logout_user
from flask import redirect, request, current_app,url_for,flash
from flask_admin.form.upload import FileUploadField
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
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


class RoomTypePriceFilter(BaseSQLAFilter):
    def __init__(self, column, label, filter_op='='):
        super().__init__(column, label)
        self.operations = {
            ">": "lớn hơn",
            "<": "nhỏ hơn",
            ">=": "lớn hơn hoặc bằng",
            "<=": "nhỏ hơn hoặc bằng",
            "ASC": "tăng dần",
            "DESC": "giảm dần",
        }
        self.filter_op = filter_op

    def apply(self, query, value, alias=None):
        # Apply filter operation first
        if self.filter_op == ">":
            query = query.filter(RoomType.price > value)
        elif self.filter_op == "<":
            query = query.filter(RoomType.price < value)
        elif self.filter_op == ">=":
            query = query.filter(RoomType.price >= value)
        elif self.filter_op == "<=":
            query = query.filter(RoomType.price <= value)

        # Then, apply sorting operation if present
        if self.filter_op == "ASC":
            query = query.order_by(RoomType.price.asc())
        elif self.filter_op == "DESC":
            query = query.order_by(RoomType.price.desc())

        return query

    def operation(self):
        # Return the operation name for UI
        return self.operations.get(self.filter_op, 'Lỗi')


class RoomView(AuthenticatedModelView):
    column_list = ['room_address', 'room_type', 'price', 'max_people']
    form_columns = ['room_address', 'max_people', 'image', 'room_type_id']
    column_labels = {
        'room_address': 'Địa chỉ phòng',
        'room_type': 'Loại phòng',
        'price': 'Giá phòng',
        'max_people': 'Số người tối đa',
        'image': 'Ảnh phòng',
        'room_type_id': 'Mã loại phòng',
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
    # Format giá phòng
    def format_price(view, context, model, name):
        if model.room_type_id:
            room_type = RoomType.query.get(model.room_type_id)
            if room_type:
                return f"{room_type.price:,.1f} VND"
        return 'Lỗi'

    # Format ảnh để hiển thị
    column_formatters = {
        'price': format_price,
        'image': format_image
    }

    column_searchable_list = ['room_address']

    column_filters = [
        'room_address',
        RoomTypePriceFilter(RoomType.price, 'Giá phòng', filter_op='>'),
        RoomTypePriceFilter(RoomType.price, 'Giá phòng', filter_op='<'),
        RoomTypePriceFilter(RoomType.price, 'Giá phòng', filter_op='ASC'),
        RoomTypePriceFilter(RoomType.price, 'Giá phòng', filter_op='DESC'),
    ]


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
    column_searchable_list = ['room_type_name','surcharge']
    column_filters = ['room_type_name','price']
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
    column_searchable_list = ['country_name', 'coefficient']
    form_columns = ['country_name', 'coefficient']

class EmployeeAccountView(AuthenticatedModelView):
    column_list = ['id', 'username', 'name', 'email', 'user_role_id']
    form_columns = ['username', 'name', 'email', 'password', 'birthday', 'user_role_id']

    column_labels = {
        'id': 'Mã nhân viên',
        'username': 'Tên đăng nhập',
        'name': 'Họ và tên',
        'email': 'Email',
        'birthday': 'Ngày sinh',
        'user_role_id':'Vai Trò'
    }

    # Tự động điền thông tin cho form khi chỉnh sửa
    def _on_form_prefill(self, form, id):
        user = User.query.get(id)
        if user:
            form.user_role_id.data = user.user_role_id
            form.password.data = ""

    def on_model_change(self, form, model, is_created):
        if model.password:
            # Băm mật khẩu bằng MD5 trước khi lưu
            model.password = hashlib.md5(model.password.strip().encode('utf-8')).hexdigest()

    def on_model_delete(self, model):
        flash(f"Đã xóa tài khoản nhân viên: {model.username}", "success")

    # Tìm kiếm theo các trường
    column_searchable_list = ['username', 'email', 'name']

    # Thêm bộ lọc vào các cột
    column_filters = ['username', 'email', 'user_role_id']

    # Khi cập nhật người dùng, nếu mật khẩu để trống thì giữ mật khẩu cũ
    def _after_model_change(self, form, model, is_created):
        if not is_created:
            if not form.password.data:
                # Giữ mật khẩu cũ nếu không thay đổi mật khẩu
                pass
            else:
                # Nếu có mật khẩu mới, băm mật khẩu mới và cập nhật
                model.password = hashlib.md5(form.password.data.strip().encode('utf-8')).hexdigest()

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('user_login'))


class StatsView(BaseView):
    @expose('/')
    def index(self):
        # Lấy các tham số từ URL (các tham số năm và loại phòng)
        year = request.args.get('year', default=datetime.now().year, type=int)
        room_type_id = request.args.get('room_type_id', default=None, type=int)
        room_types = RoomType.query.all()

        # Lấy thông tin doanh thu theo tháng
        month_stats, grand_cost = utils.monthly_revenue_report(year=year, room_type_id=room_type_id)

        # Lấy thông tin mật độ sử dụng phòng theo tháng
        density_stats = utils.usage_density_report(year=year, room_type_id=room_type_id)



        # Trả về template nếu không phải AJAX
        return self.render('admin/stats.html',
                           month_stats=month_stats,
                           grand_cost=grand_cost,
                           density_stats=density_stats,
                           room_types=room_types,
                           year=year,
                           room_type_id=room_type_id)
class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

admin = Admin(app, name="Hotel Administration", template_mode='bootstrap4')
admin.add_view(RoomView(Room, db.session, name="Quản lý phòng"))
admin.add_view(RoomTypeView(RoomType, db.session, name="Quản lý loại phòng"))
admin.add_view(RegulationView(National, db.session, name="Quản lý quy định"))
admin.add_view(EmployeeAccountView(User, db.session, name="Quản lý tài khoản"))
admin.add_view(StatsView(name="Thống kê báo cáo"))
admin.add_view(LogoutView(name='Đăng xuất'))


