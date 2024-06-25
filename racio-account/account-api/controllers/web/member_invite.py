import logging

from flask import current_app
from flask_login import current_user
from libs.login import login_required
from services.racio.account_service import AccountService
from models.racio.account import Account, AccountRole
from flask_restful import Resource, reqparse, inputs, marshal
from libs.helper import email
from libs.response import response_json
from libs.email import send_invite_member_mail
from services.dify.api_service import ApiService
from . import api
from services.errors.account import AccountAlreadyInTenantError
from fields.app_fields import (
    member_invites_fields,
)


class MemberInviteListApi(Resource):

    @login_required
    def post(self):
        """Get account list"""
        # parser = reqparse.RequestParser()
        # parser.add_argument('tenant_id', type=str, required=False, default='', location='json')
        # args = parser.parse_args()

        user_data = AccountService.get_user_data(current_user.id)
        tenant_id = None
        member_invites = []
        if user_data['tenant_id'] != '':
            tenant_id = user_data['tenant_id']
        if user_data['account_role'] == AccountRole.SUPERADMIN or user_data['account_role'] == AccountRole.OWNER:
            member_invites = AccountService.get_member_invites(tenant_id)
        elif user_data['account_role'] == AccountRole.ADMIN:
            member_invites = AccountService.get_member_invites(tenant_id, current_user.id)


        console_web_url = current_app.config.get("CONSOLE_WEB_URL")
        apiService = ApiService()
        for member_invite in member_invites:
            member_invite.invite_link = f'{console_web_url}/account/activate?token={member_invite.id}'
            account = apiService.get_account(member_invite.invited_by)
            if account:
                member_invite.invited_by = account['name']
            else:
                member_invite.invited_by = ''

        return response_json(0, 'success', marshal(member_invites, member_invites_fields))


class MemberInviteEmailApi(Resource):
    """Invite a new member by email."""

    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=False, location='json', default='')
        parser.add_argument('domain', type=str, required=True, location='json', default='')
        parser.add_argument('role', type=str, required=True, location='json', default='')
        # parser.add_argument('tenant_id', type=str, required=True, location='json', default='')
        parser.add_argument('remark', type=str, location='json', default='')
        args = parser.parse_args()

        user_data = AccountService.get_user_data(current_user.id)

        if user_data['account_role'] == AccountRole.SUPERADMIN:
            if args['role'] != AccountRole.OWNER:
                response_json(-1, '超级管理员只能邀请空间所有者')
        else:
            if user_data['account_role'] == AccountRole.OWNER:
                if args['role'] == AccountRole.OWNER:
                    response_json(-1, '空间所有者不能邀请空间所有者')

            if user_data['account_role'] == AccountRole.ADMIN:
                if args['role'] != AccountRole.NORMAL:
                    response_json(-1, '管理员只能邀请普通用户')

        invitee_email = ''
        send_flag = False
        if args['email'] != '':
            try:
                invitee_email = email(args['email'])
                send_flag = True
            except Exception as e:
                logging.info(str(e))

        tenant_id = None
        if user_data['tenant_id'] != '':
            tenant_id = user_data['tenant_id']

        invitation_result = {}
        console_web_url = current_app.config.get("CONSOLE_WEB_URL")
        try:
            member_invite = AccountService.create_member_invite(tenant_id, args['role'], current_user.id,
                                                                args['remark'], args['domain'], args['email'])
            if send_flag:
                # send email
                tenant_name = ''
                if tenant_id:
                    apiService = ApiService()
                    tenant = apiService.get_tenant(tenant_id)
                    if tenant:
                        tenant_name = tenant['name']
                        tenant_name = f'「{tenant_name}」'
                send_invite_member_mail(
                    language='zh-Hans',#current_user.interface_language,
                    to=invitee_email,
                    token=member_invite.id,
                    inviter_name='',
                    tenant_name=tenant_name
                )
            invitation_result = {
                'status': 'success',
                'email': invitee_email,
                'url': f'{console_web_url}/account/activate?token={member_invite.id}'
            }
        except AccountAlreadyInTenantError:
            invitation_result = {
                'status': 'success',
                'email': invitee_email,
                'url': f'{console_web_url}/signin'
            }
        except Exception as e:
            invitation_result = {
                'status': 'failed',
                'email': invitee_email,
                'message': str(e)
            }
        return response_json(0, 'success', invitation_result)


api.add_resource(MemberInviteListApi, '/member_invites')
api.add_resource(MemberInviteEmailApi, '/member_invites/invite-email')
