#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request
from controllers.response_helper import Result
from services.model_service import ModelService

model = Blueprint('model', __name__)


@model.route('/list', methods=['GET'])
def list():
    """
    列举模型
    ---
    tags:
      - LLM
    responses:
      200:
        res: 结果
    """
    kwargs = request.args.to_dict()
    result = ModelService.list(**kwargs)
    return Result.success(message='Successfully', data=result)
