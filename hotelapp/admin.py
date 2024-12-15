import csv
from datetime import datetime
from io import StringIO
from hotelapp import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from hotelapp.models import RoomStatus, RoomType, Room, UserRole, National
from flask_login import current_user, logout_user
from flask import redirect, request, current_app,flash
from flask_admin.form.upload import FileUploadField
from werkzeug.utils import secure_filename
import cloudinary
from cloudinary.uploader import upload
from markupsafe import Markup
import utils, os


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.role_name == 'ADMIN'

class RoomView(AuthenticatedModelView):
    column_list = ['room_address', 'room_type', 'price', 'room_status', 'max_people']
    form_columns = ['room_address', 'max_people', 'image', 'room_type_id', 'room_status_id']
    column_searchable_list = ['room_address']
    column_filters = ['room_address']
    page_size = 8
    can_export = True

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

    def on_model_change(self, form, model, is_created):
        file_data = request.files.get('image')

        # Kiểm tra khi tạo mới mà không có ảnh
        if is_created and not file_data:
            flash("Ảnh không được để trống.", "error")
            print("Ảnh không được để trống.")
            return

        self.upload_image(form)
    def _format_image(view, context, model, name):
        if model.image:
            return Markup(f'<img src="{model.image}" style="width: 100px;height:auto;" alt="Room Image">')
        return 'Không có ảnh'

    form_extra_fields = {
        'image': FileUploadField(
            'Ảnh phòng',
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
            base_path=os.path.join(app.root_path, 'static/images/rooms'),
            render_kw={'required': True}  # Đảm bảo trường ảnh là bắt buộc
        )
    }

    def upload_image(self, form):
        # Đường dẫn tới thư mục chứa ảnh
        folder_path = 'static/images/rooms'

        # Tìm tệp mới nhất trong thư mục
        latest_file = None
        latest_mtime = 0  # Thời gian chỉnh sửa tệp lớn nhất (lúc gần nhất)

        # Duyệt tất cả các tệp trong thư mục và tìm tệp mới nhất
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            # Kiểm tra xem tệp có phải là ảnh không
            if os.path.isfile(file_path) and filename.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
                # Lấy thời gian chỉnh sửa của tệp
                file_mtime = os.path.getmtime(file_path)

                # Cập nhật tệp mới nhất nếu thời gian chỉnh sửa mới hơn
                if file_mtime > latest_mtime:
                    latest_file = file_path
                    latest_mtime = file_mtime

        if latest_file:
            try:
                # Tải ảnh mới nhất lên Cloudinary
                upload_result = cloudinary.uploader.upload(latest_file)
                print(f'Uploaded {os.path.basename(latest_file)} to Cloudinary with URL: {upload_result["url"]}')
                os.remove(latest_file)
                print(f"Đã xóa tệp {os.path.basename(latest_file)} khỏi thư mục.")

            except Exception as e:
                print(f'Error uploading {latest_file}: {e}')
        else:
            print("Không có ảnh nào trong thư mục.")

    def _format_price(view, context, model, name):
        return f"{model.room_type.price:,.1f} VND" if model.room_type else 'Lỗi'

    column_formatters = {
        'price': _format_price,
        'image': _format_image
    }


class RoomTypeView(AuthenticatedModelView):
    column_list = ['id', 'room_type_name', 'price', 'surcharge']
    form_columns = ['room_type_name', 'price', 'surcharge']
    column_labels = {
        'id': 'Mã loại phòng',
        'room_type_name': 'Tên loại phòng',
        'price': 'Giá phòng',
        'surcharge': 'Tỷ lệ phụ thu'
    }

    def _format_price(view, context, model, name):
        return f"{model.price:,.1f} VND" if model else 'Lỗi'

    column_formatters = {
        'price': _format_price
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
        return redirect('/admin')

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


