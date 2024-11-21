import os

import dotenv

dotenv.load_dotenv()

DEFAULTS = {
    'DB_USERNAME': '',
    'DB_PASSWORD': '',
    'DB_HOST': '',
    'DB_PORT': '',
    'DB_DATABASE': '',
    'DB_CHARSET': 'utf8',
    'REDIS_HOST': '',
    'REDIS_PORT': '',
    'REDIS_DB': '0',
    'REDIS_USE_SSL': 'False',
    'REDIS_PASSWORD': '',
    'OAUTH_REDIRECT_PATH': '/console/api/oauth/authorize',
    'OAUTH_REDIRECT_INDEX_PATH': '/',
    'DEPLOY_ENV': 'PRODUCTION',
    'SQLALCHEMY_POOL_SIZE': 30,
    'SQLALCHEMY_MAX_OVERFLOW': 10,
    'SQLALCHEMY_POOL_RECYCLE': 3600,
    'SQLALCHEMY_ECHO': 'False',
    'CELERY_BACKEND': 'database',
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s.%(msecs)03d %(levelname)s [%(threadName)s] [%(filename)s:%(lineno)d] - %(message)s',
    'LOG_DATEFORMAT': '%Y-%m-%d %H:%M:%S',
    # 'INVITE_EXPIRY_HOURS': 72,

    # 'CONSOLE_API_URL': '',
    # 'CONSOLE_WEB_URL': '',
    # 'SERVICE_API_URL': '',
    # 'APP_WEB_URL': '',
    # 'SECRET_KEY': 'sk-9f73s3ljTXVcMT3Blb3ljTqtsKiGHXVcMT3BlbkFJLK7U'
}


def get_env(key):
    return os.environ.get(key, DEFAULTS.get(key))


def get_bool_env(key):
    value = get_env(key)
    return value.lower() == 'true' if value is not None else False


def get_cors_allow_origins(env, default):
    cors_allow_origins = []
    if get_env(env):
        for origin in get_env(env).split(','):
            cors_allow_origins.append(origin)
    else:
        cors_allow_origins = [default]

    return cors_allow_origins


class Config:
    """Application configuration class."""

    def __init__(self):
        # ------------------------
        # General Configurations.
        # ------------------------
        self.CURRENT_VERSION = "0.0.1"
        self.COMMIT_SHA = get_env('COMMIT_SHA')
        self.DEPLOY_ENV = get_env('DEPLOY_ENV')
        self.TESTING = False
        self.LOG_LEVEL = get_env('LOG_LEVEL')
        self.LOG_FILE = get_env('LOG_FILE')
        self.LOG_FORMAT = get_env('LOG_FORMAT')
        self.LOG_DATEFORMAT = get_env('LOG_DATEFORMAT')

        self.CONSOLE_API_URL = get_env('CONSOLE_API_URL')

        # The front-end URL prefix of the console web.
        # used to concatenate some front-end addresses and for CORS configuration use.
        self.CONSOLE_WEB_URL = get_env('CONSOLE_WEB_URL')

        # Your App secret key will be used for securely signing the session cookie
        # Make sure you are changing this key for your deployment with a strong key.
        # You can generate a strong key using `openssl rand -base64 42`.
        # Alternatively you can set it with `SECRET_KEY` environment variable.
        self.SECRET_KEY = get_env('SECRET_KEY')

        # cors settings
        self.CONSOLE_CORS_ALLOW_ORIGINS = get_cors_allow_origins(
            'CONSOLE_CORS_ALLOW_ORIGINS', self.CONSOLE_WEB_URL)
        self.WEB_API_CORS_ALLOW_ORIGINS = get_cors_allow_origins(
            'WEB_API_CORS_ALLOW_ORIGINS', '*')


        # cors settings
        self.WEB_API_CORS_ALLOW_ORIGINS = get_cors_allow_origins(
            'WEB_API_CORS_ALLOW_ORIGINS', '*')

        # ------------------------
        # Database Configurations.
        # ------------------------
        db_credentials = {
            key: get_env(key) for key in
            ['DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_DATABASE', 'DB_CHARSET']
        }

        db_extras = f"?client_encoding={db_credentials['DB_CHARSET']}" if db_credentials['DB_CHARSET'] else ""

        self.SQLALCHEMY_DATABASE_URI = f"postgresql://{db_credentials['DB_USERNAME']}:{db_credentials['DB_PASSWORD']}@{db_credentials['DB_HOST']}:{db_credentials['DB_PORT']}/{db_credentials['DB_DATABASE']}{db_extras}"
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': int(get_env('SQLALCHEMY_POOL_SIZE')),
            'max_overflow': int(get_env('SQLALCHEMY_MAX_OVERFLOW')),
            'pool_recycle': int(get_env('SQLALCHEMY_POOL_RECYCLE'))
        }
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        #postgresql://dify:Ejdrn2S8HaRX84mp@test.corp.chaolian360.com:8981/test&options=-c%20search_path=account
        self.SQLALCHEMY_ECHO = get_bool_env('SQLALCHEMY_ECHO')
        # db_racio_credentials = {
        #     key: get_env(key) for key in
        #     ['DB_RACIO_USERNAME', 'DB_RACIO_PASSWORD', 'DB_RACIO_HOST', 'DB_RACIO_PORT', 'DB_RACIO_DATABASE', 'DB_RACIO_CHARSET']
        # }
        # racio_db = f"postgresql://{db_racio_credentials['DB_RACIO_USERNAME']}:{db_racio_credentials['DB_RACIO_PASSWORD']}@{db_racio_credentials['DB_RACIO_HOST']}:{db_racio_credentials['DB_RACIO_PORT']}/{db_racio_credentials['DB_RACIO_DATABASE']}"
        # self.SQLALCHEMY_BINDS = {
        #     # 'account_db': self.SQLALCHEMY_DATABASE_URI+'&options=-c%20search_path=account'
        #     'racio_db': racio_db
        # }

        # ------------------------
        # Celery worker Configurations.
        # ------------------------
        # self.CELERY_BROKER_URL = get_env('CELERY_BROKER_URL')
        # self.CELERY_BACKEND = get_env('CELERY_BACKEND')
        # self.CELERY_RESULT_BACKEND = 'db+{}'.format(self.SQLALCHEMY_DATABASE_URI+'&options=-c%20search_path=account') \
        #     if self.CELERY_BACKEND == 'database' else self.CELERY_BROKER_URL
        # self.BROKER_USE_SSL = self.CELERY_BROKER_URL.startswith('redis://')

        # print(self.CELERY_BROKER_URL)
        # print(self.CELERY_BACKEND)
        # print(self.CELERY_RESULT_BACKEND)
        # print(self.BROKER_USE_SSL)


        # ------------------------
        # Redis Configurations.
        # ------------------------
        self.REDIS_HOST = get_env('REDIS_HOST')
        self.REDIS_PORT = get_env('REDIS_PORT')
        self.REDIS_USERNAME = get_env('REDIS_USERNAME')
        self.REDIS_PASSWORD = get_env('REDIS_PASSWORD')
        self.REDIS_DB = get_env('REDIS_DB')
        self.REDIS_USE_SSL = get_bool_env('REDIS_USE_SSL')

        # ------------------------
        # Mail Configurations.
        # ------------------------
        self.MAIL_TYPE = get_env('MAIL_TYPE')
        self.MAIL_DEFAULT_SEND_FROM = get_env('MAIL_DEFAULT_SEND_FROM')
        self.RESEND_API_KEY = get_env('RESEND_API_KEY')
        self.RESEND_API_URL = get_env('RESEND_API_URL')
        # SMTP settings
        self.SMTP_SERVER = get_env('SMTP_SERVER')
        self.SMTP_PORT = get_env('SMTP_PORT')
        self.SMTP_USERNAME = get_env('SMTP_USERNAME')
        self.SMTP_PASSWORD = get_env('SMTP_PASSWORD')
        self.SMTP_USE_TLS = get_bool_env('SMTP_USE_TLS')

        # self.INVITE_EXPIRY_HOURS = get_env('INVITE_EXPIRY_HOURS')

        self.TENCENT_SECRET_ID = get_env('TENCENT_SECRET_ID')
        self.TENCENT_SECRET_KEY = get_env('TENCENT_SECRET_KEY')
        self.TENCENT_SMS_SDK_APP_ID = get_env('TENCENT_SMS_SDK_APP_ID')
        self.TENCENT_SMS_TEMPLATE_ID = get_env('TENCENT_SMS_TEMPLATE_ID')
        self.TENCENT_SMS_SIGNNAME = get_env('TENCENT_SMS_SIGNNAME')
        self.TENCENT_SMS_TIMEOUT = get_env('TENCENT_SMS_TIMEOUT')

        # Cloud OAuth2 configurations
        self.WECHAT_CLIENT_ID = get_env('WECHAT_CLIENT_ID')
        self.WECHAT_CLIENT_SECRET = get_env('WECHAT_CLIENT_SECRET')

        # WeChat OAuth - # WeChat Mini Program OAuth
        self.WECHAT_APP_ID = get_env('WECHAT_APP_ID')
        self.WECHAT_APP_SECRET = get_env('WECHAT_APP_SECRET')

        self.DIFY_INNER_API_KEY = get_env('DIFY_INNER_API_KEY') # Maybe we can delete it
        self.DIFY_ADMIN_API_KEY = get_env('DIFY_ADMIN_API_KEY')
        self.DIFY_API_URL = get_env('DIFY_API_URL')

        self.INIT_PASSWORD = get_env('INIT_PASSWORD')





