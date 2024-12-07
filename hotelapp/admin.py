import csv
from io import StringIO

from hotelapp import app,db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView,expose,AdminIndexView
from hotelapp.models import RoomStatus,RoomType,Room,UserRole
from flask_login import current_user,logout_user
from flask import redirect,request
import utils

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.role_name == 'ADMIN'

class RoomView(AuthenticatedModelView):
    column_list = ['room_address', 'room_type_name', 'price', 'status_name', 'max_people']
    column_searchable_list = ['room_address']
    column_filters = ['room_address']
    page_size = 8
    can_export = True

    column_labels = {
        'room_address': 'Địa chỉ phòng',
        'room_type_name': 'Loại phòng',
        'price': 'Giá phòng',
        'status_name': 'Trạng thái phòng',
        'max_people': 'Số người tối đa'
    }

    def _format_price(view, context, model, name):
        return f"{model.room_type.price:,.1f} VND" if model.room_type else 'Lỗi'

    def _format_room_type_name(view, context, model, name):
        return model.room_type.room_type_name if model.room_type else 'Lỗi'

    def _format_status_name(view, context, model, name):
        return model.room_status.status_name if model.room_status else 'Lỗi'


    column_formatters = {
        'price': _format_price,
        'room_type_name': _format_room_type_name,
        'status_name': _format_status_name
    }


class RoomTypeView(AuthenticatedModelView):
    column_list = ['id','room_type_name']


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
        pass
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.role_name=='ADMIN'

class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):

        return self.render('admin/index.html')
                           # stats=utils.category_stats())
admin = Admin(app, name="Hotel Administration", template_mode='bootstrap4')
admin.add_view(RoomView(Room, db.session, name="Quản lý phòng"))
admin.add_view(RoomTypeView(RoomType,db.session,name="Quản lý loại phòng"))
admin.add_view(LogoutView(name='Đăng xuất'))
