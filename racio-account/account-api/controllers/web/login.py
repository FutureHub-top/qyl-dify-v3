import flask_login
from services.errors.account import AccountLoginError
from flask import request
from flask_restful import Resource, reqparse
from libs.password import valid_password
from libs.response import response_json
from services.racio.account_service import AccountService
from . import api

class LoginApi(Resource):
    """Resource for user login."""

    def post(self):
        """Authenticate user and login."""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, location='json')
        parser.add_argument('password', type=valid_password, required=True, location='json')
        parser.add_argument('remember_me', type=bool, required=False, default=False, location='json')
        args = parser.parse_args()

        try:
            account = AccountService.authenticate(args['username'], args['password'])
        except AccountLoginError as e:
            return response_json(-1, '用户名或密码错误')
            # return {'code': 'unauthorized', 'message': str(e)}, 401

        AccountService.update_last_login(account, request)

        token = AccountService.get_account_jwt_token(account)
        AccountService.set_user_data(account_id=account.id, account_role=account.account_role)
        return response_json(0, 'success', token)


class LogoutApi(Resource):

    def get(self):
        flask_login.logout_user()
        return response_json(0, 'success')


api.add_resource(LoginApi, '/login')
api.add_resource(LogoutApi, '/logout')
