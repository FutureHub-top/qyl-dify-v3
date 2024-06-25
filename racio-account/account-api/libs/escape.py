from functools import wraps
from html import escape

from flask import request


def escape_parameters(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        # 转义查询字符串参数
        for key, value in request.args.items():
            if isinstance(value, str):
                request.args[key] = escape(value)

        # 转义表单数据参数
        for key, value in request.form.items():
            if isinstance(value, str):
                request.form[key] = escape(value)

        # 调用原始函数
        return func(*args, **kwargs)

    return wrapped_function