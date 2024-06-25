import logging
from flask_restful import marshal, Resource, reqparse
from libs.response import response_json
from services.dify.api_service import ApiService
from services.racio.account_service import AccountService
from models.racio.account import AccountRole
from libs.helper import uuid_value
from libs.login import login_required
from . import api
from fields.app_fields import (
    account_partial_fields,
)


class MemberListApi(Resource):
    @login_required
    def post(self):
        apiService = ApiService()
        datas = apiService.get_members()
        if not datas:
            return response_json(-1, '暂无数据')
        members = []
        for member in datas:
            if member['role'] == AccountRole.OWNER:
                continue
            nickname = ''
            status = ''
            phone = ''
            headimgurl = ''
            last_login_at = ''
            last_login_ip = ''
            racio_account = AccountService.get_account(member['id'])
            if racio_account:
                phone = racio_account.phone
                status = racio_account.status
                last_login_at = int(racio_account.last_login_at.timestamp())
                last_login_ip = racio_account.last_login_ip
                account_integrate = AccountService.get_account_integrate_by_account_id(provider='wx',
                                                                                       account_id=member['id'])
                if account_integrate:
                    nickname = account_integrate.nickname
                    headimgurl = account_integrate.headimgurl
                member['phone'] = phone
                member['status'] = status
                member['account_role'] = member['role']
                del member['role']
                member['nickname'] = nickname
                member['headimgurl'] = headimgurl
                member['last_login_at'] = last_login_at
                member['last_login_ip'] = last_login_ip
            members.append(member)
        return response_json(0, 'success', members)


class MemberRemoveApi(Resource):
    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('account_id', type=uuid_value, required=True, location='json')
        args = parser.parse_args()
        apiService = ApiService()
        result = apiService.remove_member(args['account_id'])
        if not result:
            return response_json(-1, '移除失败')
        return response_json(0, 'success')


class MemberUpdateRoleApi(Resource):
    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('account_id', type=uuid_value, required=True, location='json')
        parser.add_argument('role', type=str, required=True, location='json')
        args = parser.parse_args()

        apiService = ApiService()
        result = apiService.member_update_role(args['account_id'], args['role'])
        if not result:
            return response_json(-1, '变更失败')
        return response_json(0, 'success')


api.add_resource(MemberListApi, '/members')
api.add_resource(MemberRemoveApi, '/member/remove')
api.add_resource(MemberUpdateRoleApi, '/member/update_role')
