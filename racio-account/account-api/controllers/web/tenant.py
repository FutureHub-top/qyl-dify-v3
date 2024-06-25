from flask_login import current_user
from flask_restful import marshal, Resource, reqparse
from libs.response import response_json
from services.dify.api_service import ApiService
from fields.app_fields import tenants_fields
from models.racio.account import AccountRole
from services.racio.account_service import AccountService
from libs.helper import uuid_value
from libs.login import login_required
from . import api


class TenantListApi(Resource):

    @login_required
    def post(self):
        apiService = ApiService()
        tenants = apiService.get_all_tenant(current_user.id)
        if tenants is None:
            return response_json(-1, '该账号无空间数据')
        tenant_list = []
        for tenant in tenants:
            if tenant['role'] != AccountRole.NORMAL:
                tenant_list.append(tenant)

        return response_json(0, 'success', marshal(tenant_list, tenants_fields))


class SwitchTenantApi(Resource):
    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('tenant_id', type=uuid_value, required=True, location='json')
        args = parser.parse_args()

        apiService = ApiService()
        tenant = apiService.switch_tenant(args['tenant_id'])
        if not tenant:
            return response_json(-1, '切换空间失败')
        current_user.account_role = tenant['role']
        AccountService.set_user_data(account_id=current_user.id, tenant_id=args['tenant_id'],
                                     account_role=tenant['role'])
        data = {
            'tenant_id': tenant['id'],
            'name': tenant['name'],
            'role': tenant['role'],
        }
        return response_json(0, 'success', data)


api.add_resource(TenantListApi, '/tenant/list')
api.add_resource(SwitchTenantApi, '/tenant/switch')
