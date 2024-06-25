from flask import current_app
from flask_restful import Resource
from libs.response import response_json
from models.racio.account import AccountRole, AccountStatus
from services.racio.account_service import AccountService
from services.dify.api_service import ApiService
from . import api


class InitApi(Resource):

    def post(self):
        # 创建超级管理员
        with current_app.app_context():
            password = current_app.config.get('INIT_PASSWORD')

        num = AccountService.get_account_num(AccountRole.SUPERADMIN)
        apiService = ApiService()
        if num == 0:
            name = "admin"
            email = "admin@racio.chat"
            account = apiService.create_account(name, email)
            if account is None:
                return response_json(-1, '超级管理员创建失败')
            account_id = account['id']
            apiService.account_update_status(account['id'], AccountStatus.ACTIVE)
            racio_account = AccountService.create_account(id=account['id'], email=account['email'],
                                                          name=account['name'],
                                                          interface_language=account['interface_language'],
                                                          password=password, status=AccountStatus.ACTIVE,
                                                          account_role=AccountRole.SUPERADMIN)
            tenant = apiService.create_tenant(name, racio_account.email)
        else:
            return response_json(-1, '超级管理员已创建')
        return response_json(0, 'success')


api.add_resource(InitApi, '/init')
