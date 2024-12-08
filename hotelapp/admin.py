import csv
from datetime import datetime
from io import StringIO
from hotelapp import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from hotelapp.models import RoomStatus, RoomType, Room, UserRole, National
from flask_login import current_user, logout_user
from flask import redirect, request
import utils

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
        'max_people': 'Số người tối đa'
    }

    def _format_price(view, context, model, name):
        return f"{model.room_type.price:,.1f} VND" if model.room_type else 'Lỗi'

    column_formatters = {
        'price': _format_price
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
        monthly_revenue_stats = utils.monthly_revenue_report(from_date=from_date, to_date=to_date)
        room_type_stats = utils.room_type_usage_report(from_date=from_date, to_date=to_date)

        return self.render('admin/stats.html',
                            monthly_revenue_stats=monthly_revenue_stats,
                            room_type_stats=room_type_stats)


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
