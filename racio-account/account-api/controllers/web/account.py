import base64
import logging
import secrets
from flask_login import current_user
from libs.login import login_required
from libs.password import hash_password
from extensions.ext_database import db
from services.racio.account_service import AccountService
from models.racio.account import Account, AccountRole
from flask_restful import Resource, reqparse, inputs, marshal
from libs.password import valid_password
from libs.response import response_json
from . import api
from libs.password import compare_password
from services.dify.api_service import ApiService
from fields.app_fields import (
    account_pagination_fields,
)


class AccountListApi(Resource):

    @login_required
    def post(self):
        """Get account list"""
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=inputs.int_range(1, 99999), required=False, default=1, location='json')
        parser.add_argument('limit', type=inputs.int_range(1, 100), required=False, default=20, location='json')
        # parser.add_argument('keyword', type=str, required=False, location='json')
        args = parser.parse_args()

        user_data = AccountService.get_user_data(current_user.id)
        if user_data['account_role'] != AccountRole.SUPERADMIN:
            return response_json(-1, '无权访问')
        # get account list
        apiService = ApiService()
        account_pagination = apiService.get_all_account(args['page'], args['limit'])
        if not account_pagination:
            data = {'data': [], 'total': 0, 'page': 1, 'limit': 20, 'has_more': False}
            return response_json(0, 'success', data)

        for account in account_pagination['data']:
            phone = ''
            status = ''
            last_login_at = ''
            last_login_ip = ''
            racio_account = AccountService.get_account(account['id'])
            if racio_account:
                phone = racio_account.phone
                status = racio_account.status
                last_login_at = int(racio_account.last_login_at.timestamp())
                last_login_ip = racio_account.last_login_ip
            tenants = apiService.get_all_tenant(account['id'])
            tenant_names = []
            if tenants:
                for tenant in tenants:
                    tenant_names.append(tenant['name'])
            nickname = ''
            headimgurl = ''
            account_integrate = AccountService.get_account_integrate_by_account_id(provider='wx', account_id=account['id'])
            if account_integrate:
                nickname = account_integrate.nickname
                headimgurl = account_integrate.headimgurl

            account['tenant_names'] = tenant_names
            account['phone'] = phone
            account['status'] = status
            account['nickname'] = nickname
            account['headimgurl'] = headimgurl
            account['last_login_at'] = last_login_at
            account['last_login_ip'] = last_login_ip

        return response_json(0, 'success', account_pagination)


# class AccountInviteEmailApi(Resource):
#     """Invite a new member by email."""
#
#     @login_required
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('email', type=str, required=False, location='json')
#         parser.add_argument('domain', type=str, required=True, location='json', default='')
#         parser.add_argument('role', type=str, required=True, location='json', default='')
#         # parser.add_argument('tenant_id', type=str, required=True, location='json', default='')
#         args = parser.parse_args()
#
#         if current_user.account_role == AccountRole.SUPERADMIN:
#             if args['role'] != AccountRole.OWNER:
#                 response_json(-1, '超级管理员只能邀请空间所有者')
#         else:
#             if current_user.account_role == AccountRole.OWNER:
#                 if args['role'] == AccountRole.OWNER:
#                     response_json(-1, '空间所有者不能邀请空间所有者')
#
#             if current_user.account_role == AccountRole.ADMIN:
#                 if args['role'] != AccountRole.NORMAL:
#                     response_json(-1, '管理员只能邀请普通用户')
#
#         invitee_email = ''
#         send_flag = True
#         if args['email'] != '':
#             invitee_email = email(args['email'])
#
#         if invitee_email == '':
#             send_flag = False
#             for i in range(10):
#                 invitee_email = str(random.randint(100000000, 999999999))+"@"+args['domain']
#                 account = Account.query.filter_by(email=invitee_email).first()
#                 if not account:
#                     break
#
#         invitation_result = {}
#         console_web_url = current_app.config.get("CONSOLE_WEB_URL")
#         try:
#             token = AccountService.invite_new_member(g.current_tenant_id, invitee_email,
#                                                      role=args['role'], send_flag=send_flag)
#             invitation_result = {
#                 'status': 'success',
#                 'email': invitee_email,
#                 'url': f'{console_web_url}/activate?email={invitee_email}&token={token}'
#             }
#         except AccountAlreadyInTenantError:
#             invitation_result = {
#                 'status': 'success',
#                 'email': invitee_email,
#                 'url': f'{console_web_url}/signin'
#             }
#         except Exception as e:
#             invitation_result = {
#                 'status': 'failed',
#                 'email': invitee_email,
#                 'message': str(e)
#             }
#         return response_json(0, 'success', invitation_result)


class UpdatePwdApi(Resource):

    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('old_pwd', type=valid_password, required=True, location='json')
        parser.add_argument('new_pwd', type=valid_password, required=True, location='json')
        args = parser.parse_args()

        user_data = AccountService.get_user_data(current_user.id)

        if user_data['account_role'] != AccountRole.SUPERADMIN:
            return response_json(-1, '无权访问')

        if current_user.password is None or not compare_password(args['old_pwd'], current_user.password, current_user.password_salt):
            return response_json(-1, '旧密码错误')

        account = Account.query.filter_by(id=current_user.id).first()

        # generate password salt
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # encrypt password with salt
        password_hashed = hash_password(args['new_pwd'], salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        account.password = base64_password_hashed
        account.password_salt = base64_salt

        db.session.commit()

        return response_json(0, 'success')



api.add_resource(AccountListApi, '/accounts')
# api.add_resource(AccountInviteEmailApi, '/accounts/invite-email')
api.add_resource(UpdatePwdApi, '/accounts/update_pwd')
