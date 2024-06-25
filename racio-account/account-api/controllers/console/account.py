from flask import request
from flask_restful import Resource, reqparse
from services.racio.account_service import AccountService
from services.dify.account_service import AccountService as Dify_AccountService
from services.dify.api_service import ApiService
from models.racio.account import AccountRole
from libs.response import response_json
from . import api


class CheckAccountApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('access_token', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()

        access_data = AccountService.get_access_code(args['access_token'])
        if not access_data:
            return response_json(-1, '未登录，请重新登录')

        account_integrate = AccountService.get_account_integrate_by_unionid(access_data['provider'], access_data['unionid'])
        exists = True
        if not account_integrate:
            exists = False
        return response_json(0, 'success', exists)


class GetTokenApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('access_token', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()

        access_data = AccountService.get_access_code(args['access_token'])
        if not access_data:
            return response_json(-1, '未登录，请重新登录')
        account_integrate = AccountService.get_account_integrate_by_unionid(access_data['provider'],
                                                                           access_data['unionid'])
        if not account_integrate:
            return response_json(-1, '未登录，请重新登录')
        account = AccountService.get_account(user_id=account_integrate.account_id)
        if not account:
            return response_json(-1, '未登录，请重新登录')
        AccountService.update_last_login(account, request)
        token = AccountService.get_account_jwt_token(account)
        account_role = Dify_AccountService.get_account_role(account)
        current_role = ""
        tenant_id = ""
        tenant_name = ""
        if account.account_role == AccountRole.SUPERADMIN:
            current_role = account.account_role
        else:
            tenant = Dify_AccountService.get_current_tenant(token, account)
            if tenant:
                current_role = tenant['role']
                tenant_id = tenant['id']
                tenant_name = tenant['name']
        AccountService.set_user_data(account_id=account.id, tenant_id=tenant_id, account_role=account_role)
        apiService = ApiService()
        dify_account = apiService.get_account(account.id)
        name = ""
        if dify_account:
            name = dify_account['name']
        data = {
            "token": token,
            "account_role": account_role,
            "current_role": current_role,
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "name": name
        }
        return response_json(0, 'success', data)


api.add_resource(CheckAccountApi, '/account/check')
api.add_resource(GetTokenApi, '/account/get_token')
