#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/8/6 12:33
"""
from tests.mock.mock_e2e_context import context_dict
from services.ai_e2e.e2e_context import ContextCutter


def test_cut_context():
    cutter = ContextCutter(1, **context_dict)
    associated_keywords, associated_steps, associated_cli, associated_api, _ = cutter.cut_context()
    assert len(associated_keywords) == 5
    assert len(associated_steps) == 8
    assert len(associated_cli) == 15
    assert len(associated_api) == 0
