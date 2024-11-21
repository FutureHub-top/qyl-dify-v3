import logging
import random

from flask import request
from flask_restful import Resource, reqparse
from libs.helper import uuid_value
from libs.response import response_json, response_json_v2

from services.racio.account_service import AccountService
from services.dify.api_service import ApiService
from services.dify.account_service import AccountService as Dify_AccountService

from models.racio.account import Account, AccountRole, AccountStatus
from . import api


class ActivateCheckApi(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=uuid_value, required=True, default='', location='args')
        args = parser.parse_args()

        # get invitation_data and tenant by token (MemberInvite id)
        invitation = AccountService.get_invitation_if_token_valid_v2(args['token'])

        tenant = None
        tenant_name = ""
        role = ""
        is_valid = False

        if invitation:
            if invitation['tenant']:
                tenant = invitation['tenant']
                tenant_name = tenant['name']
            
            if invitation['is_valid']:
                is_valid = True

            member_invite = invitation['data']
            role = member_invite.role

        data = {
            'is_valid': is_valid,
            'tenant': tenant,
            'workspace_name': tenant_name if invitation else "",
            'role': role
        }
        return response_json_v2(data, message='Checked invitation successfully')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=uuid_value, required=True, nullable=False, location='json')
        args = parser.parse_args()

        # get invitation_data and tenant by token (MemberInvite id)
        invitation = AccountService.get_invitation_if_token_valid(args['token'])

        tenant_name = ""
        role = ""

        if invitation:
            if invitation['tenant']:
                tenant = invitation['tenant']
                tenant_name = tenant['name']

            member_invite = invitation['data']
            role = member_invite.role

        data = {'is_valid': invitation is not None, 'workspace_name': tenant_name if invitation else "", 'role': role}
        return response_json(0, 'Success [Deprecated]', data)


class ActivateApi(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=uuid_value, required=True, nullable=False, location='json')
        # parser.add_argument('name', type=str_len(30), required=True, nullable=False, location='json')
        # parser.add_argument('password', type=valid_password, required=True, nullable=False, location='json')
        # parser.add_argument('interface_language', type=supported_language, required=True, nullable=False,location='json')
        # parser.add_argument('timezone', type=timezone, required=True, nullable=False, location='json')
        parser.add_argument('phone', type=str, required=True, nullable=True, location='json')
        # parser.add_argument('provider', type=str, required=True, nullable=False, location='json', default='wx')
        parser.add_argument('access_token', type=str, required=True, nullable=False, location='json', default='')
        parser.add_argument('code', type=str, required=True, nullable=True, location='json')
        parser.add_argument('tenant_name', type=str, required=True, nullable=True, location='json')
        args = parser.parse_args()

        # logging.info(args)

        # 获取登录unionid
        access_data = AccountService.get_access_code(args['access_token'])
        if not access_data:
            return response_json(-1, '无授权信息，请重新登录授权')

        # logging.info(access_data)
        account_integrate = AccountService.get_account_integrate_by_unionid(access_data['provider'], access_data['unionid'])

        if not account_integrate:
            verify_data = AccountService.get_verify_code(args['token'], args['phone'])
            logging.info('ActivateApi.post.verify_data: {}, token: {}'.format(verify_data, args['token']))
            if not verify_data:
                return response_json(-1, '验证码已过期')

            if verify_data['phone'] != args['phone']:
                return response_json(-1, '验证手机号不正确')

            if verify_data['code'] != args['code']:
                return response_json(-1, '验证码不正确')

            AccountService.revoke_verify_code(args['token'], args['phone'])
            logging.info('ActivateApi.post.revoke_verify_code: - token: {}, phone: {}'.format(args['token'], args['phone']))

        # get invitation_data and tenant by token (MemberInvite id)
        invitation = AccountService.get_invitation_if_token_valid(args['token'])
        if not invitation:
            return response_json(-1, '该邀请已被使用')
        member_invite = invitation['data']
        tenant_id = member_invite.tenant_id
        tenant_name = ""
        if invitation['tenant']:
            tenant = invitation['tenant']
            tenant_name = tenant['name']

        apiService = ApiService()
        # 判断被邀请用户是否存在
        account_id = ''
        if not account_integrate:
            name = ''
            email = ''
            # 创建账号
            for i in range(10):
                name = str(random.randint(100000000, 999999999))
                email = name + "@" + member_invite.domain
                account = Account.query.filter_by(email=email).first()
                if not account:
                    break
            account = apiService.create_account(access_data['nickname'], email)
            if not account:
                return response_json(-1, '激活失败，请重新提交激活')
            account_id = account['id']
            apiService.account_update_status(account['id'], AccountStatus.ACTIVE)
            racio_account = AccountService.create_account(id=account['id'], 
                                                          email=account['email'],
                                                          name=access_data['nickname'],
                                                          interface_language=account['interface_language'],
                                                          phone=args['phone'], 
                                                          status=AccountStatus.ACTIVE)

            apiService.link_account_integrate(access_data['provider'], access_data['open_id'], account_id)
            AccountService.link_account_integrate(access_data['provider'], access_data['open_id'], access_data['nickname'], access_data['headimgurl'], access_data['unionid'], racio_account)
        else:
            account_id = account_integrate.account_id
            racio_account = AccountService.get_account(account_id)

        if member_invite.role == AccountRole.OWNER:
            if args['tenant_name'] == '':
                return response_json(-1, '请填写空间名')
            if len(args['tenant_name']) < 3 or len(args['tenant_name']) > 12:
                return response_json(-1, '请输入3到12个字符作为空间名')
            # 判断是否已创建owner空间
            is_exists = Dify_AccountService.check_owner_exists(account_id, AccountRole.OWNER)
            if is_exists:
                return response_json(-1, '该账号已创建空间，不能重复创建')
            # 创建空间
            tenant = apiService.create_tenant(args['tenant_name'], racio_account.email)
            tenant_id = tenant['id']
            tenant_name = args['tenant_name']
        else:
            # 加入空间
            # 判断该用户是否加入了同一个空间
            is_exists = Dify_AccountService.check_account_join_exists(tenant_id, account_id)
            if is_exists:
                return response_json(-1, '不能重复加入同一个空间')
            apiService.create_tenant_member(tenant_id, account_id, member_invite.role)

        AccountService.delete_member_invite(args['token'])
        AccountService.update_last_login(racio_account, request)
        token = AccountService.get_account_jwt_token(racio_account)

        # 切换用户空间
        Dify_AccountService.switch_tenant(token, tenant_id)

        AccountService.set_user_data(account_id=account_id, tenant_id=tenant_id,
                                     account_role=member_invite.role)
        data = {
            "token": token,
            "account_role": member_invite.role,
            "current_role": member_invite.role,
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "name": access_data['nickname']
        }
        return response_json(0, 'success', data)


class TenantCreateCheckApi(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=uuid_value, required=True, default='', location='args')
        parser.add_argument('access_token', type=str, required=True, default='', location='args')
        args = parser.parse_args()

        # get invitation entity by token (MemberInvite id)
        tenant = None
        tenant_id = ""
        tenant_name = ""
        account_role = ""
        is_valid_invitation = False

        invitation = AccountService.get_invitation_if_token_valid_v2(args['token'])
        logging.info('TenantCreateCheckApi.get.invitation: {}'.format(invitation))
        if invitation:
            if invitation['tenant']:
                tenant = invitation['tenant']
                tenant_name = tenant['name']
            
            if invitation['is_valid']:
                is_valid_invitation = True

            member_invite = invitation['data']
            tenant_id = member_invite.tenant_id
            account_role = member_invite.role

        # # get tenant_id and tenant_name
        # member_invite = invitation['data']
        # tenant_id = member_invite.tenant_id
        # account_role = member_invite.role

        # if invitation['tenant']:
        #     tenant = invitation['tenant']
        #     tenant_name = tenant['name']

        # get WeChat login UnionId
        # - https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/union-id.html

        nickname = ""
        account_id = ""
        is_tenant_owner = False
        is_joined_tenant = False

        access_data = AccountService.get_access_code(args['access_token'])
        # if not access_data:
        #     return response_json(-1, '无授权信息，请重新登录授权')

        if access_data:
            # logging.info(access_data)
            nickname = access_data['nickname']

            account_integrate = AccountService.get_account_integrate_by_unionid(access_data['provider'], access_data['unionid'])
            logging.info('TenantCreateCheckApi.get.account_integrate: {}'.format(account_integrate))
            # 判断被邀请用户是否存在
            if account_integrate:
                account_id = account_integrate.account_id
                if account_role == AccountRole.OWNER:
                    # 判断是否已创建owner空间
                    is_exists = Dify_AccountService.check_owner_exists(account_id, AccountRole.OWNER)
                    if is_exists:
                        is_tenant_owner = True
                        is_joined_tenant = True
                else:
                    # 判断该用户是否加入了同一个空间
                    is_exists = Dify_AccountService.check_account_join_exists(tenant_id, account_id)
                    if is_exists:
                        is_joined_tenant = True

        data = {
            "nickname": nickname,
            "account_id": account_id,
            "account_role": account_role,
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "is_tenant_owner": is_tenant_owner,  # renamed has_owner_tenant to is_tenant_owner
            "is_joined_tenant": is_joined_tenant,
            "is_valid_invitation": is_valid_invitation
        }

        return response_json_v2(data, message='Checked invitation successfully')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=uuid_value, required=True, nullable=False, location='json')
        parser.add_argument('access_token', type=str, required=True, nullable=False, location='json', default='')
        args = parser.parse_args()

        # get invitation_data by token (MemberInvite id)
        invitation = AccountService.get_invitation_if_token_valid(args['token'])
        if not invitation:
            return response_json(-1, '该邀请已被使用')

        # get tenant_id and tenant_name
        member_invite = invitation['data']
        tenant_id = member_invite.tenant_id
        account_role = member_invite.role
        tenant_name = ""
        if invitation['tenant']:
            tenant = invitation['tenant']
            tenant_name = tenant['name']

        # get WeChat login UnionId - https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/union-id.html
        access_data = AccountService.get_access_code(args['access_token'])
        if not access_data:
            return response_json(-1, '无授权信息，请重新登录授权')
        nickname = ""
        nickname = access_data['nickname']
        account_id = ""

        # logging.info(access_data)
        is_tenant_owner = False
        is_joined_tenant = False
        account_integrate = AccountService.get_account_integrate_by_unionid(access_data['provider'], access_data['unionid'])

        # 判断被邀请用户是否存在
        if account_integrate:
            account_id = account_integrate.account_id
            if account_role == AccountRole.OWNER:
                # 判断是否已创建owner空间
                is_exists = Dify_AccountService.check_owner_exists(account_id, AccountRole.OWNER)
                if is_exists:
                    is_tenant_owner = True
            else:
                # 判断该用户是否加入了同一个空间
                is_exists = Dify_AccountService.check_account_join_exists(tenant_id, account_id)
                if is_exists:
                    is_joined_tenant = True
            
        data = {
            "nickname": nickname,
            "account_id": account_id,
            "account_role": account_role,
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "is_tenant_owner": is_tenant_owner,    # renamed has_owner_tenant to is_tenant_owner
            "is_joined_tenant": is_joined_tenant
        }

        return response_json(0, 'Success [Deprecated]', data)


api.add_resource(ActivateCheckApi, '/activate/check')
api.add_resource(ActivateApi, '/activate')
api.add_resource(TenantCreateCheckApi, '/activate/create_check')
