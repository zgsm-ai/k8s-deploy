import os

from flask_admin import expose, BaseView

from common.helpers.application_context import ApplicationContext


class AdminPermission(BaseView):
    INDEX_PAGE = 'admin/index.html'
    FORBID_PAGE = 'admin/forbidden.html'

    def is_accessible(self):
        from services.system.users_service import UsersService
        username = ApplicationContext.get_current_username()
        # 测试或者开发环境使用
        _env = os.environ.get("FLASK_ENV")
        if not username and (_env == 'development' or _env == 'test'):
            user = UsersService().create_test_user()
            ApplicationContext.update_session_user(user)
            username = ApplicationContext.get_current_username()

        current_user = UsersService().get_by_username(username)
        if current_user and current_user.is_admin:
            return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return self.render(self.FORBID_PAGE)


class AdminIndexView(AdminPermission):

    def __init__(self):
        super(AdminIndexView, self).__init__(name='主页', endpoint='admin', url='/admin/', static_folder='static')

    @expose()
    def index(self):
        return self.render(self.INDEX_PAGE)
