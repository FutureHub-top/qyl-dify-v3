from flask_restful import fields

from libs.helper import TimestampField

account_partial_fields = {
    'id': fields.String,
    'name': fields.String,
    'email': fields.String,
    'phone': fields.String,
    'account_role': fields.String,
    'status': fields.String,
    'last_login_at': TimestampField,
    'last_login_ip': fields.String,
    'created_at': TimestampField,
    'tenant_names': fields.List(fields.String),
    'nickname': fields.String,
    'headimgurl': fields.String
}

account_pagination_fields = {
    'page': fields.Integer,
    'limit': fields.Integer(attribute='per_page'),
    'total': fields.Integer,
    'has_more': fields.Boolean(attribute='has_next'),
    'data': fields.List(fields.Nested(account_partial_fields), attribute='items')
}

tenants_fields = {
    'id': fields.String,
    'name': fields.String,
    'plan': fields.String,
    'status': fields.String,
    'created_at': fields.Integer,
    "role": fields.String,
}

member_invites_fields = {
    'id': fields.String,
    'tenant_id': fields.String,
    'role': fields.String,
    'remark': fields.String,
    'created_at': TimestampField,
    'invite_link': fields.String,
    'email': fields.String,
    "invited_by": fields.String
}
