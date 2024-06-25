import urllib.parse
from abc import ABC
from dataclasses import dataclass

import requests


@dataclass
class OAuthUserInfo:
    id: str
    name: str
    email: str
    headimgurl: str
    unionid: str


class OAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self):
        raise NotImplementedError()

    def get_access_token(self, code: str):
        raise NotImplementedError()

    def get_raw_user_info(self, token: str, openid: str):
        raise NotImplementedError()

    def get_user_info(self, token: str, openid: str) -> OAuthUserInfo:
        raw_info = self.get_raw_user_info(token, openid)
        return self._transform_user_info(raw_info)

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        raise NotImplementedError()


class WxOAuth(OAuth):
    _AUTH_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    _TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    _USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo'

    def get_authorization_url(self):
        params = {
            'appid': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'snsapi_login',  # Request only basic user information
            'state': 'STATE'
        }
        return f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}#wechat_redirect"

    def get_access_token(self, code: str):
        data = {
            'appid': self.client_id,
            'secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }

        headers = {'Accept': 'application/json'}
        response = requests.post(self._TOKEN_URL, data=data, headers=headers)

        response_json = response.json()

        access_token = response_json.get('access_token')
        openid = response_json.get('openid')

        if not access_token:
            raise ValueError(f"Error in Wx OAuth: {response_json}")

        return access_token, openid

    def get_raw_user_info(self, token: str, openid: str):
        params = {
            'access_token': token,
            'openid': openid,
        }
        headers = {
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8'
        }
        response = requests.get(self._USER_INFO_URL, params=params, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
        user_info = response.json()
        return user_info

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=str(raw_info['openid']),
            name=str(raw_info['nickname']),
            email=None,
            headimgurl=str(raw_info['headimgurl']),
            unionid=str(raw_info['unionid'])
        )


class WeChatOAuth(OAuth):
    _AUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    _TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    _USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo'

    def get_authorization_url(self):
        params = {
            'appid': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'snsapi_userinfo',  # Request only basic user information
            'state': 'STATE'
        }
        return f"{self._AUTH_URL}?{urllib.parse.urlencode(params)}#wechat_redirect"

    def get_access_token(self, code: str):
        data = {
            'appid': self.client_id,
            'secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }

        headers = {'Accept': 'application/json'}
        response = requests.post(self._TOKEN_URL, data=data, headers=headers)

        response_json = response.json()

        access_token = response_json.get('access_token')
        openid = response_json.get('openid')

        if not access_token:
            raise ValueError(f"Error in Wx OAuth: {response_json}")

        return access_token, openid

    def get_raw_user_info(self, token: str, openid: str):
        params = {
            'access_token': token,
            'openid': openid,
        }
        headers = {
            'Accept': 'application/json'
        }
        response = requests.get(self._USER_INFO_URL, params=params, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
        user_info = response.json()
        return user_info

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=str(raw_info['openid']),
            name=str(raw_info['nickname']),
            email=None,
            headimgurl=str(raw_info['headimgurl']),
            unionid=str(raw_info['unionid'])
        )

