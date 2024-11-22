#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2023/3/16 14:09
"""

from flask import Blueprint, request, url_for, redirect, session
from common.helpers.application_context import ApplicationContext
from controllers.response_helper import Result
from lib.session import SessionService, IDTrustService
from config import conf

sessions = Blueprint('sessions', __name__)


@sessions.route('/idtrust', methods=['GET'])
def idtrust_auth():
    """
    idtrust认证
    ---
    tags:
      - 会话管理
    responses:
      200:
        res: 结果
    """
    state = IDTrustService.gen_state()
    session['state'] = state
    real_host = IDTrustService.get_real_host(request)
    redirect_uri = '{}{}'.format(
        conf.get('redirect_url'),
        url_for('sessions.idtrust_callback')
    )
    redirect_url = IDTrustService.get_redirect_url(redirect_uri, state, real_host)
    return redirect(redirect_url)


@sessions.route('/idtrust_callback', methods=['GET'])
def idtrust_callback():
    """
    认证回调
    ---
    tags:
      - 会话管理
    responses:
      200:
        res: 结果
    """
    code = request.args.get('code')
    state = request.args.get('state')
    real_host = IDTrustService.get_real_host(request)
    redirect_uri = '{}{}'.format(
        conf.get('redirect_url'),
        url_for('sessions.idtrust_callback')
    )
    session_state = session.get('state')
    # 临时放开登录
    if code:
        user = IDTrustService.idt_callback_login(code, state, session_state, redirect_uri, real_host)
        redirect_url = conf.get('redirect_url')
        if user:
            ApplicationContext.update_session_user(user)
            session["sid"] = request.cookies.get("sessionId")
            return redirect(redirect_url)
        else:
            return redirect(redirect_url)
    return Result.fail(message='无效调用')


@sessions.route('/logout', methods=['GET'])
def logout():
    """
    登出
    ---
    tags:
      - 会话管理
    responses:
      200:
        res: 结果
    """
    SessionService.logout()
    return Result.success(message='登出成功')
