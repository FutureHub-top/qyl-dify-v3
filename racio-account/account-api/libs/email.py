import logging
import threading
import time

import click
from flask import current_app, render_template
from extensions.ext_mail import mail


def send_invite_member_mail(language: str, to: str, token: str, inviter_name: str, tenant_name: str):
    """
    Async Send invite member mail
    :param language
    :param to
    :param token
    :param inviter_name

    Usage: send_invite_member_mail(langauge, to, token, inviter_name)
    """
    if not mail.is_inited():
        return
    logging.info(click.style('Start send invite member mail to {}'.format(to),
                             fg='green'))
    start_at = time.perf_counter()

    # send invite member mail using different languages
    try:
        url = f'{current_app.config.get("CONSOLE_WEB_URL")}/account/activate?token={token}'
        if language == 'zh-Hans':
            html_content = render_template('invite_member_mail_template_zh-CN.html',
                                           to=to,
                                           tenant_name=tenant_name,
                                           url=url)
            threading.Thread(target=mail.send,
                             args=(to, "立即加入", html_content)).start()
            # mail.send(to=to, subject="立即加入", html=html_content)
        else:
            html_content = render_template('invite_member_mail_template_en-US.html',
                                           to=to,
                                           inviter_name=inviter_name,
                                           url=url)
            threading.Thread(target=mail.send,
                             args=(to, "Join", html_content)).start()
            # mail.send(to=to, subject="Join", html=html_content)


        end_at = time.perf_counter()
        logging.info(
            click.style('Send invite member mail to {} succeeded: latency: {}'.format(to, end_at - start_at),
                        fg='green'))
    except Exception:
        logging.exception("Send invite member mail to {} failed".format(to))