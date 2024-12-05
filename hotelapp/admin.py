
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
        return current_user.is_authenticated and current_user.user_role.role_name=='ADMIN'


class RoomView(AuthenticatedModelView):
    pass

class RegulationView(AuthenticatedModelView):
    pass

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
                            # ,stats=utils.category_stats())



admin = Admin(app,
                name="Hotel Administration",
                template_mode='bootstrap4',
                index_view=MyAdminIndex())
admin.add_view(RoomView(Room,db.session))
# admin.add_view(Regulation,db.session))
admin.add_view(StatsView(name="Stats"))
admin.add_view(LogoutView(name='Đăng xuất'))
