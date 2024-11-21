import base64
import json
import logging
import random
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from flask import current_app
from constants.languages import language_timezone_mapping
from flask_sqlalchemy import Pagination
from libs.helper import get_remote_ip
from libs.password import hash_password
from extensions.ext_redis import redis_client
from models.racio.account import *
from libs.password import compare_password
from libs.passport import PassportService
from services.dify.api_service import ApiService
from services.errors.account import (
    LinkAccountIntegrateError,
    AccountAlreadyInTenantError,
    CreateAccountError,
    AccountLoginError
)
from werkzeug.exceptions import Unauthorized


class AccountService:

    @staticmethod
    def get_account(user_id: str) -> Account:
        account = Account.query.filter_by(id=user_id).first()
        return account

    @staticmethod
    def get_role(tenant_id: str, account_id: str) -> str:
        ta = TenantAccountJoin.query.filter_by(tenant_id=tenant_id, account_id=account_id).first()
        if ta:
            return ta.role
        return ''

    @staticmethod
    def check_phone_exists(phone: str) -> bool:
        account = Account.query.filter_by(phone=phone).first()
        if not account:
            return False
        else:
            return True

    @staticmethod
    def load_user(user_id: str) -> Account:
        account = Account.query.filter_by(id=user_id).first()
        if not account:
            return None

        if account.status in [AccountStatus.BANNED.value, AccountStatus.CLOSED.value]:
            raise Unauthorized("账号被停用或关闭")

        if datetime.now(timezone.utc).replace(tzinfo=None) - account.last_active_at > timedelta(minutes=10):
            account.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.session.commit()

        return account

    @staticmethod
    def authenticate(username: str, password: str) -> Account:
        """authenticate account with username and password"""

        account = Account.query.filter_by(name=username, account_role=AccountRole.SUPERADMIN).first()
        if not account:
            raise AccountLoginError('用户名或密码错误')

        if account.password is None or not compare_password(password, account.password, account.password_salt):
            raise AccountLoginError('用户名或密码错误')
        return account

    @classmethod
    def _get_invitation_token_key(cls, token: str) -> str:
        return f'member_invite:token:{token}'

    @staticmethod
    def create_account(id: str, email: str, name: str, interface_language: str, phone: str = None,
                       password: str = None,
                       interface_theme: str = 'light',
                       status: str = AccountStatus.PENDING,
                       account_role: str = None) -> Account:
        """create account"""
        account = Account()
        account.id = id
        account.email = email
        account.name = name
        account.phone = phone
        account.status = status
        account.account_role = account_role

        if password:
            # generate password salt
            salt = secrets.token_bytes(16)
            base64_salt = base64.b64encode(salt).decode()

            # encrypt password with salt
            password_hashed = hash_password(password, salt)
            base64_password_hashed = base64.b64encode(password_hashed).decode()

            account.password = base64_password_hashed
            account.password_salt = base64_salt

        account.interface_language = interface_language
        account.interface_theme = interface_theme

        # Set timezone based on language
        account.timezone = language_timezone_mapping.get(interface_language, 'UTC')

        db.session.add(account)
        db.session.commit()
        
        return account

    @staticmethod
    def link_account_integrate(provider: str, open_id: str, nickname: str, headimgurl: str, unionid: str,
                               account: Account) -> None:
        """Link account integrate"""
        try:
            # Query whether there is an existing binding record for the same provider
            account_integrate: Optional[AccountIntegrate] = AccountIntegrate.query.filter_by(account_id=account.id,
                                                                                             provider=provider).first()

            if account_integrate:
                # If it exists, update the record
                account_integrate.open_id = open_id
                account_integrate.encrypted_token = ""
                account_integrate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                account_integrate.nickname = nickname
                account_integrate.headimgurl = headimgurl
                account_integrate.unionid = unionid
            else:
                # If it does not exist, create a new record
                account_integrate = AccountIntegrate(account_id=account.id, provider=provider, open_id=open_id,
                                                     encrypted_token="", nickname=nickname, headimgurl=headimgurl,
                                                     unionid=unionid)
                db.session.add(account_integrate)

            db.session.commit()
            logging.info(f'Account {account.id} linked {provider} account {open_id}.')
        except Exception as e:
            logging.exception(f'Failed to link {provider} account {open_id} to Account {account.id}')
            raise LinkAccountIntegrateError('Failed to link account.') from e

    @staticmethod
    def update_account(account, **kwargs):
        """Update account fields"""
        for field, value in kwargs.items():
            if hasattr(account, field):
                setattr(account, field, value)
            else:
                raise AttributeError(f"Invalid field: {field}")

        db.session.commit()
        return account

    @staticmethod
    def update_last_login(account: Account, request) -> None:
        """Update last login time and ip"""
        account.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        account.last_login_ip = get_remote_ip(request)
        db.session.add(account)
        db.session.commit()
        logging.info(f'Account {account.id} logged in successfully.')

    @staticmethod
    def get_accounts(args: dict = None) -> Pagination | None:
        """
        Get app list with pagination
        :param args: request args
        :return:
        """
        query = db.select(Account).order_by(Account.created_at.desc())
        if args['phone'] != '':
            query = db.session.query(Account).filter(Account.phone.like("%" + str(args['phone']) + "%")).order_by(
                Account.created_at.desc())
        account_models = db.paginate(
            query,
            page=args['page'],
            per_page=args['limit'],
            error_out=False
        )
        return account_models

    # @classmethod
    # def invite_new_member(cls, tenant_id: str, email: str, role: str = AccountRole.NORMAL,
    #                       send_flag: bool = True) -> str:
    #     """Invite new member"""
    #     account = Account.query.filter_by(email=email).first()
    #     apiService = ApiService()
    #     if not account:
    #         name = email.split('@')[0]
    #         account = apiService.create_account(email=email, name=name)
    #         if account is None:
    #             raise CreateAccountError("create account fail by api")
    #         cls.create_account(id=account['id'], email=account['email'], name=account['name'],
    #                            interface_language=account['interface_language'],
    #                            status=account['status'])
    #
    #         if role == AccountRole.NORMAL or role == AccountRole.ADMIN:
    #             if tenant_id is not None:
    #                 # 加入空间
    #                 apiService.create_tenant_member(tenant_id, account, role)
    #     else:
    #         # Support resend invitation email when the account is pending status
    #         if account.status != AccountStatus.PENDING.value:
    #             raise AccountAlreadyInTenantError("Account already exists.")
    #
    #         if role == AccountRole.NORMAL or role == AccountRole.ADMIN:
    #             if tenant_id is not None:
    #                 # 加入空间
    #                 apiService.create_tenant_member(tenant_id, account, role)
    #
    #     token = cls.generate_invite_token(account)
    #
    #     if send_flag:
    #         # send email
    #         send_invite_member_mail(
    #             language=account.interface_language,
    #             to=email,
    #             token=token,
    #             inviter_name='Racio',
    #         )
    #     return token

    # @classmethod
    # def generate_invite_token(cls, account: Account) -> str:
    #     token = str(uuid.uuid4())
    #     invitation_data = {
    #         'account_id': account.id,
    #         'email': account.email,
    #         'workspace_id': "0",
    #     }
    #     expiryHours = current_app.config.get('INVITE_EXPIRY_HOURS')
    #     redis_client.setex(
    #         cls._get_invitation_token_key(token),
    #         int(expiryHours) * 60 * 60,
    #         json.dumps(invitation_data)
    #     )
    #     return token

    @staticmethod
    def generate_verify_code(token: str, phone: str) -> str:
        verify_code = str(random.randint(1000, 9999))
        cache_key = f'racio_verify_code:{token}:{phone}'
        logging.info(f'generate_verify_code - cache_key: {cache_key}, verify_code: {verify_code}')
        verify_data = {
            'phone': phone,
            'code': verify_code,
        }
        expiryHours = current_app.config.get('TENCENT_SMS_TIMEOUT')
        redis_client.setex(
            cache_key,
            int(expiryHours) * 60,
            json.dumps(verify_data)
        )
        return verify_code

    @staticmethod
    def get_verify_code(token: str, phone: str) -> dict:
        cache_key = f'racio_verify_code:{token}:{phone}'
        logging.info(f'get_verify_code - cache_key: {cache_key}')
        data = redis_client.get(cache_key)
        if not data:
            return None
        verify_data = json.loads(data)
        return verify_data

    @staticmethod
    def revoke_verify_code(token: str, phone: str):
        cache_key = f'racio_verify_code:{token}:{phone}'
        logging.info(f'revoke_verify_code - cache_key: {cache_key}')
        redis_client.delete(cache_key)

    @staticmethod
    def save_access_code(token: str, provider: str, open_id: str, nickname: str, headimgurl: str, unionid: str):
        cache_key = f'racio_access_code:{token}'
        access_data = {
            'provider': provider,
            'open_id': open_id,
            'nickname': nickname,
            'headimgurl': headimgurl,
            'unionid': unionid
        }
        redis_client.setex(
            cache_key,
            7200,
            json.dumps(access_data)
        )

    @staticmethod
    def get_access_code(token: str):
        cache_key = f'racio_access_code:{token}'
        data = redis_client.get(cache_key)
        if not data:
            return None
        access_data = json.loads(data)
        return access_data

    @staticmethod
    def get_account_jwt_token(account):
        payload = {
            "user_id": account.id,
            "account_role": account.account_role,
            "exp": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
            "sub": 'API Passport',
        }

        token = PassportService().issue(payload)
        return token

    @staticmethod
    def get_account_integrate_by_unionid(provider: str, unionid: str) -> bool:
        account_integrate = AccountIntegrate.query.filter_by(provider=provider, unionid=unionid).first()
        if not account_integrate:
            return None
        else:
            return account_integrate

    @staticmethod
    def get_account_integrate_by_account_id(provider: str, account_id: str) -> bool:
        account_integrate = AccountIntegrate.query.filter_by(provider=provider, account_id=account_id).first()
        if not account_integrate:
            return None
        else:
            return account_integrate

    @staticmethod
    def create_member_invite(tenant_id: str, role: str, invited_by: str, remark: str, quota: int, domain: str, email: str) -> MemberInvite:
        """create member_invite"""
        memberInvite = MemberInvite()
        memberInvite.tenant_id = tenant_id
        memberInvite.role = role
        memberInvite.invited_by = invited_by
        memberInvite.remark = remark
        memberInvite.quota = quota
        memberInvite.domain = domain
        memberInvite.email = email
        db.session.add(memberInvite)
        db.session.commit()
        return memberInvite

    @staticmethod
    def get_member_invite(id: str) -> MemberInvite:
        member_invite = MemberInvite.query.filter_by(id=id).first()
        if member_invite and member_invite.quota > 0:
            return member_invite
        else:
            return None
        
    @staticmethod
    def get_member_invite_v2(id: str) -> MemberInvite:
        member_invite = MemberInvite.query.filter_by(id=id).first()
        # Do not check quota here
        if member_invite:
            return member_invite
        else:
            return None

    @staticmethod
    def get_member_invites(tenant_id: str = None, account_id: str = None) -> list[MemberInvite]:
        member_invites = []
        # if tenant_id is not None:
        #     member_invites = MemberInvite.query.filter_by(tenant_id=tenant_id).order_by(
        #         MemberInvite.created_at.asc()).all()
        # else:
        #     member_invites = MemberInvite.query.order_by(MemberInvite.created_at.asc()).all()
        member_invites = MemberInvite.query.filter_by(tenant_id=tenant_id).order_by(
            MemberInvite.created_at.desc()).all()
        if account_id is not None:
            member_invites = MemberInvite.query.filter_by(tenant_id=tenant_id, invited_by=account_id).order_by(
                MemberInvite.created_at.desc()).all()
        return member_invites
    
    @staticmethod
    def get_member_invites_pagination(tenant_id: str = None, account_id: str = None, page: int = 1, limit: int = 20) -> Pagination | None:
        """
        Get member_invites list with pagination
        """

        query = db.select(MemberInvite).where(MemberInvite.tenant_id == tenant_id)

        if account_id != None:
            query = query.where(MemberInvite.invited_by == account_id)
            
        query = query.order_by(MemberInvite.created_at.desc())

        member_invites = db.paginate(
            query,
            page=page,
            per_page=limit,
            error_out=False
        )

        return member_invites
    
    @staticmethod
    def delete_member_invite(id: str) -> None:
        member_invite = MemberInvite.query.filter_by(id=id).first()
        if member_invite:
            if member_invite.quota <= 0:
                db.session.delete(member_invite)
                db.session.commit()
                logging.info(f'AccountService.delete_member_invite - id: {id}, quota: {member_invite.quota}.')
            else:
                AccountService.decrement_member_invite_quota(id)
        
    
    @staticmethod
    def decrement_member_invite_quota(member_invite_id: str):
        member_invite = MemberInvite.query.filter_by(id=member_invite_id).first()
        if member_invite and member_invite.quota > 0:
            member_invite.quota -= 1
            db.session.commit()
            logging.info(f'AccountService.decrement_member_invite_quota - id: {member_invite_id}, quota: {member_invite.quota}.')
            return {'message': 'Quota decremented', 'new_quota': member_invite.quota}
        elif member_invite is None:
            return {'error': 'Member not found'}, 404
        else:
            return {'error': 'Quota cannot be negative'}, 400

    @staticmethod
    def increment_member_invite_quota(member_invite_id: str):
        member_invite = MemberInvite.query.filter_by(id=member_invite_id).first()
        if member_invite and member_invite.quota > 0:
            member_invite.quota += 1
            db.session.commit()
            return {'message': 'Quota incremented', 'new_quota': member_invite.quota}
        elif member_invite is None:
            return {'error': 'Member not found'}, 404
        else:
            return {'error': 'Quota cannot be negative'}, 400

    @classmethod
    def get_invitation_if_token_valid(cls, token: str) -> Optional[dict[str, Any]]:
        invitation_data = cls.get_member_invite(token)
        if not invitation_data:
            return None

        # get tenant from invitation, if has
        tenant = None
        if invitation_data.tenant_id:
            apiService = ApiService()
            tenant = apiService.get_tenant(invitation_data.tenant_id)
        return {
            'data': invitation_data,
            'tenant': tenant
        }
    
    @classmethod
    def get_invitation_if_token_valid_v2(cls, token: str) -> Optional[dict[str, Any]]:
        invitation_data = cls.get_member_invite_v2(token)
        if not invitation_data:
            return None

        # check invitation valid
        is_valid = False
        if invitation_data.quota > 0:
            is_valid = True

        # get tenant from invitation, if has
        tenant = None
        if invitation_data.tenant_id:
            apiService = ApiService()
            tenant = apiService.get_tenant(invitation_data.tenant_id)

        return {
            'data': invitation_data,
            'is_valid': is_valid,
            'tenant': tenant
        }

    @staticmethod
    def get_account_num(account_role: str) -> int:
        num = Account.query.filter_by(account_role=account_role).count()
        return num

    @staticmethod
    def set_user_data(account_id: str, tenant_id: str = '', account_role: str = '') -> None:
        cache_key = f'racio_user_data:{account_id}'
        json_data = AccountService.get_user_data(account_id)
        if not json_data:
            json_data = {
                'tenant_id': '',
                'account_role': ''
            }

        if tenant_id != '':
            json_data['tenant_id'] = tenant_id

        if account_role != '':
            # account_role
            json_data['account_role'] = account_role

        redis_client.setex(
            cache_key,
            7200,
            json.dumps(json_data)
        )

    @staticmethod
    def get_user_data(account_id: str):
        cache_key = f'racio_user_data:{account_id}'
        data = redis_client.get(cache_key)

        if not data:
            return None
        
        json_data = json.loads(data)
        return json_data
