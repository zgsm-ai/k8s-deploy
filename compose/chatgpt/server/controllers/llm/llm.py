#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request

from controllers.response_helper import Result
from services.llm.llm_service import LLMService

llm = Blueprint('llm', __name__)


@llm.route('/list', methods=['GET'])
def list():
    """
    列举LLM
    ---
    tags:
      - LLM
    responses:
      200:
        res: 结果
    """
    kwargs = request.args.to_dict()
    result = LLMService.list(**kwargs)
    return Result.success(message='Successfully', data=result)
