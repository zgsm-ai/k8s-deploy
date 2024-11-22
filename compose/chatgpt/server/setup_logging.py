#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    设置日志模块配置

    :作者: 苏德利 16646
    :时间: 2023/3/29 9:44
    :修改者: 苏德利 16646
    :更新时间: 2023/3/29 9:44
"""

import os
import logging
import logging.config
import yaml


def setup_logging(default_path='config/logging.yml',
                  default_level=logging.INFO,
                  env_key='LOG_CFG'):
    """
    Setup logging configuration
    :param default_path:
    :param default_level:
    :param env_key:
    :return:
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        config = yaml.safe_load(open(path))
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
    # 隐藏掉不第3方包的无用的日志打印
    pydantic_spec_logger = logging.getLogger('flask_pydantic_spec.config')
    pydantic_spec_logger.setLevel(logging.ERROR)
