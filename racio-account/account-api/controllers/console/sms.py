from flask_restful import Resource, reqparse
from services.racio.account_service import AccountService
from extensions.ext_sms import sms
from libs.response import response_json
import logging
from . import api


class SmsVerifyApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=True, nullable=False, location='json')
        parser.add_argument('phone', type=str, required=True, nullable=False, location='json')
        parser.add_argument('code', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()

        account_service = AccountService()
        verify_data = account_service.get_verify_code(args['token'], args['phone'])
        logging.info(f'SmsVerifyApi.post.verify_data: {verify_data}, token: {args['token']}')
        if not verify_data:
            return response_json(-1, '验证码已过期')

        if verify_data['phone'] != args['phone']:
            return response_json(-1, '验证手机号不正确')

        if verify_data['code'] != args['code']:
            return response_json(-1, '验证码不正确')

        account_service.revoke_verify_code(args['token'], args['phone'])
        logging.info(f'SmsVerifyApi.post.revoke_verify_code: - token: {args['token']}, phone: {args['phone']}')
        return response_json(0, 'success')


class SmsSendApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('phone', type=str, required=True, nullable=False, location='json')
        parser.add_argument('token', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        if args['phone'] is None:
            return response_json(-1, '请输入手机号码')
        if AccountService.check_phone_exists(args['phone']):
            return response_json(-1, '该手机号已绑定了其他帐号，请更换手机号码验证')
        code = AccountService.generate_verify_code(args['token'], args['phone'])
        sms.send(args['phone'], code)
        return response_json(0, 'success')


api.add_resource(SmsVerifyApi, '/sms/verify')
api.add_resource(SmsSendApi, '/sms/send')
