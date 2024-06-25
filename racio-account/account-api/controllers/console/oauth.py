import logging
import requests
from flask import current_app, redirect, request
from flask_restful import Resource, reqparse
from services.racio.account_service import AccountService
from libs.oauth import WxOAuth, WeChatOAuth
from libs.response import response_json
from . import api


def get_oauth_providers():
    with current_app.app_context():

        wx_oauth = WxOAuth(client_id=current_app.config.get('WX_CLIENT_ID'),
                           client_secret=current_app.config.get('WX_CLIENT_SECRET'),
                           redirect_uri=current_app.config.get('CONSOLE_API_URL') + '/console/api/oauth/authorize/wx')

        wechat_oauth = WeChatOAuth(client_id=current_app.config.get('WECHAT_APP_ID'),
                           client_secret=current_app.config.get('WECHAT_APP_SECRET'),
                           redirect_uri=current_app.config.get('CONSOLE_WEB_URL') + '/dashboard/#/auth/gzhcheck')

        OAUTH_PROVIDERS = {
            'wx': wx_oauth,
            'wechat': wechat_oauth
        }
        return OAUTH_PROVIDERS


class OAuthLogin(Resource):
    def get(self, provider: str):
        OAUTH_PROVIDERS = get_oauth_providers()
        with current_app.app_context():
            oauth_provider = OAUTH_PROVIDERS.get(provider)
            print(vars(oauth_provider))
        if not oauth_provider:
            return response_json(-1, '未知授权方')

        auth_url = oauth_provider.get_authorization_url()
        return redirect(auth_url)


class OAuthCallback(Resource):
    def get(self, provider: str):
        OAUTH_PROVIDERS = get_oauth_providers()
        with current_app.app_context():
            oauth_provider = OAUTH_PROVIDERS.get(provider)
        if not oauth_provider:
            return response_json(-1, '未知授权方')

        code = request.args.get('code')
        try:
            token, openid = oauth_provider.get_access_token(code)
        except requests.exceptions.HTTPError as e:
            logging.exception(
                f"An error occurred during the OAuth process with {provider}: {e.response.text}")
            return response_json(-1, '获取授权信息失败')
        return redirect(f'{current_app.config.get("CONSOLE_WEB_URL")}?console_openid={openid}')


class OAuthGetAccessToken(Resource):
    def post(self, provider: str):
        OAUTH_PROVIDERS = get_oauth_providers()
        with current_app.app_context():
            oauth_provider = OAUTH_PROVIDERS.get(provider)
        if not oauth_provider:
            return response_json(-1, '未知授权方')

        parser = reqparse.RequestParser()
        parser.add_argument('code', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        try:
            access_token, openid = oauth_provider.get_access_token(args['code'])
            oauth_user_info = oauth_provider.get_user_info(access_token, openid)
            AccountService.save_access_code(access_token, 'wx', oauth_user_info.id, oauth_user_info.name, oauth_user_info.headimgurl, oauth_user_info.unionid)
        except requests.exceptions.HTTPError as e:
            logging.exception(
                f"An error occurred during the OAuth process with {provider}: {e.response.text}")
            return response_json(-1, '获取授权信息失败')
        return response_json(0, 'success', access_token)


api.add_resource(OAuthLogin, '/oauth/login/<provider>')
# api.add_resource(OAuthCallback, '/oauth/authorize/<provider>')
api.add_resource(OAuthGetAccessToken, '/oauth/access_token/<provider>')