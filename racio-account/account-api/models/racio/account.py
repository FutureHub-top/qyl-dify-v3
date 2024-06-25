import enum
from flask_login import UserMixin
from extensions.ext_database import db
from models import StringUUID
from dataclasses import dataclass

class AccountStatus(str, enum.Enum):
    PENDING = 'pending'
    UNINITIALIZED = 'uninitialized'
    ACTIVE = 'active'
    BANNED = 'banned'
    CLOSED = 'closed'


class AccountRole(str, enum.Enum):
    SUPERADMIN = 'super_admin'
    OWNER = 'owner'
    ADMIN = 'admin'
    NORMAL = 'normal'


class Account(UserMixin, db.Model):
    # __bind_key__ = 'racio_db'
    __tablename__ = 'accounts'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='account_pkey'),
        db.Index('account_email_idx', 'email'),

    )

    id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(11), nullable=True)
    account_role = db.Column(db.String(16), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    password_salt = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(255))
    interface_language = db.Column(db.String(255))
    interface_theme = db.Column(db.String(255))
    timezone = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(255))
    last_active_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    status = db.Column(db.String(16), nullable=False, server_default=db.text("'active'::character varying"))
    initialized_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))

    @property
    def is_password_set(self):
        return self.password is not None

    def get_status(self) -> AccountStatus:
        status_str = self.status
        return AccountStatus(status_str)

    @classmethod
    def get_by_openid(cls, provider: str, open_id: str) -> db.Model:
        account_integrate = db.session.query(AccountIntegrate). \
            filter(AccountIntegrate.provider == provider, AccountIntegrate.open_id == open_id). \
            one_or_none()
        if account_integrate:
            return db.session.query(Account). \
                filter(Account.id == account_integrate.account_id). \
                one_or_none()
        return None

    def get_integrates(self) -> list[db.Model]:
        ai = db.Model
        return db.session.query(ai).filter(
            ai.account_id == self.id
        ).all()
    # check current_user.current_tenant.current_role in ['admin', 'owner']
    @property
    def is_admin_or_owner(self):
        return self._current_tenant.current_role in ['admin', 'owner']


class AccountIntegrate(db.Model):
    # __bind_key__ = 'racio_db'
    __tablename__ = 'account_integrates'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='account_integrate_pkey'),
        db.UniqueConstraint('account_id', 'provider', name='unique_account_provider'),
        db.UniqueConstraint('provider', 'open_id', name='unique_provider_open_id')
    )

    id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
    account_id = db.Column(StringUUID, nullable=False)
    provider = db.Column(db.String(16), nullable=False)
    open_id = db.Column(db.String(255), nullable=False)
    encrypted_token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    nickname = db.Column(db.String(255), nullable=True, server_default='')
    headimgurl = db.Column(db.String(255), nullable=True, server_default='')
    unionid = db.Column(db.String(255), nullable=False, server_default='')


class MemberInvite(db.Model):
    # __bind_key__ = 'racio_db'
    __tablename__ = 'member_invite'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='member_invite_pkey'),
    )

    id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
    tenant_id = db.Column(StringUUID, nullable=True)
    role = db.Column(db.String(16), nullable=False)
    invited_by = db.Column(StringUUID, nullable=False)
    remark = db.Column(db.String(255), nullable=True, server_default='')
    domain = db.Column(db.String(255), nullable=True, server_default='')
    email = db.Column(db.String(255), nullable=True, server_default='')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))


# class MemberInviteTest(db.Model):
#     # __bind_key__ = 'racio_db'
#     __tablename__ = 'member_invite_test'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='member_invite_test_pkey'),
#     )
#
#     id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
#     tenant_id = db.Column(StringUUID, nullable=True)
#     role = db.Column(db.String(16), nullable=False)
#     invited_by = db.Column(StringUUID, nullable=False)
#     remark = db.Column(db.String(255), nullable=True, server_default='')
#     domain = db.Column(db.String(255), nullable=True, server_default='')
#     created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))




