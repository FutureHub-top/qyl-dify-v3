import json
import logging
from flask import g
from services.dify.api_service import ApiService
from models.racio.account import AccountRole


class AccountService:

    @staticmethod
    def check_owner_exists(account_id, role) -> bool:
        apiService = ApiService()
        data = apiService.get_account_tenant_info(account_id, role)
        if data is None:
            return False
        else:
            if len(data) > 0:
                return True
            return False

    @staticmethod
    def switch_tenant(token, tenant_id) -> None:
        setattr(g, 'auth_token', token)
        apiService = ApiService()
        apiService.switch_tenant(tenant_id)


    @staticmethod
    def get_account_role(account) -> str:
        if account.account_role == AccountRole.SUPERADMIN:
            return account.account_role
        apiService = ApiService()
        tenants = apiService.get_all_tenant(account.id)
        if not tenants:
            return AccountRole.NORMAL
        for tenant in tenants:
            if tenant['role'] == AccountRole.OWNER:
                return tenant['role']

        for tenant in tenants:
            if tenant['role'] == AccountRole.ADMIN:
                return tenant['role']

        for tenant in tenants:
            if tenant['role'] == AccountRole.NORMAL:
                return tenant['role']

        return AccountRole.NORMAL


    @staticmethod
    def get_current_tenant(token, account):
        setattr(g, 'auth_token', token)
        apiService = ApiService()
        tenant = apiService.get_current_tenant()
        if tenant:
            return tenant
        else:
            tenants = apiService.get_all_tenant(account.id)
            if tenants and len(tenants) > 0:
                return tenants[0]
            return None



    @staticmethod
    def check_account_join_exists(tenant_id, account_id) -> bool:
        apiService = ApiService()
        tenants = apiService.get_all_tenant(account_id)
        if not tenants:
            return False
        for tenant in tenants:
            if tenant['id'] == tenant_id:
                return True
        return False


    # @classmethod
    # def _get_invitation_token_key(cls, token: str) -> str:
    #     return f'member_invite:token:{token}'

    # @staticmethod
    # def create_account(email: str, name: str, interface_language: str,
    #                    interface_theme: str = 'light',
    #                    status: str = AccountStatus.PENDING,) -> Account:
    #     """create account"""
    #     account = Account()
    #     account.email = email
    #     account.name = name
    #     account.status = status
    #
    #     account.interface_language = interface_language
    #     account.interface_theme = interface_theme
    #
    #     # Set timezone based on language
    #     account.timezone = language_timezone_mapping.get(interface_language, 'UTC')
    #
    #     db.session.add(account)
    #     db.session.commit()
    #     return account

    # @staticmethod
    # def link_account_integrate(provider: str, open_id: str, account: Account) -> None:
    #     """Link account integrate"""
    #     try:
    #         # Query whether there is an existing binding record for the same provider
    #         account_integrate: Optional[AccountIntegrate] = AccountIntegrate.query.filter_by(account_id=account.id,
    #                                                                                          provider=provider).first()
    #
    #         if account_integrate:
    #             # If it exists, update the record
    #             account_integrate.open_id = open_id
    #             account_integrate.encrypted_token = ""
    #             account_integrate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    #         else:
    #             # If it does not exist, create a new record
    #             account_integrate = AccountIntegrate(account_id=account.id, provider=provider, open_id=open_id,
    #                                                  encrypted_token="")
    #             db.session.add(account_integrate)
    #
    #         db.session.commit()
    #         logging.info(f'Account {account.id} linked {provider} account {open_id}.')
    #     except Exception as e:
    #         logging.exception(f'Failed to link {provider} account {open_id} to Account {account.id}')
    #         raise LinkAccountIntegrateError('Failed to link account.') from e

# class RegisterService:
#
#     @classmethod
#     def _get_invitation_token_key(cls, token: str) -> str:
#         return f'member_invite:token:{token}'
#
#     @classmethod
#     def revoke_token(cls, token: str):
#         redis_client.delete(cls._get_invitation_token_key(token))
#
#     @classmethod
#     def get_invitation_if_token_valid(cls, token: str) -> Optional[dict[str, Any]]:
#         apiService = ApiService()
#         invitation_data = cls._get_invitation_by_token(token)
#         if not invitation_data:
#             return None
#
#         tenant = None
#
#         if invitation_data['workspace_id'] != "0":
#             tenant = apiService.get_tenant(invitation_data['workspace_id'], 'normal')
#
#         account = apiService.get_account(invitation_data['account_id'])
#         if not account:
#             return None
#
#         return {
#             'account': account,
#             'data': invitation_data,
#             'tenant': tenant,
#         }
#
#     @classmethod
#     def _get_invitation_by_token(cls, token: str) -> Optional[dict[str, str]]:
#         data = redis_client.get(cls._get_invitation_token_key(token))
#         if not data:
#             return None
#
#         invitation = json.loads(data)
#         return invitation
